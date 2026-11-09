import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { EventArtwork } from "../components/EventArtwork";
import { WrestlerNameLink } from "../components/WrestlerNameLink";
import { useEventTheme } from "../theme/EventThemeContext";
import { cleanWrestlerName, matchScoreboardPath } from "../utils/wrestlerNames";

export default function Survivor() {
  const { theme, setEventIdentity } = useEventTheme();
  const [rows, setRows] = useState<any[]>([]);

  useEffect(() => {
    setEventIdentity("Survivor Series", "Survivor Series");
    api.matches({ series: "Survivor Series", limit: 200 }).then((r) => setRows(r.items));
  }, [setEventIdentity]);

  const war = rows.filter(
    (r) =>
      String(r.match_type_group || r.match_result || "").toLowerCase().includes("cage") ||
      String(r.special_match_kind || "").includes("survivor")
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <section className="hero" style={{ minHeight: 220 }}>
        <div>
          <div className="hero-badge">WarGames & survival</div>
          <h1>Survivor Series</h1>
          <p className="muted">Traditional & WarGames cards from the match mart (series filter).</p>
        </div>
        <div className="hero-art">
          <EventArtwork series="Survivor Series" eventName="Survivor Series" size="lg" driveTheme />
        </div>
      </section>
      <div className="panel">
        <h3>Matches ({rows.length})</h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Date</th>
                <th>Event</th>
                <th>Type</th>
                <th>Winner</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((m) => (
                <tr key={m.match_id} className="winner-row">
                  <td>{m.event_date}</td>
                  <td>
                    <Link
                      to={matchScoreboardPath(m.event_id, m.match_id) || `/events/${m.event_id}`}
                      style={{ color: theme.accent }}
                    >
                      {m.event_name}
                    </Link>
                  </td>
                  <td>{m.match_type_group}</td>
                  <td>
                    {m.winner_name ? (
                      <WrestlerNameLink name={cleanWrestlerName(m.winner_name) || m.winner_name} />
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted" style={{ marginTop: 12 }}>
          Cage-classified subset (proxy for WarGames/chamber styles on card): {war.length}
        </p>
      </div>
    </div>
  );
}
