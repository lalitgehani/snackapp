"""Per-type validation running before a write."""

from __future__ import annotations

import re
from typing import Any

from snackapp.exceptions import ValidationError
from snackapp.fields.registry import get_spec

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_value(field_type: str, value: Any, *, required: bool = False, **opts: Any) -> Any:
    spec = get_spec(field_type)
    if value is None or value == "":
        if required:
            raise ValidationError("this field is required")
        return None
    serialized = spec.serialize(value)
    if field_type == "email" and not _EMAIL.match(str(serialized)):
        raise ValidationError("malformed email")
    if field_type == "number" and not isinstance(serialized, (int, float)):
        raise ValidationError("expected a number")
    if field_type == "rating":
        maximum = int(opts.get("max", 5))
        if not isinstance(serialized, (int, float)) or serialized < 0 or serialized > maximum:
            raise ValidationError(f"rating must be between 0 and {maximum}")
    if field_type == "currency":
        minimum = opts.get("min")
        if minimum is not None and serialized["amount"] < minimum:
            raise ValidationError(f"amount must be at least {minimum}")
    return serialized


def writable_fields(schema: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [f for f in schema if f.get("type") != "computed" and f.get("semantic") != "computed"]


def map_backend_errors(payload: Any) -> dict[str, str]:
    """Map a SnackBase 400 ``details`` array onto ``{field: message}``."""
    out: dict[str, str] = {}
    details = payload
    if isinstance(payload, dict):
        details = payload.get("details") or payload.get("error") or payload
    if isinstance(details, list):
        for item in details:
            if isinstance(item, dict) and item.get("field"):
                out[str(item["field"])] = str(item.get("message") or "invalid")
    return out
