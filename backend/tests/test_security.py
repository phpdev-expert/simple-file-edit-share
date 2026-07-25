"""Security hardening tests: HTML sanitization and response headers."""


def _create_doc(client):
    return client.post("/api/documents").json()["id"]


def test_script_is_stripped_on_save(alice):
    doc_id = _create_doc(alice)
    payload = {"content": '<p>ok</p><script>alert(1)</script><img src=x onerror=alert(2)>'}
    body = alice.put(f"/api/documents/{doc_id}", json=payload).json()
    assert "<script>" not in body["content"]
    assert "onerror" not in body["content"]
    assert "<img" not in body["content"]
    assert "<p>ok</p>" in body["content"]


def test_javascript_url_is_stripped(alice):
    doc_id = _create_doc(alice)
    body = alice.put(
        f"/api/documents/{doc_id}",
        json={"content": '<a href="javascript:alert(1)">x</a>'},
    ).json()
    assert "javascript:" not in body["content"]


def test_markdown_import_strips_embedded_script(alice):
    files = {"file": ("evil.md", b"# Hi\n\n<script>alert(1)</script>\n", "text/markdown")}
    body = alice.post("/api/uploads", files=files).json()
    assert "<script>" not in body["content"]
    assert "<h1>" in body["content"]


def test_security_headers_present(alice):
    resp = alice.get("/api/documents")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    # Self-hosted + inlined (data:) fonts must both be allowed, or the UI breaks.
    assert "font-src 'self' data:" in csp
