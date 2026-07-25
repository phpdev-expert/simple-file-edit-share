"""Folder tests: CRUD, moving docs, access control, and chat guardrails.

The live LLM call is not exercised here (no key in the test env), so these cover
the deterministic paths: empty-folder chat and the not-configured 503.
"""


def test_create_list_and_move_document(alice):
    fid = alice.post("/api/folders", json={"name": "Specs"}).json()["id"]
    assert alice.get("/api/folders").json()[0]["doc_count"] == 0

    doc_id = alice.post("/api/documents").json()["id"]
    resp = alice.put(f"/api/documents/{doc_id}", json={"folder_id": fid})
    assert resp.json()["folder_id"] == fid

    folders = alice.get("/api/folders").json()
    assert folders[0]["doc_count"] == 1


def test_delete_folder_detaches_documents(alice):
    fid = alice.post("/api/folders", json={"name": "Temp"}).json()["id"]
    doc_id = alice.post("/api/documents").json()["id"]
    alice.put(f"/api/documents/{doc_id}", json={"folder_id": fid})

    assert alice.delete(f"/api/folders/{fid}").status_code == 204
    # Folder gone, but the document survives (detached).
    assert alice.get(f"/api/documents/{doc_id}").json()["folder_id"] is None


def test_empty_folder_chat_needs_no_llm(alice):
    fid = alice.post("/api/folders", json={"name": "Empty"}).json()["id"]
    resp = alice.post(f"/api/folders/{fid}/chat", json={"message": "hello?"})
    assert resp.status_code == 200
    assert "no documents" in resp.json()["answer"].lower()


def test_chat_with_docs_but_no_llm_configured(alice):
    fid = alice.post("/api/folders", json={"name": "KB"}).json()["id"]
    doc_id = alice.post("/api/documents").json()["id"]
    alice.put(f"/api/documents/{doc_id}", json={"content": "<p>data</p>", "folder_id": fid})
    # No OPENROUTER_API_KEY in the test environment → cleanly disabled.
    resp = alice.post(f"/api/folders/{fid}/chat", json={"message": "summarize"})
    assert resp.status_code == 503


def test_folders_are_private(alice, bob):
    fid = alice.post("/api/folders", json={"name": "Private"}).json()["id"]
    assert bob.get("/api/folders").json() == []
    assert bob.post(f"/api/folders/{fid}/chat", json={"message": "hi"}).status_code == 404
    assert bob.delete(f"/api/folders/{fid}").status_code == 404
