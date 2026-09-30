"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { useApp } from "@/components/AppProvider";
import CaptureWidget, { CaptureTips } from "@/components/CaptureWidget";
import Icon from "@/components/Icon";
import { Notice, PageHead, Pill, Spinner } from "@/components/Ui";
import * as api from "@/lib/api";
import { addActivity } from "@/lib/activity";
import { ID_PATTERN, ID_RULE, MAX_ENROLL_IMAGES } from "@/lib/constants";

export default function EnrollPage() {
  const { refreshGallery, confirm, toast } = useApp();
  const widget = useRef(null);
  const [personId, setPersonId] = useState("");
  const [idError, setIdError] = useState("");
  const [consent, setConsent] = useState(false);
  const [blobs, setBlobs] = useState([]);
  const [busy, setBusy] = useState(false);
  const [outcome, setOutcome] = useState(null);   // { ok, id?, count?, message? }

  const n = blobs.length;
  const counterTone = n >= 3 ? "ok" : n ? "info" : "";

  async function submit() {
    const id = personId.trim();
    if (!ID_PATTERN.test(id)) return setIdError(ID_RULE);
    const ids = await refreshGallery();
    if (ids?.includes(id)) {
      const ok = await confirm({
        title: `Add samples to “${id}”?`, confirmLabel: "Add samples",
        body: "This person is already enrolled. New photos are added to their existing template and change future matching.",
      });
      if (!ok) return;
    }
    setBusy(true);
    setOutcome(null);
    try {
      const rec = await api.enroll(id, blobs);
      setOutcome({ ok: true, id, count: rec.num_samples });
      addActivity({ op: "enroll", subject: id, outcome: "enrolled", detail: `${rec.num_samples} samples` });
      toast(`Enrolled ${id}`, "ok");
      widget.current?.stopCamera();
      widget.current?.clear();
      setPersonId("");
      setConsent(false);
      refreshGallery();
    } catch (e) {
      const message = e.status === 422 ? `${e.message} Enrollment is all-or-nothing — retake any photo where the face isn't clearly visible.` : e.message;
      setOutcome({ ok: false, message });
      addActivity({ op: "enroll", subject: id, outcome: "error", detail: e.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead title="Enrollment" sub="Register a person by capturing reference photos. Three or more varied shots give a more robust template." />
      <div className="grid split">
        <section className="card">
          <div className="card-b">
            <div className="field">
              <label htmlFor="e-id">Person ID</label>
              <input id="e-id" type="text" autoComplete="off" autoCapitalize="off" spellCheck={false} placeholder="e.g. emp-10482"
                value={personId} aria-invalid={idError ? true : undefined} aria-describedby="e-id-hint e-id-err"
                onChange={(e) => { setPersonId(e.target.value); setIdError(""); }} />
              {idError && <div className="err" id="e-id-err">{idError}</div>}
              <div className="hint" id="e-id-hint">Letters, digits, “_”, “.”, “-”. Use an opaque ID (e.g. employee number), not a full name.</div>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <h3>Reference photos</h3><Pill tone={counterTone}>{n} / {MAX_ENROLL_IMAGES} photos</Pill>
            </div>
            <CaptureWidget ref={widget} max={MAX_ENROLL_IMAGES} onChange={setBlobs} />
            <CaptureTips />
          </div>
        </section>
        <section className="card">
          <div className="card-h"><h2>Consent &amp; submit</h2></div>
          <div className="card-b">
            <Notice style={{ marginBottom: 14 }}>
              <p>Public demo: use synthetic or sample faces only.</p>
              <p>Everything is wiped daily and offers no privacy guarantees.</p>
            </Notice>
            <label className="check" htmlFor="e-consent">
              <input id="e-consent" type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
              <span>The person has given informed consent to have their facial template stored for identity verification, and I am authorised to enroll them.</span>
            </label>
            <div style={{ marginTop: 16 }}>
              <button className="btn primary" disabled={busy || !n || !personId.trim() || !consent} onClick={submit}>
                {busy ? <><Spinner />Enrolling…</> : <><Icon name="user-plus" />Enroll person</>}
              </button>
            </div>
            <div style={{ marginTop: 12 }} aria-live="polite">
              {outcome?.ok && (
                <Notice tone="ok" icon="check">
                  <p>{outcome.id} is enrolled with {outcome.count} reference photo{outcome.count === 1 ? "" : "s"}.</p>
                  <p><Link href={`/verify?id=${encodeURIComponent(outcome.id)}`}>Run an access check →</Link></p>
                </Notice>
              )}
              {outcome && !outcome.ok && (
                <Notice tone="bad" role="alert"><p>Enrollment failed. Nothing was stored.</p><p>{outcome.message}</p></Notice>
              )}
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
