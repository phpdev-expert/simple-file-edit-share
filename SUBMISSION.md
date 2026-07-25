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
| Automated tests | `backend/tests/` (17 tests, `pytest`) |
| Deployment config | `Dockerfile`, `render.yaml` |
| Screenshots | `docs/screenshots/` |
| Walkthrough video link | `VIDEO.txt` |

## Live deployment

- **URL:** _<add deployed URL>_
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
- **Export** to Markdown and PDF.
- Seeded users with bcrypt passwords and **JWT auth** (Bearer header + HTTP-only
  cookie).
- Validation & error handling on auth, uploads, and access control.
- Security hardening: server-side HTML sanitization (anti-XSS), CSP + security
  headers, bounded uploads, fail-fast on default secret.
- 17 passing automated tests + AI-driven browser QA.

## What is incomplete / intentionally out of scope

- **Real-time collaborative editing / presence** — single-writer autosave only.
- **Concurrent-edit conflict resolution** — last write wins (no versioning yet).
- **Full auth** (signup, verification, password reset) — seeded accounts instead.
- **PDF fidelity** — export uses the browser print path, not a server renderer.

## What I'd build next with another 2–4 hours

1. WebSocket **presence indicators** (who else is viewing/editing).
2. **Optimistic concurrency** (a `version` column + conflict detection on save).
3. **Version history** (snapshot on save, diff/restore).
4. A few **frontend component tests** to complement the backend suite.

## Verifying locally in 60 seconds

```bash
# backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pytest        # 9 pass
uvicorn app.main:app --port 8000 &

# frontend
cd ../frontend && npm install && npm run dev      # http://localhost:5173
```

Sign in as `alice@demo.com` / `password123`.
