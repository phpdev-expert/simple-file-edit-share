import { useEffect, useState } from "react";
import { api, ApiError, Share } from "../api";

export default function ShareDialog({ docId, onClose }: { docId: number; onClose: () => void }) {
  const [shares, setShares] = useState<Share[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("editor");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setShares(await api.listShares(docId));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load collaborators");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.addShare(docId, email.trim(), role);
      setEmail("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not share");
    } finally {
      setBusy(false);
    }
  }

  async function remove(userId: number) {
    await api.removeShare(docId, userId);
    load();
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Share document</h3>

        <form onSubmit={add} className="row" style={{ gap: "0.5rem", alignItems: "stretch" }}>
          <input
            placeholder="teammate@demo.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            autoFocus
          />
          <select value={role} onChange={(e) => setRole(e.target.value)} style={{ width: "auto" }}>
            <option value="editor">Can edit</option>
            <option value="viewer">View only</option>
          </select>
          <button className="btn-primary" disabled={busy}>
            Share
          </button>
        </form>
        {error && <div className="error">{error}</div>}

        <div style={{ marginTop: "1rem" }}>
          {shares.length === 0 ? (
            <p className="muted small">Not shared with anyone yet.</p>
          ) : (
            shares.map((s) => (
              <div className="share-row" key={s.user.id}>
                <div>
                  <div>{s.user.name}</div>
                  <div className="muted small">{s.user.email}</div>
                </div>
                <div className="spacer" />
                <span className={`badge ${s.role === "viewer" ? "viewer" : "editor"}`}>
                  {s.role === "viewer" ? "View only" : "Can edit"}
                </span>
                <button
                  className="btn-secondary"
                  style={{ color: "var(--danger)", padding: "0.35rem 0.7rem" }}
                  onClick={() => remove(s.user.id)}
                >
                  Remove
                </button>
              </div>
            ))
          )}
        </div>

        <div className="row" style={{ marginTop: "1.25rem" }}>
          <div className="spacer" />
          <button onClick={onClose}>Done</button>
        </div>
      </div>
    </div>
  );
}
