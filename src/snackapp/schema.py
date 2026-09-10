"""Collection declaration and access presets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from snackapp.exceptions import ValidationError
from snackapp.fields.registry import get_spec


def rules_for(access: str, owner_field: str = "owner") -> dict[str, str | None]:
    """Compile an access preset into SnackBase rule expressions."""
    if access == "team":
        return {
            k: ""
            for k in ("list_rule", "view_rule", "create_rule", "update_rule", "delete_rule")
        }
    if access == "private":
        own = f"{owner_field} = @request.auth.id"
        return {
            "list_rule": own,
            "view_rule": own,
            "create_rule": "",
            "update_rule": own,
            "delete_rule": own,
        }
    if access == "readonly":
        return {
            "list_rule": "",
            "view_rule": "",
            "create_rule": None,
            "update_rule": None,
            "delete_rule": None,
        }
    if access == "public":
        return {
            "list_rule": "",
            "view_rule": "",
            "create_rule": None,
            "update_rule": None,
            "delete_rule": None,
        }
    raise ValueError(f"unknown access preset: {access!r}")


class Field:
    """Constructors that emit SnackBase storage definitions plus semantic metadata."""

    @staticmethod
    def _mk(name: str, semantic: str, **kw: Any) -> dict[str, Any]:
        spec = get_spec(semantic)
        d: dict[str, Any] = {
            "name": name,
            "type": spec.storage,
            "semantic": semantic,
            "renderer": spec.renderer,
            "operands": list(spec.operands),
            "sortable": spec.sortable,
        }
        d.update({k: v for k, v in kw.items() if v is not None})
        return d

    @staticmethod
    def text(name: str, required: bool = False, unique: bool = False, default: Any = None) -> dict[str, Any]:
        return Field._mk(name, "text", required=required or None, unique=unique or None, default=default)

    @staticmethod
    def long_text(name: str, required: bool = False) -> dict[str, Any]:
        return Field._mk(name, "long_text", required=required or None)

    @staticmethod
    def rich_text(name: str) -> dict[str, Any]:
        return Field._mk(name, "rich_text")

    @staticmethod
    def number(name: str, required: bool = False, default: Any = None) -> dict[str, Any]:
        return Field._mk(name, "number", required=required or None, default=default)

    @staticmethod
    def currency(name: str, required: bool = False) -> dict[str, Any]:
        return Field._mk(name, "currency", required=required or None)

    @staticmethod
    def percent(name: str) -> dict[str, Any]:
        return Field._mk(name, "percent")

    @staticmethod
    def rating(name: str, max: int = 5) -> dict[str, Any]:
        if max > 10:
            raise ValidationError(f"rating max {max} exceeds 10")
        return Field._mk(name, "rating", options={"max": max})

    @staticmethod
    def boolean(name: str, default: Any = None) -> dict[str, Any]:
        return Field._mk(name, "boolean", default=default)

    @staticmethod
    def date(name: str, required: bool = False) -> dict[str, Any]:
        return Field._mk(name, "date", required=required or None)

    @staticmethod
    def datetime(name: str, required: bool = False) -> dict[str, Any]:
        return Field._mk(name, "datetime", required=required or None)

    @staticmethod
    def select(name: str, options: list[str], required: bool = False, default: str | None = None) -> dict[str, Any]:
        return Field._mk(
            name,
            "select",
            required=required or None,
            default=default,
            options={"choices": options},
        )

    @staticmethod
    def multi_select(name: str, options: list[str]) -> dict[str, Any]:
        return Field._mk(name, "multi_select", options={"choices": options})

    @staticmethod
    def email(name: str, required: bool = False, unique: bool = False) -> dict[str, Any]:
        return Field._mk(name, "email", required=required or None, unique=unique or None, pii=True, mask_type="email")

    @staticmethod
    def emails(name: str) -> dict[str, Any]:
        return Field._mk(name, "emails")

    @staticmethod
    def phone(name: str) -> dict[str, Any]:
        return Field._mk(name, "phone", pii=True, mask_type="phone")

    @staticmethod
    def phones(name: str) -> dict[str, Any]:
        return Field._mk(name, "phones")

    @staticmethod
    def url(name: str, required: bool = False) -> dict[str, Any]:
        return Field._mk(name, "url", required=required or None)

    @staticmethod
    def links(name: str) -> dict[str, Any]:
        return Field._mk(name, "links")

    @staticmethod
    def full_name(name: str) -> dict[str, Any]:
        return Field._mk(name, "full_name")

    @staticmethod
    def address(name: str) -> dict[str, Any]:
        return Field._mk(name, "address")

    @staticmethod
    def json(name: str) -> dict[str, Any]:
        return Field._mk(name, "json")

    @staticmethod
    def array(name: str) -> dict[str, Any]:
        return Field._mk(name, "array")

    @staticmethod
    def file(name: str) -> dict[str, Any]:
        return Field._mk(name, "file")

    @staticmethod
    def files(name: str) -> dict[str, Any]:
        return Field._mk(name, "files")

    @staticmethod
    def relation(
        name: str,
        to: str,
        display: str | None = None,
        required: bool = False,
        on_delete: str = "restrict",
    ) -> dict[str, Any]:
        return Field._mk(
            name,
            "relation",
            collection=to,
            required=required or None,
            on_delete=on_delete,
            display=display,
        )

    @staticmethod
    def relation_many(name: str, to: str, display: str | None = None) -> dict[str, Any]:
        return Field._mk(name, "relation", collection=to, display=display, options={"many": True})

    @staticmethod
    def user(name: str, required: bool = False, on_delete: str = "restrict") -> dict[str, Any]:
        if on_delete == "cascade":
            raise ValidationError(f"on_delete 'cascade' is not allowed for user field '{name}'")
        return Field._mk(name, "user", required=required or None, on_delete=on_delete)

    @staticmethod
    def computed(name: str, expression: str, return_type: str = "text") -> dict[str, Any]:
        return {
            "name": name,
            "type": "computed",
            "semantic": "computed",
            "expression": expression,
            "return_type": return_type,
            "renderer": "text",
            "operands": list(get_spec("text").operands)
            if return_type == "text"
            else list(get_spec("number").operands),
            "sortable": return_type in {"text", "number", "boolean", "datetime"},
        }


def display_field_fallback(fields: list[dict[str, Any]]) -> str:
    names = {f["name"] for f in fields}
    for candidate in ("name", "title", "id"):
        if candidate in names:
            return candidate
    return fields[0]["name"] if fields else "id"


@dataclass
class CollectionDef:
    name: str
    fields: list[dict[str, Any]]
    access: str = "team"
    owner_field: str = "owner"
    label_field: str | None = None
    rules: dict[str, str | None] | None = None
    views: list[dict[str, Any]] | None = None

    def rule_map(self) -> dict[str, str | None]:
        return self.rules or rules_for(self.access, self.owner_field)

    def storage_fields(self) -> list[dict[str, Any]]:
        """Strip semantic-only keys before sending to SnackBase."""
        out: list[dict[str, Any]] = []
        for item in self.fields:
            wire = {
                k: v
                for k, v in item.items()
                if k
                not in {
                    "semantic",
                    "renderer",
                    "operands",
                    "sortable",
                    "display",
                }
                and v is not None
            }
            out.append(wire)
        return out


class Schema:
    def __init__(self) -> None:
        self.defs: dict[str, CollectionDef] = {}

    def collection(
        self,
        name: str,
        *fields: dict[str, Any],
        access: str = "team",
        owner_field: str = "owner",
        label_field: str | None = None,
        rules: dict[str, str | None] | None = None,
        views: list[dict[str, Any]] | None = None,
    ) -> CollectionDef:
        declared = list(fields)
        if access == "private" and not any(f.get("name") == owner_field for f in declared):
            declared.append(Field.user(owner_field))
        cd = CollectionDef(
            name=name,
            fields=declared,
            access=access,
            owner_field=owner_field,
            label_field=label_field,
            rules=rules,
            views=views,
        )
        self.defs[name] = cd
        return cd

    def declared_payload(self) -> list[dict[str, Any]]:
        return [
            {"name": cd.name, "schema": cd.storage_fields()}
            for cd in self.defs.values()
        ]
