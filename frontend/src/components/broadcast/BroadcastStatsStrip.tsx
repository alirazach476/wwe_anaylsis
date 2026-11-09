import { useEffect, useState } from "react";

type Stat = {
  label: string;
  value: string | number;
  context?: string;
  spark?: number[];
};

function Spark({ values }: { values: number[] }) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const w = 72;
  const h = 28;
  const pts = values
    .map((v, i) => {
      const x = (i / Math.max(values.length - 1, 1)) * w;
      const y = h - (v / max) * (h - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <svg className="bc-stat-spark" width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden>
      <polyline fill="none" stroke="var(--event-primary)" strokeWidth="2" points={pts} />
    </svg>
  );
}

function AnimatedNumber({ value }: { value: string | number }) {
  const numeric = typeof value === "number" ? value : Number(String(value).replace(/[^\d.-]/g, ""));
  const isNum = typeof value === "number" || (!Number.isNaN(numeric) && String(value).match(/^\d[\d,]*$/));
  const [n, setN] = useState(0);

  useEffect(() => {
    if (!isNum) return;
    const target = typeof value === "number" ? value : numeric;
    const start = performance.now();
    const dur = 700;
    let raf = 0;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      setN(Math.round(target * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, isNum, numeric]);

  if (!isNum) return <>{value}</>;
  return <>{n.toLocaleString()}</>;
}

export function BroadcastStatsStrip({ stats }: { stats: Stat[] }) {
  return (
    <div className="bc-stats-strip">
      {stats.map((s) => (
        <div key={s.label} className="bc-stat">
          <div className="bc-stat-label">{s.label}</div>
          <div className="bc-stat-value">
            <AnimatedNumber value={s.value} />
          </div>
          {s.context ? <div className="bc-stat-context">{s.context}</div> : null}
          {s.spark ? <Spark values={s.spark} /> : null}
        </div>
      ))}
    </div>
  );
}
