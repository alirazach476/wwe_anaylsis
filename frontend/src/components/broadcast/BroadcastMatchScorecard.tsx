import { useEffect, useState } from "react";
import { loadEventLogoManifest, logoPathFromManifest } from "../../assets/eventLogoLookup";
import { useEventTheme } from "../../theme/EventThemeContext";
import { WrestlerPortrait } from "../WrestlerPortrait";
import { ChampionshipBelt } from "./ChampionshipBelt";
import {
  Participant,
  championshipLabel,
  detectMatchState,
  fmtDuration,
  parseVsNames,
  resultKind,
} from "./matchUtils";

function matchContext(match: any, title: string | null) {
  return {
    matchResult: match.match_result,
    championshipLabel: title,
    matchType: match.match_type_group || match.match_type_raw,
  };
}

function Cutout({
  name,
  size = 118,
  match,
  title,
}: {
  name?: string | null;
  size?: number;
  match: any;
  title: string | null;
}) {
  return (
    <div className="bc-cutout">
      <WrestlerPortrait name={name} size={size} matchContext={matchContext(match, title)} />
    </div>
  );
}

function TopBar({
  match,
  title,
  eventLogo,
}: {
  match: any;
  title: string | null;
  eventLogo?: string | null;
}) {
  const duration = fmtDuration(match.match_duration_seconds);
  const kind = resultKind(match);
  return (
    <div className="bc-match-top">
      <span className="bc-match-order">
        {match.match_number != null ? `MATCH ${match.match_number}` : "MATCH"}
      </span>
      {match.match_type_group || match.match_type_raw ? (
        <span className="bc-pill">{match.match_type_group || match.match_type_raw}</span>
      ) : null}
      {title ? (
        <span className="bc-pill gold">{title}</span>
      ) : match.special_match_kind ? (
        <span className="bc-pill">{String(match.special_match_kind).replace(/_/g, " ")}</span>
      ) : null}
      {String(match.is_main_event).match(/1|true/i) ? <span className="bc-pill primary">Main Event</span> : null}
      {kind === "no-contest" ? <span className="bc-pill draw">No Contest</span> : null}
      {kind === "draw" ? <span className="bc-pill draw">Draw</span> : null}
      {duration ? <span className="bc-pill">{duration}</span> : <span className="bc-pill">Duration n/a</span>}
      {eventLogo ? (
        <img className="bc-match-event-logo" src={eventLogo} alt="" title="Event logo" />
      ) : null}
    </div>
  );
}

function Foot({ match, watermark }: { match: any; watermark?: string }) {
  return (
    <div className="bc-match-foot">
      <div className="bc-result-line">{match.match_result || "Result unavailable"}</div>
      <div className="bc-match-watermark">{watermark}</div>
    </div>
  );
}

export function SinglesMatchGraphic({ match }: { match: any }) {
  const parts: Participant[] = match.participants || [];
  const { a, b } = parseVsNames(match);
  const title = championshipLabel(match);
  const kind = resultKind(match);
  const aWin = kind === "win" && (parts.find((p) => p.ring_name === a)?.result === "win" || match.winner_name === a);
  const bWin = kind === "win" && (parts.find((p) => p.ring_name === b)?.result === "win" || match.winner_name === b);

  return (
    <div className="bc-singles">
      <div className={`bc-fighter${aWin ? " winner" : ""}`}>
        <Cutout name={a} match={match} title={title} />
        <div className="bc-fighter-copy">
          <p className="bc-fighter-name">{a || "TBA"}</p>
          <div className="bc-fighter-sub">
            {aWin ? "Winner" : "Competitor"}
          </div>
          {aWin ? <span className="bc-pill win" style={{ marginTop: 8 }}>Winner</span> : null}
        </div>
      </div>
      <div className="bc-vs-block">
        <div className="bc-vs">VS</div>
        {title ? <ChampionshipBelt label={title} /> : null}
      </div>
      <div className={`bc-fighter right${bWin ? " winner" : ""}`}>
        <Cutout name={b} match={match} title={title} />
        <div className="bc-fighter-copy">
          <p className="bc-fighter-name">{b || "TBA"}</p>
          <div className="bc-fighter-sub">
            {bWin ? "Winner" : "Competitor"}
          </div>
          {bWin ? <span className="bc-pill win" style={{ marginTop: 8 }}>Winner</span> : null}
        </div>
      </div>
    </div>
  );
}

