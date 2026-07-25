import { useEffect, useState } from "react";
import { Editor } from "@tiptap/react";
import { api, ApiError, Comment } from "../api";
import { IconComment } from "./icons";

// Find the first occurrence of `text` in the editor and replace it in place.
// Works when the quote lies within a single text node (the common case).
function replaceFirst(editor: Editor, text: string, replacement: string): boolean {
  if (!text) return false;
  let range: { from: number; to: number } | null = null;
  editor.state.doc.descendants((node, pos) => {
    if (range || !node.isText || !node.text) return;
    const i = node.text.indexOf(text);
    if (i >= 0) {
      range = { from: pos + i, to: pos + i + text.length };
      return false;
    }
  });
  if (!range) return false;
  editor.chain().focus().setTextSelection(range).insertContent(replacement).run();
  return true;
}

export default function CommentsPanel({
  docId,
  editor,
  canEdit,
  onClose,
}: {
  docId: number;
  editor: Editor | null;
  canEdit: boolean;
  onClose: () => void;
}) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [mode, setMode] = useState<"comment" | "suggestion">("comment");
  const [selection, setSelection] = useState("");
  const [body, setBody] = useState("");
  const [suggested, setSuggested] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    try {
      setComments(await api.getComments(docId));
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    load();
  }, [docId]);

  // Track the current text selection in the editor for anchoring.
  useEffect(() => {
    if (!editor) return;
    const update = () => {
      const { from, to } = editor.state.selection;
      setSelection(from === to ? "" : editor.state.doc.textBetween(from, to, " "));
    };
    update();
    editor.on("selectionUpdate", update);
    return () => {
      editor.off("selectionUpdate", update);
    };
  }, [editor]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!selection) {
      setError("Select some text in the document first.");
      return;
    }
    if (mode === "comment" && !body.trim()) {
      setError("Write a comment.");
      return;
    }
    if (mode === "suggestion" && !suggested.trim()) {
      setError("Enter the replacement text.");
      return;
    }
    setBusy(true);
    try {
      await api.addComment(docId, {
        kind: mode,
        quote: selection,
        body: body.trim(),
        suggested_text: mode === "suggestion" ? suggested.trim() : undefined,
      });
      setBody("");
      setSuggested("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save");
    } finally {
      setBusy(false);
    }
  }

  async function resolve(c: Comment) {
    await api.resolveComment(docId, c.id);
    load();
  }

  async function accept(c: Comment) {
    if (!editor || !c.suggested_text) return;
    const ok = replaceFirst(editor, c.quote, c.suggested_text);
    if (!ok) {
      alert("Couldn't locate the original text — it may have changed since the suggestion.");
      return;
    }
    await api.acceptSuggestion(docId, c.id); // autosave persists the replacement
    load();
  }

  const open = comments.filter((c) => !c.resolved);
  const resolved = comments.filter((c) => c.resolved);

  return (
    <div className="chat-panel comments-panel">
      <div className="chat-head">
        <div className="chat-title">
          <IconComment size={18} /> Comments &amp; suggestions
        </div>
        <button className="icon-btn" onClick={onClose} title="Close">
          ✕
        </button>
      </div>

      <form className="comment-compose" onSubmit={submit}>
        <div className="mode-toggle">
          <button
            type="button"
            className={mode === "comment" ? "active" : ""}
            onClick={() => setMode("comment")}
          >
            Comment
          </button>
          <button
            type="button"
            className={mode === "suggestion" ? "active" : ""}
            onClick={() => setMode("suggestion")}
          >
            Suggest edit
          </button>
        </div>
        <div className={`selection-quote ${selection ? "" : "muted"}`}>
          {selection ? `“${selection}”` : "Select text in the document to anchor this…"}
        </div>
        {mode === "suggestion" && (
          <input
            placeholder="Replace with…"
            value={suggested}
            onChange={(e) => setSuggested(e.target.value)}
          />
        )}
        <input
          placeholder={mode === "suggestion" ? "Reason (optional)" : "Add a comment…"}
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
        {error && <div className="error">{error}</div>}
        <button className="btn-primary full" disabled={busy || !selection}>
          {mode === "suggestion" ? "Suggest edit" : "Comment"}
        </button>
      </form>

      <div className="comment-list">
        {open.length === 0 && resolved.length === 0 && (
          <div className="chat-hint">No comments yet. Select text and add one above.</div>
        )}
        {open.map((c) => (
          <CommentCard key={c.id} c={c} canEdit={canEdit} onResolve={resolve} onAccept={accept} />
        ))}
        {resolved.length > 0 && <div className="comment-divider">Resolved</div>}
        {resolved.map((c) => (
          <CommentCard key={c.id} c={c} canEdit={canEdit} resolved onResolve={resolve} onAccept={accept} />
        ))}
      </div>
    </div>
  );
}

function CommentCard({
  c,
  canEdit,
  resolved,
  onResolve,
  onAccept,
}: {
  c: Comment;
  canEdit: boolean;
  resolved?: boolean;
  onResolve: (c: Comment) => void;
  onAccept: (c: Comment) => void;
}) {
  return (
    <div className={`comment-card ${resolved ? "is-resolved" : ""}`}>
      <div className="comment-top">
        <span className={`badge ${c.kind === "suggestion" ? "editor" : "owner"}`}>
          {c.kind === "suggestion" ? "Suggestion" : "Comment"}
        </span>
        <span className="muted small">{c.author_name}</span>
      </div>
      {c.quote && <div className="comment-quote">“{c.quote}”</div>}
      {c.kind === "suggestion" ? (
        <div className="comment-suggest">
          → <strong>{c.suggested_text}</strong>
          {c.body && <div className="muted small">{c.body}</div>}
        </div>
      ) : (
        <div className="comment-body">{c.body}</div>
      )}
      {!resolved && (
        <div className="comment-actions">
          {c.kind === "suggestion" && canEdit && (
            <button className="btn-primary" onClick={() => onAccept(c)}>
              Accept
            </button>
          )}
          <button className="btn-secondary" onClick={() => onResolve(c)}>
            {c.kind === "suggestion" ? "Dismiss" : "Resolve"}
          </button>
        </div>
      )}
    </div>
  );
}
