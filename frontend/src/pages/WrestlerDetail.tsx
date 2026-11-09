import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Plot from "react-plotly.js";
import { api } from "../api";
import { BroadcastStatsStrip } from "../components/broadcast/BroadcastStatsStrip";
import { PremiumSportsDataTable } from "../components/broadcast/PremiumSportsDataTable";
import { WrestlerProfileHeader } from "../components/broadcast/WrestlerProfileHeader";
import { useEventTheme } from "../theme/EventThemeContext";
import { plotlyLayout, accentColor } from "../theme/chartTheme";

export default function WrestlerDetail() {
  const { wrestlerId } = useParams();
  const navigate = useNavigate();
  const { theme } = useEventTheme();
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!wrestlerId) return;
    api.wrestler(wrestlerId).then(setData).catch((e) => setErr(String(e)));
  }, [wrestlerId]);

  const history = data?.match_history || [];
  const byYear = useMemo(() => {
    const map = new Map<number, { matches: number; wins: number }>();
    for (const m of history) {
      const y = Number(m.event_year);
      if (!y) continue;
      const cur = map.get(y) || { matches: 0, wins: 0 };
      cur.matches += 1;
      if (m.result === "win") cur.wins += 1;
      map.set(y, cur);
    }
    return Array.from(map.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([year, v]) => ({ year, ...v }));
  }, [history]);

  const typeDist = useMemo(() => {
    const map = new Map<string, number>();
    for (const m of history) {
      const t = m.match_type_group || "other";
      map.set(t, (map.get(t) || 0) + 1);
    }
    return Array.from(map.entries()).map(([type, count]) => ({ type, count }));
  }, [history]);

  const wm = history.filter((m: any) => String(m.event_series || m.event_name || "").toLowerCase().includes("wrestlemania")).length;
  const rr = history.filter((m: any) => String(m.event_series || m.event_name || "").toLowerCase().includes("royal rumble")).length;
  const events = new Set(history.map((m: any) => m.event_id).filter(Boolean)).size;

  if (err) return <div className="bc-empty"><h4>Profile error</h4><p>{err}</p></div>;
  if (!data) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div className="bc-skeleton" style={{ height: 280 }} />
        <div className="bc-skeleton" style={{ height: 120 }} />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <WrestlerProfileHeader
        name={data.canonical_name}
        subtitle={`Active ${data.first_year}–${data.last_year} in the PLE dataset`}
        stats={[
          { label: "Matches", value: data.matches },
          { label: "Wins", value: data.wins },
          { label: "Win %", value: data.win_pct != null ? `${(data.win_pct * 100).toFixed(1)}%` : "—" },
          { label: "Main events", value: data.main_events ?? "—" },
        ]}
      />
      <Link className="btn ghost" to="/wrestlers" style={{ alignSelf: "flex-start" }}>
        ← Back to wrestlers
      </Link>

      <BroadcastStatsStrip
        stats={[
          { label: "Total matches", value: data.matches, spark: byYear.map((r) => r.matches) },
          { label: "Wins", value: data.wins, spark: byYear.map((r) => r.wins) },
          { label: "Win %", value: data.win_pct != null ? `${(data.win_pct * 100).toFixed(1)}%` : "—" },
          { label: "Main events", value: data.main_events ?? "—" },
          { label: "WrestleMania*", value: wm, context: "From history sample" },
          { label: "Royal Rumble*", value: rr, context: "From history sample" },
          { label: "Events*", value: events, context: "Distinct events in sample" },
          { label: "Title matches", value: data.title_matches ?? "—" },
        ]}
      />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: 14 }}>
        <div className="bc-chart-panel">
          <h3>Finishers</h3>
          <p className="muted">Primary finishing moves</p>
          {(data.finishers || []).length ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
              {(data.finishers as string[]).map((m) => (
                <span key={m} className="bc-pill gold">
                  {m}
                </span>
              ))}
            </div>
          ) : (
            <div className="bc-empty" style={{ marginTop: 8 }}>
              Finisher catalog not listed for this name yet
            </div>
          )}
        </div>
        <div className="bc-chart-panel">
          <h3>Signature moves</h3>
          <p className="muted">Trademark offense</p>
          {(data.signature_moves || []).length ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
              {(data.signature_moves as string[]).map((m) => (
                <span key={m} className="bc-pill primary">
                  {m}
                </span>
              ))}
            </div>
          ) : (
            <div className="bc-empty" style={{ marginTop: 8 }}>
              Signature moves not listed for this name yet
            </div>
          )}
        </div>
        <div className="bc-chart-panel">
          <h3>Managers &amp; allies</h3>
          <p className="muted">From curated notes + PLE cards “(with …)”</p>
          {(data.managers || []).length ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
              {(data.managers as string[]).map((m) => (
                <span key={m} className="bc-pill">
                  {m}
                </span>
              ))}
            </div>
          ) : (
            <div className="bc-empty" style={{ marginTop: 8 }}>
              No managers recorded on PLE cards for this wrestler
            </div>
          )}
          {(data.clients || []).length ? (
            <>
              <h4 style={{ margin: "14px 0 6px", fontFamily: "var(--font-display)", letterSpacing: "0.06em" }}>
                Notable clients
              </h4>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {(data.clients as string[]).map((m) => (
                  <span key={m} className="bc-pill gold">
                    {m}
                  </span>
                ))}
              </div>
            </>
          ) : null}
          {(data.managers_from_card || []).length ? (
            <p className="muted" style={{ marginTop: 12, fontSize: "0.8rem" }}>
              Card appearances:{" "}
              {(data.managers_from_card as { name: string; appearances: number }[])
                .slice(0, 5)
                .map((x) => `${x.name} (${x.appearances})`)
                .join(" · ")}
            </p>
          ) : null}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(320px,1fr))", gap: 14 }}>
        <div className="bc-chart-panel">
          <h3>Yearly performance</h3>
          <p className="muted">Matches and wins from the loaded history window</p>
          {byYear.length ? (
            <Plot
              data={[
                {
                  x: byYear.map((r) => r.year),
                  y: byYear.map((r) => r.matches),
                  type: "bar",
                  name: "Matches",
                  marker: { color: accentColor(theme) },
                  hovertemplate: "%{x}<br>%{y} matches<extra></extra>",
                },
                {
                  x: byYear.map((r) => r.year),
                  y: byYear.map((r) => r.wins),
                  type: "scatter",
                  mode: "lines+markers",
                  name: "Wins",
                  line: { color: theme.accent },
                  hovertemplate: "%{x}<br>%{y} wins<extra></extra>",
                },
              ]}
              layout={plotlyLayout(theme, { height: 320 })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          ) : (
            <div className="bc-empty">Yearly trend unavailable</div>
          )}
        </div>
        <div className="bc-chart-panel">
          <h3>Match-type distribution</h3>
          <p className="muted">Stipulation mix in career sample</p>
          {typeDist.length ? (
            <Plot
              data={[
                {
                  labels: typeDist.map((r) => r.type),
                  values: typeDist.map((r) => r.count),
                  type: "pie",
                  hole: 0.48,
                  marker: { colors: [theme.primary, theme.accent, "#71717a", "#f4f4f5", "#7f1d1d"] },
                  hovertemplate: "<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",
                },
              ]}
              layout={plotlyLayout(theme, { height: 320, showlegend: false })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          ) : (
            <div className="bc-empty">Type distribution unavailable</div>
          )}
        </div>
      </div>

      <PremiumSportsDataTable
        title="Yearly performance table"
        variant="yearly"
        rows={byYear}
        rowKey={(r) => String(r.year)}
        pageSize={20}
        columns={[
          { key: "year", header: "Year", primary: true },
          { key: "matches", header: "Matches" },
          { key: "wins", header: "Wins" },
          {
            key: "win_rate",
            header: "Win rate",
            sortValue: (r) => (r.matches ? r.wins / r.matches : 0),
            render: (r) => (r.matches ? `${((r.wins / r.matches) * 100).toFixed(0)}%` : "—"),
          },
        ]}
      />

      <PremiumSportsDataTable
        title="Match history"
        variant="history"
        rows={history}
        rowKey={(m, i) => `${m.match_id || m.event_id || m.event_name}-${i}`}
        searchPlaceholder="Search event or result…"
        searchFilter={(m, q) =>
          [m.event_name, m.event_series, m.match_type_group, m.result, m.match_result]
            .join(" ")
            .toLowerCase()
            .includes(q)
        }
        isWinnerRow={(m) => m.result === "win"}
        pageSize={25}
        onRowClick={(m) => {
          if (!m.event_id) return;
          const path = m.match_id
            ? `/events/${m.event_id}?match=${encodeURIComponent(m.match_id)}`
            : `/events/${m.event_id}`;
          navigate(path);
        }}
        columns={[
          { key: "event_date", header: "Date" },
          {
            key: "event_name",
            header: "Event",
            primary: true,
            render: (m) =>
              m.event_id ? (
                <Link
                  to={
                    m.match_id
                      ? `/events/${m.event_id}?match=${encodeURIComponent(m.match_id)}`
                      : `/events/${m.event_id}`
                  }
                  style={{ color: theme.accent }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {m.event_name}
                </Link>
              ) : (
                m.event_name
              ),
          },
          { key: "event_series", header: "Series", render: (m) => m.event_series || "—" },
          {
            key: "match_type_group",
            header: "Type",
            render: (m) => <span className="pst-badge">{m.match_type_group || "—"}</span>,
          },
          {
            key: "result",
            header: "Result",
            render: (m) => (
              <span title={m.match_result || undefined}>
                {m.result || "—"}
                {m.match_result ? (
                  <span className="muted" style={{ display: "block", fontSize: "0.75rem", fontWeight: 400 }}>
                    {m.match_result}
                  </span>
                ) : null}
              </span>
            ),
          },
        ]}
      />

      <p className="muted" style={{ fontSize: "0.8rem" }}>
        * Appearance counters use the API match-history window (up to 50 rows), not a full career invent.
      </p>
    </div>
  );
}
