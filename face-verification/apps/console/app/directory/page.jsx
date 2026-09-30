"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useApp } from "@/components/AppProvider";
import Icon from "@/components/Icon";
import { Empty, Notice, PageHead, Pill, Skeleton } from "@/components/Ui";
import { CAPACITY } from "@/lib/constants";

export default function DirectoryPage() {
  const { gallery, galleryError, refreshGallery } = useApp();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => { setLoading(true); await refreshGallery(); setLoading(false); };
  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const all = gallery || [];
  const q = query.trim().toLowerCase();
  const ids = all.filter((i) => i.toLowerCase().includes(q));

  let body;
  if (loading && !gallery) {
    body = <div className="card-b">{[0, 1, 2].map((i) => <Skeleton key={i} />)}</div>;
  } else if (galleryError && !gallery) {
    body = <div className="card-b"><Notice tone="bad"><p>The directory could not be loaded.</p><p>{galleryError}</p></Notice></div>;
  } else if (!ids.length) {
    body = (
      <Empty icon="users">
        <p>{all.length ? "No one matches your search." : "Nobody is enrolled yet."}</p>
        {!all.length && <p style={{ marginTop: 10 }}><Link className="btn primary" href="/enroll">Enroll the first person</Link></p>}
      </Empty>
    );
  } else {
    body = (
      <div className="table-wrap">
        <table>
          <thead><tr><th>Person</th><th>Status</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
          <tbody>
            {ids.map((id) => (
              <tr key={id}>
                <td><span className="avatar" aria-hidden="true">{id.slice(0, 2).toUpperCase()}</span><span className="mono">{id}</span></td>
                <td><Pill tone="ok" dot>Enrolled</Pill></td>
                <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                  <Link className="btn sm" href={`/verify?id=${encodeURIComponent(id)}`}>Verify</Link>{" "}
                  <Link className="btn sm" href="/enroll" title="Add more samples by enrolling with the same ID">Add samples</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <>
      <PageHead title="Directory" sub="Everyone currently enrolled in the gallery.">
        <Link href="/enroll" className="btn primary"><Icon name="user-plus" />Enroll person</Link>
      </PageHead>
      <section className="card">
        <div className="toolbar">
          <input type="search" className="grow" placeholder="Search person ID…" aria-label="Search person ID" value={query} onChange={(e) => setQuery(e.target.value)} />
          <span className="muted">{ids.length} of {all.length} · capacity {all.length}/{CAPACITY}</span>
          <button className="btn sm" onClick={load}><Icon name="refresh" />Refresh</button>
        </div>
        {body}
      </section>
    </>
  );
}
