"""JWT authentication tests: token issuance and Bearer-header access."""
from fastapi.testclient import TestClient

from app.main import app
from app.seed import DEMO_PASSWORD


def test_login_returns_jwt_and_user():
    client = TestClient(app)
    resp = client.post(
        "/api/auth/login", json={"email": "alice@demo.com", "password": DEMO_PASSWORD}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "alice@demo.com"
    # A JWT has three dot-separated segments (header.payload.signature).
    assert body["access_token"].count(".") == 2


def test_bearer_token_grants_access_without_cookie():
    # Log in, grab the token, then use a cookie-less client with the Bearer header.
    login = TestClient(app).post(
        "/api/auth/login", json={"email": "bob@demo.com", "password": DEMO_PASSWORD}
    )
    token = login.json()["access_token"]

    anon = TestClient(app)
    anon.cookies.clear()
    assert anon.get("/api/documents").status_code == 401  # no credentials
    ok = anon.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200


def test_garbage_token_is_rejected():
    anon = TestClient(app)
    resp = anon.get("/api/documents", headers={"Authorization": "Bearer not.a.jwt"})
    assert resp.status_code == 401
