import { PageHead } from "@/components/Ui";
import { CAPACITY, MAX_ENROLL_IMAGES } from "@/lib/constants";

export const metadata = { title: "Policy & about" };

const PARAMS = [
  ["Decision threshold (cosine)", "0.40 default; shown with every decision"],
  ["Model pack", "InsightFace buffalo_sc (compact)"],
  ["Photos per enrollment", `1–${MAX_ENROLL_IMAGES}`],
  ["Gallery capacity", `${CAPACITY} people`],
  ["Max upload", "6 MB (auto-downscaled)"],
  ["Data retention", "Gallery wiped daily at 03:00 UTC"],
];

const CHECKLIST = [
  "Authenticate operators and add role-based access; this demo’s endpoints are public.",
  "Calibrate the threshold on your own population and cameras against a target false-accept rate.",
  "Add liveness / anti-spoofing; a printed photo or a screen can defeat a matcher alone.",
  "Obtain a commercially licensed model — the bundled InsightFace weights are non-commercial research only.",
  "Comply with biometric privacy law (consent, retention, deletion rights, DPIA) in your jurisdictions.",
  "Provide a manual fallback for people the system cannot recognise, and log every decision server-side.",
];

export default function AboutPage() {
  return (
    <>
      <PageHead title="Policy & about" sub="How this system decides, and what it is (and isn’t) suitable for." />
      <div className="grid cols-2">
        <section className="card">
          <div className="card-h"><h2>How decisions are made</h2></div>
          <div className="card-b" style={{ display: "grid", gap: 10, color: "var(--text-2)" }}>
            <p>1. The largest face in the photo is detected and aligned to a canonical 112×112 crop.</p>
            <p>2. A 512-dimension embedding is computed and compared to the enrolled template by cosine similarity.</p>
            <p>3. The claim is accepted only when the score meets the threshold. Missing faces and missing enrollments are reported as inconclusive — never as a low score.</p>
          </div>
        </section>
        <section className="card">
          <div className="card-h"><h2>Operating parameters</h2></div>
          <table><tbody>
            {PARAMS.map(([k, v]) => <tr key={k}><td style={{ width: "42%", color: "var(--text-2)" }}>{k}</td><td>{v}</td></tr>)}
          </tbody></table>
        </section>
        <section className="card" style={{ gridColumn: "1 / -1" }}>
          <div className="card-h"><h2>Before any real deployment</h2></div>
          <div className="card-b" style={{ display: "grid", gap: 8, color: "var(--text-2)" }}>
            {CHECKLIST.map((c) => <p key={c}>• {c}</p>)}
          </div>
        </section>
      </div>
    </>
  );
}
