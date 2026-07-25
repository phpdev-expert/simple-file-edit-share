"""File-import tests: supported types convert, unsupported ones are rejected."""
import os

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_markdown_import_creates_editable_doc(alice):
    files = {"file": ("notes.md", b"# Title\n\nHello **world**", "text/markdown")}
    resp = alice.post("/api/uploads", files=files)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "notes"
    assert body["role"] == "owner"
    assert "<h1>" in body["content"] and "<strong>" in body["content"]

    # It is a real, reopenable document owned by the caller.
    assert alice.get(f"/api/documents/{body['id']}").status_code == 200


def test_txt_import_wraps_paragraphs(alice):
    files = {"file": ("memo.txt", b"line one\n\nline two", "text/plain")}
    resp = alice.post("/api/uploads", files=files)
    assert resp.status_code == 201
    assert resp.json()["content"].count("<p>") == 2


def test_docx_import_converts_formatting(alice):
    with open(os.path.join(FIXTURES, "sample.docx"), "rb") as f:
        files = {
            "file": (
                "sample.docx",
                f.read(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
    resp = alice.post("/api/uploads", files=files)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "sample"
    assert body["role"] == "owner"
    # mammoth maps the heading, bold/italic runs, and bullets to semantic HTML.
    assert "<h1>" in body["content"]
    assert "<strong>" in body["content"] and "<em>" in body["content"]
    assert "<li>" in body["content"]


def test_unsupported_extension_rejected(alice):
    files = {"file": ("evil.exe", b"MZ...", "application/octet-stream")}
    resp = alice.post("/api/uploads", files=files)
    assert resp.status_code == 400
    assert "Unsupported" in resp.json()["detail"]
