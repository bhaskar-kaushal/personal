import { OP_LABEL, OutcomePill } from "./Ui";

const fmtScore = (s) => (s == null ? "—" : s.toFixed(3));

export default function ActivityTable({ rows, compact = false }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Time</th><th>Operation</th><th>Subject</th><th>Outcome</th>
            {!compact && <th style={{ textAlign: "right" }}>Score</th>}
            {!compact && <th>Detail</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.ts}-${r.op}-${r.subject}`}>
              <td style={{ whiteSpace: "nowrap" }}>
                {compact ? new Date(r.ts).toLocaleTimeString() : new Date(r.ts).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "medium" })}
              </td>
              <td>{OP_LABEL[r.op] || r.op}</td>
              <td className="mono">{r.subject}</td>
              <td><OutcomePill outcome={r.outcome} /></td>
              {!compact && <td className="num">{fmtScore(r.score)}</td>}
              {!compact && <td className="muted">{r.detail || ""}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
