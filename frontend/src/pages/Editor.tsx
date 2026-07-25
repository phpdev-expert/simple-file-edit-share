import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useEditor, EditorContent, Editor as TiptapEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import { api, ApiError, DocDetail } from "../api";
import ShareDialog from "../components/ShareDialog";
import VersionHistory from "../components/VersionHistory";
import { IconHistory } from "../components/icons";
import { useDocRealtime } from "../useDocRealtime";
import { exportMarkdown, exportPdf } from "../export";

type SaveState = "idle" | "saving" | "saved" | "error";

export default function EditorPage() {
  const { id } = useParams();
  const docId = Number(id);
  const navigate = useNavigate();

  const [doc, setDoc] = useState<DocDetail | null>(null);
  const [title, setTitle] = useState("");
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [loadError, setLoadError] = useState("");
  const [showShare, setShowShare] = useState(false);
  const [showExport, setShowExport] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const canEdit = doc?.role === "owner" || doc?.role === "editor";
  const isOwner = doc?.role === "owner";
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const editor = useEditor(
    {
      extensions: [StarterKit, Underline],
      content: "",
      editable: false,
      editorProps: { attributes: { class: "ProseMirror" } },
    },
    []
  );

  // Live presence + content sync (once the doc is loaded so access is known).
  const { presence } = useDocRealtime(docId, doc ? editor : null, canEdit);

  // Load the document once, then hydrate the editor.
  useEffect(() => {
    let active = true;
    api
      .getDocument(docId)
      .then((d) => {
        if (!active) return;
        setDoc(d);
        setTitle(d.title);
        editor?.commands.setContent(d.content || "<p></p>");
        editor?.setEditable(d.role !== "viewer");
      })
      .catch((e) => setLoadError(e instanceof ApiError ? e.message : "Could not open document"));
    return () => {
      active = false;
    };
  }, [docId, editor]);

  const persist = useCallback(
    async (patch: { title?: string; content?: string }) => {
      setSaveState("saving");
      try {
        const updated = await api.updateDocument(docId, patch);
        setDoc((prev) => (prev ? { ...prev, updated_at: updated.updated_at } : prev));
        setSaveState("saved");
      } catch (e) {
        setSaveState("error");
      }
    },
    [docId]
  );

  // Debounced autosave on content changes.
  useEffect(() => {
    if (!editor || !canEdit) return;
    const onUpdate = ({ editor }: { editor: TiptapEditor }) => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
      setSaveState("saving");
      const html = editor.getHTML();
      saveTimer.current = setTimeout(() => persist({ content: html }), 800);
    };
    editor.on("update", onUpdate);
    return () => {
      editor.off("update", onUpdate);
    };
  }, [editor, canEdit, persist]);

  function onTitleBlur() {
    if (doc && title.trim() && title !== doc.title) {
      persist({ title: title.trim() });
      setDoc({ ...doc, title: title.trim() });
    } else if (doc) {
      setTitle(doc.title);
    }
  }

  if (loadError) {
    return (
      <div className="center">
        <div className="login-card">
          <h1>Cannot open document</h1>
          <p className="muted">{loadError}</p>
          <button className="btn-primary full" onClick={() => navigate("/")}>
            Back to documents
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="editor-topbar">
        <button className="btn-secondary" onClick={() => navigate("/")}>
          ← All docs
        </button>
        <input
          className="doc-title-input"
          value={title}
          disabled={!isOwner}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={onTitleBlur}
          onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
        />
        <span className="save-status">
          {saveState === "saving" && "Saving…"}
          {saveState === "saved" && <span className="ok">✓ All changes saved</span>}
          {saveState === "error" && <span style={{ color: "var(--danger)" }}>Save failed</span>}
          {saveState === "idle" && !canEdit && "View only"}
        </span>
        <div className="spacer" />
        {presence.length > 0 && (
          <div className="presence" title={`${presence.length} here: ${presence.map((p) => p.name).join(", ")}`}>
            {presence.slice(0, 4).map((p) => (
              <span key={p.id} className="presence-avatar" title={p.name}>
                {p.name.slice(0, 1).toUpperCase()}
              </span>
            ))}
            <span className="presence-label">
              {presence.length === 1 ? "Only you" : `${presence.length} editing`}
            </span>
          </div>
        )}
        <button className="btn-secondary" onClick={() => setShowHistory(true)} title="Version history">
          <IconHistory size={17} /> History
        </button>
        <div className="dropdown">
          <button onClick={() => setShowExport((v) => !v)}>Export ▾</button>
          {showExport && (
            <div className="dropdown-menu" onMouseLeave={() => setShowExport(false)}>
              <button
                onClick={() => {
                  editor && exportMarkdown(title, editor.getHTML());
                  setShowExport(false);
                }}
              >
                Markdown (.md)
              </button>
              <button
                onClick={() => {
                  editor && exportPdf(title, editor.getHTML());
                  setShowExport(false);
                }}
              >
                PDF (print)
              </button>
            </div>
          )}
        </div>
        {isOwner && (
          <button className="btn-primary" onClick={() => setShowShare(true)}>
            Share
          </button>
        )}
      </div>

      {canEdit && editor && <Toolbar editor={editor} />}

      <div className="editor-scroll">
        <div className="paper">
          <EditorContent editor={editor} />
        </div>
      </div>

      {showShare && <ShareDialog docId={docId} onClose={() => setShowShare(false)} />}
      {showHistory && (
        <VersionHistory
          docId={docId}
          canEdit={canEdit}
          onClose={() => setShowHistory(false)}
          onRestored={(html) => editor?.commands.setContent(html || "<p></p>")}
        />
      )}
    </>
  );
}

function Toolbar({ editor }: { editor: TiptapEditor }) {
  // Re-render the toolbar when selection/formatting state changes.
  const [, force] = useState(0);
  useEffect(() => {
    const rerender = () => force((n) => n + 1);
    editor.on("selectionUpdate", rerender);
    editor.on("transaction", rerender);
    return () => {
      editor.off("selectionUpdate", rerender);
      editor.off("transaction", rerender);
    };
  }, [editor]);

  const btn = (label: string, isActive: boolean, onClick: () => void, title: string) => (
    <button className={isActive ? "active" : ""} title={title} onMouseDown={(e) => e.preventDefault()} onClick={onClick}>
      {label}
    </button>
  );

  return (
    <div className="toolbar">
      {btn("B", editor.isActive("bold"), () => editor.chain().focus().toggleBold().run(), "Bold")}
      {btn("I", editor.isActive("italic"), () => editor.chain().focus().toggleItalic().run(), "Italic")}
      {btn("U", editor.isActive("underline"), () => editor.chain().focus().toggleUnderline().run(), "Underline")}
      <div className="divider" />
      {btn("H1", editor.isActive("heading", { level: 1 }), () => editor.chain().focus().toggleHeading({ level: 1 }).run(), "Heading 1")}
      {btn("H2", editor.isActive("heading", { level: 2 }), () => editor.chain().focus().toggleHeading({ level: 2 }).run(), "Heading 2")}
      {btn("¶", editor.isActive("paragraph"), () => editor.chain().focus().setParagraph().run(), "Paragraph")}
      <div className="divider" />
      {btn("• List", editor.isActive("bulletList"), () => editor.chain().focus().toggleBulletList().run(), "Bulleted list")}
      {btn("1. List", editor.isActive("orderedList"), () => editor.chain().focus().toggleOrderedList().run(), "Numbered list")}
    </div>
  );
}
