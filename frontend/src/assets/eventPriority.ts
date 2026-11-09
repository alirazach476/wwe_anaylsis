/** Featured / gallery priority for major WWE event families. */
export const TOP_EVENT_SERIES = [
  "WrestleMania",
  "SummerSlam",
  "Elimination Chamber",
  "Royal Rumble",
  "Backlash",
  "Crown Jewel",
  "Clash at the Castle",
  "Money in the Bank",
  "Wrestlepalooza",
  "Survivor Series",
  "Night of Champions",
] as const;

export type TopEventSeries = (typeof TOP_EVENT_SERIES)[number];

export function seriesSlug(series: string): string {
  return String(series || "")
    .toLowerCase()
    .replace(/['']/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function seriesFromSlug(slug: string): string {
  const hit = TOP_EVENT_SERIES.find((s) => seriesSlug(s) === slug);
  if (hit) return hit;
  return decodeURIComponent(slug || "")
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/** More-specific family labels win (e.g. WrestleMania Backlash → Backlash). */
export function matchesEventFamily(
  family: string,
  series?: string | null,
  name?: string | null
): boolean {
  const f = family.toLowerCase();
  const s = String(series || "").toLowerCase();
  const n = String(name || "").toLowerCase();
  const hay = `${s} ${n}`;

  if (f === "backlash") {
    return hay.includes("backlash");
  }
  if (f === "wrestlemania") {
    // Core Mania events only — branded Backlash stays under Backlash hub
    if (n.includes("backlash")) return false;
    return s.includes("wrestlemania") || /^wrestlemania\b/.test(n);
  }
  if (f === "survivor series") {
    return hay.includes("survivor series");
  }
  if (f === "clash at the castle") {
    return hay.includes("clash at the castle") || hay.includes("clash in ");
  }
  return hay.includes(f);
}

function seriesRank(series?: string | null, name?: string | null): number {
  // Prefer longest / most specific TOP match
  let best = TOP_EVENT_SERIES.length + 1;
  let bestLen = -1;
  const hay = `${series || ""} ${name || ""}`.toLowerCase();
  TOP_EVENT_SERIES.forEach((label, i) => {
    const key = label.toLowerCase();
    if (!hay.includes(key)) return;
    // Special-case: WrestleMania Backlash belongs with Backlash rank
    if (key === "wrestlemania" && hay.includes("backlash")) return;
    if (key.length > bestLen) {
      bestLen = key.length;
      best = i;
    }
  });
  return best;
}

/** Sort major series first (priority order), then newest date within each tier. */
export function sortEventsByPriority<
  T extends { event_series?: string | null; event_name?: string | null; event_date?: string | null },
>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const ra = seriesRank(a.event_series, a.event_name);
    const rb = seriesRank(b.event_series, b.event_name);
    if (ra !== rb) return ra - rb;
    return String(b.event_date || "").localeCompare(String(a.event_date || ""));
  });
}

export function filterEventsByFamily<
  T extends { event_series?: string | null; event_name?: string | null; event_date?: string | null },
>(items: T[], family: string): T[] {
  return sortEventsByPriority(
    items.filter((e) => matchesEventFamily(family, e.event_series, e.event_name))
  );
}

function eventKey<T extends { event_id?: string; event_name?: string | null; event_date?: string | null }>(e: T): string {
  return String(e.event_id || `${e.event_name}|${e.event_date}`);
}

/** Normalize raw warehouse series labels into a display family name. */
export function normalizeSeriesFamily(series?: string | null, name?: string | null): string {
  const s = String(series || "").trim();
  const n = String(name || "").trim();
  const hay = `${s} ${n}`.toLowerCase();

  if (hay.includes("survivor series")) return "Survivor Series";
  if (hay.includes("clash at the castle") || hay.includes("clash in ")) return "Clash at the Castle";
  if (hay.includes("backlash")) return "Backlash";
  if ((s.toLowerCase().includes("wrestlemania") || /^wrestlemania\b/i.test(n)) && !hay.includes("backlash")) {
    return "WrestleMania";
  }
  if (hay.includes("king and queen of the ring") || hay.includes("king of the ring")) return "King of the Ring";
  if (hay.includes("saturday night") && hay.includes("main event")) return "Saturday Night's Main Event";
  if (hay.includes("sunday night") && hay.includes("main event")) return "Sunday Night's Main Event";
  if (s) return s;
  if (n) {
    // Strip year / night suffixes for one-offs
    return n.replace(/\s*\(\d{4}\)\s*$/i, "").replace(/\s+night\s*[12]\s*$/i, "").trim() || "Special Events";
  }
  return "Special Events";
}

export function groupEventsByFamily<
  T extends { event_series?: string | null; event_name?: string | null; event_date?: string | null; event_id?: string },
>(items: T[]): { family: string; events: T[]; latest?: T }[] {
  const groups: { family: string; events: T[]; latest?: T }[] = [];
  const used = new Set<string>();

  // Priority hubs first (WrestleMania, SummerSlam, …)
  for (const family of TOP_EVENT_SERIES) {
    const events = filterEventsByFamily(items, family);
    events.forEach((e) => used.add(eventKey(e)));
    if (!events.length) continue;
    groups.push({ family, events, latest: events[0] });
  }

  // Remaining series each get their own header (Hell in a Cell, TLC, No Mercy, …)
  const leftover = items.filter((e) => !used.has(eventKey(e)));
  const byFamily = new Map<string, T[]>();
  for (const e of leftover) {
    const family = normalizeSeriesFamily(e.event_series, e.event_name);
    if (!byFamily.has(family)) byFamily.set(family, []);
    byFamily.get(family)!.push(e);
  }

  const extra = [...byFamily.entries()]
    .map(([family, events]) => {
      const sorted = [...events].sort((a, b) =>
        String(b.event_date || "").localeCompare(String(a.event_date || ""))
      );
      return { family, events: sorted, latest: sorted[0] };
    })
    .sort((a, b) => {
      // More editions first, then A–Z
      if (b.events.length !== a.events.length) return b.events.length - a.events.length;
      return a.family.localeCompare(b.family);
    });

  groups.push(...extra);
  return groups;
}

export function pickFeaturedTopEvents<
  T extends { event_series?: string | null; event_name?: string | null; event_date?: string | null },
>(items: T[], limit = 12): T[] {
  const featured: T[] = [];
  const seen = new Set<string>();

  for (const series of TOP_EVENT_SERIES) {
    const list = filterEventsByFamily(items, series);
    const hit = list[0];
    if (!hit) continue;
    const key = `${hit.event_series}|${hit.event_name}|${hit.event_date}`;
    if (seen.has(key)) continue;
    seen.add(key);
    featured.push(hit);
    if (featured.length >= limit) return featured;
  }

  for (const e of sortEventsByPriority(items)) {
    const key = `${e.event_series}|${e.event_name}|${e.event_date}`;
    if (seen.has(key)) continue;
    seen.add(key);
    featured.push(e);
    if (featured.length >= limit) break;
  }
  return featured;
}
