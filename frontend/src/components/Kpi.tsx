export function Kpi({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {hint ? <div className="muted" style={{ marginTop: 8, fontSize: "0.78rem" }}>{hint}</div> : null}
    </div>
  );
}
