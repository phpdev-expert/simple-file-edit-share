import { ReactNode, useState } from "react";
import { Folder, User } from "../api";
import {
  IconChevronDown,
  IconFolder,
  IconGrid,
  IconLogo,
  IconLogout,
  IconPlus,
  IconUser,
  IconUsers,
  IconSearch,
} from "./icons";
import NotificationBell from "./NotificationBell";

export type View = "all" | "owned" | "shared";

const NAV: { key: View; label: string; icon: ReactNode }[] = [
  { key: "all", label: "All documents", icon: <IconGrid /> },
  { key: "owned", label: "Owned by me", icon: <IconUser /> },
  { key: "shared", label: "Shared with me", icon: <IconUsers /> },
];

function initials(name: string) {
  return name.slice(0, 2).toUpperCase();
}

export default function AppShell({
  user,
  view,
  onView,
  folders,
  folderId,
  onSelectFolder,
  onNewFolder,
  search,
  onSearch,
  onSignOut,
  children,
}: {
  user: User;
  view: View;
  onView: (v: View) => void;
  folders: Folder[];
  folderId: number | null;
  onSelectFolder: (id: number) => void;
  onNewFolder: () => void;
  search: string;
  onSearch: (s: string) => void;
  onSignOut: () => void;
  children: ReactNode;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <IconLogo />
          <span>
            Ajaia<span className="brand-accent"> Docs</span>
          </span>
        </div>

        <nav className="nav-group">
          <div className="nav-label">Menu</div>
          {NAV.map((item) => (
            <button
              key={item.key}
              className={`nav-item ${view === item.key && folderId === null ? "active" : ""}`}
              onClick={() => onView(item.key)}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <nav className="nav-group folders-group">
          <div className="nav-label">
            Folders
            <button className="folder-add" onClick={onNewFolder} title="New folder">
              <IconPlus size={15} />
            </button>
          </div>
          {folders.length === 0 && <div className="folder-empty">No folders yet</div>}
          {folders.map((f) => (
            <button
              key={f.id}
              className={`nav-item ${folderId === f.id ? "active" : ""}`}
              onClick={() => onSelectFolder(f.id)}
            >
              <IconFolder />
              <span className="folder-name">{f.name}</span>
              <span className="folder-count">{f.doc_count}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-foot">
          <div className="nav-label">Account</div>
          <button className="nav-item" onClick={onSignOut}>
            <IconLogout />
            Sign out
          </button>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="search">
            <IconSearch size={18} />
            <input
              placeholder="Search documents…"
              value={search}
              onChange={(e) => onSearch(e.target.value)}
            />
          </div>
          <div className="spacer" />
          <NotificationBell />
          <div className="userbox">
            <button className="user-btn" onClick={() => setMenuOpen((v) => !v)}>
              <span className="avatar">{initials(user.name)}</span>
              <span className="user-name">{user.name}</span>
              <IconChevronDown size={16} />
            </button>
            {menuOpen && (
              <div className="dropdown-menu" onMouseLeave={() => setMenuOpen(false)}>
                <div className="menu-head">
                  <div className="user-name">{user.name}</div>
                  <div className="menu-mail">{user.email}</div>
                </div>
                <button onClick={onSignOut}>
                  <IconLogout size={16} /> Sign out
                </button>
              </div>
            )}
          </div>
        </header>

        <div className="content">{children}</div>
      </div>
    </div>
  );
}