export function TagTeamMatchGraphic({ match }: { match: any }) {
  const parts: Participant[] = match.participants || [];
  const teams = new Map<string, Participant[]>();
  parts.forEach((p) => {
    const key = String(p.team_id ?? p.result ?? "solo");
    if (!teams.has(key)) teams.set(key, []);
    teams.get(key)!.push(p);
  });
  let groups = Array.from(teams.values());
  if (groups.length < 2) {
    groups = [
      parts.filter((p) => p.result === "win").length
        ? parts.filter((p) => p.result === "win")
        : [{ ring_name: match.winner_name } as Participant],
      parts.filter((p) => p.result === "loss").length
        ? parts.filter((p) => p.result === "loss")
        : [{ ring_name: match.loser_name } as Participant],
    ];
  }
  const sorted = [...groups].sort((a, b) => {
    const aw = a.some((p) => p.result === "win") ? 0 : 1;
    const bw = b.some((p) => p.result === "win") ? 0 : 1;
    return aw - bw;
  });
  const left = sorted[0] || [];
  const right = sorted[1] || [];
  const leftWin = left.some((p) => p.result === "win");
  const rightWin = right.some((p) => p.result === "win");
  const title = championshipLabel(match);

  return (
    <div className="bc-tag">
      <div className={`bc-team${leftWin ? " winner" : ""}`}>
        <div className="bc-team-portraits">
          {left.map((p, i) => (
            <Cutout key={i} name={p.ring_name} size={76} match={match} title={title} />
          ))}
        </div>
        <p className="bc-team-name">{left.map((p) => p.ring_name).filter(Boolean).join(" & ") || "Team A"}</p>
        <div className="bc-team-members">{leftWin ? "Winning team" : "Team"}</div>
      </div>
      <div className="bc-vs-block">
        <div className="bc-vs">VS</div>
        {title ? <ChampionshipBelt label={title} /> : null}
        {match.special_match_kind ? (
          <span className="bc-pill">{String(match.special_match_kind).replace(/_/g, " ")}</span>
        ) : null}
      </div>
      <div className={`bc-team${rightWin ? " winner" : ""}`}>
        <div className="bc-team-portraits">
          {right.map((p, i) => (
            <Cutout key={i} name={p.ring_name} size={76} match={match} title={title} />
          ))}
        </div>
        <p className="bc-team-name">{right.map((p) => p.ring_name).filter(Boolean).join(" & ") || "Team B"}</p>
        <div className="bc-team-members">{rightWin ? "Winning team" : "Team"}</div>
      </div>
    </div>
  );
}

export function MultiPersonMatchGraphic({ match }: { match: any }) {
  const title = championshipLabel(match);
  const parts: Participant[] = match.participants?.length
    ? match.participants
    : [
        { ring_name: match.winner_name, result: "win" },
        ...(match.loser_name ? [{ ring_name: match.loser_name, result: "loss" }] : []),
      ];
  return (
    <div className="bc-multi">
      {parts.map((p, i) => (
        <div key={i} className={`bc-multi-slot${p.result === "win" ? " winner" : ""}`}>
          <Cutout name={p.ring_name} size={88} match={match} title={title} />
          <p className="bc-multi-name">{p.ring_name || "TBA"}</p>
          {p.result === "win" ? <span className="bc-pill win">Winner</span> : null}
        </div>
      ))}
    </div>
  );
}

