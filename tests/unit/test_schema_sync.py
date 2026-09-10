from snackapp.app import App
from snackapp.exceptions import DestructiveChangeError
from snackapp.schema import Field
from snackapp.schema_sync import plan_schema


def test_plan_schema_reports_added_collection():
    app = App("t")
    app.collection("items", Field.text("name"), access="team")
    plan = plan_schema(app, {})
    assert plan["added"]
    assert plan["added"][0]["collection"] == "items"
    assert plan["added"][0]["destructive"] is False


def test_plan_schema_empty_when_unchanged():
    app = App("t")
    app.collection("items", Field.text("name"), access="team")
    current = {"items": app.schema.defs["items"].storage_fields()}
    plan = plan_schema(app, current)
    assert plan["added"] == []
    assert plan["removed"] == []
    assert plan["changed"] == []


def test_plan_schema_marks_type_change_destructive():
    app = App("t")
    app.collection("items", Field.number("n"), access="team")
    current = {"items": [{"name": "n", "type": "text"}]}
    plan = plan_schema(app, current)
    assert plan["changed"]
    assert plan["changed"][0]["destructive"] is True


def test_destructive_error_message():
    err = DestructiveChangeError("Destructive change on items.n; run `snackapp migrate --confirm`")
    assert "migrate --confirm" in str(err)
