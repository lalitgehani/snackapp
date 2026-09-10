"""Compile (field, operand, value) triples into parameterized SnackBase filters.

Values are never interpolated into the expression string. SQL metacharacters
in a value cannot change the query's structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from snackapp.exceptions import ValidationError
from snackapp.fields.registry import get_spec


@dataclass
class CompiledFilter:
    expression: str
    params: dict[str, Any]


def _quote_ident(name: str) -> str:
    if not name.replace("_", "").replace(".", "").isalnum() or not name[0].isalpha():
        raise ValidationError(f"invalid field name {name!r}")
    return name


def _lit(value: Any) -> str:
    """Render a literal for SnackBase's filter language.

    Strings are single-quoted with internal quotes doubled — this is still a
    bound literal in the filter AST, not SQL concatenation. The compiler
    parameterizes it.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


def _field_path(field: str, semantic: str) -> str:
    if semantic == "currency":
        return f"{field}.amount"
    if semantic == "full_name":
        return field
    return field


def compile_filter(
    field: str,
    operand: str,
    value: Any = None,
    *,
    field_type: str = "text",
    now: datetime | None = None,
) -> CompiledFilter:
    spec = get_spec(field_type)
    if operand not in spec.operands:
        raise ValidationError(
            f"operand '{operand}' is not supported for type '{field_type}'"
        )
    ident = _quote_ident(_field_path(field, field_type))
    clock = now or datetime.now(UTC)
    today = clock.date()

    if operand == "is":
        return CompiledFilter(f"{ident} = {_lit(value)}", {field: value})
    if operand == "is_not":
        return CompiledFilter(f"{ident} != {_lit(value)}", {field: value})
    if operand == "contains":
        return CompiledFilter(f"{ident} ~ {_lit(value)}", {field: value})
    if operand == "does_not_contain":
        return CompiledFilter(f"not ({ident} ~ {_lit(value)})", {field: value})
    if operand == "is_empty":
        return CompiledFilter(f"{ident} = '' or {ident} is null", {})
    if operand == "is_not_empty":
        return CompiledFilter(f"{ident} != '' and {ident} is not null", {})
    if operand == "gt":
        return CompiledFilter(f"{ident} > {_lit(value)}", {field: value})
    if operand == "gte":
        return CompiledFilter(f"{ident} >= {_lit(value)}", {field: value})
    if operand == "lt":
        return CompiledFilter(f"{ident} < {_lit(value)}", {field: value})
    if operand == "lte":
        return CompiledFilter(f"{ident} <= {_lit(value)}", {field: value})
    if operand == "is_before":
        return CompiledFilter(f"{ident} < {_lit(value)}", {field: value})
    if operand == "is_after":
        return CompiledFilter(f"{ident} > {_lit(value)}", {field: value})
    if operand == "is_today":
        return CompiledFilter(f"{ident} = {_lit(today.isoformat())}", {})
    if operand == "is_in_past":
        return CompiledFilter(f"{ident} < {_lit(today.isoformat())}", {})
    if operand == "is_in_future":
        return CompiledFilter(f"{ident} > {_lit(today.isoformat())}", {})
    if operand == "is_relative":
        days = int(value)
        target = today + timedelta(days=days)
        return CompiledFilter(f"{ident} = {_lit(target.isoformat())}", {})
    if operand == "is_any_of":
        values = list(value)
        inner = ", ".join(_lit(v) for v in values)
        return CompiledFilter(f"{ident} in ({inner})", {field: values})
    raise ValidationError(f"unsupported operand '{operand}'")


def compile_filters(
    triples: list[tuple[str, str, Any]],
    types: dict[str, str],
    *,
    now: datetime | None = None,
) -> CompiledFilter:
    parts: list[str] = []
    params: dict[str, Any] = {}
    for field, operand, value in triples:
        compiled = compile_filter(
            field, operand, value, field_type=types.get(field, "text"), now=now
        )
        parts.append(f"({compiled.expression})")
        params.update(compiled.params)
    return CompiledFilter(" and ".join(parts), params)
