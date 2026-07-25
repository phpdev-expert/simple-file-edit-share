"""Access-control tests — the core of the sharing model."""


def _create_doc(client, title="Secret", content="<p>hi</p>"):
    resp = client.post("/api/documents")
    assert resp.status_code == 201, resp.text
    doc_id = resp.json()["id"]
    client.put(f"/api/documents/{doc_id}", json={"title": title, "content": content})
    return doc_id


def test_non_collaborator_is_forbidden(alice, bob):
    doc_id = _create_doc(alice)
    # Bob has no access at all.
    assert bob.get(f"/api/documents/{doc_id}").status_code == 403
    assert bob.put(f"/api/documents/{doc_id}", json={"title": "hack"}).status_code == 403


def test_share_grants_read_and_edit(alice, bob):
    doc_id = _create_doc(alice)
    resp = alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com"})
    assert resp.status_code == 201

    # Bob can now read and (as editor) write.
    assert bob.get(f"/api/documents/{doc_id}").status_code == 200
    assert bob.put(f"/api/documents/{doc_id}", json={"content": "<p>edited</p>"}).status_code == 200

    # And the doc shows up in Bob's "shared with me" list.
    shared = bob.get("/api/documents").json()["shared"]
    assert any(d["id"] == doc_id for d in shared)


def test_viewer_role_is_read_only(alice, bob):
    doc_id = _create_doc(alice)
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com", "role": "viewer"})
    assert bob.get(f"/api/documents/{doc_id}").status_code == 200
    assert bob.put(f"/api/documents/{doc_id}", json={"content": "<p>nope</p>"}).status_code == 403


def test_only_owner_can_delete_and_manage_shares(alice, bob):
    doc_id = _create_doc(alice)
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com"})
    # Bob is a collaborator but cannot delete or re-share.
    assert bob.delete(f"/api/documents/{doc_id}").status_code == 403
    assert bob.post(f"/api/documents/{doc_id}/shares", json={"email": "carol@demo.com"}).status_code == 403


def test_share_with_unknown_email_404_and_dedup(alice):
    doc_id = _create_doc(alice)
    assert alice.post(
        f"/api/documents/{doc_id}/shares", json={"email": "nobody@demo.com"}
    ).status_code == 404

    # Sharing the same user twice is idempotent (updates, no duplicate row).
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com", "role": "viewer"})
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com", "role": "editor"})
    shares = alice.get(f"/api/documents/{doc_id}/shares").json()
    assert len([s for s in shares if s["user"]["email"] == "bob@demo.com"]) == 1


def test_requires_authentication(alice):
    doc_id = _create_doc(alice)
    from fastapi.testclient import TestClient

    from app.main import app

    anon = TestClient(app)
    assert anon.get(f"/api/documents/{doc_id}").status_code == 401
