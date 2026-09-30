"use client";

import Link from "next/link";
import { useApp } from "@/components/AppProvider";
import ActivityTable from "@/components/ActivityTable";
import Icon from "@/components/Icon";
import { Empty, PageHead, Skeleton } from "@/components/Ui";
import { CAPACITY } from "@/lib/constants";
import useActivity from "@/lib/useActivity";

function Kpi({ label, value, sub, meter }) {
  return (
    <div className="card kpi">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      <div className="sub">{sub}</div>
      {meter != null && <div className={`meter ${meter > 90 ? "bad" : meter > 70 ? "warn" : ""}`}><i style={{ width: `${meter}%` }} /></div>}
    </div>
  );
}

function Quick({ href, icon, title, sub }) {
  return (
    <Link href={href} className="btn" style={{ justifyContent: "flex-start", textAlign: "left", height: "auto", padding: 12 }}>
      <Icon name={icon} />
      <span><div>{title}</div><div className="muted" style={{ fontWeight: 400, fontSize: 12 }}>{sub}</div></span>
    </Link>
  );
}

export default function Overview() {
  const { gallery, galleryError } = useApp();
  const rows = useActivity();
  const decisions = (rows || []).filter((r) => r.op === "verify" || r.op === "identify");
  const count = (o) => decisions.filter((r) => r.outcome === o).length;
  const loading = rows === null || (gallery === null && !galleryError);

  return (
    <>
      <PageHead title="Overview" sub="Operational summary for this workstation. Decision statistics are computed from the activity recorded in this browser.">
        <Link href="/verify" className="btn primary"><Icon name="check" />New access check</Link>
      </PageHead>

      <div className="grid kpis">
        {loading ? [0, 1, 2, 3].map((i) => <div key={i} className="card kpi"><Skeleton height={14} width="60%" /><Skeleton height={28} /></div>) : (
          <>
            <Kpi label="Enrolled people" value={gallery ? gallery.length : "—"} sub={galleryError || `of ${CAPACITY} demo capacity`}
              meter={gallery ? (gallery.length / CAPACITY) * 100 : 0} />
            <Kpi label="Access granted" value={count("granted")} sub="this browser" />
            <Kpi label="Access denied" value={count("denied")} sub="this browser" />
            <Kpi label="Inconclusive" value={count("inconclusive")} sub="no face / not enrolled / empty" />
          </>
        )}
      </div>

      <div className="grid split" style={{ marginTop: 16 }}>
        <section className="card">
          <div className="card-h"><h2>Recent activity</h2><Link href="/activity">View all</Link></div>
          {rows && rows.length ? <ActivityTable rows={rows.slice(0, 6)} compact />
            : <Empty icon="log"><p>No activity yet. Run an access check to see it here.</p></Empty>}
        </section>
        <section className="card">
          <div className="card-h"><h2>Quick actions</h2></div>
          <div className="card-b" style={{ display: "grid", gap: 10 }}>
            <Quick href="/verify" icon="check" title="Verify a claimed identity" sub="1:1 — badge-in style check" />
            <Quick href="/identify" icon="search" title="Identify an unknown face" sub="1:N — search the whole gallery" />
            <Quick href="/enroll" icon="user-plus" title="Enroll a person" sub="Capture up to 5 reference photos" />
          </div>
        </section>
      </div>
    </>
  );
}
