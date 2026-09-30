import Icon from "./Icon";

export function PageHead({ title, sub, children }) {
  return (
    <div className="page-head">
      <div><h1>{title}</h1>{sub && <p>{sub}</p>}</div>
      {children && <div style={{ display: "flex", gap: 8 }}>{children}</div>}
    </div>
  );
}

export function Notice({ tone = "warn", icon = "alert", children, role, style }) {
  const cls = tone === "warn" ? "notice" : `notice ${tone}`;
  return <div className={cls} role={role} style={style}><Icon name={icon} /><div>{children}</div></div>;
}

export function Pill({ tone = "", dot, children }) {
  return <span className={`pill ${tone}`}>{dot && <span className="dot" />}{children}</span>;
}

export function Empty({ icon = "face", children }) {
  return <div className="empty"><Icon name={icon} />{children}</div>;
}

export function Skeleton({ height = 34, width, style }) {
  return <div className="skeleton" style={{ height, width, marginBottom: 10, ...style }} />;
}

export function Spinner() { return <span className="spinner" aria-hidden="true" />; }

export const OP_LABEL = { verify: "Access check (1:1)", identify: "Identify (1:N)", enroll: "Enrollment" };

const OUTCOME = {
  granted: ["ok", "Granted"], denied: ["bad", "Denied"], inconclusive: ["warn", "Inconclusive"],
  enrolled: ["info", "Enrolled"], error: ["bad", "Error"],
};
export function OutcomePill({ outcome }) {
  const [tone, text] = OUTCOME[outcome] || ["", outcome];
  return <Pill tone={tone} dot>{text}</Pill>;
}
