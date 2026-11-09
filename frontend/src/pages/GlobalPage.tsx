import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { api } from "../api";
import { useEventTheme } from "../theme/EventThemeContext";
import { plotlyLayout } from "../theme/chartTheme";

export default function GlobalPage() {
  const { theme } = useEventTheme();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.global().then(setData);
  }, []);

  if (!data) return <p className="empty">Loading global analytics…</p>;

  const byCountry: Record<string, number> = {};
  data.geography.forEach((r: any) => {
    const c = r.country || "Unknown";
    byCountry[c] = (byCountry[c] || 0) + Number(r.events || 0);
  });
  const countries = Object.keys(byCountry);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div className="panel">
        <h3>Events by country</h3>
        <Plot
          data={[
            {
              type: "choropleth",
              locationmode: "country names",
              locations: countries,
              z: countries.map((c) => byCountry[c]),
              colorscale: [
                [0, "#1c1c22"],
                [0.5, theme.primary],
                [1, theme.accent],
              ],
              colorbar: { title: { text: "Events" } },
            },
          ]}
          layout={plotlyLayout(theme, {
            height: 420,
            geo: { bgcolor: "transparent", showframe: false, projection: { type: "natural earth" } },
            margin: { t: 10, b: 10, l: 10, r: 10 },
          })}
          style={{ width: "100%" }}
          config={{ displayModeBar: false, responsive: true }}
        />
      </div>
      <div className="panel">
        <h3>City / country table</h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Country</th>
                <th>City</th>
                <th>Events</th>
                <th>Attendance sum</th>
              </tr>
            </thead>
            <tbody>
              {data.geography.slice(0, 50).map((r: any, i: number) => (
                <tr key={i}>
                  <td>{r.country}</td>
                  <td>{r.city}</td>
                  <td>{r.events}</td>
                  <td>{r.attendance != null ? Number(r.attendance).toLocaleString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
