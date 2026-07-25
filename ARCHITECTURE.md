# Architecture Note

## What I prioritized and why

The prompt rewards **depth in a few areas over shallow coverage**. I anchored on the
things a "collaborative document editor" lives or dies on, then layered stretch
features on top once the core was solid and tested:

1. **A coherent editing experience.** Real rich text (TipTap/ProseMirror), a toolbar
   that reflects the current selection, and **autosave** so work is never lost.
2. **A correct sharing/access model.** This is the part with genuine business logic
   and the easiest place to be subtly wrong, so it gets the strongest test coverage.
3. **A frictionless review path.** One deployable service, one URL, seeded accounts,
   and a sample document already shared — a reviewer sees the whole flow in a minute.

On top of that core: JWT auth, security hardening, live editing, notifications,
version history, and a folder-based RAG chat.

## Shape of the system

```
Browser (React SPA · TipTap)
    │   REST  /api/*         (JWT: Bearer header or HTTP-only cookie)
    │   WebSocket /ws/...    (live presence + content sync)
    ▼
FastAPI
    routers:  auth · documents · shares · uploads · notifications · folders · ws
    deps.py:  get_current_user, get_document_for_user  (auth + access control)
    services: notifications · versions · rag           (business logic)
    core:     config · database · security             (primitives)
    realtime: in-memory WebSocket room manager
    ▼
SQLAlchemy  ──  SQLite (local)  /  Postgres (prod)         External: OpenRouter (LLM)
```

In production FastAPI also serves the built SPA (`frontend/dist`) and falls back to
`index.html` for client-side routes. That collapses frontend + backend into **one
origin and one service**: no CORS in prod, no second deploy, cookies "just work,"
and same-origin WebSockets need no CSP relaxation.

## Backend structure

The app is organized along conventional FastAPI lines so responsibilities are obvious:

- **`core/`** — framework-agnostic primitives: `config` (env), `database` (engine +
  session), `security` (bcrypt, JWT, cookies, HTML sanitization).
- **`deps.py`** — request-scoped dependencies: current-user resolution and the central
  `get_document_for_user` access check.
- **`services/`** — business logic kept out of the routers: `notifications`,
  `versions` (snapshot/restore), `rag` (folder chat context-building + LLM call).
- **`routers/`** — thin HTTP/WS layer; validation via Pydantic, delegation to services.
- **`realtime.py`** — the in-memory room manager for live editing.

## Key decisions & trade-offs

**Content stored as HTML.** TipTap can emit JSON or HTML; I store HTML. It renders
directly, converts cleanly to Markdown on export, feeds the RAG prompt after a
tag-strip, and keeps the schema trivial. Trade-off: less structurally strict than the
ProseMirror JSON doc — acceptable here, and every write is sanitized (below).

**JWT authentication.** Login issues a signed **HS256 JWT** (PyJWT) with standard
`sub`/`iat`/`exp` claims, accepted as an `Authorization: Bearer` header (API clients)
or an **HTTP-only cookie** carrying the same token (browser SPA — XSS-safe while still
a real JWT). One `get_current_user` dependency verifies signature + expiry everywhere,
with an explicit algorithm allow-list (no `alg=none` confusion). The same resolver is
reused for the WebSocket handshake (token via query param or cookie).

**Central access-control helper.** Every document route (and the WS handshake) goes
through `get_document_for_user(...)` in `deps.py`, which resolves the caller's role
(`owner`/`editor`/`viewer`) and raises a uniform `404` (missing) or `403` (no access).
Concentrating the rule in one place is why the sharing tests are short and behavior is
consistent across read, write, delete, share management, and live editing.

**Security hardening.** Document HTML is **sanitized server-side** (bleach, strict
allow-list) on every save and import — this closes a stored-XSS path that would
otherwise reach the editor and, more dangerously, the PDF-export iframe. Every
response carries a **CSP** (self-only scripts, no framing) plus `X-Frame-Options`,
`X-Content-Type-Options`, and `Referrer-Policy`. Uploads are extension- and
size-bounded (bounded read to avoid memory blowups). The app **fails fast** on boot if
run in production with the default JWT secret.

