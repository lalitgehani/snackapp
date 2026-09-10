from fastapi import FastAPI
from fastapi.testclient import TestClient

from snackapp.app import App


def test_login_cookie_flags(monkeypatch):
    app = App("t")

    class FakeClient:
        async def request(self, *args, **kwargs):
            return {"token": "tok_secret"}

        async def me(self):
            return {"id": "u1", "email": "a@b.c"}

    monkeypatch.setattr(app, "_client_for", lambda token=None: FakeClient())
    api = FastAPI()
    app.mount(api)
    client = TestClient(api)
    response = client.post("/_sa/login", json={"email": "a@b.c", "password": "x", "account": "AA0001"})
    assert response.status_code == 200
    cookie = response.cookies.get("sa_token")
    assert cookie == "tok_secret"
    header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in header
    assert "SameSite=lax" in header or "SameSite=Lax" in header
