"use client";

import { useMemo, useState } from "react";
import { useApp } from "@/components/AppProvider";
import ActivityTable from "@/components/ActivityTable";
import Icon from "@/components/Icon";
import { Empty, Notice, OP_LABEL, PageHead } from "@/components/Ui";
import { clearActivity, toCsv } from "@/lib/activity";
import useActivity from "@/lib/useActivity";

const OUTCOMES = ["granted", "denied", "inconclusive", "enrolled", "error"];

export default function ActivityPage() {
  const { confirm, toast } = useApp();
  const all = useActivity();
  const [op, setOp] = useState("");
  const [outcome, setOutcome] = useState("");
  const [query, setQuery] = useState("");

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (all || []).filter((r) => (!op || r.op === op) && (!outcome || r.outcome === outcome) && (!q || String(r.subject).toLowerCase().includes(q)));
  }, [all, op, outcome, query]);

  function exportCsv() {
    const url = URL.createObjectURL(new Blob([toCsv(rows)], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `facegate-activity-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.append(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  }

  async function clear() {
    const ok = await confirm({ title: "Clear the activity log?", confirmLabel: "Clear log", danger: true,
      body: "This removes the log stored in this browser. It cannot be undone." });
    if (ok) { clearActivity(); toast("Activity log cleared"); }
  }

  return (
    <>
      <PageHead title="Activity log" sub="A local audit trail of decisions made in this browser. Images are never stored — only outcomes and scores." />
      <section className="card">
        <div className="toolbar">
          <input type="search" className="grow" placeholder="Search subject…" aria-label="Search subject" value={query} onChange={(e) => setQuery(e.target.value)} />
          <select aria-label="Filter by operation" value={op} onChange={(e) => setOp(e.target.value)}>
            <option value="">All operations</option>
            {Object.entries(OP_LABEL).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
          <select aria-label="Filter by outcome" value={outcome} onChange={(e) => setOutcome(e.target.value)}>
            <option value="">All outcomes</option>
            {OUTCOMES.map((v) => <option key={v} value={v}>{v[0].toUpperCase() + v.slice(1)}</option>)}
          </select>
          <span className="muted">{rows.length} event{rows.length === 1 ? "" : "s"}</span>
          <button className="btn sm" disabled={!rows.length} onClick={exportCsv}><Icon name="download" />Export CSV</button>
          <button className="btn sm danger" disabled={!all?.length} onClick={clear}>Clear log</button>
        </div>
        {rows.length ? <ActivityTable rows={rows} />
          : <Empty icon="log"><p>{all?.length ? "No events match these filters." : "No activity recorded yet."}</p></Empty>}
      </section>
      <Notice tone="info" icon="info" style={{ marginTop: 16 }}>
        <p>This log lives in your browser&apos;s local storage and is not a tamper-evident record. A production deployment needs a server-side, append-only audit store.</p>
      </Notice>
    </>
  );
}
