"""CRM clone isolation: zero overlapping ids; favorites are per-user."""

from __future__ import annotations

import importlib.util
import uuid
from datetime import UTC, datetime
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from snackapp.app import App
from snackapp.provision import apply_runtime_env, generate_password, provision_first_user
from snackapp.schema_sync import apply_schema

ROOT = Path(__file__).resolve().parents[2] / "examples" / "crm"
COLLECTIONS = (
    "companies",
    "people",
    "opportunities",
    "notes",
    "tasks",
    "attachments",
    "activities",
    "favorites",
)


def _models():
    spec = importlib.util.spec_from_file_location("crm_models_iso", ROOT / "models.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _crm_app() -> App:
    models = _models()
    app = App("SnackCRM")
    app.collection("companies", *models.COMPANIES, access="team")
    app.collection("people", *models.PEOPLE, access="team")
    app.collection("opportunities", *models.OPPORTUNITIES, access="team")
    app.collection("notes", *models.NOTES, access="team")
    app.collection("tasks", *models.TASKS, access="team")
    app.collection("attachments", *models.ATTACHMENTS, access="team")
    app.collection("activities", *models.ACTIVITIES, access="team")
    app.collection("favorites", *models.FAVORITES, access="private")
    return app


def _payload(collection: str, owner_id: str | None = None) -> dict:
    if collection == "companies":
        return {"name": f"Co {uuid.uuid4().hex[:8]}"}
    if collection == "people":
        return {"name": {"first": "Ada", "last": "Lovelace"}}
    if collection == "opportunities":
        return {"name": f"Opp {uuid.uuid4().hex[:8]}", "stage": "lead"}
    if collection == "notes":
        return {"body": {"doc": "note"}}
    if collection == "tasks":
        return {"title": f"Task {uuid.uuid4().hex[:8]}"}
    if collection == "attachments":
        return {"tags": ["a"]}
    if collection == "activities":
        return {"summary": "created"}
    if collection == "favorites":
        body: dict = {"pinned": True}
        if owner_id:
            body["owner"] = owner_id
        return body
    raise AssertionError(collection)


async def _login(client: AsyncClient, creds: dict[str, str]) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": creds["email"],
            "password": creds["password"],
            "account": creds["account"],
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    token = payload.get("token") or payload.get("access_token")
    assert token
    return str(token)


async def _ids(client: AsyncClient, token: str, collection: str) -> set[str]:
    response = await client.get(
        f"/api/v1/records/{collection}",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 100},
    )
    assert response.status_code == 200, response.text
    items = response.json().get("items") or response.json().get("data") or []
    return {str(item["id"]) for item in items}


async def _create_user(account_id: str, email: str) -> dict[str, str]:
    from snackbase.domain.services.account_service import AccountService
    from snackbase.infrastructure.auth.password_hasher import hash_password
    from snackbase.infrastructure.persistence.database import get_db_manager
    from snackbase.infrastructure.persistence.models import AccountModel, RoleModel, UserModel
    from sqlalchemy import select

    password = generate_password()
    db = get_db_manager()
    async with db.session() as session:
        if account_id == "new":
            account = await AccountService(session).create_account("Other")
        else:
            account = (
                await session.execute(select(AccountModel).where(AccountModel.id == account_id))
            ).scalar_one()
        role = (
            await session.execute(select(RoleModel).where(RoleModel.name == "admin"))
        ).scalar_one()
        user = UserModel(
            id=str(uuid.uuid4()),
            email=email,
            account_id=account.id,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            email_verified=True,
            email_verified_at=datetime.now(UTC),
        )
        session.add(user)
        await session.commit()
        return {
            "account": account.account_code,
            "email": email,
            "password": password,
            "id": user.id,
            "account_id": account.id,
        }


def test_crm_accounts_share_zero_ids_and_favorites_are_per_user(tmp_path, monkeypatch):
    import asyncio

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SNACKBASE_ALEMBIC_INI", raising=False)
    monkeypatch.delenv("SNACKBASE_DATABASE_URL", raising=False)
    apply_runtime_env(tmp_path)

    asyncio.run(_crm_isolation_body(tmp_path))


async def _crm_isolation_body(tmp_path) -> None:
    from snackbase.infrastructure.persistence.database import init_database

    await init_database()
    primary = await provision_first_user(tmp_path)
    assert primary is not None

    app = _crm_app()
    await apply_schema(app, confirm=False)
    asgi = app.fastapi()
    transport = ASGITransport(app=asgi)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a = await _login(client, primary)
        me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        assert me.status_code == 200, me.text
        user_a = me.json()
        owner_a = user_a.get("id") or user_a.get("user_id")
        account_id = user_a.get("account_id")
        assert account_id

        created_a: dict[str, str] = {}
        for name in COLLECTIONS:
            response = await client.post(
                f"/api/v1/records/{name}",
                headers={"Authorization": f"Bearer {token_a}"},
                json=_payload(name, owner_a),
            )
            assert response.status_code in (200, 201), (name, response.text)
            created_a[name] = response.json()["id"]

        other = await _create_user("new", "other@example.com")
        token_b = await _login(client, other)
        me_b = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
        owner_b = me_b.json().get("id") or me_b.json().get("user_id")
        created_b: dict[str, str] = {}
        for name in COLLECTIONS:
            response = await client.post(
                f"/api/v1/records/{name}",
                headers={"Authorization": f"Bearer {token_b}"},
                json=_payload(name, owner_b),
            )
            assert response.status_code in (200, 201), (name, response.text)
            created_b[name] = response.json()["id"]

        overlap: dict[str, set[str]] = {}
        for name in COLLECTIONS:
            ids_a = await _ids(client, token_a, name)
            ids_b = await _ids(client, token_b, name)
            shared = ids_a & ids_b
            overlap[name] = shared
            assert created_a[name] in ids_a
            assert created_b[name] in ids_b
            assert created_a[name] not in ids_b
            assert created_b[name] not in ids_a
        assert all(len(v) == 0 for v in overlap.values()), overlap

        teammate = await _create_user(account_id, "teammate@example.com")
        teammate["account"] = primary["account"]
        token_t = await _login(client, teammate)
        favs_t = await _ids(client, token_t, "favorites")
        assert created_a["favorites"] not in favs_t
        favs_a = await _ids(client, token_a, "favorites")
        assert created_a["favorites"] in favs_a
