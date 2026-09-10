from fastapi import FastAPI
from fastapi.testclient import TestClient

from snackapp import ui
from snackapp.app import App


def _app() -> App:
    app = App("Demo")

    @app.page("/", title="Home", nav=True, order=1)
    def home():
        ui.header("Home")

    @app.page("/public", title="Pub", public=True)
    def pub():
        ui.text("hi")

    @app.action
    def save(ctx):
        ctx.toast("ok")

    return app


def test_meta_and_logout_and_view_auth():
    app = _app()
    api = FastAPI()
    app.mount(api)
    client = TestClient(api)
    meta = client.get("/_sa/meta")
    assert meta.status_code == 200
    assert meta.json()["title"] == "Demo"
    assert meta.json()["nav"]
    assert meta.json()["fields"]
    view = client.get("/_sa/view", params={"path": "/"})
    assert view.status_code == 401
    pub = client.get("/_sa/view", params={"path": "/public"})
    assert pub.status_code == 200
    missing = client.get("/_sa/view", params={"path": "/nope"})
    assert missing.status_code == 404
    logout = client.post("/_sa/logout")
    assert logout.status_code == 200
    action = client.post("/_sa/action/save", json={})
    assert action.status_code == 401
    spa = client.get("/")
    assert spa.status_code == 200
    assert b"root" in spa.content
    assert b"/_sa/static" in spa.content or b"data-base" in spa.content
    head = client.head("/")
    assert head.status_code == 200


def test_nav_order():
    app = App("t")

    @app.page("/b", title="B", nav=True, order=2)
    def b():
        return None

    @app.page("/a", title="A", nav=True, order=1)
    def a():
        return None

    items = app.nav_items()
    assert [i["title"] for i in items] == ["A", "B"]