**Live editing (presence + sync), not CRDT.** Each open editor connects to
`/ws/documents/{id}`. A single-process `RealtimeManager` keeps a "room" per document;
it broadcasts **presence** (who's here) and **relays content updates** between
participants. Persistence still flows through the REST autosave — the WebSocket layer
only propagates live state, so there's no double-writing. Conflict handling is
last-writer-wins, and the client skips applying a remote update while the user is
mid-keystroke to avoid clobbering. I chose this over full CRDT (Yjs) deliberately: it
delivers visible real-time collaboration reliably within the timebox; conflict-free
concurrent typing is the honest next step.

**Notifications.** A `Notification` row is created for the recipient when a document is
newly shared (idempotent re-shares don't spam). The frontend bell polls a lightweight
endpoint for the unread count and list.

**Version history.** On each content-changing save the server records a **throttled**
snapshot (`services/versions.py`, at most one per ~45s, pruned to the last 30) so
history is useful without a row per keystroke. Restore snapshots the current state
first, so it's itself reversible.

**Comments & suggestions.** Both are stored as separate `Comment` records keyed to
the **quoted text** (not embedded marks in the content). This is a deliberate choice:
it lets even view-only collaborators comment and suggest without content-write access,
needs no change to the HTML sanitizer, and stays robust across edits. A suggestion
carries a `suggested_text`; **accepting** it (owner/editor only) does a find-and-
replace of the quote in the editor and lets autosave persist — so the server stays out
of fragile HTML surgery. Trade-off: no inline highlight painted into the doc; the
anchor lives in the side panel. Adding someone's comment also notifies the owner.

**Folders + RAG chat.** A `Folder` groups a user's documents into a knowledge base.
`POST /api/folders/{id}/chat` gathers the folder's documents, strips them to text, and
packs them (up to a char budget) into an LLM system prompt via **OpenRouter**
(OpenAI-compatible), instructing the model to answer only from those documents and
cite titles. Retrieval here is **context-stuffing** — appropriate for small folders and
honest about its limits; swapping in embeddings + vector search would only change
`build_context()`. The feature is **env-gated**: with no `OPENROUTER_API_KEY` it's
cleanly disabled (clear message), so the "don't require reviewers to pay" constraint
holds — the rest of the app never depends on it.

**Export on the client.** Markdown (`turndown`) and PDF (hidden print iframe) run in
the browser, avoiding heavy server-side PDF dependencies and keeping the image small.

**Database portability + migrations.** A `DATABASE_URL` switch gives SQLite locally and
Postgres in prod with no code changes. Since production Postgres persists across
deploys, startup runs a lightweight **additive migration** (`ensure_schema`):
`create_all()` for new tables, plus an `ALTER TABLE ... ADD COLUMN` backfill for new
columns on existing tables (e.g. `documents.folder_id`). This is a deliberate
stand-in; **Alembic** is the right tool for anything beyond additive changes.

## Data model

- **User** — `id, email (unique), name, password_hash`
- **Document** — `id, title, content (HTML), owner_id, folder_id?, created_at, updated_at`
- **Share** — `id, document_id, user_id, role`, unique on `(document_id, user_id)`
- **Folder** — `id, name, owner_id, created_at`
- **Notification** — `id, user_id, message, document_id?, read, created_at`
- **DocumentVersion** — `id, document_id, title, content, author_name, created_at`
- **Comment** — `id, document_id, author_name, kind (comment|suggestion), quote, body,
  suggested_text?, resolved, created_at`

The share unique constraint makes sharing idempotent: re-sharing updates the role
instead of duplicating.

## Validation & error handling

- Pydantic validates request bodies; emails are normalized to lowercase.
- Uploads are checked for extension, a 5 MB bounded read, and UTF-8 decodability.
- Auth failures → `401`; no-access → `403`; unknown doc/folder/user → `404`; LLM not
  configured → `503`; LLM provider errors → `502` (with the provider's message
  surfaced). All render as readable messages in the UI.

## What I intentionally deprioritized

- **Character-level conflict-free co-editing (CRDT).** Live editing is presence +
  last-writer-wins sync, not Google-Docs-grade concurrent merge.
- **Inline comment highlights.** Comments/suggestions anchor to the quoted text in a
  side panel rather than painting a persisted highlight into the document body.
- **Vector-search RAG.** Folder chat stuffs documents into context (fine for small
  folders); no embeddings/chunking yet.
- **Full auth (signup, verification, reset).** Seeded accounts exercise the model.
- **Pixel-perfect PDF.** The print-based export is dependency-free and good enough.

## What I'd build next with another 2–4 hours

1. **CRDT co-editing** (Yjs) for conflict-free concurrent typing + live cursors.
2. **Inline comment highlights** persisted as a document mark.
3. **Embeddings-based RAG** (chunk + vector search) so folder chat scales to large
   knowledge bases.
4. **Alembic migrations** and a few **frontend component tests**.
