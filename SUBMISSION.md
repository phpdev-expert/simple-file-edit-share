# Submission

## What's included

| Item | Location |
|------|----------|
| Source code — backend | `backend/` (FastAPI + SQLAlchemy) |
| Source code — frontend | `frontend/` (Vite + React + TipTap) |
| Setup & run instructions | `README.md` |
| Architecture note | `ARCHITECTURE.md` |
| AI workflow note | `AI_WORKFLOW.md` |
| This file | `SUBMISSION.md` |
| Automated tests | `backend/tests/` (30 tests, `pytest`) |
| Deployment config | `Dockerfile`, `render.yaml` |
| Screenshots | `docs/screenshots/` |
| Walkthrough video link | `VIDEO.txt` |

## Live deployment

- **URL:** https://ajaia-docs-mkhz.onrender.com/
- **Seeded accounts** (password `password123`): `alice@demo.com`, `bob@demo.com`,
  `carol@demo.com`. Alice owns a document pre-shared with Bob.

To demo sharing: sign in as Alice → open a doc → **Share** → add `bob@demo.com`;
then sign in as Bob in another window to see it under **Shared with me**. Carol has
no access.

## What is working (end to end)

- Create, open, **rename** (inline), and delete documents.
- Rich-text editing: **bold, italic, underline, H1/H2, bulleted & numbered lists**.
- **Autosave** (debounced) with a live save-status indicator; content persists across
  refresh and restart (Postgres in prod).
- **Import** a `.txt`, `.md`, or `.docx` file → new editable document (`.md` and
  `.docx` rendered to formatted HTML).
- **Sharing** by email with **Can edit** / **View only** roles; enforced server-side.
- Dashboard split into **Owned by me** and **Shared with me**.
- **Live editing**: per-document presence + live content sync over WebSockets.
- **Notifications**: in-app bell; recipient is notified when a doc is shared.
- **Version history**: throttled snapshots on edit, with view + restore.
- **Folders + AI chat (RAG)**: group docs into a folder and chat with it; the LLM
  answers grounded in the folder's contents and cites sources (OpenRouter).
- **Export** to Markdown and PDF.
- Seeded users with bcrypt passwords and **JWT auth** (Bearer header + HTTP-only
  cookie).
- Validation & error handling on auth, uploads, and access control.
- Security hardening: server-side HTML sanitization (anti-XSS), CSP + security
  headers, bounded uploads, fail-fast on default secret.
- 30 passing automated tests + AI-driven browser QA.

## What is incomplete / intentionally out of scope

- **Character-level conflict-free co-editing (CRDT)** — live editing uses presence +
  last-writer-wins sync, not Google-Docs-grade concurrent merge.
- **Commenting / suggestion mode** — not built (the remaining stretch item).
- **Vector-search RAG** — folder chat stuffs the folder's documents into context
  (fine for small folders); no embeddings/chunking yet.
- **Full auth** (signup, verification, password reset) — seeded accounts instead.
- **PDF fidelity** — export uses the browser print path, not a server renderer.

## What I'd build next with another 2–4 hours

1. **Commenting / suggestion mode** anchored to text ranges.
2. **CRDT co-editing** (Yjs) for conflict-free concurrent typing + live cursors.
3. **Embeddings-based RAG** (chunk + vector search) so folder chat scales to large
   knowledge bases.
4. A few **frontend component tests** to complement the backend suite.

## Verifying locally in 60 seconds

```bash
# backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pytest        # 30 pass
uvicorn app.main:app --port 8000 &

# frontend
cd ../frontend && npm install && npm run dev      # http://localhost:5173
```

Sign in as `alice@demo.com` / `password123`.
