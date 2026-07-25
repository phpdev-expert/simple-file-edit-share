# Walkthrough Video Script (~5 minutes)

The app grew well past the core, so this covers a lot. Target **4:45–5:15**. Segments
marked _(trim if tight)_ can be dropped to hit 5:00 — keep the ⭐ ones.

**Setup before recording**
- Two browser windows: **Window A** (Alice), **Window B** (incognito, for Bob).
- A sample `.docx` or `.md` on the desktop to import.
- Pre-load the live site once so it's warm (Render free tier sleeps): https://ajaia-docs-mkhz.onrender.com/
- Zoom the browser to ~110–125% so text is readable.
- Seeded accounts (password `password123`): `alice@demo.com`, `bob@demo.com`, `carol@demo.com`.

---

## 0:00 – 0:20 · Intro ⭐

> "This is Ajaia Docs — a collaborative document editor. React + TipTap on the front,
> FastAPI + Postgres on the back, JWT auth, deployed as a single service on Render.
> Beyond the core editor it does live editing, comments and suggestions, version
> history, and an AI chat over folders of documents. Let me show the main flow."

---

## 0:20 – 1:10 · Dashboard + editing ⭐

Sign in as **Alice**.

> "This is the workspace — a sidebar with All / Owned / Shared and Folders, a search
> bar, a notification bell, and a documents table with owner, access level, and
> last-modified. On the right, an overview of my documents."

Open a document (or **New document**), then type and format.

> "The editor is real rich text — bold, italic, underline, headings, lists — and it
> autosaves; you can see 'All changes saved'. I'll rename it in the title bar, and if I
> refresh, everything persists, because it's stored server-side in Postgres."

*(Refresh to prove persistence.)*

---

## 1:10 – 1:35 · Version history _(trim if tight)_

Click **History**.

> "Every edit is snapshotted as I work. From History I can see prior versions and
> restore any of them — and the restore itself is saved first, so it's reversible."

*(Restore a version to show it swap, then carry on.)*

---

## 1:35 – 2:00 · Import ⭐

Back to the dashboard → **Import file** → pick a `.docx`.

> "I can import a file into a new document. This Word doc is converted server-side with
> mammoth into editable rich text — headings, bold, lists preserved. Supported types
> are .txt, .md, and .docx, and that's stated in the UI."

---

## 2:00 – 2:50 · Folders + AI chat (RAG) ⭐⭐  — the AI-native piece

In the sidebar, create a **folder** and file a couple of documents into it (use the
folder selector in the editor, or create docs while the folder is selected).

> "Here's the AI-native part. I can group documents into a folder, which becomes a
> knowledge base. I'll click 'Chat with folder' and ask a question."

Ask something answerable from the folder's docs, e.g. *"What's the pricing and how do I
invite teammates?"*

> "The answer is grounded only in this folder's documents, and it cites which documents
> it used. On the backend that's retrieval-augmented generation — I pull the folder's
> contents into the prompt and call an LLM through OpenRouter. It's env-gated, so if no
> API key is set the rest of the app is unaffected and chat just shows a clear message."

---

## 2:50 – 3:35 · Sharing + notifications + live editing ⭐⭐

Open a doc → **Share** → add `bob@demo.com` as _Can edit_.

> "Sharing is by email with an edit or view-only role, enforced on the server."

Switch to **Window B** as **Bob**.

> "As Bob, there's a notification that Alice shared a document, and it shows under
> 'Shared with me'."

Open the same doc in both windows, place them side by side.

> "And it's live — you can see presence up here, who else is in the document. Watch:
> when Alice types…"

*(Type in Window A; show it appear in Window B.)*

> "…it syncs to Bob in real time over a WebSocket. Persistence still goes through
> autosave; this channel just propagates the live state."

---

## 3:35 – 4:05 · Comments + suggestions ⭐

In the doc, select some text → **Comments** panel.

> "Anyone with access — even view-only — can select text and leave a comment, or suggest
> an edit."

Switch to **Suggest edit**, propose a replacement, submit.

> "Here I suggest replacing this text. The owner or an editor sees it and can Accept —
> which rewrites the document — or dismiss it."

*(Click **Accept**; show the text change in the document.)*

> "Accepting applied the change and resolved the suggestion."

---

## 4:05 – 4:35 · Key decisions + how AI helped ⭐

*(Show ~2 files briefly — why, not line-by-line.)*

> "A couple of engineering notes. Access control lives in one helper — every route and
> the WebSocket resolve owner/editor/viewer through it, which is why the rules stay
> consistent and the tests are short. Document HTML is sanitized server-side on every
> save to prevent stored XSS, including in the PDF-export path. There are 35 automated
> tests across auth, sharing, versions, comments, folders, and the WebSocket.
>
> On AI: I used Claude Code to scaffold, write tests, and even drive a browser to QA
> flows and capture screenshots. But I didn't take output on faith — it produced a
> passlib/bcrypt combo that broke, which I pinned and re-ran; its first PDF export used
> an unsafe DOM-write, which I replaced with a sandboxed iframe; and my strict CSP
> blocked web fonts in production until I caught it in the console. Every 'it works' is
> backed by a test, a status code, or a screenshot."

---

## 4:35 – 5:00 · Deprioritized + close ⭐

> "What I deliberately left: live editing is presence plus last-writer-wins sync, not
> full CRDT conflict-free merge; folder chat stuffs documents into context rather than
> using a vector database — both are fine at this scale and are the honest next steps.
>
> That's Ajaia Docs — code, 35 tests, and a live deployment, all linked in the README.
> Thanks for watching."

---

### Fast path (if you can only do ~3 min)
Intro → editing + autosave + persistence → folders + AI chat → share + live editing +
comments/suggestions → one AI-workflow example → close. (Drop version history, import,
and the code walk.)