export function RoyalRumbleGraphic({ match }: { match: any }) {
  const title = championshipLabel(match);
  const parts: Participant[] = [...(match.participants || [])];
  const winner: Participant =
    parts.find((p) => p.result === "win") ||
    parts.find((p) => String(p.eliminated_by || "").toLowerCase() === "winner") ||
    { ring_name: match.winner_name, result: "win" };
  const withEntry = parts
    .filter((p) => p.entry_number != null)
    .sort((a, b) => Number(a.entry_number) - Number(b.entry_number));
  const finalFour = [...parts]
    .filter((p) => p.elimination_order != null || p.result === "win")
    .sort((a, b) => {
      if (a.result === "win") return -1;
      if (b.result === "win") return 1;
      return Number(b.elimination_order || 0) - Number(a.elimination_order || 0);
    })
    .slice(0, 4);

  return (
    <div className="bc-rumble">
      <div className="bc-rumble-winner">
        <Cutout name={winner.ring_name} size={128} match={match} title={title} />
        <p className="bc-fighter-name" style={{ fontSize: "1.6rem" }}>
          {winner.ring_name || "Winner unavailable"}
        </p>
        <span className="bc-pill gold" style={{ marginTop: 8 }}>
          Rumble Winner
        </span>
        {winner.entry_number != null ? <div className="bc-fighter-sub">Entry #{winner.entry_number}</div> : null}
      </div>
      <div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          <span className="bc-pill">{parts.length ? `${parts.length} participants` : "Count n/a"}</span>
          {fmtDuration(match.match_duration_seconds) ? (
            <span className="bc-pill">{fmtDuration(match.match_duration_seconds)}</span>
          ) : null}
        </div>
        {finalFour.length > 0 && (
          <>
            <h4 style={{ fontFamily: "var(--font-display)", letterSpacing: "0.08em", margin: "14px 0 8px" }}>
              Final stretch
            </h4>
            <div className="bc-final-four">
              {finalFour.map((p, i) => (
                <div key={i} className={`bc-multi-slot${p.result === "win" ? " winner" : ""}`}>
                  <Cutout name={p.ring_name} size={64} match={match} title={title} />
                  <p className="bc-multi-name" style={{ fontSize: "0.95rem" }}>
                    {p.ring_name}
                  </p>
                </div>
              ))}
            </div>
          </>
        )}
        {withEntry.length > 0 && (
          <div className="pst" data-variant="rumble" style={{ marginTop: 14, boxShadow: "none" }}>
            <div className="pst-scroll" style={{ maxHeight: Math.min(520, 48 + withEntry.length * 34) }}>
              <table>
                <thead>
                  <tr>
                    <th>Entry</th>
                    <th>Wrestler</th>
                    <th>Result</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {withEntry.map((p, i) => (
                    <tr key={`${p.entry_number}-${p.wrestler_id || p.ring_name || i}`} className={p.result === "win" ? "is-winner" : undefined}>
                      <td>{p.entry_number}</td>
                      <td>{p.ring_name}</td>
                      <td>{p.result || (p.elimination_order != null ? `Elim #${p.elimination_order}` : "—")}</td>
                      <td>{fmtDuration(p.time_in_match_seconds) || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="bc-fighter-sub" style={{ marginTop: 8 }}>
              Showing all {withEntry.length} entrances
              {parts.length > withEntry.length
                ? ` (${parts.length - withEntry.length} without entry # omitted)`
                : ""}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function ChampionshipMatchGraphic({ match }: { match: any }) {
  return <SinglesMatchGraphic match={match} />;
}

export function BroadcastMatchScorecard({
  match,
  watermark,
  eventName,
  eventYear,
  eventId,
}: {
  match: any;
  watermark?: string;
  eventName?: string;
  eventYear?: number | string;
  eventId?: string;
}) {
  const { theme } = useEventTheme();
  const group = String(match.match_type_group || match.match_type_raw || "").toLowerCase();
  const state = detectMatchState(match);
  const title = championshipLabel(match);
  const [logo, setLogo] = useState<string | null>(null);

  useEffect(() => {
    loadEventLogoManifest().then((m) => {
      setLogo(
        logoPathFromManifest(m, {
          eventId: eventId || match.event_id,
          eventName: eventName || match.event_name,
          eventYear: eventYear || match.event_year,
          series: match.event_series,
        })
      );
    });
  }, [eventId, eventName, eventYear, match.event_id, match.event_name, match.event_year, match.event_series]);

  let body;
  if (group.includes("rumble")) body = <RoyalRumbleGraphic match={match} />;
  else if (group.includes("tag")) body = <TagTeamMatchGraphic match={match} />;
  else if (
    group.includes("triple") ||
    group.includes("fatal") ||
    group.includes("ladder") ||
    group.includes("cage") ||
    group.includes("battle") ||
    (match.participants || []).length > 2
  )
    body = <MultiPersonMatchGraphic match={match} />;
  else if (title || String(match.is_title_match).match(/1|true/i)) body = <ChampionshipMatchGraphic match={match} />;
  else body = <SinglesMatchGraphic match={match} />;

  const matchDomId = match.match_id ? `match-${match.match_id}` : undefined;

  return (
    <article id={matchDomId} className="bc-match" data-state={state}>
      {logo ? (
        <>
          <div className="bc-match-bg-logo">
            <img src={logo} alt="" />
          </div>
          <div className="bc-match-logo-badge">
            <img src={logo} alt="" />
          </div>
        </>
      ) : null}
      <TopBar match={match} title={title} eventLogo={logo} />
      {body}
      <Foot match={match} watermark={watermark || theme.wordmark} />
    </article>
  );
}
