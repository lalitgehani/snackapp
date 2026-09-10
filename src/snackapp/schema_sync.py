"""Apply a declared SnackApp schema through SnackBase collection APIs."""

from __future__ import annotations

import json
from typing import Any

from snackapp.exceptions import DestructiveChangeError

SYSTEM_ACCOUNT_ID = "00000000-0000-0000-0000-000000000000"


async def current_schemas() -> dict[str, list[dict[str, Any]]]:
    from snackbase.infrastructure.persistence.database import get_db_manager
    from snackbase.infrastructure.persistence.models import CollectionModel
    from sqlalchemy import select

    db = get_db_manager()
    async with db.session() as session:
        rows = (await session.execute(select(CollectionModel))).scalars().all()
        return {row.name: json.loads(row.schema) for row in rows}


def plan_schema(app_obj: Any, current: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    from snackbase.domain.services.schema_diff import diff_collection_schemas

    declared = {cd.name: cd.storage_fields() for cd in app_obj.schema.defs.values()}
    return diff_collection_schemas(current, declared).to_dict()


async def apply_schema(app_obj: Any, *, confirm: bool = False) -> dict[str, Any]:
    """Create missing collections and apply non-destructive field adds.

    Destructive diffs require ``confirm=True`` (``snackapp migrate --confirm``).
    """
    from snackbase.domain.services.collection_service import CollectionService
    from snackbase.domain.services.schema_diff import diff_collection_schemas
    from snackbase.infrastructure.persistence.database import get_db_manager
    from snackbase.infrastructure.persistence.migration_service import (
        MigrationService,
        resolve_alembic_ini,
    )
    from snackbase.infrastructure.persistence.models import CollectionModel, UserModel
    from sqlalchemy import select

    declared = {cd.name: cd.storage_fields() for cd in app_obj.schema.defs.values()}
    db = get_db_manager()
    async with db.session() as session:
        rows = list((await session.execute(select(CollectionModel))).scalars().all())
        current = {row.name: json.loads(row.schema) for row in rows}
        plan = diff_collection_schemas(current, declared)
        if plan.is_empty():
            return plan.to_dict()
        if plan.has_destructive() and not confirm:
            changed = next(
                item
                for item in (*plan.changed, *plan.removed, *plan.added)
                if item.get("destructive")
            )
            raise DestructiveChangeError(
                f"Destructive change on {changed.get('collection')}.{changed.get('field')}; "
                "run `snackapp migrate --confirm`"
            )

        user = (
            await session.execute(
                select(UserModel).where(UserModel.account_id != SYSTEM_ACCOUNT_ID)
            )
        ).scalars().first()
        if user is None:
            user = (await session.execute(select(UserModel))).scalars().first()
        user_id = user.id if user else SYSTEM_ACCOUNT_ID

        service = CollectionService(
            session,
            db.engine,
            migration_service=MigrationService(
                alembic_ini_path=str(resolve_alembic_ini()),
                engine=db.engine,
            ),
        )
        existing = {row.name: row for row in rows}
        for name, schema in declared.items():
            cd = app_obj.schema.defs[name]
            if name not in existing:
                await service.create_collection(
                    name, schema, user_id, rules_data=cd.rule_map()
                )
                continue
            live = {field["name"] for field in current[name]}
            if any(field["name"] not in live for field in schema):
                await service.update_collection_schema(existing[name].id, schema)
        await session.commit()
        return plan.to_dict()
