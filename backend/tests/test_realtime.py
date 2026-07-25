"""WebSocket tests: authentication, presence, and live update relay."""
import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from app.main import app
from app.seed import DEMO_PASSWORD


def _token(email: str) -> str:
    resp = TestClient(app).post(
        "/api/auth/login", json={"email": email, "password": DEMO_PASSWORD}
    )
    return resp.json()["access_token"]


def _make_shared_doc() -> int:
    client = TestClient(app)
    client.post("/api/auth/login", json={"email": "alice@demo.com", "password": DEMO_PASSWORD})
    doc_id = client.post("/api/documents").json()["id"]
    client.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com"})
    return doc_id


def test_ws_requires_valid_token():
    doc_id = _make_shared_doc()
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/documents/{doc_id}") as ws:
            ws.receive_json()


def test_ws_presence_and_update_relay():
    doc_id = _make_shared_doc()
    alice_tok, bob_tok = _token("alice@demo.com"), _token("bob@demo.com")
    client = TestClient(app)

    with client.websocket_connect(f"/ws/documents/{doc_id}?token={alice_tok}") as wa:
        assert wa.receive_json()["type"] == "presence"
        with client.websocket_connect(f"/ws/documents/{doc_id}?token={bob_tok}") as wb:
            # Both sides learn about the two participants.
            assert wb.receive_json()["type"] == "presence"
            assert wa.receive_json()["type"] == "presence"

            # Alice edits; Bob receives the live update.
            wa.send_json({"type": "update", "html": "<p>live</p>"})
            msg = wb.receive_json()
            assert msg["type"] == "update"
            assert msg["html"] == "<p>live</p>"


def test_ws_rejects_non_collaborator():
    doc_id = _make_shared_doc()
    carol_tok = _token("carol@demo.com")
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/documents/{doc_id}?token={carol_tok}") as ws:
            ws.receive_json()
