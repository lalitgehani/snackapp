
from snackapp import ui
from snackapp.app import App, Ctx
from snackapp.discovery import load_package
from snackapp.fields.filters import compile_filter
from snackapp.fields.validate import validate_value
from snackapp.provision import already_provisioned, ensure_secret, mark_provisioned
from snackapp.schema import Field, Schema, display_field_fallback


def test_ui_tree_kinds():
    root, token = ui.new_tree()
    ui.header("Hi", "sub")
    with ui.row():
        with ui.column():
            with ui.card("C"):
                ui.text("hello")
                ui.stat("N", 1)
                ui.badge("ok")
                ui.divider()
                ui.empty("none")
                ui.markdown("**x**")
    with ui.tabs():
        with ui.tab("A"):
            ui.text("a")
    with ui.fragment("board"):
        ui.table([{"id": "1"}], ["id"])
        ui.kanban([], "stage", ["open"], "name")
        ui.timeline([], "t", "ts")
        ui.bar_chart([], "l", "v")
        ui.form("f", "save", ["name"])
        ui.filter_bar([])
        ui.record("c", "1", panel=True)
        ui.chart("bar", data=[])
        ui.list_view([], "name")
        ui.calendar([], "due")
        ui.view_bar([])
    ui.end_tree(token)
    kinds = []

    def walk(n):
        kinds.append(n["kind"])
        for c in n.get("children") or []:
            walk(c)

    walk(root)
    for required in (
        "page", "header", "row", "column", "card", "tabs", "tab", "fragment",
        "text", "stat", "table", "kanban", "form", "record", "chart", "calendar",
    ):
        assert required in kinds


def test_field_constructors_and_private_owner():
    schema = Schema()
    schema.collection(
        "notes",
        Field.text("body"),
        Field.long_text("bio"),
        Field.rich_text("doc"),
        Field.number("n"),
        Field.currency("value"),
        Field.percent("p"),
        Field.rating("score"),
        Field.boolean("ok"),
        Field.date("d"),
        Field.datetime("dt"),
        Field.select("stage", ["a", "b"]),
        Field.multi_select("tags", ["x"]),
        Field.email("e"),
        Field.emails("es"),
        Field.phone("ph"),
        Field.phones("phs"),
        Field.url("u"),
        Field.links("ls"),
        Field.full_name("nm"),
        Field.address("addr"),
        Field.json("j"),
        Field.array("arr"),
        Field.file("f"),
        Field.files("fs"),
        Field.relation("company", to="companies"),
        Field.relation_many("people", to="people"),
        Field.user("assignee"),
        Field.computed("full", "concat(a, b)", "text"),
        access="private",
    )
    cd = schema.defs["notes"]
    assert any(f["name"] == "owner" and f["type"] == "user" for f in cd.fields)
    types = {f["semantic"] for f in cd.fields}
    assert "currency" in types
    assert display_field_fallback(cd.fields) in {"name", "title", "id", "body"}


def test_validate_and_remaining_operands():
    assert validate_value("number", 3) == 3
    assert validate_value("email", "a@b.com")
    compiled = compile_filter("n", "gte", 1, field_type="number")
    assert ">=" in compiled.expression
    compiled = compile_filter("d", "is_in_past", field_type="date")
    assert "<" in compiled.expression
    compiled = compile_filter("d", "is_today", field_type="date")
    assert compiled.expression
    compiled = compile_filter("d", "is_in_future", field_type="date")
    assert compiled.expression
    compiled = compile_filter("stage", "is_any_of", ["a", "b"], field_type="select")
    assert "in (" in compiled.expression
    compiled = compile_filter("n", "is_empty", field_type="text")
    assert "null" in compiled.expression
    compiled = compile_filter("n", "is_not_empty", field_type="text")
    assert compiled.expression
    compiled = compile_filter("n", "is_not", "x", field_type="text")
    assert "!=" in compiled.expression
    compiled = compile_filter("n", "does_not_contain", "x", field_type="text")
    assert "not" in compiled.expression
    compiled = compile_filter("n", "gt", 1, field_type="number")
    compiled = compile_filter("n", "lt", 1, field_type="number")
    compiled = compile_filter("n", "lte", 1, field_type="number")
    compiled = compile_filter("d", "is_before", "2020-01-01", field_type="date")
    compiled = compile_filter("d", "is_after", "2020-01-01", field_type="date")
    compiled = compile_filter("d", "is_relative", 1, field_type="date")


def test_secret_mode(tmp_path):
    secret = ensure_secret(tmp_path)
    path = tmp_path / ".snackapp" / "secret.key"
    assert path.exists()
    assert (path.stat().st_mode & 0o777) == 0o600
    assert ensure_secret(tmp_path) == secret
    assert already_provisioned(tmp_path) is False
    mark_provisioned(tmp_path)
    assert already_provisioned(tmp_path) is True


def test_app_render_without_ctx():
    app = App("t")

    @app.page("/")
    def home():
        ui.header("Home")

    ctx = Ctx(app, client=None, user={"id": "u"}, query={})
    tree = app._render(ctx, app.pages[0], {})
    assert tree["kind"] == "page"


def test_app_render_with_ctx():
    app = App("t")

    @app.page("/hi")
    def hello(ctx):
        ui.text(ctx.user["id"])

    ctx = Ctx(app, client=None, user={"id": "u1"}, query={})
    tree = app._render(ctx, app.pages[0], {})
    assert any(c.get("value") == "u1" for c in tree["children"])


def test_load_package(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "__init__.py").write_text("")
    (pages / "index.py").write_text(
        "from snackapp.discovery import page\nfrom snackapp import ui\n"
        "@page('/', title='Home')\ndef home():\n    ui.header('H')\n"
    )
    app = App("t")
    loaded = load_package(app, pages, "pages")
    assert loaded
    assert any(p.path == "/" for p in app.pages)
