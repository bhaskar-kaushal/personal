"use client";

import { useState } from "react";
import CaptureWidget, { CaptureTips } from "@/components/CaptureWidget";
import Decision, { DecisionIdle } from "@/components/Decision";
import Icon from "@/components/Icon";
import { Notice, PageHead, Spinner } from "@/components/Ui";
import * as api from "@/lib/api";
import useDecisionRunner from "@/lib/useDecisionRunner";

export default function IdentifyPage() {
  const [blobs, setBlobs] = useState([]);
  const { busy, body, error, run } = useDecisionRunner("identify");

  return (
    <>
      <PageHead title="Identify" sub="1:N search: find who this is among everyone enrolled. Use for lookup, not as a substitute for a claimed-ID check." />
      <div className="grid split">
        <section className="card">
          <div className="card-b">
            <CaptureWidget max={1} onChange={setBlobs} />
            <CaptureTips />
            <div style={{ marginTop: 16 }}>
              <button className="btn primary" disabled={busy || !blobs.length} onClick={() => run(null, () => api.identify(blobs[0]))}>
                {busy ? <><Spinner />Analysing…</> : <><Icon name="search" />Search gallery</>}
              </button>
            </div>
          </div>
        </section>
        <div>
          {error ? <Notice tone="bad" role="alert"><p>The check could not be completed.</p><p>{error}</p></Notice>
            : body ? <Decision mode="identify" body={body} />
              : <DecisionIdle>Capture a photo and press “Search gallery”.</DecisionIdle>}
          <Notice tone="info" icon="info" style={{ marginTop: 12 }}>
            <p>False accepts compound across every enrolled person, so 1:N should run at a stricter threshold than 1:1.</p>
            <p>Treat a match as a lead to confirm, especially for access decisions.</p>
          </Notice>
        </div>
      </div>
    </>
  );
}
