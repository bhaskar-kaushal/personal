"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import Icon from "./Icon";
import { useApp } from "./AppProvider";

const NAV = [
  { label: "Operations", items: [
    { href: "/", icon: "home", text: "Overview" },
    { href: "/verify", icon: "check", text: "Access check", tag: "1:1" },
    { href: "/identify", icon: "search", text: "Identify", tag: "1:N" },
  ] },
  { label: "Administration", items: [
    { href: "/enroll", icon: "user-plus", text: "Enrollment" },
    { href: "/directory", icon: "users", text: "Directory", count: true },
    { href: "/activity", icon: "log", text: "Activity log" },
  ] },
  { label: "System", items: [{ href: "/about", icon: "info", text: "Policy & about" }] },
];

const HEALTH = {
  checking: ["", "Checking…"], ok: ["ok", "All systems operational"],
  degraded: ["warn", "Storage degraded"], down: ["bad", "Service unreachable"],
};

export default function AppShell({ children }) {
  const pathname = usePathname();
  const { gallery, health } = useApp();
  const [open, setOpen] = useState(false);
  const [dark, setDark] = useState(false);

  useEffect(() => {
    let saved = null;
    try { saved = localStorage.getItem("facegate.theme"); } catch { /* ignore */ }
    const initial = saved ? saved === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    setDark(initial);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }, [dark]);
  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    try { localStorage.setItem("facegate.theme", next ? "dark" : "light"); } catch { /* ignore */ }
  };
  const [healthTone, healthText] = HEALTH[health.state];

  return (
    <div className="app">
      <aside className={`sidebar${open ? " open" : ""}`} id="sidebar" aria-label="Primary">
        <div className="brand">
          <svg width="32" height="32" viewBox="0 0 32 32" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="var(--accent)" />
            <g transform="translate(5 5) scale(.917)" stroke="#fff" fill="none" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 8V6a2 2 0 0 1 2-2h2M16 4h2a2 2 0 0 1 2 2v2M20 16v2a2 2 0 0 1-2 2h-2M8 20H6a2 2 0 0 1-2-2v-2M9 10v1M15 10v1M9.5 15c.7.6 1.5 1 2.5 1s1.8-.4 2.5-1M12 10v3" />
            </g>
          </svg>
          <div>FaceGate<small>Identity console</small></div>
        </div>
        <nav className="nav">
          {NAV.map((group) => (
            <div key={group.label}>
              <div className="nav-label">{group.label}</div>
              {group.items.map((it) => {
                const active = it.href === "/" ? pathname === "/" : pathname.startsWith(it.href);
                return (
                  <Link key={it.href} href={it.href} aria-current={active ? "page" : undefined}>
                    <Icon name={it.icon} />{it.text}
                    {it.tag && <span className="muted" style={{ marginLeft: "auto", fontSize: 11 }}>{it.tag}</span>}
                    {it.count && <span className="count">{gallery ? gallery.length : "–"}</span>}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
        <div className="sidebar-foot">Demo build · compact model pack<br />Data reset daily</div>
      </aside>
      {open && <div className="scrim" onClick={() => setOpen(false)} />}

      <div className="main">
        <header className="topbar">
          <button className="btn ghost sm menu-btn" aria-label="Open navigation" aria-controls="sidebar"
            aria-expanded={open} onClick={() => setOpen(true)}><Icon name="menu" /></button>
          <span className="pill warn" title="This deployment is a public demo, not for real biometric data">
            <span className="dot" />Demo environment
          </span>
          <span className="spacer" />
          <span className={`pill ${healthTone}`} role="status" aria-live="polite"><span className="dot" />{healthText}</span>
          <button className="btn ghost sm" aria-label="Toggle dark mode" onClick={toggleTheme}><Icon name="moon" /></button>
        </header>
        <main className="content" tabIndex={-1}>{children}</main>
      </div>
    </div>
  );
}
