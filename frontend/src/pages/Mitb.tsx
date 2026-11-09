import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { api } from "../api";
import { EventArtwork } from "../components/EventArtwork";
import { WrestlerNameLink } from "../components/WrestlerNameLink";
import { useEventTheme } from "../theme/EventThemeContext";
import { plotlyLayout, accentColor } from "../theme/chartTheme";

export default function Mitb() {
  const { theme, setEventIdentity } = useEventTheme();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    setEventIdentity("Money in the Bank", "Money in the Bank");
    api.mitb().then(setData);
  }, [setEventIdentity]);

  if (!data) return <p className="empty">Loading Money in the Bank…</p>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <section className="hero" style={{ minHeight: 220 }}>
        <div>
          <div className="hero-badge">Contract briefcase analytics</div>
          <h1>Money in the Bank</h1>
          <p className="muted">Cash-in outcomes and historical briefcase results from the MITB mart.</p>
        </div>
        <div className="hero-art">
          <EventArtwork series="Money in the Bank" eventName="Money in the Bank" size="lg" driveTheme />
        </div>
      </section>
      <div className="panel">
        <h3>Cash-in outcomes</h3>
        <Plot
          data={[
            {
              labels: data.outcomes.map((r: any) => r.outcome),
              values: data.outcomes.map((r: any) => r.count),
              type: "pie",
              hole: 0.42,
              marker: { colors: [accentColor(theme), theme.accent, "#71717a", "#fbbf24"] },
            },
          ]}
          layout={plotlyLayout(theme, { height: 320 })}
          style={{ width: "100%" }}
          config={{ displayModeBar: false, responsive: true }}
        />
      </div>
      <div className="panel">
        <h3>Cash-ins</h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Winner</th>
                <th>Cash-in date</th>
                <th>Event</th>
                <th>Opponent</th>
                <th>Outcome</th>
                <th>Championship</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((r: any, i: number) => (
                <tr key={i} className="winner-row">
                  <td>{r.winner_name ? <WrestlerNameLink name={r.winner_name} /> : "—"}</td>
                  <td>{r.cash_in_date || "—"}</td>
                  <td>{r.cash_in_event || "—"}</td>
                  <td>{r.cash_in_opponent ? <WrestlerNameLink name={r.cash_in_opponent} /> : "—"}</td>
                  <td>{r.cash_in_outcome || "—"}</td>
                  <td>{r.championship_won || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
