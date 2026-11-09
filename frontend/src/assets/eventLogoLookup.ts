/**
 * Year-specific event logos from project `/logos` (served via /logos/files + logo_index.json)
 * Falls back to older manifest at /assets/wwe/events/event_logo_manifest.json
 */

export type EventLogoManifestItem = {
  event_id?: string;
  event_name: string;
  event_year: number | null;
  event_family?: string;
  local_logo_path?: string | null;
  path?: string | null;
  file?: string;
  download_status?: string;
  needs_manual_review?: boolean;
  relevance_score?: number | null;
};

export type EventLogoManifest = {
  items: EventLogoManifestItem[];
  by_event_id?: Record<string, string | null>;
  by_key?: Record<string, string>;
  count?: number;
};

let cached: EventLogoManifest | null = null;
let loadPromise: Promise<EventLogoManifest | null> | null = null;

/** Dev/HMR: drop in-memory cache so logo_index.json updates are picked up. */
export function clearEventLogoManifestCache() {
  cached = null;
  loadPromise = null;
}

// Ensure HMR / code updates never reuse a stale in-memory manifest
clearEventLogoManifestCache();

function normalizeName(s: string): string {
  return String(s || "")
    .toLowerCase()
    .replace(/['’]/g, "")
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function slugify(s: string): string {
  return normalizeName(s).replace(/\s+/g, "-");
}

async function fetchJson(url: string): Promise<any | null> {
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}

function mergeManifests(primary: any | null, secondary: any | null): EventLogoManifest | null {
  const items: EventLogoManifestItem[] = [];
  const by_key: Record<string, string> = {};
  const by_event_id: Record<string, string | null> = {};

  const ingest = (raw: any, { preferExisting = false }: { preferExisting?: boolean } = {}) => {
    if (!raw) return;
    if (raw.by_key && typeof raw.by_key === "object") {
      for (const [k, v] of Object.entries(raw.by_key)) {
        if (!v) continue;
        if (preferExisting && by_key[k]) continue;
        by_key[k] = v as string;
      }
    }
    if (raw.by_event_id && typeof raw.by_event_id === "object") {
      for (const [k, v] of Object.entries(raw.by_event_id)) {
        if (preferExisting && by_event_id[k]) continue;
        by_event_id[k] = v as string | null;
      }
    }
    for (const it of raw.items || []) {
      const path = it.path || it.local_logo_path || null;
      if (!path) continue;
      const name = it.event_name;
      const year = it.event_year == null || it.event_year === "" ? null : Number(it.event_year);
      items.push({
        ...it,
        event_name: name,
        event_year: Number.isNaN(year as number) ? null : year,
        path,
        local_logo_path: path,
      });
      const n = normalizeName(name);
      const setKey = (k: string) => {
        if (preferExisting && by_key[k]) return;
        by_key[k] = path;
      };
      if (year != null) {
        setKey(`${n}|${year}`);
        setKey(`${slugify(name)}|${year}`);
      } else {
        setKey(n);
        setKey(slugify(name));
      }
      if (it.event_id) {
        if (!(preferExisting && by_event_id[it.event_id])) by_event_id[it.event_id] = path;
      }
    }
  };

  // Project logos/ wins; legacy only fills missing keys
  ingest(primary);
  ingest(secondary, { preferExisting: true });
  if (!items.length && !Object.keys(by_key).length) return null;
  return { items, by_key, by_event_id, count: items.length };
}

export async function loadEventLogoManifest(): Promise<EventLogoManifest | null> {
  if (cached) return cached;
  if (!loadPromise) {
    loadPromise = Promise.all([
      fetchJson(`/logos/logo_index.json?v=${Date.now()}`),
      fetchJson("/assets/wwe/events/event_logo_manifest.json"),
    ]).then(([idx, legacy]) => {
      // Prefer project logos/ index; legacy fills gaps only
      cached = mergeManifests(idx, legacy);
      return cached;
    });
  }
  return loadPromise;
}

export function logoPathFromManifest(
  manifest: EventLogoManifest | null | undefined,
  opts: {
    eventId?: string | null;
    eventName?: string | null;
    eventYear?: number | string | null;
    series?: string | null;
  }
): string | null {
  if (!manifest) return null;
  const { eventId, eventName, eventYear, series } = opts;

  const year = eventYear != null && eventYear !== "" ? Number(eventYear) : null;
  const name = eventName ? normalizeName(eventName) : "";
  const slug = eventName ? slugify(eventName) : "";
  const seriesName = series ? normalizeName(series) : "";
  const seriesSlug = series ? slugify(series) : "";

  // Family aliases: "WrestleMania X8" -> wrestlemania, "Royal Rumble" stays
  const family = name
    .replace(/\b(x|xx|xxx)?\d*\b/g, " ")
    .replace(/\b(i{1,3}|iv|v|vi{0,3}|ix|x)\b/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const familySlug = family ? family.replace(/\s+/g, "-") : "";

  // Prefer year-specific logos/ assets over legacy by_event_id mappings
  if ((name || seriesName) && year != null && !Number.isNaN(year)) {
    const candidates = [
      name ? manifest.by_key?.[`${name}|${year}`] : null,
      slug ? manifest.by_key?.[`${slug}|${year}`] : null,
      family ? manifest.by_key?.[`${family}|${year}`] : null,
      familySlug ? manifest.by_key?.[`${familySlug}|${year}`] : null,
      seriesName ? manifest.by_key?.[`${seriesName}|${year}`] : null,
      seriesSlug ? manifest.by_key?.[`${seriesSlug}|${year}`] : null,
    ].filter(Boolean) as string[];
    // Prefer project logos/ over legacy /assets paths when both exist
    const fromLogos = candidates.find((p) => p.includes("/logos/"));
    if (fromLogos) return fromLogos;
    if (candidates[0]) return candidates[0];

    const exact = manifest.items.find(
      (i) =>
        (i.path || i.local_logo_path) &&
        i.event_year === year &&
        normalizeName(i.event_name) === name
    );
    if (exact) return exact.path || exact.local_logo_path || null;

    const familyHit = manifest.items.find((i) => {
      if (!(i.path || i.local_logo_path) || i.event_year !== year) return false;
      const n = normalizeName(i.event_name);
      return (
        (family && (n === family || n.startsWith(family) || family.startsWith(n))) ||
        (seriesName && n === seriesName) ||
        n.split(" ")[0] === name.split(" ")[0]
      );
    });
    if (familyHit) return familyHit.path || familyHit.local_logo_path || null;
  }

  // Yearless assets (e.g. "John Cena's Final SmackDown.svg")
  if (name) {
    const yearless = manifest.by_key?.[name] || manifest.by_key?.[slug];
    if (yearless) return yearless;
    const fuzzy = manifest.items.find((i) => {
      const p = i.path || i.local_logo_path;
      if (!p) return false;
      const n = normalizeName(i.event_name);
      return n === name || n.includes(name) || name.includes(n);
    });
    if (fuzzy) return fuzzy.path || fuzzy.local_logo_path || null;
  }

  if (eventId && manifest.by_event_id?.[eventId]) return manifest.by_event_id[eventId];

  if (eventId) {
    const byId = manifest.items.find((i) => i.event_id === eventId && (i.path || i.local_logo_path));
    if (byId) return byId.path || byId.local_logo_path || null;
  }
  return null;
}
