import { ReactNode, useState } from "react";
import { User } from "../api";
import {
  IconChevronDown,
  IconGrid,
  IconLogo,
  IconLogout,
  IconShare,
  IconUser,
  IconUsers,
  IconSearch,
} from "./icons";

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
  search,
  onSearch,
  onSignOut,
  children,
}: {
  user: User;
  view: View;
  onView: (v: View) => void;
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
              className={`nav-item ${view === item.key ? "active" : ""}`}
              onClick={() => onView(item.key)}
            >
              {item.icon}
              {item.label}
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
