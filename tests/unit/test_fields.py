import pytest

from snackapp.exceptions import ValidationError
from snackapp.fields.filters import compile_filter, compile_filters
from snackapp.fields.registry import FIELD_REGISTRY, get_spec
from snackapp.fields.validate import map_backend_errors, writable_fields
from snackapp.schema import Field


def test_all_twenty_six_types_registered():
    expected = {
        "text", "long_text", "rich_text", "number", "currency", "percent", "rating",
        "boolean", "date", "datetime", "select", "multi_select", "email", "emails",
        "phone", "phones", "url", "links", "full_name", "address", "json", "array",
        "file", "files", "relation", "user",
    }
    assert set(FIELD_REGISTRY) == expected


def test_round_trip_every_type():
    samples = {
        "text": "hello",
        "long_text": "hello\nworld",
        "rich_text": {"doc": "x"},
        "number": 3.5,
        "currency": {"amount": 1000, "code": "USD"},
        "percent": 0.2,
        "rating": 4,
        "boolean": True,
        "date": "2026-01-01",
        "datetime": "2026-01-01T00:00:00Z",
        "select": "open",
        "multi_select": ["a", "b"],
        "email": "a@b.com",
        "emails": [{"value": "a@b.com", "primary": True}],
        "phone": "+1",
        "phones": [{"value": "+1", "primary": True}],
        "url": "https://example.com",
        "links": [{"value": "https://example.com", "primary": True}],
        "full_name": {"first": "Ada", "last": "Lovelace"},
        "address": {"street1": "1 Main", "city": "Town", "country": "US"},
        "json": {"k": 1},
        "array": [1, 2],
        "file": {"path": "x", "size": 1, "mime_type": "text/plain"},
        "files": [{"path": "x"}],
        "relation": "id-1",
        "user": "id-1",
    }
    for name, sample in samples.items():
        spec = get_spec(name)
        assert spec.deserialize(spec.serialize(sample)) is not None


def test_currency_requires_code():
    with pytest.raises(ValidationError):
        get_spec("currency").serialize({"amount": 1})


def test_rating_max_rejected():
    with pytest.raises(ValidationError):
        Field.rating("score", max=50)


def test_unknown_type():
    with pytest.raises(ValidationError, match="unknown"):
        get_spec("nope")


def test_sortable_false_for_files_json_array():
    assert get_spec("files").sortable is False
    assert get_spec("json").sortable is False
    assert get_spec("array").sortable is False


def test_filter_is():
    compiled = compile_filter("stage", "is", "won", field_type="select")
    assert compiled.expression == "stage = 'won'"


def test_filter_contains_sql_metacharacters_are_quoted():
    compiled = compile_filter("name", "contains", "' OR 1=1 --", field_type="text")
    assert "OR 1=1" not in compiled.expression.split("name")[0]
    assert "'' OR 1=1 --" in compiled.expression


def test_unsupported_operand():
    with pytest.raises(ValidationError, match="operand"):
        compile_filter("name", "gt", "x", field_type="text")


def test_conjunctive_filters():
    compiled = compile_filters(
        [("a", "is", "1"), ("b", "is", "2"), ("c", "is", "3")],
        {"a": "text", "b": "text", "c": "text"},
    )
    assert compiled.expression.count(" and ") == 2


def test_writable_excludes_computed():
    schema = [
        {"name": "n", "type": "text"},
        {"name": "full", "type": "computed", "semantic": "computed"},
    ]
    names = [f["name"] for f in writable_fields(schema)]
    assert names == ["n"]


def test_map_backend_errors():
    mapped = map_backend_errors(
        {"details": [{"field": "email", "message": "taken"}]}
    )
    assert mapped == {"email": "taken"}


def test_emails_primary():
    out = get_spec("emails").serialize(
        [{"value": "a@b.com"}, {"value": "c@d.com", "primary": True}]
    )
    assert sum(1 for i in out if i["primary"]) == 1
