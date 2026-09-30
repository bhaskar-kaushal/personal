const PATHS = {
  home: "M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
  check: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z M8.5 12l2.5 2.5 4.5-5",
  search: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14z M21 21l-4.5-4.5",
  "user-plus": "M9 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8z M2 21a7 7 0 0 1 14 0 M19 8v6 M16 11h6",
  users: "M9 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8z M2 21a7 7 0 0 1 14 0 M17 4a4 4 0 0 1 0 8 M22 21a7 7 0 0 0-4-6.3",
  log: "M6 3h9l4 4v14H6z M14 3v5h5 M9 13h7 M9 17h7",
  info: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M12 11v6 M12 7.5v.01",
  camera: "M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M12 9a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",
  upload: "M12 16V4 M7 9l5-5 5 5 M4 20h16",
  x: "M6 6l12 12 M18 6L6 18",
  tick: "M5 12.5l4.5 4.5L19 7.5",
  alert: "M12 3l10 18H2z M12 10v5 M12 18v.01",
  help: "M9 9a3 3 0 1 1 4.5 2.6c-1 .6-1.5 1.2-1.5 2.4 M12 18v.01",
  menu: "M4 6h16 M4 12h16 M4 18h16",
  moon: "M21 13a9 9 0 1 1-10-10 7 7 0 0 0 10 10z",
  download: "M12 4v12 M7 11l5 5 5-5 M4 20h16",
  refresh: "M20 11a8 8 0 0 0-14.5-4 M4 5v4h4 M4 13a8 8 0 0 0 14.5 4 M20 19v-4h-4",
  face: "M4 8V6a2 2 0 0 1 2-2h2 M16 4h2a2 2 0 0 1 2 2v2 M20 16v2a2 2 0 0 1-2 2h-2 M8 20H6a2 2 0 0 1-2-2v-2 M9 10v1 M15 10v1 M9.5 15c.7.6 1.5 1 2.5 1s1.8-.4 2.5-1 M12 10v3",
};

export default function Icon({ name, size, className }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true" focusable="false">
      <path d={PATHS[name]} />
    </svg>
  );
}
