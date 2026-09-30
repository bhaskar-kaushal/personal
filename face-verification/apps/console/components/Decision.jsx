import Icon from "./Icon";

// key: [tone, verdict, icon, explanation]
const OUTCOMES = {
  match_verify: ["ok", "ACCESS GRANTED", "tick", "The face matches the enrolled identity above the required threshold."],
  no_match_verify: ["bad", "ACCESS DENIED", "x", "The face does not match the claimed identity."],
  match_identify: ["ok", "IDENTIFIED", "tick", "Best gallery match is above the required threshold."],
  no_match_identify: ["bad", "NOT RECOGNISED", "x", "No enrolled person matched above the threshold. The closest candidate is not reported as an identity."],
  no_face: ["warn", "NO FACE DETECTED", "help", "The check was inconclusive — this is not a mismatch. Retake the photo with the face clearly visible."],
  not_enrolled: ["warn", "NOT ENROLLED", "help", "There is no enrollment for this person ID. Enroll them first or check the ID."],
  empty_gallery: ["warn", "GALLERY EMPTY", "help", "Nobody is enrolled yet, so there is nothing to search."],
};

export function describeDecision(mode, body) {
  const key = body.status === "match" || body.status === "no_match" ? `${body.status}_${mode}` : body.status;
  const [tone, verdict, icon, why] = OUTCOMES[key] || ["warn", String(body.status).toUpperCase(), "help", ""];
  return { tone, verdict, icon, why, outcome: tone === "ok" ? "granted" : tone === "bad" ? "denied" : "inconclusive" };
}

const pct = (v) => `${Math.max(0, Math.min(1, v)) * 100}%`;
const fmt = (s) => (s == null ? "—" : s.toFixed(3));

export function DecisionIdle({ children }) {
  return <div className="card decision-idle"><Icon name="face" size={36} /><p>{children}</p></div>;
}

export default function Decision({ mode, body }) {
  const { tone, verdict, icon, why } = describeDecision(mode, body);
  const scored = typeof body.score === "number";
  const t = body.threshold;
  const subject = mode === "verify" ? body.person_id : body.identified ? body.person_id : null;
  const margin = scored && t != null ? body.score - t : null;

  return (
    <div className={`decision ${tone}`} role="status" aria-live="polite">
      <div className="icon"><Icon name={icon} /></div>
      <div className="verdict">{verdict}</div>
      {subject && <div className="who">{subject}</div>}
      <p className="why">{why}</p>
      {scored && (
        <div className="gauge">
          <div className="gauge-bar" role="img" aria-label={`Similarity ${fmt(body.score)} against threshold ${t}`}>
            <div className="gauge-fill" style={{ width: pct(body.score) }} />
            <div className="gauge-tick" style={{ left: pct(t) }} title={`Threshold ${t}`} />
          </div>
          <div className="gauge-legend"><span>0</span><span>Threshold {t.toFixed(2)}</span><span>1.0</span></div>
        </div>
      )}
      <div className="facts">
        <div className="fact"><b>{fmt(body.score)}</b><span>Similarity</span></div>
        <div className="fact"><b>{t != null ? t.toFixed(2) : "—"}</b><span>Threshold</span></div>
        {mode === "identify"
          ? <div className="fact"><b>{body.num_candidates ?? "—"}</b><span>Candidates searched</span></div>
          : <div className="fact"><b>{margin == null ? "—" : `${margin >= 0 ? "+" : ""}${margin.toFixed(3)}`}</b><span>Margin</span></div>}
      </div>
    </div>
  );
}
