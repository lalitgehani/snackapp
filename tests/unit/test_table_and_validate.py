import pytest

from snackapp import ui
from snackapp.app import App, Ctx
from snackapp.exceptions import ValidationError
from snackapp.fields.validate import validate_value
from snackapp.provision import apply_runtime_env
from snackapp.schema import Field, rules_for


def test_public_and_readonly():
    assert rules_for("public")["create_rule"] is None
    assert rules_for("readonly")["delete_rule"] is None
    with pytest.raises(ValueError):
        rules_for("nope")


def test_validate_required_and_rating():
    with pytest.raises(ValidationError):
        validate_value("text", None, required=True)
    with pytest.raises(ValidationError):
        validate_value("email", "not-an-email")
    with pytest.raises(ValidationError):
        validate_value("number", "x")
    with pytest.raises(ValidationError):
        validate_value("rating", 99, max=5)
    with pytest.raises(ValidationError):
        validate_value("currency", {"amount": 1, "code": "USD"}, min=10)
    assert validate_value("text", None) is None


def test_table_crud_records_reads_and_writes():
    app = App("t")
    table = app.collection("items", Field.text("name"))

    class Fake:
        def list(self, *a, **k):
            return {"items": [{"id": "1"}], "total": 1}

        def get(self, *a, **k):
            return {"id": "1"}

        def create(self, *a, **k):
            return {"id": "2"}

        def update(self, *a, **k):
            return {"id": "1"}

        def delete(self, *a, **k):
            return None

        def aggregate(self, *a, **k):
            return {"count": 1}

    ctx = Ctx(app, Fake(), {"id": "u"}, {})
    tok = app._ctx_var.set(ctx)
    try:
        assert table.list() == [{"id": "1"}]
        assert table.get("1")["id"] == "1"
        assert table.create(name="n")["id"] == "2"
        assert table.update("1", name="m")["id"] == "1"
        table.delete("1")
        assert table.aggregate()["count"] == 1
        assert table.count() == 1
        assert "items" in ctx._wrote
        assert "items" in ctx._page_reads
        ctx.toast("saved")
        ctx.go("/x")
        ctx.refresh("board")
        assert ctx._toast == "saved"
        assert ctx._redirect == "/x"
        assert ctx._refresh == ["board"]
    finally:
        app._ctx_var.reset(tok)


def test_ui_fields_button_modal():
    root, token = ui.new_tree()
    ui.fields({"n": "v"}, ["n"], editable=True, action="save")
    ui.button("Go", action="x")
    ui.modal_form("m", "save", [{"field": "n"}])
    ui.end_tree(token)
    kinds = {c["kind"] for c in root["children"]}
    assert "fields" in kinds
    assert "form" in kinds


def test_apply_runtime_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    apply_runtime_env(tmp_path)
    assert "SNACKBASE_SECRET_KEY" in __import__("os").environ
    assert "snackbase.db" in __import__("os").environ["SNACKBASE_DATABASE_URL"]
