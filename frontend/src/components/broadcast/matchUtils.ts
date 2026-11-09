export type Participant = {
  wrestler_id?: string;
  ring_name?: string;
  team_id?: string | number | null;
  result?: string | null;
  entry_number?: number | null;
  elimination_order?: number | null;
  eliminated_by?: string | null;
  time_in_match_seconds?: number | null;
};

export function fmtDuration(sec?: number | null) {
  if (sec == null || Number.isNaN(Number(sec))) return null;
  const s = Math.round(Number(sec));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, "0")}`;
}

export function championshipLabel(match: any): string | null {
  const rows = match.championships || [];
  if (rows.length) {
    return rows
      .map((c: any) => prettyChampId(c.championship_id || c.championship_name))
      .filter(Boolean)
      .join(" · ");
  }
  if (match.is_title_match && String(match.is_title_match).match(/1|true/i)) {
    const kind = String(match.special_match_kind || "").replace(/_/g, " ");
    if (kind && !kind.includes("other")) return kind;
    return "Championship match";
  }
  return null;
}

export function prettyChampId(id?: string | null) {
  if (!id) return "";
  return String(id)
    .replace(/^chp_/, "")
    .replace(/_[a-f0-9]{6,}$/i, "")
    .replace(/-/g, " ")
    .replace(/\bwwe\b/gi, "WWE")
    .replace(/\bwcw\b/gi, "WCW")
    .replace(/\bnxt\b/gi, "NXT");
}

export function detectMatchState(match: any): string {
  const result = String(match.match_result || "").toLowerCase();
  const parts: Participant[] = match.participants || [];
  const hasDraw = parts.some((p) => String(p.result || "").toLowerCase() === "draw");
  if (/no contest|double dq|draw/.test(result) || hasDraw) {
    return /no contest/.test(result) ? "no-contest" : "draw";
  }
  if (!result && !match.winner_name && !(parts || []).length) return "missing";
  if (String(match.is_main_event).match(/1|true/i)) return "main-event";
  if (String(match.is_title_match).match(/1|true/i) || (match.championships || []).length) return "championship";
  if (!result && !match.winner_name) return "upcoming";
  return "completed";
}

export function parseVsNames(match: any): { a?: string; b?: string } {
  const parts: Participant[] = match.participants || [];
  if (parts.length >= 2) {
    const win = parts.find((p) => p.result === "win");
    const loss = parts.find((p) => p.result === "loss");
    const drawA = parts[0];
    const drawB = parts[1];
    if (win || loss) {
      return {
        a: win?.ring_name || match.winner_name || parts[0]?.ring_name,
        b: loss?.ring_name || match.loser_name || parts.find((p) => p.ring_name !== win?.ring_name)?.ring_name,
      };
    }
    return { a: drawA?.ring_name, b: drawB?.ring_name };
  }
  const text = String(match.match_result || "");
  const vs = text.match(/(.+?)\s+vs\.?\s+(.+?)(?:\s+ended|\s+defeated|$)/i);
  if (vs) {
    return {
      a: vs[1].replace(/^(?:united states|intercontinental|wwe|world|women'?s|universal|raw|smackdown)\s+champion\s+/i, "").trim(),
      b: vs[2].replace(/\s+ended.*$/i, "").trim(),
    };
  }
  return { a: match.winner_name, b: match.loser_name };
}

export function resultKind(match: any): "win" | "draw" | "no-contest" | "unknown" {
  const r = String(match.match_result || "").toLowerCase();
  if (/no contest/.test(r)) return "no-contest";
  if (/draw|double/.test(r)) return "draw";
  const parts: Participant[] = match.participants || [];
  if (parts.some((p) => p.result === "draw")) return "draw";
  if (match.winner_name || parts.some((p) => p.result === "win")) return "win";
  return "unknown";
}
