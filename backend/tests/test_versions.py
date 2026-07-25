"""Version-history tests: snapshots are recorded and can be restored."""


def _new_doc(alice):
    return alice.post("/api/documents").json()["id"]


def test_edit_creates_version_and_restore_reverts(alice):
    doc_id = _new_doc(alice)
    alice.put(f"/api/documents/{doc_id}", json={"content": "<p>first</p>"})

    versions = alice.get(f"/api/documents/{doc_id}/versions").json()
    assert len(versions) >= 1
    first_version_id = versions[0]["id"]

    # Change the content, then restore the earlier version.
    alice.put(f"/api/documents/{doc_id}", json={"content": "<p>second</p>"})
    restored = alice.post(
        f"/api/documents/{doc_id}/versions/{first_version_id}/restore"
    ).json()
    assert "first" in restored["content"]


def test_non_editor_cannot_restore(alice, bob):
    doc_id = _new_doc(alice)
    alice.put(f"/api/documents/{doc_id}", json={"content": "<p>owner</p>"})
    version_id = alice.get(f"/api/documents/{doc_id}/versions").json()[0]["id"]

    # Share as viewer — Bob can see history but not restore.
    alice.post(f"/api/documents/{doc_id}/shares", json={"email": "bob@demo.com", "role": "viewer"})
    assert bob.get(f"/api/documents/{doc_id}/versions").status_code == 200
    assert (
        bob.post(f"/api/documents/{doc_id}/versions/{version_id}/restore").status_code == 403
    )
