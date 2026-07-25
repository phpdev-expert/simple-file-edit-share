import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, DocSummary } from "../api";
import { useAuth } from "../auth";
import AppShell, { View } from "../components/AppShell";
import { IconFile, IconPlus, IconTrash, IconUpload } from "../components/icons";

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function accessLabel(role: string) {
  if (role === "owner") return { text: "Owner", cls: "owner" };
  if (role === "viewer") return { text: "View only", cls: "viewer" };
  return { text: "Can edit", cls: "editor" };
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [owned, setOwned] = useState<DocSummary[]>([]);
  const [shared, setShared] = useState<DocSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [view, setView] = useState<View>("all");
  const [search, setSearch] = useState("");
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

  const all = useMemo(() => [...owned, ...shared], [owned, shared]);
  const recent = useMemo(
    () =>
      [...all]
        .sort((a, b) => +new Date(b.updated_at) - +new Date(a.updated_at))
        .slice(0, 3),
    [all]
  );

  const rows = useMemo(() => {
    const base = view === "owned" ? owned : view === "shared" ? shared : all;
    const q = search.trim().toLowerCase();
    const filtered = q ? base.filter((d) => d.title.toLowerCase().includes(q)) : base;
    return [...filtered].sort((a, b) => +new Date(b.updated_at) - +new Date(a.updated_at));
  }, [view, owned, shared, all, search]);

  async function createDoc() {
    const doc = await api.createDocument();
    navigate(`/documents/${doc.id}`);
  }

  async function onImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
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

  const title = view === "owned" ? "Owned by me" : view === "shared" ? "Shared with me" : "All documents";
  const total = all.length;
  const ownedPct = total ? Math.round((owned.length / total) * 100) : 0;

  if (!user) return null;

  return (
    <AppShell
      user={user}
      view={view}
      onView={setView}
      search={search}
      onSearch={setSearch}
      onSignOut={() => logout().then(() => navigate("/login"))}
    >
      <div className="content-head">
        <div>
          <h1>{title}</h1>
          <p className="muted">All of your documents live here — create, import, and share.</p>
        </div>
        <div className="head-actions">
          <button className="btn-secondary" onClick={() => fileInput.current?.click()}>
            <IconUpload size={18} /> Import file
          </button>
          <button className="btn-primary" onClick={createDoc}>
            <IconPlus size={18} /> New document
          </button>
          <input
            ref={fileInput}
            type="file"
            accept=".txt,.md,.docx"
            style={{ display: "none" }}
            onChange={onImport}
          />
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {recent.length > 0 && (
        <>
          <div className="subhead">Recently modified</div>
          <div className="recent-row">
            {recent.map((d) => (
              <button key={d.id} className="recent-card" onClick={() => navigate(`/documents/${d.id}`)}>
                <span className="recent-ico">
                  <IconFile size={20} />
                </span>
                <span className="recent-meta">
                  <span className="recent-title">{d.title}</span>
                  <span className="muted small">
                    {d.role === "owner" ? "You" : d.owner.name} · {fmtDate(d.updated_at)}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </>
      )}

      <div className="content-body">
        <section className="panel">
          <div className="panel-head">
            <h3>{title}</h3>
            <span className="count-pill">{rows.length}</span>
          </div>

          {loading ? (
            <div className="empty">Loading…</div>
          ) : rows.length === 0 ? (
            <div className="empty">
              {search ? "No documents match your search." : "No documents here yet."}
            </div>
          ) : (
            <table className="doc-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Owner</th>
                  <th>Access</th>
                  <th>Modified</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((d) => {
                  const a = accessLabel(d.role);
                  return (
                    <tr key={d.id} onClick={() => navigate(`/documents/${d.id}`)}>
                      <td className="cell-name">
                        <span className="file-ico">
                          <IconFile size={18} />
                        </span>
                        <span className="doc-name">{d.title}</span>
                      </td>
                      <td className="muted">{d.role === "owner" ? "You" : d.owner.name}</td>
                      <td>
                        <span className={`badge ${a.cls}`}>{a.text}</span>
                      </td>
                      <td className="muted">{fmtDate(d.updated_at)}</td>
                      <td className="cell-actions">
                        {d.role === "owner" && (
                          <button
                            className="icon-btn danger"
                            title="Delete"
                            onClick={(e) => onDelete(e, d.id)}
                          >
                            <IconTrash size={17} />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </section>

        <aside className="rail">
          <div className="rail-card">
            <div className="rail-title">Overview</div>
            <div className="stat-big">{total}</div>
            <div className="muted small">total documents</div>

            <div className="split-bar">
              <span className="seg owned" style={{ width: `${ownedPct}%` }} />
              <span className="seg shared" style={{ width: `${100 - ownedPct}%` }} />
            </div>

            <ul className="rail-list">
              <li>
                <span className="dot owned" /> Owned by me
                <span className="spacer" />
                <strong>{owned.length}</strong>
              </li>
              <li>
                <span className="dot shared" /> Shared with me
                <span className="spacer" />
                <strong>{shared.length}</strong>
              </li>
            </ul>
          </div>

          <div className="rail-card promo">
            <div className="rail-title">Tip</div>
            <p className="muted small">
              Import a <code>.txt</code>, <code>.md</code>, or <code>.docx</code> file to turn it
              into an editable document, then share it by email.
            </p>
            <button className="btn-primary full" onClick={() => fileInput.current?.click()}>
              <IconUpload size={17} /> Import a file
            </button>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
