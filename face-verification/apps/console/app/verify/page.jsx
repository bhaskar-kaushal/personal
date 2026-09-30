"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useApp } from "@/components/AppProvider";
import { CaptureTips } from "@/components/CaptureWidget";
import CaptureWidget from "@/components/CaptureWidget";
import Decision, { DecisionIdle } from "@/components/Decision";
import Icon from "@/components/Icon";
import { Notice, PageHead, Spinner } from "@/components/Ui";
import * as api from "@/lib/api";
import { ID_PATTERN, ID_RULE } from "@/lib/constants";
import useDecisionRunner from "@/lib/useDecisionRunner";

function VerifyView() {
  const params = useSearchParams();
  const { gallery, refreshGallery } = useApp();
  const [personId, setPersonId] = useState(params.get("id") || "");
  const [idError, setIdError] = useState("");
  const [blobs, setBlobs] = useState([]);
  const { busy, body, error, run } = useDecisionRunner("verify");

  useEffect(() => { refreshGallery(); }, [refreshGallery]);

  function submit() {
    const id = personId.trim();
    if (!ID_PATTERN.test(id)) return setIdError(ID_RULE);
    run(id, () => api.verify(id, blobs[0]));
  }

  return (
    <>
      <PageHead title="Access check" sub="1:1 verification: confirm that the person at the door is the person they claim to be." />
      <div className="grid split">
        <section className="card">
          <div className="card-b">
            <div className="field">
              <label htmlFor="v-id">Claimed person ID</label>
              <input id="v-id" type="text" list="person-ids" autoComplete="off" autoCapitalize="off" spellCheck={false}
                placeholder="e.g. alice" value={personId} aria-invalid={idError ? true : undefined} aria-describedby="v-id-err"
                onChange={(e) => { setPersonId(e.target.value); setIdError(""); }} />
              {idError && <div className="err" id="v-id-err">{idError}</div>}
              <div className="hint">Scan a badge or type the ID. Suggestions come from the directory.</div>
              <datalist id="person-ids">{(gallery || []).map((g) => <option key={g} value={g} />)}</datalist>
            </div>
            <CaptureWidget max={1} onChange={setBlobs} />
            <CaptureTips />
            <div style={{ marginTop: 16 }}>
              <button className="btn primary" disabled={busy || !blobs.length || !personId.trim()} onClick={submit}>
                {busy ? <><Spinner />Analysing…</> : <><Icon name="check" />Run access check</>}
              </button>
            </div>
          </div>
        </section>
        <div>
          {error ? <Notice tone="bad" role="alert"><p>The check could not be completed.</p><p>{error}</p></Notice>
            : body ? <Decision mode="verify" body={body} />
              : <DecisionIdle>Capture a photo and press “Run access check”.</DecisionIdle>}
        </div>
      </div>
    </>
  );
}

export default function VerifyPage() {
  return <Suspense><VerifyView /></Suspense>;
}
