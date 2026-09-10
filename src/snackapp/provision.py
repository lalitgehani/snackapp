"""First-run account/user provisioning and secret handling."""

from __future__ import annotations

import os
import secrets
import stat
from pathlib import Path

MARKER = "provisioned"


def instance_dir(root: Path | None = None) -> Path:
    return (root or Path.cwd()) / ".snackapp"


def secret_path(root: Path | None = None) -> Path:
    return instance_dir(root) / "secret.key"


def ensure_secret(root: Path | None = None) -> str:
    path = secret_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    (path.parent / "migrations").mkdir(parents=True, exist_ok=True)
    (path.parent / "files").mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path.read_text().strip()
    value = secrets.token_hex(32)
    path.write_text(value)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    return value


def apply_runtime_env(root: Path | None = None) -> Path:
    """Point SnackBase at this project's .snackapp directory."""
    base = instance_dir(root)
    base.mkdir(parents=True, exist_ok=True)
    secret = ensure_secret(root)
    os.environ.setdefault("SNACKBASE_SECRET_KEY", secret)
    os.environ.setdefault(
        "SNACKBASE_DATABASE_URL",
        f"sqlite+aiosqlite:///{base / 'snackbase.db'}",
    )
    os.environ.setdefault("SNACKBASE_STORAGE_PATH", str(base / "files"))
    os.environ["SNACKBASE_TEST_DATA_DIR"] = str(base)
    return base


def already_provisioned(root: Path | None = None) -> bool:
    return (instance_dir(root) / MARKER).exists()


def mark_provisioned(root: Path | None = None) -> None:
    (instance_dir(root) / MARKER).write_text("1")


def generate_password() -> str:
    return secrets.token_urlsafe(12)


async def provision_first_user(root: Path | None = None) -> dict[str, str] | None:
    """Create one account and one admin user if the database is empty of app users.

    Superadmin in the system account is not counted. Returns credentials once.
    """
    if already_provisioned(root):
        return None

    from snackbase.domain.services.account_service import AccountService
    from snackbase.infrastructure.auth.password_hasher import hash_password
    from snackbase.infrastructure.persistence.database import get_db_manager
    from snackbase.infrastructure.persistence.models import RoleModel, UserModel
    from sqlalchemy import func, select

    db = get_db_manager()
    async with db.session() as session:
        count = (
            await session.execute(
                select(func.count()).select_from(UserModel).where(
                    UserModel.account_id != "00000000-0000-0000-0000-000000000000"
                )
            )
        ).scalar_one()
        if count:
            mark_provisioned(root)
            return None

        service = AccountService(session)
        account = await service.create_account("SnackApp")
        role = (
            await session.execute(select(RoleModel).where(RoleModel.name == "admin"))
        ).scalar_one()
        password = generate_password()
        email = "admin@local"
        import uuid

        user = UserModel(
            id=str(uuid.uuid4()),
            email=email,
            account_id=account.id,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        mark_provisioned(root)
        return {
            "account": account.account_code,
            "email": email,
            "password": password,
        }
