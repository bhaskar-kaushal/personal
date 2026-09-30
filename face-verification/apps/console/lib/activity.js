// Local audit trail. Stores outcomes and scores only — never images.
const KEY = "facegate.activity.v1";
const MAX = 500;

export function loadActivity() {
  try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch { return []; }
}

export function addActivity(entry) {
  const rows = [{ ts: Date.now(), ...entry }, ...loadActivity()].slice(0, MAX);
  try { localStorage.setItem(KEY, JSON.stringify(rows)); } catch { /* storage full or blocked */ }
  window.dispatchEvent(new Event("facegate:activity"));
}

export function clearActivity() {
  try { localStorage.removeItem(KEY); } catch { /* ignore */ }
  window.dispatchEvent(new Event("facegate:activity"));
}

export function toCsv(rows) {
  const esc = (v) => {
    let s = String(v ?? "");
    if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`; // neutralise spreadsheet formula injection
    return `"${s.replaceAll('"', '""')}"`;
  };
  const head = ["timestamp", "operation", "subject", "outcome", "score", "threshold", "detail"];
  const lines = rows.map((r) =>
    [new Date(r.ts).toISOString(), r.op, r.subject, r.outcome, r.score, r.threshold, r.detail].map(esc).join(","));
  return [head.join(","), ...lines].join("\n");
}
