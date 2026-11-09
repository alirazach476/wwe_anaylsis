import { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";
import { api } from "../api";
import { BroadcastStatsStrip } from "../components/broadcast/BroadcastStatsStrip";
import { WrestlerNameLink } from "../components/WrestlerNameLink";
import { WrestlerPortrait } from "../components/WrestlerPortrait";
import { HISTORICAL_RECORDS, RECORD_CATEGORIES, type HistoricalRecord } from "../data/historicalRecords";
import { useFilters } from "../state/filters";
import { useEventTheme } from "../theme/EventThemeContext";
import { plotlyLayout, accentColor } from "../theme/chartTheme";

function HolderLinks({ holder }: { holder: string }) {
  const parts = String(holder || "")
    .split("/")
    .map((p) => p.replace(/\*$/, "").trim())
    .filter(Boolean);
  if (!parts.length) return <strong>—</strong>;
  return (
    <strong>
      {parts.map((p, i) => (
        <span key={`${p}-${i}`}>
          {i > 0 ? " / " : null}
          <WrestlerNameLink name={p} />
        </span>
      ))}
    </strong>
  );
}

export default function Timeline() {
  const { query } = useFilters();
  const { theme } = useEventTheme();
  const [overview, setOverview] = useState<any>(null);
  const [champs, setChamps] = useState<any>(null);
  const [warehouse, setWarehouse] = useState<any>(null);
  const [category, setCategory] = useState<(typeof RECORD_CATEGORIES)[number] | "All">("All");

  useEffect(() => {
    api.overview(query).then(setOverview);
    api.championships().then(setChamps);
    api.historicalRecords().then(setWarehouse).catch(() => setWarehouse(null));
  }, [query]);

  const filteredRecords = useMemo(() => {
    if (category === "All") return HISTORICAL_RECORDS;
    return HISTORICAL_RECORDS.filter((r) => r.category === category);
  }, [category]);

  const spotlight = useMemo(() => {
    const ids = ["most-world-titles", "longest-universal-reign", "heaviest", "lightest-mens", "shortest-wwe-reign"];
    return ids
      .map((id) => HISTORICAL_RECORDS.find((r) => r.id === id))
      .filter(Boolean) as HistoricalRecord[];
  }, []);

  if (!overview) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div className="bc-skeleton" style={{ height: 120 }} />
        <div className="bc-skeleton" style={{ height: 320 }} />
      </div>
    );
  }

  const accent = accentColor(theme);
  const pleWins = warehouse?.ple_most_title_wins || [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <BroadcastStatsStrip
        stats={[
          {
            label: "Landmark records",
            value: HISTORICAL_RECORDS.length,
            context: "Curated all-time WWE marks",
          },
          {
            label: "Avg attendance",
            value: overview.kpis.avg_attendance ?? "—",
            context: "Filtered known gates",
          },
          {
            label: "PLE title changes",
            value: champs?.recent_changes?.length ?? overview.kpis.title_changes ?? "—",
            context: "Recent / mart coverage",
          },
          {
            label: "Coverage",
            value:
              overview.kpis.year_from != null && overview.kpis.year_to != null
                ? `${overview.kpis.year_from}–${overview.kpis.year_to}`
                : "—",
            context: "Historical window",
          },
        ]}
      />

      <section className="bc-chart-panel">
        <h3>Signature historical records</h3>
        <p className="muted">
          Original all-time marks fans recognize — Cena’s 17, Reigns’ 1,316-day reign, heaviest & lightest billed weights, and more
        </p>
        <div className="hist-spotlight-grid">
          {spotlight.map((r) => (
            <article key={r.id} className="hist-spotlight-card">
              <div className="hist-spotlight-cat">{r.category}</div>
              <div className="hist-spotlight-value">{r.value}</div>
              <h4>{r.title}</h4>
              <div className="hist-spotlight-holder">
                <WrestlerPortrait name={r.holder.split("/")[0].trim()} size={44} showGenderBadge={false} />
                <div>
                  <HolderLinks holder={r.holder} />
                  {r.era ? <span>{r.era}</span> : null}
                </div>
              </div>
              <p>{r.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="bc-chart-panel">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h3 style={{ marginBottom: 4 }}>All-time record book</h3>
            <p className="muted" style={{ margin: 0 }}>
              Championships · physical extremes · specials · milestones
            </p>
          </div>
          <div className="filters">
            <button
              type="button"
              className={`tab${category === "All" ? " active" : ""}`}
              onClick={() => setCategory("All")}
            >
              All
            </button>
            {RECORD_CATEGORIES.map((c) => (
              <button
                key={c}
                type="button"
                className={`tab${category === c ? " active" : ""}`}
                onClick={() => setCategory(c)}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        <div className="hist-record-grid">
          {filteredRecords.map((r) => (
            <article key={r.id} className="hist-record-card" data-category={r.category}>
              <div className="hist-record-top">
                <span className="hist-record-cat">{r.category}</span>
                {r.era ? <span className="hist-record-era">{r.era}</span> : null}
              </div>
              <div className="hist-record-value">{r.value}</div>
              <h4>{r.title}</h4>
              <div className="hist-record-holder">
                <WrestlerPortrait name={r.holder.split("/")[0].replace(/\*$/, "").trim()} size={40} showGenderBadge={false} />
                <HolderLinks holder={r.holder} />
              </div>
              <p>{r.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(320px,1fr))", gap: 14 }}>
        <div className="bc-chart-panel">
          <h3>Events 2000–2027</h3>
          <p className="muted">PLE volume across the historical window</p>
          <Plot
            data={[
              {
                x: overview.by_year.map((r: any) => r.event_year),
                y: overview.by_year.map((r: any) => r.events),
                type: "scatter",
                mode: "lines+markers",
                fill: "tozeroy",
                line: { color: accent },
                marker: { size: 8, color: theme.accent },
                hovertemplate: "<b>%{x}</b><br>%{y} events<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 320 })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        {pleWins.length ? (
          <div className="bc-chart-panel">
            <h3>Most PLE title wins (warehouse)</h3>
            <p className="muted">{warehouse?.note || "Title changes recorded on PLE cards only"}</p>
            <Plot
              data={[
                {
                  x: pleWins.map((r: any) => r.ple_title_wins),
                  y: pleWins.map((r: any) => r.name),
                  type: "bar",
                  orientation: "h",
                  marker: { color: accent },
                  hovertemplate: "<b>%{y}</b><br>%{x} PLE title wins<extra></extra>",
                },
              ]}
              layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 40, l: 120, r: 16 } })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          </div>
        ) : null}
      </div>

      <div className="bc-chart-panel">
        <h3>Attendance & title-change coverage</h3>
        <p className="muted">
          Filtered total attendance: {Number(overview.kpis.total_attendance || 0).toLocaleString()} across{" "}
          {overview.kpis.attendance_known_events} events with known figures
          {overview.kpis.avg_attendance != null
            ? ` · avg ${Number(overview.kpis.avg_attendance).toLocaleString()} per event`
            : ""}
          .
        </p>
        {champs && (
          <p className="muted">
            PLE title-change rows tracked: {champs.recent_changes?.length ?? 0} in recent window (mart). Official
            all-time marks (Cena 17, Reigns 1,316 days, etc.) are listed above — warehouse counts are PLE-card only.
          </p>
        )}
      </div>
    </div>
  );
}
