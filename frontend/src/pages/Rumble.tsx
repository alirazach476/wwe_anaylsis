import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { api } from "../api";
import { EventArtwork } from "../components/EventArtwork";
import { PremiumSportsDataTable } from "../components/broadcast/PremiumSportsDataTable";
import { WrestlerPortrait } from "../components/WrestlerPortrait";
import { useEventTheme } from "../theme/EventThemeContext";
import { plotlyLayout, accentColor } from "../theme/chartTheme";

export default function Rumble() {
  const { theme, setEventIdentity } = useEventTheme();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    setEventIdentity("Royal Rumble", "Royal Rumble");
    api.rumble().then(setData);
  }, [setEventIdentity]);

  if (!data) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div className="bc-skeleton" style={{ height: 220 }} />
        <div className="bc-skeleton" style={{ height: 320 }} />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <section className="event-hero" style={{ minHeight: 260 }}>
        <div>
          <div className="event-hero-badge">Special Event Analytics</div>
          <h1>Royal Rumble</h1>
          <p className="muted">Entry-number wins, elimination leaders, and historical winners from the rumble mart.</p>
        </div>
        <div className="event-hero-art">
          <EventArtwork series="Royal Rumble" eventName="Royal Rumble" size="lg" driveTheme />
        </div>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(320px,1fr))", gap: 14 }}>
        <div className="bc-chart-panel">
          <h3>Wins by entry number</h3>
          <p className="muted">Which draw slots historically produce winners</p>
          <Plot
            data={[
              {
                x: data.wins_by_entry_number.map((r: any) => r.entry_number),
                y: data.wins_by_entry_number.map((r: any) => r.wins),
                type: "bar",
                marker: { color: accentColor(theme) },
                hovertemplate: "Entry %{x}<br>%{y} wins<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 320 })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
        <PremiumSportsDataTable
          title="Elimination leaders"
          variant="rumble"
          rows={data.elimination_leaders || []}
          rowKey={(r) => r.canonical_name}
          pageSize={15}
          columns={[
            {
              key: "canonical_name",
              header: "Wrestler",
              primary: true,
              render: (r) => (
                <div className="pst-cell-wrestler">
                  <WrestlerPortrait name={r.canonical_name} size={36} />
                  <span>{r.canonical_name}</span>
                </div>
              ),
            },
            {
              key: "eliminations_made",
              header: "Eliminations",
              sortValue: (r) => Number(r.eliminations_made) || 0,
            },
          ]}
        />
      </div>

      <PremiumSportsDataTable
        title="Royal Rumble entries — winners"
        variant="rumble"
        rows={data.winners || []}
        rowKey={(r, i) => `${r.event_year}-${r.canonical_name}-${i}`}
        searchPlaceholder="Search winner or year…"
        searchFilter={(r, q) =>
          [r.canonical_name, r.event_name, r.event_year].join(" ").toLowerCase().includes(q)
        }
        isWinnerRow={() => true}
        pageSize={25}
        columns={[
          { key: "event_year", header: "Year" },
          {
            key: "canonical_name",
            header: "Winner",
            primary: true,
            render: (r) => (
              <div className="pst-cell-wrestler">
                <WrestlerPortrait name={r.canonical_name} size={36} />
                <span>{r.canonical_name}</span>
              </div>
            ),
          },
          { key: "entry_number", header: "Entry", render: (r) => r.entry_number ?? "—" },
          { key: "event_name", header: "Event" },
        ]}
      />
    </div>
  );
}
