import { useEffect, useState } from "react";
import { api, DocVersion } from "../api";

function when(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function VersionHistory({
  docId,
  canEdit,
  onClose,
  onRestored,
}: {
  docId: number;
  canEdit: boolean;
  onClose: () => void;
  onRestored: (html: string) => void;
}) {
  const [versions, setVersions] = useState<DocVersion[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getVersions(docId).then(setVersions).catch(() => setVersions([]));
  }, [docId]);

  async function restore(v: DocVersion) {
    if (!confirm(`Restore the version from ${when(v.created_at)}? Current state is saved first.`))
      return;
    setBusy(true);
    try {
      const doc = await api.restoreVersion(docId, v.id);
      onRestored(doc.content);
      onClose();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Version history</h3>
        {versions.length === 0 ? (
          <p className="muted small">No saved versions yet — edits are snapshotted as you work.</p>
        ) : (
          <div className="version-list">
            {versions.map((v, i) => (
              <div className="version-row" key={v.id}>
                <div>
                  <div className="version-when">
                    {when(v.created_at)}
                    {i === 0 && <span className="badge editor" style={{ marginLeft: 8 }}>Latest</span>}
                  </div>
                  <div className="muted small">
                    {v.author_name || "Unknown"} · "{v.title}"
                  </div>
                </div>
                <div className="spacer" />
                {canEdit && (
                  <button className="btn-secondary" disabled={busy} onClick={() => restore(v)}>
                    Restore
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
        <div className="row" style={{ marginTop: "1.25rem" }}>
          <div className="spacer" />
          <button onClick={onClose}>Done</button>
        </div>
      </div>
    </div>
  );
}
