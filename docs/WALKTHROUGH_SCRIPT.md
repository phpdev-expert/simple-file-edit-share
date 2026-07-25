# Walkthrough Video Script (~4 minutes)

Target length: **3:45–4:15**. Read naturally — the timings are a guide, not a metronome.
Have two browser windows ready: **Window A** (normal) logged out, **Window B**
(incognito) for the second user. Live URL: https://ajaia-docs-mkhz.onrender.com/

Seeded accounts (password `password123`): `alice@demo.com`, `bob@demo.com`, `carol@demo.com`.

---

## 0:00 – 0:20 · Intro

> "Hi — this is Ajaia Docs, a lightweight collaborative document editor built for the
> AI-Native Full Stack assignment. It's a React and TipTap frontend with a FastAPI
> backend, JWT auth, and Postgres, deployed as a single service on Render. Let me walk
> through the main flow, then a couple of implementation decisions and how I used AI."

*(Screen: the login page.)*

---

## 0:20 – 2:15 · Product demo (the core)

**Log in** *(type or show the pre-filled Alice credentials)*

> "I'll sign in as Alice. Accounts are seeded with hashed passwords — I'll come back to
> auth in a second."

**Dashboard**

> "This is the workspace. Left is navigation — all documents, the ones I own, and ones
> shared with me. There's search up top, a documents table with owner, access level and
> last-modified, and an overview panel showing how my documents split between owned and
> shared."

**Create + edit** *(click New document)*

> "Let me create a document. The editor supports real rich text — bold, italic,
> underline, headings, and bulleted and numbered lists."

*(Type a heading, some text, apply bold/italic, add a list.)*

> "Notice it autosaves — 'All changes saved' up here. I'll rename it in the title bar…
> and if I refresh, the content and formatting persist, because it's stored server-side."

*(Rename, then refresh the page to show persistence.)*

**Import** *(go back to dashboard → Import file → pick a .docx or .md)*

> "I can also import a file. I'll upload a Word document — the server converts it with
> mammoth into an editable rich-text document, preserving headings, bold, and lists.
> Supported types are .txt, .md, and .docx, and that's stated in the UI."

**Share** *(open a doc → Share → add `bob@demo.com` as 'Can edit')*

> "Now sharing. As the owner, I share by email and choose a role — 'Can edit' or
> 'View only'. I'll give Bob edit access."

**Switch to Bob** *(Window B / incognito → log in as bob@demo.com)*

> "In a separate session as Bob, the document now shows up under 'Shared with me', and
> because he's an editor, he can open and edit it."

**Access control** *(mention Carol — optionally log in as carol)*

> "Carol, who wasn't shared, doesn't see it at all — and if she tried the URL directly,
> the API returns 403. Access is enforced on the server, not just hidden in the UI."

**Export** *(back in a doc → Export → Markdown or PDF)*

> "Finally, I can export any document to Markdown or PDF."

---

## 2:15 – 3:10 · Key implementation decisions (talk over code — keep it brief)

*(Open the repo / editor. Show only these, ~15–20s each. Don't read code line by line.)*

**1. `backend/app/auth.py`**

> "The heart of sharing is one helper — `get_document_for_user`. Every document route
> goes through it to resolve the caller's role — owner, editor, or viewer — and return a
> consistent 403 or 404. Centralizing it is why the access rules stay correct and are
> easy to test. Auth itself is a signed JWT, accepted as a Bearer token or an HTTP-only
> cookie."

**2. `backend/app/security.py`**

> "Because document content is HTML that gets re-rendered — including into the PDF-export
> iframe — I sanitize it server-side on every save and import with an allow-list. That
> closes a stored-XSS path that could otherwise steal a token."

**3. `backend/tests/test_sharing.py`**

> "And the access-control matrix is covered by automated tests — non-collaborators get
> 403, viewers are read-only, only owners can delete or re-share. Seventeen tests total."

---

## 3:10 – 3:45 · AI workflow

> "On AI: I used Claude Code as a pair to scaffold the app, write the tests, and even
> drive a browser to QA the flows and capture screenshots. It sped up the boilerplate —
> models, the API client, the editor wiring — enormously.
>
> But I didn't take output blindly. Three concrete examples: it produced a passlib and
> bcrypt combo that broke at runtime, so I pinned a compatible version and re-ran the
> suite. Its first PDF export used a legacy synchronous document-writing API — an XSS
> anti-pattern — so I rewrote it to a sandboxed iframe. And my strict CSP initially
> blocked the web fonts in production — I caught that in the browser console and fixed the
> font-src directive. Every 'it works' is backed by a test, an HTTP status, or a
> screenshot."

---

## 3:45 – 4:10 · Deprioritized + close

> "What I deliberately cut: real-time co-editing with live cursors — that's a project on
> its own, so I chose single-writer autosave. I also kept auth to seeded accounts instead
> of full signup. With another few hours I'd add presence indicators and document version
> history.
>
> That's Ajaia Docs — the code, tests, and a live deployment are all linked in the README.
> Thanks for watching."

---

### Quick recording checklist
- [ ] Two windows ready (Alice in one, Bob incognito)
- [ ] A sample `.docx` or `.md` on the desktop to import
- [ ] Live site pre-loaded (avoid the cold-start wait on camera — hit it once first)
- [ ] Zoom the browser to ~110–125% so text is readable
- [ ] Keep the code portion to ~3 files, focus on *why* not *how*
