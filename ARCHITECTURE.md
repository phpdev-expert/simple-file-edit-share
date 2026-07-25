# Architecture Note

## What I prioritized and why

The prompt rewards **depth in a few areas over shallow coverage**. I spent my time on
the three things a "collaborative document editor" lives or dies on:

1. **A coherent editing experience.** Real rich text (TipTap/ProseMirror), a toolbar
   that reflects the current selection, and **autosave** so work is never lost. This
   is the surface a reviewer touches first, so it had to feel solid.
2. **A correct sharing/access model.** This is the part with genuine business logic
   and the easiest place to be subtly wrong, so it gets the strongest test coverage.
3. **A frictionless review path.** One deployable service, one URL, seeded accounts,
   and a sample document already shared — a reviewer can see the whole flow in under a
   minute.

## Shape of the system

```
Browser (React SPA, TipTap)
    │  fetch /api/*  (session cookie, credentials: include)
    ▼
FastAPI  ──  routers: auth · documents · shares · uploads
    │
    ▼
SQLAlchemy  ──  SQLite (local)  /  Postgres (prod)
```

In production FastAPI also serves the built SPA (`frontend/dist`) and falls back to
`index.html` for client-side routes. That collapses frontend + backend into **one
origin and one service**: no CORS in prod, no second deploy, cookies "just work."

## Key decisions & trade-offs

**Content stored as HTML.** TipTap can emit JSON or HTML; I store the HTML string.
It renders directly, converts cleanly to Markdown on export, and keeps the schema
trivial. Trade-off: HTML is less structurally strict than the ProseMirror JSON doc.
For this scope, simplicity and export-friendliness won. HTML is escaped on `.txt`
import; TipTap sanitizes on load.

**JWT authentication.** Login issues a signed **HS256 JWT** (PyJWT) carrying standard
`sub`/`iat`/`exp` claims. The API accepts it two ways: an `Authorization: Bearer`
header (for API clients) or an **HTTP-only cookie** carrying the same token (for the
browser SPA, which keeps it out of reach of XSS while still being a real JWT). A
single `get_current_user` dependency verifies the signature/expiry on every protected
route. Seeded users with bcrypt hashes keep auth realistic without burning time on
signup/verification flows.

**Central access-control helper.** Every document route goes through
`get_document_for_user(...)` in `backend/app/auth.py`, which resolves the caller's
role (`owner` / `editor` / `viewer`) and raises a uniform `404` (missing) or `403`
(no access). Concentrating the rule in one place is why the sharing tests are short
and the behavior is consistent across read, write, delete, and share management.

**Roles.** The data model carries a `role` on each share (`editor` default,
`viewer` read-only), and the backend enforces it (viewers get `403` on writes; the
editor is read-only in the UI). This was the "role-based permissions" stretch, kept
minimal but real.

**Import via format-specific converters.** Uploads are normalized to the editor's
HTML on the server: `.md` through the `markdown` library, `.docx` through `mammoth`
(which maps Word styles to semantic HTML — headings, bold/italic, lists), and `.txt`
wrapped into paragraphs. `.docx` is binary, so it's converted before the UTF-8 text
path; every branch ends in the same HTML the editor already understands.

**Export on the client.** Markdown (via `turndown`) and PDF (via a hidden print
iframe) run entirely in the browser. This avoids heavy server-side PDF dependencies
(e.g. WeasyPrint's system libraries), keeping the Docker image small and the deploy
reliable.

**Database portability.** SQLAlchemy with a `DATABASE_URL` switch means SQLite for a
zero-setup local run and Postgres for persistent production, with no code changes.

## Data model

- **User** — `id, email (unique), name, password_hash`
- **Document** — `id, title, content (HTML), owner_id, created_at, updated_at`
- **Share** — `id, document_id, user_id, role`, unique on `(document_id, user_id)`

The unique constraint makes sharing idempotent: re-sharing with an existing
collaborator updates their role instead of creating duplicates.

## Validation & error handling

- Pydantic validates request bodies; emails are normalized to lowercase.
- Uploads are checked for extension, 1 MB size limit, and UTF-8 decodability.
- Auth failures → `401`; no-access → `403`; unknown doc/user → `404`; these surface
  as readable messages in the UI (login errors, share "no user with that email",
  rejected upload types, a dedicated "cannot open document" screen).

## What I intentionally deprioritized

- **Real-time co-editing / presence.** True OT/CRDT collaboration is a project on its
  own. I chose single-writer autosave, which is honest about its scope and still
  demonstrates the shared-access model. (See "next steps.")
- **Full auth (signup, email verification, password reset).** Seeded accounts are
  enough to exercise ownership and sharing.
- **Pixel-perfect PDF.** The print-based export is dependency-free and good enough to
  demonstrate the feature.

## What I'd build next with another 2–4 hours

1. **Presence indicators** — a lightweight WebSocket channel showing who else has the
   doc open (the smallest slice of "real-time" with high perceived value).
2. **Optimistic concurrency** — a `version` column + last-writer detection so two
   editors don't silently clobber each other.
3. **Document version history** — snapshot on save; diff/restore.
4. **A few frontend component tests** (React Testing Library) to complement the
   backend suite.
