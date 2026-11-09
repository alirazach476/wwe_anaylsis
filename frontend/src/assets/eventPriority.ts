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

export function groupEventsByFamily<
  T extends { event_series?: string | null; event_name?: string | null; event_date?: string | null; event_id?: string },
>(items: T[]): { family: string; events: T[]; latest?: T }[] {
  const groups: { family: string; events: T[]; latest?: T }[] = [];
  const used = new Set<string>();

  for (const family of TOP_EVENT_SERIES) {
    const events = filterEventsByFamily(items, family);
    events.forEach((e) => used.add(String(e.event_id || `${e.event_name}|${e.event_date}`)));
    if (!events.length) continue;
    groups.push({ family, events, latest: events[0] });
  }

  const other = items.filter((e) => !used.has(String(e.event_id || `${e.event_name}|${e.event_date}`)));
  if (other.length) {
    const sorted = [...other].sort((a, b) =>
      String(b.event_date || "").localeCompare(String(a.event_date || ""))
    );
    groups.push({ family: "Other Events", events: sorted, latest: sorted[0] });
  }
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
