import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Plot from "react-plotly.js";
import { api } from "../api";
import { BroadcastStatsStrip } from "../components/broadcast/BroadcastStatsStrip";
import { PremiumSportsDataTable } from "../components/broadcast/PremiumSportsDataTable";
import { WrestlerPortrait } from "../components/WrestlerPortrait";
import { inferFighterGender } from "../assets/wrestlerGender";
import { useFilters } from "../state/filters";
import { useEventTheme } from "../theme/EventThemeContext";
import { plotlyLayout, accentColor } from "../theme/chartTheme";

function fmtDur(sec?: number | null) {
  if (sec == null || Number.isNaN(Number(sec))) return "Unavailable";
  const s = Math.round(Number(sec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export default function Matches() {
  const { query } = useFilters();
  const { theme } = useEventTheme();
  const [analytics, setAnalytics] = useState<any>(null);
  const [rows, setRows] = useState<any[]>([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    api.matchAnalytics().then(setAnalytics);
  }, []);

  useEffect(() => {
    api.matches({ ...query, limit: 400 }).then((r) => {
      setRows(r.items);
      setTotal(r.total);
    });
  }, [query]);

  const teamRows = useMemo(
    () => rows.filter((m) => String(m.match_type_group || "").toLowerCase().includes("tag")),
    [rows]
  );

  const sampleByYear = useMemo(() => {
    const map = new Map<number, number>();
    for (const m of rows) {
      const y = Number(m.event_year);
      if (!Number.isFinite(y)) continue;
      map.set(y, (map.get(y) || 0) + 1);
    }
    return [...map.entries()].sort((a, b) => a[0] - b[0]);
  }, [rows]);

  const titleMix = useMemo(() => {
    let title = 0;
    let regular = 0;
    for (const m of rows) {
      if (String(m.is_title_match).match(/1|true/i)) title += 1;
      else regular += 1;
    }
    return [
      { label: "Title", value: title },
      { label: "Non-title", value: regular },
    ];
  }, [rows]);

  const winnerGenderMix = useMemo(() => {
    let women = 0;
    let men = 0;
    for (const m of rows) {
      const g = inferFighterGender(m.winner_name, {
        matchResult: m.match_result,
        matchType: m.match_type_group || m.match_type_raw,
      });
      if (g === "female") women += 1;
      else men += 1;
    }
    return [
      { label: "Women winners", value: women },
      { label: "Men winners", value: men },
    ];
  }, [rows]);

  const mainMixSample = useMemo(() => {
    let main = 0;
    let under = 0;
    for (const m of rows) {
      if (String(m.is_main_event).match(/1|true/i)) main += 1;
      else under += 1;
    }
    return [
      { label: "Main event", value: main },
      { label: "Undercard", value: under },
    ];
  }, [rows]);

  if (!analytics) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div className="bc-skeleton" style={{ height: 120 }} />
        <div className="bc-skeleton" style={{ height: 320 }} />
      </div>
    );
  }

  const accent = accentColor(theme);
  const byYear = analytics.by_year || [];
  const durByType = analytics.duration_by_type || [];
  const hist = analytics.duration_histogram || [];
  const finishes = analytics.finish_methods || [];
  const bySeries = analytics.by_series || [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <BroadcastStatsStrip
        stats={[
          {
            label: "Mean duration",
            value: analytics.duration.mean ? `${Math.round(analytics.duration.mean / 60)}m` : "—",
            context: "Seconds averaged across timed matches",
          },
          {
            label: "Median duration",
            value: analytics.duration.median ? `${Math.round(analytics.duration.median / 60)}m` : "—",
            context: "Typical bout length",
          },
          {
            label: "Title share",
            value: `${(analytics.title_share * 100).toFixed(1)}%`,
            context: "Championship stipulation rate",
          },
          {
            label: "Main-event share",
            value: analytics.main_event_share != null ? `${(analytics.main_event_share * 100).toFixed(1)}%` : "—",
            context: "Card-closer rate",
          },
          {
            label: "Sample",
            value: rows.length,
            context: `of ${total} API total`,
            spark: analytics.type_distribution?.map((r: any) => r.count) || [],
          },
        ]}
      />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(320px,1fr))", gap: 14 }}>
        <div className="bc-chart-panel">
          <h3>Match type distribution</h3>
          <p className="muted">Which stipulation groups dominate the catalog</p>
          <Plot
            data={[
              {
                labels: analytics.type_distribution.map((r: any) => r.match_type_group),
                values: analytics.type_distribution.map((r: any) => r.count),
                type: "pie",
                hole: 0.55,
                marker: { colors: [accent, theme.accent, "#71717a", "#d4af37", "#38bdf8", "#f472b6"] },
                textinfo: "label+percent",
                hovertemplate: "<b>%{label}</b><br>%{value} matches (%{percent})<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 340, margin: { t: 10, b: 10, l: 10, r: 10 }, showlegend: false })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        <div className="bc-chart-panel">
          <h3>Matches per year</h3>
          <p className="muted">Full-catalog volume with title-match overlay</p>
          <Plot
            data={[
              {
                x: byYear.map((r: any) => r.year),
                y: byYear.map((r: any) => r.matches),
                type: "scatter",
                mode: "lines+markers",
                name: "All matches",
                line: { color: accent, width: 2.5 },
                marker: { size: 5 },
                hovertemplate: "<b>%{x}</b><br>%{y} matches<extra></extra>",
              },
              {
                x: byYear.map((r: any) => r.year),
                y: byYear.map((r: any) => r.title_matches),
                type: "bar",
                name: "Title matches",
                marker: { color: "rgba(212,175,55,0.55)" },
                hovertemplate: "<b>%{x}</b><br>%{y} title matches<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 340, barmode: "overlay", margin: { t: 10, b: 40, l: 44, r: 10 } })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        <div className="bc-chart-panel">
          <h3>Duration histogram</h3>
          <p className="muted">How long PLE matches usually run (minutes)</p>
          <Plot
            data={[
              {
                x: hist.map((r: any) => `${r.bin_start}–${r.bin_end}m`),
                y: hist.map((r: any) => r.count),
                type: "bar",
                marker: { color: accent },
                hovertemplate: "<b>%{x}</b><br>%{y} matches<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 340, margin: { t: 10, b: 60, l: 44, r: 10 } })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        <div className="bc-chart-panel">
          <h3>Avg duration by type</h3>
          <p className="muted">Mean bout length per stipulation group</p>
          <Plot
            data={[
              {
                x: durByType.map((r: any) => r.match_type_group),
                y: durByType.map((r: any) => (r.avg_sec != null ? r.avg_sec / 60 : null)),
                type: "bar",
                marker: { color: theme.accent },
                hovertemplate: "<b>%{x}</b><br>%{y:.1f} min avg<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, {
              height: 340,
              margin: { t: 10, b: 80, l: 44, r: 10 },
              yaxis: { title: { text: "Minutes" }, gridcolor: "rgba(255,255,255,0.06)" },
            })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        <div className="bc-chart-panel">
          <h3>Finish methods</h3>
          <p className="muted">How results are recorded in match text</p>
          <Plot
            data={[
              {
                x: finishes.map((r: any) => r.count),
                y: finishes.map((r: any) => r.method),
                type: "bar",
                orientation: "h",
                marker: { color: accent },
                hovertemplate: "<b>%{y}</b><br>%{x} matches<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 340, margin: { t: 10, b: 40, l: 100, r: 16 } })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        <div className="bc-chart-panel">
          <h3>Matches by series</h3>
          <p className="muted">Top event families by bout count</p>
          <Plot
            data={[
              {
                x: bySeries.map((r: any) => r.event_series),
                y: bySeries.map((r: any) => r.count),
                type: "bar",
                marker: { color: accent },
                hovertemplate: "<b>%{x}</b><br>%{y} matches<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 340, margin: { t: 10, b: 90, l: 44, r: 10 } })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        <div className="bc-chart-panel">
          <h3>Avg duration trend</h3>
          <p className="muted">Mean match length by year (catalog)</p>
          <Plot
            data={[
              {
                x: byYear.map((r: any) => r.year),
                y: byYear.map((r: any) => (r.avg_duration_sec != null ? r.avg_duration_sec / 60 : null)),
                type: "scatter",
                mode: "lines+markers",
                fill: "tozeroy",
                line: { color: accent, width: 2 },
                marker: { size: 4 },
                hovertemplate: "<b>%{x}</b><br>%{y:.1f} min<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, {
              height: 340,
              margin: { t: 10, b: 40, l: 44, r: 10 },
              yaxis: { title: { text: "Minutes" }, gridcolor: "rgba(255,255,255,0.06)" },
            })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        <div className="bc-chart-panel">
          <h3>Filtered sample mix</h3>
          <p className="muted">Title vs non-title in the current filter board</p>
          <Plot
            data={[
              {
                labels: titleMix.map((r) => r.label),
                values: titleMix.map((r) => r.value),
                type: "pie",
                hole: 0.5,
                marker: { colors: ["#d4af37", accent] },
                textinfo: "label+value",
                hovertemplate: "<b>%{label}</b><br>%{value}<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 340, margin: { t: 10, b: 10, l: 10, r: 10 }, showlegend: false })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        <div className="bc-chart-panel">
          <h3>Winner gender mix</h3>
          <p className="muted">Women vs men winners in the filtered sample</p>
          <Plot
            data={[
              {
                labels: winnerGenderMix.map((r) => r.label),
                values: winnerGenderMix.map((r) => r.value),
                type: "pie",
                hole: 0.5,
                marker: { colors: ["#f472b6", "#38bdf8"] },
                textinfo: "label+value",
                hovertemplate: "<b>%{label}</b><br>%{value}<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 340, margin: { t: 10, b: 10, l: 10, r: 10 }, showlegend: false })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        <div className="bc-chart-panel">
          <h3>Main event share</h3>
          <p className="muted">Headline vs undercard in the filtered sample</p>
          <Plot
            data={[
              {
                labels: mainMixSample.map((r) => r.label),
                values: mainMixSample.map((r) => r.value),
                type: "pie",
                hole: 0.5,
                marker: { colors: [theme.accent, "#52525b"] },
                textinfo: "label+value",
                hovertemplate: "<b>%{label}</b><br>%{value}<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 340, margin: { t: 10, b: 10, l: 10, r: 10 }, showlegend: false })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
      </div>

      {sampleByYear.length > 1 ? (
        <div className="bc-chart-panel">
          <h3>Filtered matches by year</h3>
          <p className="muted">Current filter sample volume across years</p>
          <Plot
            data={[
              {
                x: sampleByYear.map(([y]) => y),
                y: sampleByYear.map(([, n]) => n),
                type: "bar",
                marker: { color: accent },
                hovertemplate: "<b>%{x}</b><br>%{y} in sample<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 280, margin: { t: 10, b: 40, l: 44, r: 10 } })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
      ) : null}

      <PremiumSportsDataTable
        title="Match history board"
        variant="history"
        rows={rows}
        rowKey={(m) => m.match_id}
        searchPlaceholder="Search wrestler, event, type…"
        searchFilter={(m, q) =>
          [m.event_name, m.winner_name, m.loser_name, m.match_type_group, m.match_result]
            .join(" ")
            .toLowerCase()
            .includes(q)
        }
        pageSize={40}
        isWinnerRow={(m) => Boolean(m.winner_name)}
        expandable={(m) => m.match_result || null}
        columns={[
          {
            key: "event_name",
            header: "Event",
            primary: true,
            render: (m) => (
              <Link to={`/events/${m.event_id}`} style={{ color: theme.accent }}>
                {m.event_name}
              </Link>
            ),
          },
          { key: "event_year", header: "Year" },
          {
            key: "match_type_group",
            header: "Type",
            render: (m) => <span className="pst-badge">{m.match_type_group || "—"}</span>,
          },
          {
            key: "winner_name",
            header: "Winner",
            render: (m) => (
              <div className="pst-cell-wrestler">
                <WrestlerPortrait
                  name={m.winner_name}
                  size={36}
                  matchContext={{
                    matchResult: m.match_result,
                    matchType: m.match_type_group || m.match_type_raw,
                    championshipLabel: String(m.is_title_match).match(/1|true/i) ? m.match_result : null,
                  }}
                />
                <span>{m.winner_name || "—"}</span>
              </div>
            ),
          },
          {
            key: "is_title_match",
            header: "Title",
            render: (m) =>
              String(m.is_title_match).match(/1|true/i) ? <span className="pst-badge title">Title</span> : "—",
          },
          {
            key: "match_result",
            header: "Result",
            render: (m) => {
              const r = String(m.match_result || "").toLowerCase();
              if (r.includes("no contest")) return <span className="pst-badge result-draw">No Contest</span>;
              if (r.includes("draw")) return <span className="pst-badge result-draw">Draw</span>;
              return <span className="pst-badge result-win">Decision</span>;
            },
          },
          {
            key: "match_duration_seconds",
            header: "Duration",
            sortValue: (m) => Number(m.match_duration_seconds) || 0,
            render: (m) => fmtDur(m.match_duration_seconds),
          },
        ]}
      />

      <PremiumSportsDataTable
        title="Team match results"
        variant="teams"
        rows={teamRows}
        rowKey={(m) => m.match_id}
        searchPlaceholder="Search tag matches…"
        searchFilter={(m, q) =>
          [m.event_name, m.winner_name, m.loser_name, m.match_result].join(" ").toLowerCase().includes(q)
        }
        emptyMessage="No tag-team matches in the current filter sample."
        pageSize={20}
        columns={[
          {
            key: "event_name",
            header: "Event",
            render: (m) => (
              <Link to={`/events/${m.event_id}`} style={{ color: theme.accent }}>
                {m.event_name}
              </Link>
            ),
          },
          { key: "event_year", header: "Year" },
          { key: "winner_name", header: "Winning side", primary: true },
          { key: "loser_name", header: "Opposing side" },
          {
            key: "match_duration_seconds",
            header: "Duration",
            render: (m) => fmtDur(m.match_duration_seconds),
          },
        ]}
      />
    </div>
  );
}
