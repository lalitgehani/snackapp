"""The App object: pages, actions, auth, and the ASGI mount."""

from __future__ import annotations

import inspect
import re
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Cookie, FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from snackapp import ui
from snackapp.exceptions import DuplicateRouteError, ValidationError
from snackapp.fields.registry import serialize_registry
from snackapp.schema import CollectionDef, Schema

STATIC = Path(__file__).parent / "static"


@dataclass
class Page:
    path: str
    fn: Callable[..., Any]
    title: str
    nav: bool
    icon: str | None
    regex: re.Pattern[str]
    params: list[str]
    order: int = 0
    public: bool = False
    command: bool = False


def _compile_path(path: str) -> tuple[re.Pattern[str], list[str]]:
    params = re.findall(r"\{(\w+)\}", path)
    pattern = "^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path) + "$"
    return re.compile(pattern), params


def route_specificity(path: str) -> tuple[int, int]:
    """Static segments beat parameterised ones; longer paths first."""
    return (path.count("{"), -len(path))


class Ctx:
    def __init__(self, app: App, client: Any, user: dict[str, Any], query: dict[str, str]) -> None:
        self.app = app
        self.db = client
        self.user = user
        self.query = query
        self._refresh: list[str] = []
        self._reads: dict[str, set[str]] = {}
        self._page_reads: set[str] = set()
        self._wrote: set[str] = set()
        self._redirect: str | None = None
        self._toast: str | None = None

    def refresh(self, *fragments: str) -> None:
        self._refresh.extend(fragments)

    def go(self, path: str) -> None:
        self._redirect = path

    def toast(self, msg: str) -> None:
        self._toast = msg


class Table:
    def __init__(self, cd: CollectionDef, ctx_getter: Callable[[], Ctx]) -> None:
        self.cd = cd
        self.name = cd.name
        self._ctx = ctx_getter

    @property
    def db(self) -> Any:
        return self._ctx().db

    def _read(self) -> None:
        ctx = self._ctx()
        ctx._page_reads.add(self.name)
        for frag in ui.active_fragments():
            ctx._reads.setdefault(frag, set()).add(self.name)

    def _write(self) -> None:
        self._ctx()._wrote.add(self.name)

    def list(self, **params: Any) -> list[dict[str, Any]]:
        self._read()
        payload = _run(self.db.list(self.name, **params))
        if isinstance(payload, dict):
            return list(payload.get("items") or payload.get("data") or [])
        return list(payload or [])

    def get(self, rid: str, expand: str | None = None) -> dict[str, Any]:
        self._read()
        return _run(self.db.get(self.name, rid, expand=expand))

    def create(self, **data: Any) -> dict[str, Any]:
        self._write()
        return _run(self.db.create(self.name, data))

    def update(self, rid: str, **data: Any) -> dict[str, Any]:
        self._write()
        return _run(self.db.update(self.name, rid, data))

    def delete(self, rid: str) -> None:
        self._write()
        _run(self.db.delete(self.name, rid))

    def aggregate(self, **params: Any) -> dict[str, Any]:
        self._read()
        return _run(self.db.aggregate(self.name, **params))

    def count(self, filter: str | None = None) -> int:
        self._read()
        payload = _run(self.db.list(self.name, filter=filter, limit=1))
        if isinstance(payload, dict):
            return int(payload.get("total") or 0)
        return 0


def _run(result: Any) -> Any:
    import asyncio

    if asyncio.iscoroutine(result):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(result)
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, result).result()
    return result


def intersecting_fragments(
    reads: dict[str, set[str]], wrote: set[str], page_reads: set[str]
) -> list[str]:
    """Fragments whose recorded reads intersect the action's wrote set."""
    out: list[str] = []
    for name, deps in reads.items():
        target = deps if deps else page_reads
        if target & wrote:
            out.append(name)
    return sorted(out)


