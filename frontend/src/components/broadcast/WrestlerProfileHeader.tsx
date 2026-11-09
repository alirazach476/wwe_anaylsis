import { WrestlerPortrait } from "../WrestlerPortrait";

export function WrestlerProfileHeader({
  name,
  subtitle,
  stats,
}: {
  name: string;
  subtitle?: string;
  stats?: { label: string; value: string | number }[];
}) {
  return (
    <section className="event-hero" style={{ minHeight: 280, gridTemplateColumns: "160px 1fr" }}>
      <div style={{ display: "grid", placeItems: "center" }}>
        <div className="bc-cutout" style={{ width: 140, height: 160 }}>
          <WrestlerPortrait name={name} size={128} />
        </div>
      </div>
      <div>
        <div className="event-hero-badge">Wrestler profile</div>
        <h1 style={{ fontSize: "clamp(2.2rem, 5vw, 3.6rem)" }}>{name}</h1>
        {subtitle ? <p className="muted">{subtitle}</p> : null}
        {stats?.length ? (
          <div className="event-hero-strip" style={{ marginTop: 16 }}>
            {stats.map((s) => (
              <span key={s.label}>
                <strong>{s.label}</strong>
                {s.value}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
