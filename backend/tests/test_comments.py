"""Comment + suggestion tests: creation, access, resolve, and accept rules."""


def _new_doc(alice):
    doc_id = alice.post("/api/documents").json()["id"]
    alice.put(f"/api/documents/{doc_id}", json={"content": "<p>The plan costs ten dollars.</p>"})
    return doc_id


def test_viewer_can_comment_and_suggest(alice, bob):
    doc_id = _new_doc(alice)
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com", "role": "viewer"})

    # Even a view-only collaborator may comment and suggest.
    c = bob.post(
        f"/api/documents/{doc_id}/comments",
        json={"kind": "comment", "quote": "ten dollars", "body": "Is this current?"},
    )
    assert c.status_code == 201
    s = bob.post(
        f"/api/documents/{doc_id}/comments",
        json={"kind": "suggestion", "quote": "ten dollars", "suggested_text": "twenty dollars"},
    )
    assert s.status_code == 201
    assert len(alice.get(f"/api/documents/{doc_id}/comments").json()) == 2


def test_comment_notifies_owner(alice, bob):
    doc_id = _new_doc(alice)
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com", "role": "viewer"})
    bob.post(f"/api/documents/{doc_id}/comments", json={"kind": "comment", "body": "note"})
    notes = alice.get("/api/notifications").json()["items"]
    assert any(n["document_id"] == doc_id and "commented" in n["message"] for n in notes)


def test_suggestion_requires_replacement_text(alice):
    doc_id = _new_doc(alice)
    resp = alice.post(
        f"/api/documents/{doc_id}/comments", json={"kind": "suggestion", "quote": "x"}
    )
    assert resp.status_code == 400


def test_viewer_cannot_accept_suggestion(alice, bob):
    doc_id = _new_doc(alice)
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com", "role": "viewer"})
    cid = bob.post(
        f"/api/documents/{doc_id}/comments",
        json={"kind": "suggestion", "quote": "ten", "suggested_text": "twenty"},
    ).json()["id"]

    # Viewer can't accept (it applies an edit); owner can.
    assert bob.post(f"/api/documents/{doc_id}/comments/{cid}/accept").status_code == 403
    accepted = alice.post(f"/api/documents/{doc_id}/comments/{cid}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["resolved"] is True


def test_non_collaborator_cannot_see_comments(alice, carol):
    doc_id = _new_doc(alice)
    assert carol.get(f"/api/documents/{doc_id}/comments").status_code == 403
