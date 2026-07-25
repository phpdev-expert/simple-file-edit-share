import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, Notification } from "../api";
import { IconBell } from "./icons";

function timeAgo(iso: string) {
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export default function NotificationBell() {
  const navigate = useNavigate();
  const [items, setItems] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  async function refresh() {
    try {
      const data = await api.getNotifications();
      setItems(data.items);
      setUnread(data.unread);
    } catch {
      /* not fatal */
    }
  }

  useEffect(() => {
    refresh();
    timer.current = setInterval(refresh, 20000); // light polling
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, []);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && unread > 0) {
      await api.markNotificationsRead();
      setUnread(0);
      setItems((prev) => prev.map((n) => ({ ...n, read: true })));
    }
  }

  return (
    <div className="userbox">
      <button className="bell-btn" onClick={toggle} title="Notifications">
        <IconBell size={19} />
        {unread > 0 && <span className="bell-badge">{unread}</span>}
      </button>
      {open && (
        <div className="dropdown-menu notif-menu" onMouseLeave={() => setOpen(false)}>
          <div className="menu-head">
            <div className="user-name">Notifications</div>
          </div>
          {items.length === 0 ? (
            <div className="notif-empty">You're all caught up.</div>
          ) : (
            items.slice(0, 8).map((n) => (
              <button
                key={n.id}
                className="notif-item"
                onClick={() => {
                  setOpen(false);
                  if (n.document_id) navigate(`/documents/${n.document_id}`);
                }}
              >
                <span className="notif-msg">{n.message}</span>
                <span className="notif-time">{timeAgo(n.created_at)}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
