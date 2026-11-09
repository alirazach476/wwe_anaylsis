import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { api } from "../api";
import { BroadcastStatsStrip } from "../components/broadcast/BroadcastStatsStrip";
import { PremiumSportsDataTable } from "../components/broadcast/PremiumSportsDataTable";
import { WrestlerNameLink } from "../components/WrestlerNameLink";
import { useEventTheme } from "../theme/EventThemeContext";
import { plotlyLayout, accentColor } from "../theme/chartTheme";

export default function Championships() {
  const { theme, setEventIdentity } = useEventTheme();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    setEventIdentity("championship", "Championship");
    api.championships().then(setData);
  }, [setEventIdentity]);

  if (!data) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div className="bc-skeleton" style={{ height: 120 }} />
        <div className="bc-skeleton" style={{ height: 360 }} />
      </div>
    );
  }
  const featured = (data.featured || []).filter((r: any) =>
    String(r.championship_name || "").toLowerCase().includes("crown jewel")
  );
  const top = [...(data.summary || [])]
    .filter((r: any) => !String(r.championship_name || "").toLowerCase().includes("crown jewel"))
    .slice(0, 15);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <BroadcastStatsStrip
        stats={[
          { label: "Title lineages", value: data.summary?.length ?? "—", context: "Tracked championships" },
          {
            label: "Recent changes",
            value: data.recent_changes?.length ?? "—",
            context: "PLE title transitions in sample",
          },
          {
            label: "Top changer",
            value: top[0]?.championship_name || "—",
            context: top[0] ? `${top[0].title_changes} PLE changes` : "Unavailable",
          },
          {
            label: "Crown Jewel titles",
            value: featured.length || 2,
            context: "Men’s + Women’s Crown Jewel Championship",
          },
        ]}
      />

      <section className="bc-chart-panel">
        <h3>WWE Crown Jewel Championship</h3>
        <p className="muted">
          Special Saudi PLE championship awarded when brand world champions collide — included in championship analytics
        </p>
        <div className="hist-spotlight-grid">
          {(featured.length
            ? featured
            : [
                {
                  championship_name: "WWE Crown Jewel Championship",
                  inaugural: "Cody Rhodes",
                  note: "Undisputed WWE Champion vs World Heavyweight Champion",
                },
                {
                  championship_name: "WWE Women's Crown Jewel Championship",
                  inaugural: "Liv Morgan",
                  note: "Raw Women’s World Champion vs SmackDown Women’s Champion",
                },
              ]
          ).map((r: any) => {
            const change = (data.recent_changes || []).find(
              (c: any) => c.championship_name === r.championship_name && c.featured
            );
            return (
              <article key={r.championship_name} className="hist-spotlight-card">
                <div className="hist-spotlight-cat">Crown Jewel</div>
                <div className="hist-spotlight-value" style={{ fontSize: "1.55rem" }}>
                  {r.championship_name.replace(/^WWE\s+/i, "")}
                </div>
                <h4>{r.championship_name}</h4>
                <p>
                  <strong>{change?.champion_after || r.inaugural || "—"}</strong>
                  {change?.inaugural_event || change?.event_name
                    ? ` · ${change.event_name}`
                    : " · Crown Jewel landmark"}
                </p>
                <p className="muted">{change?.note || r.note || "Featured championship lineage"}</p>
              </article>
            );
          })}
        </div>
      </section>

      <div className="bc-chart-panel">
        <h3>Most PLE title changes</h3>
        <p className="muted">{data.limitation}</p>
        <Plot
          data={[
            {
              x: top.map((r: any) => r.championship_name),
              y: top.map((r: any) => r.title_changes),
              type: "bar",
              marker: { color: accentColor(theme) },
              hovertemplate: "<b>%{x}</b><br>%{y} changes<extra></extra>",
            },
          ]}
          layout={plotlyLayout(theme, { height: 380, margin: { t: 10, b: 120, l: 40, r: 10 } })}
          style={{ width: "100%" }}
          config={{ displayModeBar: false, responsive: true }}
        />
      </div>

      <PremiumSportsDataTable
        title="Championship changes"
        variant="changes"
        rows={data.recent_changes || []}
        rowKey={(r, i) => `${r.event_date}-${r.championship_name}-${i}`}
        searchPlaceholder="Search title, event, champion…"
        searchFilter={(r, q) =>
          [r.event_name, r.championship_name, r.champion_after, r.winner].join(" ").toLowerCase().includes(q)
        }
        pageSize={30}
        isWinnerRow={() => true}
        columns={[
          { key: "event_date", header: "Date", sortValue: (r) => String(r.event_date || "") },
          { key: "event_name", header: "Event", primary: true },
          {
            key: "championship_name",
            header: "Championship",
            render: (r) => <span className="pst-badge title">{r.championship_name}</span>,
          },
          {
            key: "champion_after",
            header: "New / retaining champion",
            render: (r) => {
              const name = r.champion_after || r.winner;
              return name ? <WrestlerNameLink name={name} /> : "—";
            },
          },
        ]}
      />

      <PremiumSportsDataTable
        title="Championship reign summary"
        variant="reigns"
        rows={data.summary || []}
        rowKey={(r) => r.championship_name}
        searchPlaceholder="Search championship…"
        searchFilter={(r, q) => String(r.championship_name || "").toLowerCase().includes(q)}
        pageSize={25}
        columns={[
          { key: "championship_name", header: "Championship", primary: true },
          { key: "title_changes", header: "PLE changes", sortValue: (r) => Number(r.title_changes) || 0 },
          { key: "title_matches", header: "Title matches", sortValue: (r) => Number(r.title_matches) || 0 },
        ]}
      />
    </div>
  );
}
