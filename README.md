# Ajaia Docs — a lightweight collaborative document editor

A small full-stack app inspired by Google Docs: create and edit rich-text
documents, import `.txt`/`.md` files, share documents with teammates, and export
to Markdown or PDF. Built for the AI-Native Full Stack assignment.

**Stack:** React + Vite + TipTap (frontend) · FastAPI + SQLAlchemy (backend) ·
SQLite locally / Postgres in production. The backend serves the built frontend, so
production runs as **a single service on one URL**.

---

## Live demo

- **URL:** _<add your deployed URL here>_
- **Demo accounts** (password `password123` for all):
  - `alice@demo.com` — owns a document already shared with Bob
  - `bob@demo.com`
  - `carol@demo.com`

To see the sharing flow: sign in as **Alice**, open *Welcome to Ajaia Docs*, click
**Share**, and add `bob@demo.com`. Then sign in as **Bob** (a separate/incognito
window) — the document appears under **Shared with me**. **Carol** has no access and
receives a clear "no access" screen.

---

## Features

| Area | What works |
|------|------------|
| **Editing** | Rich text via TipTap: bold, italic, underline, H1/H2, bulleted & numbered lists. Debounced **autosave** + live "All changes saved" status. |
| **Documents** | Create, open, inline **rename**, delete. Content persists across refresh and restart. |
| **Import** | Upload a `.txt`, `.md`, or `.docx` file → converted into a new editable document. `.md` renders to formatted HTML; `.docx` is converted with mammoth (headings, bold/italic, lists preserved). |
| **Sharing** | Owner shares by **email** with **Can edit** or **View only** roles. Dashboard separates **Owned by me** vs **Shared with me**. Only the owner can share/delete. |
| **Export** | Download as **Markdown**, or print/save as **PDF**. |
| **Auth** | Seeded users, bcrypt-hashed passwords, **JWT** (HS256) sent as a Bearer token and mirrored in an HTTP-only cookie. |

**Supported upload types:** `.txt`, `.md`, and `.docx`, up to **5 MB**. Other types
are rejected with a clear message (enforced in both the UI and the API).

---

## Run locally

Requires **Python 3.10+** and **Node 18+**. Run the two services in two terminals.

### 1. Backend (FastAPI, port 8000)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

On first start it creates the SQLite DB (`backend/docs.db`) and seeds the demo
users and sample shared document.

### 2. Frontend (Vite, port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api` → `:8000`, so
cookies stay same-site and there are no CORS issues.

### Run the tests

```bash
cd backend
source .venv/bin/activate
pytest
```

17 tests cover JWT authentication, the sharing access-control model, file-import
behavior (including `.docx` conversion), and security hardening (HTML sanitization,
response headers).

---

## Run the production build locally (single service)

This mirrors how it runs when deployed — FastAPI serves the built SPA:

```bash
cd frontend && npm install && npm run build      # outputs frontend/dist
cd ../backend && source .venv/bin/activate
uvicorn app.main:app --port 8000
```

Open **http://localhost:8000** — app and API on one origin.

Or with Docker (identical to the deployed image):

```bash
docker build -t ajaia-docs .
docker run -p 8000:8000 -e SESSION_SECRET=changeme ajaia-docs
```

---

## Deploy (Render, free tier — one click)

The repo includes a `Dockerfile` and a `render.yaml` Blueprint that provisions a free
managed Postgres **and** the web service, wiring them together automatically.

1. Push this repo to GitHub (already done if you cloned it from there).
2. On [Render](https://dashboard.render.com): **New → Blueprint**.
3. Connect your GitHub account and select this repository.
4. Render reads `render.yaml` and shows the plan: one web service (`ajaia-docs`) +
   one Postgres (`ajaia-docs-db`). Click **Apply**.
5. Wait for the first build (~2–4 min). Render builds the Docker image, injects
   `DATABASE_URL` from the managed Postgres, generates `SESSION_SECRET`, and starts
   the app. Seeding runs automatically on boot; health check is `/api/health`.
6. Open the service URL Render gives you (e.g. `https://ajaia-docs.onrender.com`) and
   sign in with a demo account.

That's it — no manual database or env-var setup. (Free Render services sleep after
inactivity, so the first request after idle takes a few seconds to wake.)

**Manual alternative** (if you prefer not to use the Blueprint): New → **Web Service**
→ select the repo → Runtime **Docker** → create a free Render **Postgres** separately
→ set `DATABASE_URL` to its Internal Connection String, `SESSION_SECRET` to any strong
value, and `COOKIE_SECURE=1`.

---

## Configuration

| Env var | Default | Purpose |
|---------|---------|---------|
| `DATABASE_URL` | `sqlite:///./docs.db` | SQLAlchemy URL. `postgres://` is auto-normalized. |
| `SESSION_SECRET` | `dev-secret-change-me` | Secret used to sign JWTs. **Change in prod.** |
| `COOKIE_SECURE` | `0` | Set to `1` in production (HTTPS-only cookie). |

---

## Project layout

```
backend/    FastAPI app, SQLAlchemy models, routers, tests
frontend/   Vite + React + TipTap SPA
Dockerfile  Multi-stage build (node → python) for single-service deploy
render.yaml Render blueprint
docs/       Screenshots used in the docs
```

## Security hardening

- **JWT** signed with HS256, verified with an explicit algorithm allow-list (no
  `alg=none` confusion); short-lived tokens with `exp`; delivered via an HTTP-only,
  `SameSite=Lax`, `Secure` (prod) cookie or a Bearer header.
- **Passwords** hashed with bcrypt; login returns a generic error (no user
  enumeration).
- **Server-side HTML sanitization** (bleach, strict allow-list) on every document
  save and import — blocks stored XSS via `<script>`, `on*` handlers, and
  `javascript:` URLs before they reach the editor or the PDF-export iframe.
- **Access control** centralized in one helper; every document route enforces
  owner/editor/viewer with uniform 401/403/404.
- **Security headers** on every response: `Content-Security-Policy` (self-only
  scripts, no framing), `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`.
- **Upload limits**: extension allow-list + bounded (5 MB) read to avoid memory
  exhaustion.
- **Fail-fast**: the app refuses to boot in production (`COOKIE_SECURE=1`) with the
  default JWT secret.

Known trade-offs for the timebox: JWTs are stateless (logout clears the cookie but a
leaked Bearer token stays valid until `exp` — no revocation list), and there's no
login rate-limiting yet.

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for design decisions and trade-offs, and
[`AI_WORKFLOW.md`](./AI_WORKFLOW.md) for how AI was used.
