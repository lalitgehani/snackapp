"""Semantic field-type registry.

Each type maps onto a SnackBase storage type plus serialize/deserialize,
filter operands, sortability, and the renderer name the client switches on.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from snackapp.exceptions import ValidationError

Operand = str

ALL_OPERANDS: tuple[str, ...] = (
    "is",
    "is_not",
    "contains",
    "does_not_contain",
    "is_empty",
    "is_not_empty",
    "gt",
    "gte",
    "lt",
    "lte",
    "is_before",
    "is_after",
    "is_today",
    "is_in_past",
    "is_in_future",
    "is_relative",
    "is_any_of",
)

TEXT_OPS = (
    "is",
    "is_not",
    "contains",
    "does_not_contain",
    "is_empty",
    "is_not_empty",
    "is_any_of",
)
NUMBER_OPS = ("is", "is_not", "gt", "gte", "lt", "lte", "is_empty", "is_not_empty")
DATE_OPS = (
    "is",
    "is_not",
    "is_before",
    "is_after",
    "is_today",
    "is_in_past",
    "is_in_future",
    "is_relative",
    "is_empty",
    "is_not_empty",
)
BOOL_OPS = ("is", "is_not", "is_empty", "is_not_empty")
ARRAY_OPS = ("contains", "does_not_contain", "is_empty", "is_not_empty", "is_any_of")
EQ_OPS = ("is", "is_not", "is_empty", "is_not_empty", "is_any_of")


def _identity(value: Any) -> Any:
    return value


def _require_currency(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or "amount" not in value or "code" not in value:
        raise ValidationError("currency requires {amount, code}")
    return {"amount": value["amount"], "code": value["code"]}


def _require_full_name(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError("full_name requires {first, last}")
    return {"first": value.get("first"), "last": value.get("last")}


def _require_address(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError("address requires an object")
    keys = ("street1", "street2", "city", "region", "postcode", "country")
    return {k: value.get(k) for k in keys}


def _require_multi(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValidationError("expected a list")
    out: list[dict[str, Any]] = []
    seen_primary = False
    for item in value:
        if not isinstance(item, dict) or "value" not in item:
            raise ValidationError("each entry needs a value")
        primary = bool(item.get("primary"))
        if primary:
            if seen_primary:
                item = {**item, "primary": False}
            seen_primary = True
        out.append(
            {
                "value": item["value"],
                "label": item.get("label"),
                "primary": primary and seen_primary,
            }
        )
    if out and not any(i.get("primary") for i in out):
        out[0]["primary"] = True
    return out


@dataclass(frozen=True)
class FieldSpec:
    name: str
    storage: str
    operands: tuple[str, ...]
    sortable: bool
    renderer: str
    serialize: Callable[[Any], Any] = _identity
    deserialize: Callable[[Any], Any] = _identity


FIELD_REGISTRY: dict[str, FieldSpec] = {}


def _reg(spec: FieldSpec) -> FieldSpec:
    FIELD_REGISTRY[spec.name] = spec
    return spec


_reg(FieldSpec("text", "text", TEXT_OPS, True, "text"))
_reg(FieldSpec("long_text", "text", TEXT_OPS, True, "long_text"))
_reg(FieldSpec("rich_text", "json", TEXT_OPS, False, "rich_text"))
_reg(FieldSpec("number", "number", NUMBER_OPS, True, "number"))
_reg(
    FieldSpec(
        "currency",
        "json",
        NUMBER_OPS,
        True,
        "currency",
        serialize=_require_currency,
        deserialize=_require_currency,
    )
)
_reg(FieldSpec("percent", "number", NUMBER_OPS, True, "percent"))
_reg(FieldSpec("rating", "number", NUMBER_OPS, True, "rating"))
_reg(FieldSpec("boolean", "boolean", BOOL_OPS, True, "boolean"))
_reg(FieldSpec("date", "date", DATE_OPS, True, "date"))
_reg(FieldSpec("datetime", "datetime", DATE_OPS, True, "datetime"))
_reg(FieldSpec("select", "text", EQ_OPS, True, "select"))
_reg(FieldSpec("multi_select", "json", ARRAY_OPS, False, "multi_select"))
_reg(FieldSpec("email", "email", TEXT_OPS, True, "email"))
_reg(
    FieldSpec(
        "emails",
        "json",
        ARRAY_OPS,
        False,
        "emails",
        serialize=_require_multi,
        deserialize=_require_multi,
    )
)
_reg(FieldSpec("phone", "text", TEXT_OPS, True, "phone"))
_reg(
    FieldSpec(
        "phones",
        "json",
        ARRAY_OPS,
        False,
        "phones",
        serialize=_require_multi,
        deserialize=_require_multi,
    )
)
_reg(FieldSpec("url", "url", TEXT_OPS, True, "url"))
_reg(
    FieldSpec(
        "links",
        "json",
        ARRAY_OPS,
        False,
        "links",
        serialize=_require_multi,
        deserialize=_require_multi,
    )
)
_reg(
    FieldSpec(
        "full_name",
        "json",
        TEXT_OPS,
        True,
        "full_name",
        serialize=_require_full_name,
        deserialize=_require_full_name,
    )
)
_reg(
    FieldSpec(
        "address",
        "json",
        TEXT_OPS,
        False,
        "address",
        serialize=_require_address,
        deserialize=_require_address,
    )
)
_reg(FieldSpec("json", "json", ("is_empty", "is_not_empty"), False, "json"))
_reg(FieldSpec("array", "json", ARRAY_OPS, False, "array"))
_reg(FieldSpec("file", "file", EQ_OPS, False, "file"))
_reg(FieldSpec("files", "json", ARRAY_OPS, False, "files"))
_reg(FieldSpec("relation", "reference", EQ_OPS, True, "record_chip"))
_reg(FieldSpec("user", "user", EQ_OPS, True, "record_chip"))


def get_spec(name: str) -> FieldSpec:
    spec = FIELD_REGISTRY.get(name)
    if spec is None:
        raise ValidationError(f"unknown field type '{name}'")
    return spec


def serialize_registry() -> list[dict[str, Any]]:
    return [
        {
            "name": spec.name,
            "storage": spec.storage,
            "operands": list(spec.operands),
            "sortable": spec.sortable,
            "renderer": spec.renderer,
        }
        for spec in FIELD_REGISTRY.values()
    ]
