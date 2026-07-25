# AI Workflow Note

## Tools used

- **Claude Code (Opus)** as the primary pair — scaffolding the FastAPI + React app,
  writing the access-control layer, tests, and docs.
- **Chrome DevTools (via MCP)** driven by the agent to load the running app, click
  through login → dashboard → editor → share, capture screenshots, and confirm zero
  console errors — i.e. AI-driven manual QA, not just codegen.

## Where AI materially sped things up

- **Boilerplate and wiring.** SQLAlchemy models, Pydantic schemas, the typed
  `fetch` client, the TipTap editor + toolbar, and the Vite/Docker/Render config are
  all mechanical work that AI produced quickly and consistently, letting me spend
  attention on the design decisions instead.
- **Test scaffolding.** The pytest fixtures (throwaway SQLite DB, per-user logged-in
  `TestClient`s) and the sharing/permission test matrix were generated fast, which
  made it cheap to assert the 403/404/idempotency edge cases explicitly.
- **Verification loop.** Using the browser through MCP, the app was exercised like a
  real user and screenshots were captured for the README — collapsing a normally
  manual QA pass into the same session.

## AI output I changed or rejected

- **passlib + bcrypt version break.** The first dependency set produced a runtime
  error (`bcrypt` 4.x dropped the attribute passlib probes for its version, surfacing
  as a bogus "password too long" error). I pinned `bcrypt==4.0.1` against
  `passlib==1.7.4` and re-ran the suite to confirm green.
- **Pydantic `role` field.** The initial `DocumentDetail` schema made `role` required
  and set it *after* `model_validate`, which raised a validation error. I changed
  `role` to a defaulted field that's populated per-request — a deliberate fix, not a
  blind retry.
- **Unsafe DOM write for PDF export.** The first export implementation used a legacy
  synchronous document-writing API, an XSS/perf anti-pattern (a security hook flagged
  it). I rewrote it to render into an off-screen `<iframe srcdoc>` and print that
  frame instead.
- **Scope discipline.** AI can happily sprawl toward "every Google Docs feature." I
  held the line on the deliberate cuts (no real-time OT, no full auth) and documented
  them rather than shipping half-built versions.

## How I verified correctness, UX, and reliability

- **Automated tests** (`pytest`, 13 passing) covering JWT auth (token issuance,
  Bearer-header access, rejection of tampered tokens) and the access-control core:
  non-collaborators get 403, sharing grants read/edit, viewers are read-only,
  non-owners can't delete or manage shares, unknown emails 404, shares are
  idempotent, and unauthenticated requests 401.
- **End-to-end API checks** with `curl` + cookie jars across three users, asserting
  the exact status codes (Bob 200 on a shared doc, Carol 403).
- **Real-browser QA** via Chrome DevTools MCP: logged in, rendered a formatted
  document (heading/bold/italic/underline/list all preserved), opened the share
  dialog and confirmed the seeded collaborator, and checked the console was clean.
- **Import correctness** confirmed by uploading Markdown and `.docx` files and
  asserting the converted HTML (`<h1>`, `<strong>`, `<em>`, `<ul>`) plus rejection of
  an unsupported type.

The throughline: AI accelerated production, but every claim of "it works" is backed
by a test run, an HTTP status, or a screenshot — not by assertion.
