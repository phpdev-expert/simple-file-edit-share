import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, DocSummary } from "../api";
import { useAuth } from "../auth";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [owned, setOwned] = useState<DocSummary[]>([]);
  const [shared, setShared] = useState<DocSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await api.listDocuments();
      setOwned(data.owned);
      setShared(data.shared);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function createDoc() {
    const doc = await api.createDocument();
    navigate(`/documents/${doc.id}`);
  }

  async function onImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-selecting the same file
    if (!file) return;
    try {
      const doc = await api.importFile(file);
      navigate(`/documents/${doc.id}`);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Import failed");
    }
  }

  async function onDelete(e: React.MouseEvent, id: number) {
    e.stopPropagation();
    if (!confirm("Delete this document? This cannot be undone.")) return;
    await api.deleteDocument(id);
    load();
  }

  return (
    <>
      <div className="topbar">
        <span className="brand">
          Ajaia<span className="dot">.</span>Docs
        </span>
        <div className="spacer" />
        <span className="muted small">{user?.name}</span>
        <button className="ghost" onClick={() => logout().then(() => navigate("/login"))}>
          Sign out
        </button>
      </div>

      <div className="container">
        <div className="row page-head">
          <h2>Documents</h2>
          <div className="spacer" />
          <button onClick={() => fileInput.current?.click()}>Import file</button>
          <button className="primary" onClick={createDoc}>
            New document
          </button>
          <input
            ref={fileInput}
            type="file"
            accept=".txt,.md,.docx"
            style={{ display: "none" }}
            onChange={onImport}
          />
        </div>
        <p className="muted small">Supported imports: .txt, .md and .docx files (max 5 MB).</p>

        {error && <div className="error">{error}</div>}
        {loading ? (
          <p className="muted">Loading…</p>
        ) : (
          <>
            <div className="section-title">Owned by me</div>
            <DocGrid docs={owned} onOpen={(id) => navigate(`/documents/${id}`)} onDelete={onDelete} emptyText="No documents yet — create one to get started." />

            <div className="section-title">Shared with me</div>
            <DocGrid docs={shared} onOpen={(id) => navigate(`/documents/${id}`)} emptyText="Nothing shared with you yet." />
          </>
        )}
      </div>
    </>
  );
}

function DocGrid({
  docs,
  onOpen,
  onDelete,
  emptyText,
}: {
  docs: DocSummary[];
  onOpen: (id: number) => void;
  onDelete?: (e: React.MouseEvent, id: number) => void;
  emptyText: string;
}) {
  if (docs.length === 0) return <div className="empty">{emptyText}</div>;
  return (
    <div className="doc-grid">
      {docs.map((d) => (
        <div key={d.id} className="doc-card" onClick={() => onOpen(d.id)}>
          <div className="title">{d.title}</div>
          {d.role !== "owner" && (
            <span className={`badge ${d.role === "viewer" ? "viewer" : ""}`}>
              {d.role === "viewer" ? "View only" : "Can edit"}
            </span>
          )}
          <div className="spacer" />
          <div className="row small muted">
            <span>
              {d.role === "owner" ? "You" : d.owner.name} · {new Date(d.updated_at).toLocaleDateString()}
            </span>
            {onDelete && (
              <>
                <div className="spacer" />
                <button className="ghost danger small" onClick={(e) => onDelete(e, d.id)}>
                  Delete
                </button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
