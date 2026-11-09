import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Plot from "react-plotly.js";
import { api } from "../api";
import { BroadcastStatsStrip } from "../components/broadcast/BroadcastStatsStrip";
import { PremiumSportsDataTable } from "../components/broadcast/PremiumSportsDataTable";
import { WrestlerPortrait } from "../components/WrestlerPortrait";
import { useEventTheme } from "../theme/EventThemeContext";
import { plotlyLayout, accentColor } from "../theme/chartTheme";

export default function Wrestlers() {
  const { theme } = useEventTheme();
  const navigate = useNavigate();
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    // Load every wrestler who has played in a PLE event (no min_matches cutoff).
    api
      .wrestlers({ limit: 10000, min_matches: 0, q: q || undefined })
      .then((r) => {
        if (cancelled) return;
        setItems(r.items || []);
        setTotal(r.total ?? r.items?.length ?? 0);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [q]);

  const chartLeaders = useMemo(() => items.slice(0, 15), [items]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <BroadcastStatsStrip
        stats={[
          {
            label: "All wrestlers",
            value: loading ? "…" : total,
            context: "Every competitor with a PLE match",
          },
          {
            label: "Top volume",
            value: items[0]?.canonical_name || "—",
            context: items[0] ? `${items[0].matches} matches` : "Loading roster",
          },
          {
            label: "Best win %",
            value: (() => {
              const best = [...items].filter((w) => w.win_pct != null && Number(w.matches) >= 5).sort((a, b) => b.win_pct - a.win_pct)[0];
              return best ? `${(best.win_pct * 100).toFixed(1)}%` : "—";
            })(),
            context: "Min 5 matches",
          },
        ]}
      />

      <div className="bc-chart-panel">
        <h3>Wrestler Analytics</h3>
        <p className="muted">
          Full PLE roster · {loading ? "loading…" : `${total.toLocaleString()} wrestlers`} · open a profile for career detail
        </p>
        <div className="filters">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search name…"
            style={{
              minWidth: 220,
              height: 40,
              borderRadius: 4,
              border: "1px solid var(--border-subtle)",
              background: "rgba(0,0,0,.35)",
              color: "#fff",
              padding: "0 12px",
            }}
          />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(320px,1fr))", gap: 14 }}>
        <div className="bc-chart-panel">
          <h3>Top appearances</h3>
          <p className="muted">Match volume leaders across the full roster</p>
          <Plot
            data={[
              {
                x: chartLeaders.map((w) => w.canonical_name),
                y: chartLeaders.map((w) => w.matches),
                type: "bar",
                marker: { color: accentColor(theme) },
                hovertemplate: "<b>%{x}</b><br>%{y} matches<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 360, margin: { t: 10, b: 100, l: 40, r: 10 } })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>

        <div className="bc-chart-panel" style={{ minHeight: 280 }}>
          <h3>Open a profile</h3>
          <p className="muted">Click Preview or a wrestler name to open finishers, managers, and full match history.</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 14 }}>
            {chartLeaders.slice(0, 8).map((w) => (
              <Link
                key={w.wrestler_id}
                to={`/wrestlers/${w.wrestler_id}`}
                className="pst-cell-wrestler"
                style={{
                  textDecoration: "none",
                  color: "inherit",
                  padding: "8px 10px",
                  borderRadius: 6,
                  border: "1px solid rgba(255,255,255,0.08)",
                  background: "rgba(0,0,0,0.25)",
                }}
              >
                <WrestlerPortrait name={w.canonical_name} size={36} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: theme.accent, fontWeight: 600 }}>{w.canonical_name}</div>
                  <div className="muted" style={{ fontSize: "0.8rem" }}>
                    {w.matches} matches · {w.wins} wins
                  </div>
                </div>
                <span className="bc-pill">Open</span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <PremiumSportsDataTable
        title={`Wrestler statistics (${total.toLocaleString()})`}
        variant="wrestlers"
        rows={items}
        rowKey={(w) => w.wrestler_id}
        searchPlaceholder="Filter by name…"
        searchFilter={(w, needle) => String(w.canonical_name || "").toLowerCase().includes(needle)}
        pageSize={50}
        isWinnerRow={(w) => Number(w.win_pct) > 0.55}
        columns={[
          {
            key: "canonical_name",
            header: "Wrestler",
            primary: true,
            render: (w) => (
              <div className="pst-cell-wrestler">
                <WrestlerPortrait name={w.canonical_name} size={36} />
                <Link
                  to={`/wrestlers/${w.wrestler_id}`}
                  style={{ color: theme.accent }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {w.canonical_name}
                </Link>
              </div>
            ),
          },
          { key: "matches", header: "Matches", sortValue: (w) => Number(w.matches) || 0 },
          { key: "wins", header: "Wins" },
          { key: "losses", header: "Losses" },
          {
            key: "win_pct",
            header: "Win %",
            sortValue: (w) => Number(w.win_pct) || 0,
            render: (w) => (w.win_pct != null ? `${(w.win_pct * 100).toFixed(1)}%` : "—"),
          },
          {
            key: "main_events",
            header: "Main",
          },
          {
            key: "span",
            header: "Years",
            render: (w) => `${w.first_year ?? "—"}–${w.last_year ?? "—"}`,
          },
          {
            key: "preview",
            header: "Profile",
            sortable: false,
            width: "110px",
            render: (w) => (
              <Link
                to={`/wrestlers/${encodeURIComponent(w.wrestler_id)}`}
                className="btn pst-preview-btn"
                onClick={(e) => {
                  e.stopPropagation();
                }}
                onMouseDown={(e) => {
                  // Prevent sticky-header / sort handlers from stealing the click
                  e.stopPropagation();
                }}
              >
                Preview
              </Link>
            ),
          },
        ]}
        onRowClick={(w) => navigate(`/wrestlers/${encodeURIComponent(w.wrestler_id)}`)}
      />
    </div>
  );
}
