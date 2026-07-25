"""Notification tests: sharing a document notifies the recipient.

Note: the seed gives Bob one starter notification, so these assert on the
*specific* document rather than absolute unread counts.
"""


def _new_doc(client, title="Doc"):
    doc_id = client.post("/api/documents").json()["id"]
    client.put(f"/api/documents/{doc_id}", json={"title": title, "content": "<p>x</p>"})
    return doc_id


def _for_doc(client, doc_id):
    items = client.get("/api/notifications").json()["items"]
    return [n for n in items if n["document_id"] == doc_id]


def test_share_creates_notification_for_recipient(alice, bob):
    doc_id = _new_doc(alice, "Roadmap")
    assert _for_doc(bob, doc_id) == []

    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com"})

    notes = _for_doc(bob, doc_id)
    assert len(notes) == 1
    assert "Roadmap" in notes[0]["message"]


def test_mark_read_clears_unread(alice, bob):
    doc_id = _new_doc(alice)
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com"})
    assert bob.get("/api/notifications").json()["unread"] >= 1

    bob.post("/api/notifications/read")
    assert bob.get("/api/notifications").json()["unread"] == 0


def test_reshare_does_not_duplicate_notification(alice, bob):
    doc_id = _new_doc(alice)
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com", "role": "viewer"})
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com", "role": "editor"})
    # Only the first (new) share notifies; the role change does not.
    assert len(_for_doc(bob, doc_id)) == 1