class App:
    def __init__(self, title: str, account: str | None = None) -> None:
        self.title = title
        self.account = account
        self.schema = Schema()
        self.base_path = ""
        self.pages: list[Page] = []
        self.actions: dict[str, Callable[..., Any]] = {}
        import contextvars

        self._ctx_var: contextvars.ContextVar[Ctx] = contextvars.ContextVar("sa_ctx")
        self._host: FastAPI | None = None

    def collection(self, name: str, *fields: dict[str, Any], **kw: Any) -> Table:
        cd = self.schema.collection(name, *fields, **kw)
        return Table(cd, lambda: self._ctx_var.get())

    def page(
        self,
        path: str,
        title: str = "",
        nav: bool = False,
        icon: str | None = None,
        order: int = 0,
        public: bool = False,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
            existing = [p for p in self.pages if p.path == path]
            if existing:
                raise DuplicateRouteError(
                    f"duplicate route {path!r}: {existing[0].fn.__module__} and {fn.__module__}"
                )
            rx, params = _compile_path(path)
            self.pages.append(
                Page(
                    path,
                    fn,
                    title or fn.__name__,
                    nav,
                    icon,
                    rx,
                    params,
                    order,
                    public,
                )
            )
            self.pages.sort(key=lambda p: route_specificity(p.path))
            return fn

        return deco

    def autodiscover(
        self,
        pages: str | Path = "pages",
        actions: str | Path | None = "actions",
        base: str | Path | None = None,
    ) -> dict[str, list[str]]:
        from snackapp.discovery import load_package

        root = Path(base) if base else Path(self._caller_dir())
        out = {"pages": load_package(self, root / Path(pages), "pages")}
        if actions:
            out["actions"] = load_package(self, root / Path(actions), "actions")
        self.pages.sort(key=lambda p: route_specificity(p.path))
        return out

    @staticmethod
    def _caller_dir() -> str:
        for frame in inspect.stack():
            f = frame.filename
            if "snackapp/" not in f and not f.startswith("<"):
                return str(Path(f).resolve().parent)
        return str(Path.cwd())

    def action(
        self, fn: Callable[..., Any] | None = None, *, command: bool = False
    ) -> Callable[..., Any]:
        def deco(func: Callable[..., Any]) -> Callable[..., Any]:
            setattr(func, "command", command)
            self.actions[func.__name__] = func
            return func

        if fn is None:
            return deco  # type: ignore[return-value]
        return deco(fn)

    def _client_for(self, token: str | None) -> Any:
        from snackbase.embedded import create_client
        from snackbase.infrastructure.api.app import app as host

        return create_client(app=self._host or host, token=token, account=self.account)

    def _match(self, path: str) -> tuple[Page, dict[str, str]] | None:
        for page in self.pages:
            matched = page.regex.match(path)
            if matched:
                return page, matched.groupdict()
        return None

    def _render(self, ctx: Ctx, page: Page, params: dict[str, str]) -> dict[str, Any]:
        root, token = ui.new_tree()
        tok2 = self._ctx_var.set(ctx)
        try:
            sig = inspect.signature(page.fn).parameters
            kwargs: dict[str, Any] = {k: v for k, v in params.items() if k in sig}
            if "ctx" in sig:
                kwargs["ctx"] = ctx
            page.fn(**kwargs)
        finally:
            ui.end_tree(token)
            self._ctx_var.reset(tok2)

        def stamp(node: dict[str, Any]) -> None:
            if node.get("kind") == "fragment":
                own = ctx._reads.get(node["name"])
                node["deps"] = sorted(own if own else ctx._page_reads)
            for child in node.get("children", []):
                stamp(child)

        stamp(root)
        return root

    def nav_items(self) -> list[dict[str, Any]]:
        items = [p for p in self.pages if p.nav]
        items.sort(key=lambda p: (p.order, p.title))
        return [{"path": p.path, "title": p.title, "icon": p.icon} for p in items]

    def router(self, at: str = "") -> APIRouter:
        r = APIRouter(prefix=f"{at}/_sa")

        @r.post("/login")
        async def login(request: Request) -> Response:
            body = await request.json()
            client = self._client_for(None)
            try:
                payload = await client.request(
                    "POST",
                    "/api/v1/auth/login",
                    json={
                        "email": body["email"],
                        "password": body["password"],
                        "account": body.get("account") or self.account,
                    },
                )
            except Exception as exc:
                status = getattr(exc, "status_code", 401)
                return JSONResponse({"error": str(exc)}, status_code=int(status) or 401)
            token = payload.get("token") or payload.get("access_token")
            resp = JSONResponse({"ok": True})
            resp.set_cookie(
                "sa_token",
                token,
                httponly=True,
                samesite="lax",
                path="/",
            )
            return resp

        @r.post("/logout")
        async def logout() -> Response:
            resp = JSONResponse({"ok": True})
            resp.delete_cookie("sa_token", path="/")
            return resp

        @r.get("/meta")
        async def meta(sa_token: str | None = Cookie(default=None)) -> dict[str, Any]:
            out: dict[str, Any] = {
                "title": self.title,
                "nav": self.nav_items(),
                "user": None,
                "fields": serialize_registry(),
                "single_account": True,
            }
            if sa_token:
                try:
                    user = await self._client_for(sa_token).me()
                    out["user"] = user
                except Exception:
                    pass
            return out

        @r.get("/view")
        async def view(
            path: str,
            request: Request,
            sa_token: str | None = Cookie(default=None),
        ) -> Any:
            hit = self._match(path)
            if not hit:
                return JSONResponse({"error": f"no page for {path}"}, status_code=404)
            page, params = hit
            if not page.public and not sa_token:
                return JSONResponse({"error": "auth"}, status_code=401)
            client = self._client_for(sa_token)
            user: dict[str, Any] = {}
            if sa_token:
                try:
                    user = await client.me()
                except Exception:
                    if not page.public:
                        return JSONResponse({"error": "auth"}, status_code=401)
            query = dict(request.query_params)
            query.pop("path", None)
            ctx = Ctx(self, client, user, query)
            try:
                tree = await run_in_threadpool(self._render, ctx, page, params)
            except Exception as exc:
                return JSONResponse(
                    {
                        "error": "render",
                        "detail": str(exc),
                        "trace": traceback.format_exc()[-1500:],
                    },
                    status_code=200,
                )
            return {"title": page.title, "tree": tree, "user": user}

        @r.post("/action/{name}")
        async def run_action(
            name: str,
            request: Request,
            sa_token: str | None = Cookie(default=None),
        ) -> Any:
            if not sa_token:
                return JSONResponse({"error": "auth"}, status_code=401)
            fn = self.actions.get(name)
            if not fn:
                return JSONResponse({"error": f"no action {name}"}, status_code=404)
            client = self._client_for(sa_token)
            body = await request.json()
            user = await client.me()
            ctx = Ctx(self, client, user, {})
            sig = inspect.signature(fn)
            params_ = sig.parameters
            has_kwargs = any(
                p.kind is inspect.Parameter.VAR_KEYWORD for p in params_.values()
            )
            kwargs = {k: v for k, v in body.items() if has_kwargs or k in params_}
            kwargs.pop("ctx", None)
            if "ctx" in params_:
                kwargs["ctx"] = ctx

            def _call() -> None:
                tok = self._ctx_var.set(ctx)
                try:
                    fn(**kwargs)
                finally:
                    self._ctx_var.reset(tok)

            try:
                await run_in_threadpool(_call)
            except ValidationError as exc:
                return JSONResponse(
                    {"ok": False, "error": exc.message, "field": exc.field}
                )
            except Exception as exc:
                return JSONResponse({"ok": False, "error": str(exc)})
            auto = intersecting_fragments(ctx._reads, ctx._wrote, ctx._page_reads)
            refresh = list(dict.fromkeys([*ctx._refresh, *auto]))
            return {
                "ok": True,
                "refresh": refresh,
                "wrote": sorted(ctx._wrote),
                "redirect": ctx._redirect,
                "toast": ctx._toast,
            }

        return r

    def mount(self, api: FastAPI, at: str = "") -> FastAPI:
        at = at.rstrip("/")
        self.base_path = at
        self._host = api
        if not at:
            api.router.routes = [
                route for route in api.router.routes if getattr(route, "path", None) != "/"
            ]
        api.include_router(self.router(at))
        if STATIC.exists():
            api.mount(f"{at}/_sa/static", StaticFiles(directory=STATIC), name="sa_static")

        shell = (STATIC / "index.html").read_text() if (STATIC / "index.html").exists() else (
            "<!doctype html><html><body><div id='root'></div>"
            "<script src='/_sa/static/app.js' data-base=''></script></body></html>"
        )
        if "data-base" not in shell:
            shell = shell.replace("<script", f'<script data-base="{at}"', 1)
        if at:
            shell = shell.replace(
                'src="/_sa/static/app.js"',
                f'src="{at}/_sa/static/app.js" data-base="{at}"',
            )

        @api.api_route(at + "/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
        async def spa(full_path: str) -> Response:
            if full_path.startswith(("api/", "_sa/")):
                return JSONResponse({"error": "not found"}, status_code=404)
            return HTMLResponse(
                shell,
                headers={"Cache-Control": "no-store"},
            )

        if at:
            @api.api_route(at, methods=["GET", "HEAD"], include_in_schema=False)
            async def spa_root() -> Response:
                return HTMLResponse(shell, headers={"Cache-Control": "no-store"})

        return api

    def fastapi(self, at: str = "") -> FastAPI:
        from snackbase.infrastructure.api.app import create_app

        return self.mount(create_app(), at=at)
