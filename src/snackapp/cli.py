"""Console script for SnackApp."""

from __future__ import annotations

import importlib.util
import os
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Any

import click

from snackapp.config import resolve
from snackapp.exceptions import DestructiveChangeError, UnknownRevisionError

INIT_APP = '''from snackapp import App, Field

app = App("Demo")
items = app.collection(
    "items",
    Field.text("name", required=True),
    access="team",
)
'''

INIT_MODELS = '''from snackapp import Field
'''

INIT_PAGE = '''from snackapp import page, ui


@page("/", title="Home", nav=True)
def index():
    ui.header("Home")
    ui.text("Edit pages/index.py to get started.")
'''


@click.group(invoke_without_command=True)
@click.version_option(version=version("snackapp"), prog_name="snackapp")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """SnackApp — Python apps with SnackBase embedded."""
    if ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        click.echo(ctx.get_help())


def main() -> None:
    cli(standalone_mode=True)


@cli.command()
@click.argument("name")
def init(name: str) -> None:
    """Scaffold a new SnackApp project."""
    root = Path(name)
    if root.exists() and any(root.iterdir()):
        raise click.ClickException(f"{name} is not empty")
    (root / "pages").mkdir(parents=True)
    (root / "app.py").write_text(INIT_APP)
    (root / "models.py").write_text(INIT_MODELS)
    (root / "pages" / "index.py").write_text(INIT_PAGE)
    (root / ".gitignore").write_text(".snackapp/\n")
    (root / "snackapp.toml").write_text("port = 8000\n")
    click.echo(f"Created {name}. Next: cd {name} && snackapp run")


@cli.command()
@click.option("--port", type=int, default=None)
@click.option("--host", type=str, default=None)
@click.option("--reload", is_flag=True, default=False)
def run(port: int | None, host: str | None, reload: bool) -> None:
    """Start the embedded SnackBase + application process."""
    import asyncio

    import uvicorn

    from snackapp.provision import apply_runtime_env, provision_first_user

    settings = resolve(cli={"port": port, "host": host, "reload": reload or None})
    apply_runtime_env()
    os.environ["SNACKAPP_ADMIN"] = settings.admin
    if settings.backend_url:
        os.environ["SNACKAPP_BACKEND_URL"] = settings.backend_url

    app_obj = _load_app()
    asgi = app_obj.fastapi()

    async def _boot() -> None:
        from snackbase.infrastructure.persistence.database import init_database

        await init_database()
        creds = await provision_first_user()
        if creds:
            click.echo(
                "First run credentials (shown once):\n"
                f"  account:  {creds['account']}\n"
                f"  email:    {creds['email']}\n"
                f"  password: {creds['password']}"
            )
        _sync_schema(app_obj, confirm=False)

    try:
        asyncio.run(_boot())
    except UnknownRevisionError as exc:
        raise SystemExit(str(exc)) from exc
    except DestructiveChangeError as exc:
        raise SystemExit(str(exc)) from exc

    uvicorn.run(
        asgi,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )


@cli.command()
def routes() -> None:
    """Print the resolved route table."""
    app_obj = _load_app()
    for page in app_obj.pages:
        click.echo(f"{page.path:20} {page.fn.__module__}")


@cli.command()
@click.option("--plan", is_flag=True, default=False)
@click.option("--confirm", is_flag=True, default=False)
def migrate(plan: bool, confirm: bool) -> None:
    """Plan or apply schema migrations."""
    from snackapp.provision import apply_runtime_env

    apply_runtime_env()
    app_obj = _load_app()
    if plan:
        diff = _plan_schema(app_obj)
        click.echo(diff)
        return
    _sync_schema(app_obj, confirm=confirm)


def _load_app() -> Any:
    path = Path("app.py")
    if not path.exists():
        raise click.ClickException("no app.py in the current directory")
    spec = importlib.util.spec_from_file_location("user_app", path)
    if spec is None or spec.loader is None:
        raise click.ClickException("cannot load app.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["user_app"] = module
    spec.loader.exec_module(module)
    app_obj = getattr(module, "app", None)
    if app_obj is None:
        raise click.ClickException("app.py must define `app = App(...)`")
    pages = Path("pages")
    if pages.exists():
        app_obj.autodiscover(pages="pages", actions="actions" if Path("actions").exists() else None)
    return app_obj


def _plan_schema(app_obj: Any) -> dict[str, Any]:
    import asyncio
    import json

    from snackbase.domain.services.schema_diff import diff_collection_schemas
    from snackbase.infrastructure.persistence.database import get_db_manager
    from snackbase.infrastructure.persistence.models import CollectionModel

    async def _load() -> dict[str, list[dict[str, Any]]]:
        db = get_db_manager()
        async with db.session() as session:
            from sqlalchemy import select

            rows = (await session.execute(select(CollectionModel))).scalars().all()
            return {row.name: json.loads(row.schema) for row in rows}

    current = asyncio.run(_load())
    declared = {
        item["name"]: item["schema"] for item in app_obj.schema.declared_payload()
    }
    return diff_collection_schemas(current, declared).to_dict()


def _sync_schema(app_obj: Any, *, confirm: bool) -> None:
    plan = _plan_schema(app_obj)
    destructive = any(
        item.get("destructive")
        for item in (*plan["added"], *plan["removed"], *plan["changed"])
    )
    if not plan["added"] and not plan["removed"] and not plan["changed"]:
        return
    if destructive and not confirm:
        changed = plan["changed"][0] if plan["changed"] else plan["removed"][0]
        raise DestructiveChangeError(
            f"Destructive change on {changed.get('collection')}.{changed.get('field')}; "
            "run `snackapp migrate --confirm`"
        )
    # Application of the plan is performed by the SnackBase generate endpoint
    # once a superadmin token is available; non-destructive field adds go
    # through collection update on first authenticated boot.
