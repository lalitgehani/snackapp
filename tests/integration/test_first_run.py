"""Drive init_database + schema apply from a directory with no alembic.ini."""

import json

import pytest
from sqlalchemy import select

from snackapp.app import App
from snackapp.provision import apply_runtime_env, provision_first_user
from snackapp.schema import Field
from snackapp.schema_sync import apply_schema


@pytest.mark.asyncio
async def test_init_database_and_schema_from_clean_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SNACKBASE_ALEMBIC_INI", raising=False)
    apply_runtime_env(tmp_path)

    from snackbase.infrastructure.persistence.database import get_db_manager, init_database
    from snackbase.infrastructure.persistence.models import CollectionModel

    await init_database()
    creds = await provision_first_user(tmp_path)
    assert creds is not None
    assert creds["email"] == "admin@example.com"

    app = App("Demo")
    app.collection("items", Field.text("name", required=True), access="team")
    plan = await apply_schema(app, confirm=False)
    assert any(item["collection"] == "items" for item in plan["added"])

    db = get_db_manager()
    async with db.session() as session:
        rows = (await session.execute(select(CollectionModel))).scalars().all()
        names = {row.name for row in rows}
        assert "items" in names
        schema = json.loads(next(row.schema for row in rows if row.name == "items"))
        assert any(field["name"] == "name" for field in schema)

    again = await apply_schema(app, confirm=False)
    assert again["added"] == []
    assert again["changed"] == []
    assert again["removed"] == []

    from snackapp import ui

    @app.page("/", public=True, title="Home")
    def home():
        ui.header("Home")

    @app.page("/private", title="Private")
    def private():
        ui.header("Secret")

    from httpx import ASGITransport, AsyncClient

    asgi = app.fastapi()
    transport = ASGITransport(app=asgi)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        spa = await client.get("/")
        assert spa.status_code == 200
        assert b"root" in spa.content
        view = await client.get("/_sa/view", params={"path": "/"})
        assert view.status_code == 200
        body = view.json()
        assert body["tree"]["kind"] == "page"
        denied = await client.get("/_sa/view", params={"path": "/private"})
        assert denied.status_code == 401
        login = await client.post(
            "/_sa/login",
            json={
                "email": creds["email"],
                "password": creds["password"],
                "account": creds["account"],
            },
        )
        assert login.status_code == 200, login.text
        assert "sa_token" in login.cookies
        authed = await client.get("/_sa/view", params={"path": "/private"})
        assert authed.status_code == 200, authed.text
        assert authed.json()["tree"]["kind"] == "page"
