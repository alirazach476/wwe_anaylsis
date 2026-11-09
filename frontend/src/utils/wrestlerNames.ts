/** Display cleanup for scraped ring names (e.g. "and Jimmy Uso", title clutter). */
export function cleanWrestlerName(name?: string | null): string {
  let s = String(name || "").trim();
  if (!s) return "";
  s = s.replace(/\([^)]*\)/g, " ");
  s = s.replace(/\[[^\]]*\]/g, " ");
  s = s.replace(/[)"'\u201c\u201d*]+/g, " ");
  s = s.replace(/^\s*and\s+/i, "");
  s = s.replace(/^\s*(although|team|the shield)\s+/i, "");
  s = s.replace(/\s+by\s+.+$/i, "");
  s = s.replace(/\s+\d+$/g, "");
  s = s.replace(/\s+/g, " ").replace(/^[\s\-–,./]+|[\s\-–,./]+$/g, "").trim();
  // Prefer "Miz" over "The Miz"; keep Undertaker
  const the = s.match(/^the\s+(.+)$/i);
  if (the) {
    const rest = the[1].trim();
    const rl = rest.toLowerCase();
    if (rl === "undertaker") s = "The Undertaker";
    else if (rl === "miz" || rl === "big show" || !rest.includes(" ")) s = rest;
  }
  return s.replace(/\s+/g, " ").trim();
}

export function wrestlerNameKey(name?: string | null): string {
  const display = cleanWrestlerName(name).toLowerCase();
  let key = display.replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
  if (key.startsWith("the ")) {
    const rest = key.slice(4);
    if (rest === "miz" || rest === "big show") key = rest;
  }
  return key;
}

export function matchScoreboardPath(eventId?: string | null, matchId?: string | null): string | null {
  if (!eventId) return null;
  if (matchId) return `/events/${eventId}?match=${encodeURIComponent(String(matchId))}`;
  return `/events/${eventId}`;
}

export function isUpcomingEvent(event: {
  event_status?: string | null;
  event_date?: string | null;
  matches?: number | null;
}): boolean {
  const status = String(event.event_status || "").toLowerCase();
  if (status === "announced" || status === "upcoming" || status === "scheduled") return true;
  if (event.event_date) {
    const d = new Date(String(event.event_date));
    if (!Number.isNaN(d.getTime())) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (d > today) return true;
    }
  }
  const n = Number(event.matches);
  if (status !== "completed" && (!Number.isFinite(n) || n <= 0)) return true;
  return false;
}
