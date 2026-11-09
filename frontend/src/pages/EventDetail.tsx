import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import Plot from "react-plotly.js";
import { api } from "../api";
import { MatchScorecard } from "../components/MatchScorecard";
import { BroadcastStatsStrip } from "../components/broadcast/BroadcastStatsStrip";
import { EventHero } from "../components/broadcast/EventHero";
import { PremiumSportsDataTable } from "../components/broadcast/PremiumSportsDataTable";
import { WrestlerNameLink } from "../components/WrestlerNameLink";
import { WrestlerPortrait } from "../components/WrestlerPortrait";
import { useEventTheme } from "../theme/EventThemeContext";
import { plotlyLayout, accentColor } from "../theme/chartTheme";
import { prettyChampId } from "../components/broadcast/matchUtils";
import { cleanWrestlerName, isUpcomingEvent } from "../utils/wrestlerNames";
import { useWrestlerIndex } from "../state/WrestlerIndex";

type Tab = "overview" | "card" | "results" | "analytics" | "wrestlers" | "titles";

function fmtDur(sec?: number | null) {
  if (sec == null || Number.isNaN(Number(sec))) return "Unavailable";
  const s = Math.round(Number(sec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export default function EventDetail() {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const focusMatchId = searchParams.get("match");
  const { theme, setEventIdentity } = useEventTheme();
  const { resolveId } = useWrestlerIndex();
  const [event, setEvent] = useState<any>(null);
  const [tab, setTab] = useState<Tab>("card");
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!eventId) return;
    setErr("");
    api
      .event(eventId)
      .then((e) => {
        setEvent(e);
        setEventIdentity(e.event_series, e.event_name);
      })
      .catch((e) => setErr(String(e)));
  }, [eventId, setEventIdentity]);

  useEffect(() => {
    if (focusMatchId) setTab("card");
  }, [focusMatchId]);

  // Deep-link from wrestler match history → scroll to that scoreboard.
  useEffect(() => {
    if (!focusMatchId || !event || tab !== "card") return;
    const targetId = `match-${focusMatchId}`;
    let cancelled = false;
    const focus = () => {
      if (cancelled) return;
      const el = document.getElementById(targetId);
      if (!el) return false;
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      el.classList.add("bc-match-focus");
      window.setTimeout(() => el.classList.remove("bc-match-focus"), 2200);
      return true;
    };
    // Wait past route scroll-to-top + scorecard paint.
    const timers = [80, 280, 600].map((ms) => window.setTimeout(() => focus(), ms));
    return () => {
      cancelled = true;
      timers.forEach((id) => window.clearTimeout(id));
    };
  }, [focusMatchId, event, tab]);

  const matches = event?.matches || [];
  const upcoming = event ? isUpcomingEvent({ ...event, matches: matches.length }) : false;
  const wrestlerStats = useMemo(() => {
    const map = new Map<
      string,
      { name: string; wrestler_id?: string | null; wins: number; losses: number; draws: number; appearances: number }
    >();
    for (const m of matches) {
      for (const p of m.participants || []) {
        const name = cleanWrestlerName(p.ring_name) || String(p.ring_name || "Unknown").trim() || "Unknown";
        if (/^and\b/i.test(name)) continue;
        const cur = map.get(name) || {
          name,
          wrestler_id: p.wrestler_id,
          wins: 0,
          losses: 0,
          draws: 0,
          appearances: 0,
        };
        cur.appearances += 1;
        if (p.result === "win") cur.wins += 1;
        if (p.result === "loss") cur.losses += 1;
        if (p.result === "draw") cur.draws += 1;
        // Prefer a clean roster id when available
        const resolved = resolveId(name, p.wrestler_id);
        if (resolved) cur.wrestler_id = resolved;
        map.set(name, cur);
      }
    }
    return Array.from(map.values()).sort((a, b) => b.appearances - a.appearances);
  }, [matches, resolveId]);

  function openMatchScoreboard(matchId?: string | null) {
    if (!matchId || !eventId) return;
    setTab("card");
    const next = new URLSearchParams(searchParams);
    next.set("match", String(matchId));
    setSearchParams(next, { replace: true });
  }

  const titleRows = useMemo(
    () =>
      matches.flatMap((m: any) =>
        (m.championships || []).map((c: any) => ({
          ...c,
          match_number: m.match_number,
          winner_name: m.winner_name,
          match_id: m.match_id,
          match_result: m.match_result,
        }))
      ),
    [matches]
  );

  const typeDist: Record<string, number> = useMemo(
    () =>
      matches.reduce((acc: Record<string, number>, m: any) => {
        const k = m.match_type_group || "other";
        acc[k] = (acc[k] || 0) + 1;
        return acc;
      }, {}),
    [matches]
  );
  const typeKeys = Object.keys(typeDist);
  const typeVals = typeKeys.map((k) => typeDist[k]);

  const durationSpark = useMemo(
    () =>
      matches
        .map((m: any) => Number(m.match_duration_seconds))
        .filter((n: number) => !Number.isNaN(n) && n > 0)
        .map((n: number) => Math.round(n / 60)),
    [matches]
  );

  const analyticsCharts = useMemo(() => {
    const ordered = [...matches].sort(
      (a, b) => (Number(a.match_number) || 0) - (Number(b.match_number) || 0)
    );
    const durations = ordered.map((m) => {
      const sec = Number(m.match_duration_seconds);
      return Number.isFinite(sec) && sec > 0 ? Math.round(sec / 60) : null;
    });
    const titleFlags = ordered.map((m) =>
      String(m.is_title_match).match(/1|true/i) || (m.championships || []).length ? 1 : 0
    );
    let title = 0;
    let regular = 0;
    let main = 0;
    let nonMain = 0;
    const finishes: Record<string, number> = {};
    for (const m of matches) {
      if (String(m.is_title_match).match(/1|true/i) || (m.championships || []).length) title += 1;
      else regular += 1;
      if (String(m.is_main_event).match(/1|true/i)) main += 1;
      else nonMain += 1;
      const r = String(m.match_result || "").toLowerCase();
      const method = r.includes("submission")
        ? "Submission"
        : r.includes("dq") || r.includes("disqualif")
          ? "DQ"
          : r.includes("count") && r.includes("out")
            ? "Countout"
            : r.includes("no contest")
              ? "No Contest"
              : r.includes("draw")
                ? "Draw"
                : r.includes("pin")
                  ? "Pinfall"
                  : "Other";
      finishes[method] = (finishes[method] || 0) + 1;
    }
    const finishRows = Object.entries(finishes)
      .map(([method, count]) => ({ method, count }))
      .sort((a, b) => b.count - a.count);
    const winLeaders = [...wrestlerStats]
      .filter((w) => w.wins > 0)
      .sort((a, b) => b.wins - a.wins || b.appearances - a.appearances)
      .slice(0, 10);
    return {
      ordered,
      durations,
      titleFlags,
      titleMix: [
        { label: "Title", value: title },
        { label: "Non-title", value: regular },
      ],
      mainMix: [
        { label: "Main event", value: main },
        { label: "Undercard", value: nonMain },
      ],
      finishRows,
      winLeaders,
    };
  }, [matches, wrestlerStats]);

  if (err) return <div className="bc-empty"><h4>Unable to load event</h4><p>{err}</p></div>;
  if (!event) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div className="bc-skeleton" style={{ height: 360 }} />
        <div className="bc-skeleton" style={{ height: 48 }} />
        <div className="bc-skeleton" style={{ height: 220 }} />
      </div>
    );
  }

  const titleCount = matches.filter((m: any) => String(m.is_title_match).match(/1|true/i) || (m.championships || []).length).length;
  const mainCount = matches.filter((m: any) => String(m.is_main_event).match(/1|true/i)).length;
  const avgDur = (() => {
    const vals = matches.map((m: any) => Number(m.match_duration_seconds)).filter((n: number) => !Number.isNaN(n));
    return vals.length ? `${Math.round(vals.reduce((a: number, b: number) => a + b, 0) / vals.length / 60)} min` : "—";
  })();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <EventHero event={event} matchCount={matches.length} />

      <div className="tabs bc-tabs">
        {(
          [
            ["overview", "Overview"],
            ["card", "Match Card"],
            ["results", "Results"],
            ["analytics", "Match Analytics"],
            ["wrestlers", "Wrestler Statistics"],
            ["titles", "Championship History"],
          ] as [Tab, string][]
        ).map(([id, label]) => (
          <button key={id} type="button" className={`tab${tab === id ? " active" : ""}`} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <>
          <BroadcastStatsStrip
            stats={[
              { label: "Matches", value: matches.length, context: "Full premium card", spark: typeVals },
              { label: "Title matches", value: titleCount, context: "Championship stipulation" },
              { label: "Main events", value: mainCount, context: "Headline slots" },
              { label: "Avg duration", value: avgDur, context: "Timed matches only", spark: durationSpark.slice(0, 12) },
            ]}
          />
          <div className="bc-chart-panel">
            <h3>Card preview</h3>
            <p className="muted">Broadcast scorecards — first three matches</p>
            {matches.slice(0, 3).map((m: any) => (
              <MatchScorecard
                key={m.match_id}
                match={m}
                watermark={theme.wordmark}
                eventName={event.event_name}
                eventYear={event.event_year}
                eventId={event.event_id}
              />
            ))}
          </div>
        </>
      )}

      {tab === "card" && (
        <div>
          {matches.length === 0 ? (
            <div className="bc-empty">
              <h4>{upcoming ? "Coming Soon" : "Empty card"}</h4>
              <p>
                {upcoming
                  ? "This premium live event is announced — match card and scoreboards will appear here after the show."
                  : "No matches recorded for this event."}
              </p>
            </div>
          ) : (
            matches.map((m: any) => (
              <MatchScorecard
                key={m.match_id}
                match={m}
                watermark={theme.wordmark}
                eventName={event.event_name}
                eventYear={event.event_year}
                eventId={event.event_id}
              />
            ))
          )}
        </div>
      )}

      {tab === "results" && (
        <PremiumSportsDataTable
          title="Event results"
          variant="results"
          rows={matches}
          rowKey={(m) => m.match_id}
          searchPlaceholder="Search winner, type, result…"
          searchFilter={(m, q) =>
            [m.winner_name, m.loser_name, m.match_type_group, m.match_result, m.match_number]
              .join(" ")
              .toLowerCase()
              .includes(q)
          }
          isWinnerRow={(m) => Boolean(m.winner_name)}
          onRowClick={(m) => openMatchScoreboard(m.match_id)}
          columns={[
            { key: "match_number", header: "#", primary: true, sortValue: (m) => Number(m.match_number) || 0 },
            {
              key: "match_type_group",
              header: "Type",
              render: (m) => <span className="pst-badge">{m.match_type_group || "—"}</span>,
            },
            {
              key: "winner_name",
              header: "Winner",
              primary: true,
              render: (m) => {
                const winner = cleanWrestlerName(m.winner_name) || m.winner_name;
                return (
                  <div className="pst-cell-wrestler">
                    <WrestlerPortrait
                      name={winner}
                      size={36}
                      matchContext={{
                        matchResult: m.match_result,
                        matchType: m.match_type_group,
                        championshipLabel: (m.championships || [])
                          .map((c: any) => prettyChampId(c.championship_id))
                          .join(" "),
                      }}
                    />
                    {winner ? (
                      <WrestlerNameLink name={winner} />
                    ) : (
                      <span>
                        {String(m.match_result || "").toLowerCase().includes("no contest") ? "No Contest" : "—"}
                      </span>
                    )}
                  </div>
                );
              },
            },
            {
              key: "loser_name",
              header: "Opponent",
              render: (m) => {
                const loser = cleanWrestlerName(m.loser_name) || m.loser_name;
                return loser ? <WrestlerNameLink name={loser} /> : "—";
              },
            },
            {
              key: "title",
              header: "Title",
              sortable: false,
              render: (m) =>
                (m.championships || []).length || String(m.is_title_match).match(/1|true/i) ? (
                  <span className="pst-badge title">Championship</span>
                ) : (
                  "—"
                ),
            },
            {
              key: "match_result",
              header: "Result",
              render: (m) => {
                const r = String(m.match_result || "").toLowerCase();
                if (r.includes("no contest")) return <span className="pst-badge result-draw">No Contest</span>;
                if (r.includes("draw")) return <span className="pst-badge result-draw">Draw</span>;
                return (
                  <span className="pst-badge result-win" title={m.match_result || "Open scoreboard"}>
                    {m.match_result ? "View scoreboard" : "Decision"}
                  </span>
                );
              },
            },
            { key: "duration", header: "Duration", sortValue: (m) => Number(m.match_duration_seconds) || 0, render: (m) => fmtDur(m.match_duration_seconds) },
          ]}
        />
      )}

      {tab === "analytics" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <BroadcastStatsStrip
            stats={[
              { label: "Matches", value: matches.length, context: "This event card" },
              { label: "Title matches", value: titleCount, context: "Championship stipulation" },
              { label: "Main events", value: mainCount, context: "Headline slots" },
              { label: "Avg duration", value: avgDur, context: "Timed matches only", spark: durationSpark.slice(0, 12) },
            ]}
          />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(300px,1fr))", gap: 14 }}>
            <div className="bc-chart-panel">
              <h3>Match-type mix</h3>
              <p className="muted">Stipulation groups on this card</p>
              <Plot
                data={[
                  {
                    labels: typeKeys,
                    values: typeVals,
                    type: "pie",
                    hole: 0.52,
                    textinfo: "label+value",
                    marker: { colors: [accentColor(theme), theme.accent, "#71717a", "#d4af37", "#38bdf8"] },
                    hovertemplate: "<b>%{label}</b><br>%{value}<extra></extra>",
                  },
                ]}
                layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 10, l: 10, r: 10 }, showlegend: false })}
                style={{ width: "100%" }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </div>

            <div className="bc-chart-panel">
              <h3>Duration by match order</h3>
              <p className="muted">How bout length changes through the card</p>
              <Plot
                data={[
                  {
                    x: analyticsCharts.ordered.map((m) => m.match_number ?? ""),
                    y: analyticsCharts.durations,
                    type: "scatter",
                    mode: "lines+markers",
                    fill: "tozeroy",
                    line: { color: accentColor(theme), width: 2.5 },
                    marker: { size: 7 },
                    hovertemplate: "Match %{x}<br>%{y} min<extra></extra>",
                  },
                ]}
                layout={plotlyLayout(theme, {
                  height: 320,
                  margin: { t: 10, b: 48, l: 44, r: 10 },
                  xaxis: { title: { text: "Match #" }, gridcolor: "rgba(255,255,255,0.06)" },
                  yaxis: { title: { text: "Minutes" }, gridcolor: "rgba(255,255,255,0.06)" },
                })}
                style={{ width: "100%" }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </div>

            <div className="bc-chart-panel">
              <h3>Title vs non-title</h3>
              <p className="muted">Championship share of the card</p>
              <Plot
                data={[
                  {
                    labels: analyticsCharts.titleMix.map((r) => r.label),
                    values: analyticsCharts.titleMix.map((r) => r.value),
                    type: "pie",
                    hole: 0.5,
                    marker: { colors: ["#d4af37", accentColor(theme)] },
                    textinfo: "label+value",
                    hovertemplate: "<b>%{label}</b><br>%{value}<extra></extra>",
                  },
                ]}
                layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 10, l: 10, r: 10 }, showlegend: false })}
                style={{ width: "100%" }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </div>

            <div className="bc-chart-panel">
              <h3>Main event vs undercard</h3>
              <p className="muted">Headline slot share</p>
              <Plot
                data={[
                  {
                    labels: analyticsCharts.mainMix.map((r) => r.label),
                    values: analyticsCharts.mainMix.map((r) => r.value),
                    type: "pie",
                    hole: 0.5,
                    marker: { colors: [theme.accent, "#52525b"] },
                    textinfo: "label+value",
                    hovertemplate: "<b>%{label}</b><br>%{value}<extra></extra>",
                  },
                ]}
                layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 10, l: 10, r: 10 }, showlegend: false })}
                style={{ width: "100%" }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </div>

            <div className="bc-chart-panel">
              <h3>Finish methods</h3>
              <p className="muted">How results were recorded</p>
              <Plot
                data={[
                  {
                    x: analyticsCharts.finishRows.map((r) => r.count),
                    y: analyticsCharts.finishRows.map((r) => r.method),
                    type: "bar",
                    orientation: "h",
                    marker: { color: accentColor(theme) },
                    hovertemplate: "<b>%{y}</b><br>%{x}<extra></extra>",
                  },
                ]}
                layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 40, l: 100, r: 16 } })}
                style={{ width: "100%" }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </div>

            <div className="bc-chart-panel">
              <h3>Title matches on the card</h3>
              <p className="muted">1 = title match by order</p>
              <Plot
                data={[
                  {
                    x: analyticsCharts.ordered.map((m) => m.match_number ?? ""),
                    y: analyticsCharts.titleFlags,
                    type: "bar",
                    marker: { color: analyticsCharts.titleFlags.map((v) => (v ? "#d4af37" : "rgba(255,255,255,0.18)")) },
                    hovertemplate: "Match %{x}<br>%{y}<extra></extra>",
                  },
                ]}
                layout={plotlyLayout(theme, {
                  height: 320,
                  margin: { t: 10, b: 48, l: 44, r: 10 },
                  yaxis: { dtick: 1, range: [-0.1, 1.2], gridcolor: "rgba(255,255,255,0.06)" },
                })}
                style={{ width: "100%" }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </div>

            <div className="bc-chart-panel">
              <h3>Win leaders</h3>
              <p className="muted">Most wins among this event’s roster</p>
              <Plot
                data={[
                  {
                    x: analyticsCharts.winLeaders.map((w) => w.wins),
                    y: analyticsCharts.winLeaders.map((w) => w.name),
                    type: "bar",
                    orientation: "h",
                    marker: { color: accentColor(theme) },
                    hovertemplate: "<b>%{y}</b><br>%{x} wins<extra></extra>",
                  },
                ]}
                layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 40, l: 120, r: 16 } })}
                style={{ width: "100%" }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </div>

            <div className="bc-chart-panel">
              <h3>Type volume (bars)</h3>
              <p className="muted">Counts by stipulation group</p>
              <Plot
                data={[
                  {
                    x: typeKeys,
                    y: typeVals,
                    type: "bar",
                    marker: { color: accentColor(theme) },
                    hovertemplate: "<b>%{x}</b><br>%{y}<extra></extra>",
                  },
                ]}
                layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 70, l: 44, r: 10 } })}
                style={{ width: "100%" }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </div>
          </div>
        </div>
      )}

      {tab === "wrestlers" && (
        <PremiumSportsDataTable
          title="Wrestler statistics"
          variant="wrestlers"
          rows={wrestlerStats}
          rowKey={(w) => w.name}
          searchPlaceholder="Search wrestler…"
          searchFilter={(w, q) => w.name.toLowerCase().includes(q)}
          isWinnerRow={(w) => w.wins > 0}
          emptyMessage={
            upcoming
              ? "Coming Soon — wrestler statistics will appear after the event."
              : "Participant detail unavailable for this event."
          }
          onRowClick={(w) => {
            const id = resolveId(w.name, w.wrestler_id);
            if (id) navigate(`/wrestlers/${id}`);
          }}
          columns={[
            {
              key: "name",
              header: "Wrestler",
              primary: true,
              render: (w) => (
                <div className="pst-cell-wrestler">
                  <WrestlerPortrait
                    name={w.name}
                    size={36}
                    matchContext={{
                      matchResult: matches.map((m: any) => m.match_result).join(" "),
                      championshipLabel: titleRows.map((r: any) => prettyChampId(r.championship_id)).join(" "),
                    }}
                  />
                  <WrestlerNameLink name={w.name} wrestlerId={w.wrestler_id} />
                </div>
              ),
            },
            { key: "appearances", header: "Appearances" },
            { key: "wins", header: "Wins" },
            { key: "losses", header: "Losses" },
            { key: "draws", header: "Draws / NC" },
          ]}
        />
      )}

      {tab === "titles" && (
        <PremiumSportsDataTable
          title="Championship history"
          variant="reigns"
          rows={titleRows}
          rowKey={(r, i) => `${r.match_id}-${i}`}
          searchPlaceholder="Search championship…"
          searchFilter={(r, q) =>
            [prettyChampId(r.championship_id), r.champion_before, r.champion_after, r.match_result]
              .join(" ")
              .toLowerCase()
              .includes(q)
          }
          emptyMessage={
            upcoming
              ? "Coming Soon — championship history will appear after the event."
              : "No championship rows linked to this event’s matches."
          }
          onRowClick={(r) => openMatchScoreboard(r.match_id)}
          columns={[
            { key: "match_number", header: "Match #" },
            {
              key: "championship_id",
              header: "Championship",
              primary: true,
              render: (r) => <span className="pst-badge title">{prettyChampId(r.championship_id)}</span>,
            },
            {
              key: "champion_before",
              header: "Before",
              render: (r) =>
                r.champion_before ? <WrestlerNameLink name={cleanWrestlerName(r.champion_before) || r.champion_before} /> : "—",
            },
            {
              key: "champion_after",
              header: "After",
              render: (r) => {
                const name = r.champion_after || r.winner_name;
                return name ? <WrestlerNameLink name={cleanWrestlerName(name) || name} /> : "—";
              },
            },
            {
              key: "title_change",
              header: "Change",
              render: (r) => (String(r.title_change).match(/1|true/i) ? "Yes" : "No"),
            },
          ]}
        />
      )}

      <p className="muted" style={{ fontSize: "0.78rem" }}>
        <Link to="/events" style={{ color: theme.accent }}>
          Browse all events
        </Link>
      </p>
    </div>
  );
}
