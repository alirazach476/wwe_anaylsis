/** Pair consecutive same-weekend PLE shows into Night 1 / Night 2 bundles. */

export type NightInfo = {
  night: 1 | 2;
  event_id: string;
  event_date?: string | null;
  event_name?: string | null;
  matches?: number | null;
};

function dayMs(date?: string | null): number | null {
  if (!date) return null;
  const d = new Date(String(date));
  if (Number.isNaN(d.getTime())) return null;
  return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
}

function baseEventKey(e: {
  event_series?: string | null;
  event_name?: string | null;
  event_year?: number | string | null;
}): string {
  const series = String(e.event_series || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
  const name = String(e.event_name || "")
    .toLowerCase()
    .replace(/\bnight\s*[12]\b/g, "")
    .replace(/\bday\s*[12]\b/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
  const year = String(e.event_year || "");
  // Prefer series+year for known multi-night brands; fall back to cleaned name+year
  if (series.includes("wrestlemania") || series.includes("summerslam")) {
    return `${series}|${year}`;
  }
  return `${series || name}|${name}|${year}`;
}

export function areSiblingNights(a: any, b: any): boolean {
  if (!a || !b || a.event_id === b.event_id) return false;
  if (baseEventKey(a) !== baseEventKey(b)) return false;
  const da = dayMs(a.event_date);
  const db = dayMs(b.event_date);
  if (da == null || db == null) return false;
  const diff = Math.abs(db - da) / 86400000;
  return diff >= 1 && diff <= 2;
}

/** Collapse consecutive Night 1/2 pairs into one list item for posters/tables. */
export function collapseMultiNightEvents<T extends Record<string, any>>(events: T[]): T[] {
  const sorted = [...events].sort((a, b) => String(a.event_date || "").localeCompare(String(b.event_date || "")));
  const used = new Set<string>();
  const out: T[] = [];

  for (let i = 0; i < sorted.length; i++) {
    const a = sorted[i];
    const ida = String(a.event_id || "");
    if (!ida || used.has(ida)) continue;

    let partner: T | null = null;
    for (let j = i + 1; j < sorted.length; j++) {
      const b = sorted[j];
      const idb = String(b.event_id || "");
      if (!idb || used.has(idb)) continue;
      if (areSiblingNights(a, b)) {
        partner = b;
        break;
      }
      // same key but farther away — stop scanning this key cluster later
      if (baseEventKey(a) === baseEventKey(b)) {
        const da = dayMs(a.event_date);
        const db = dayMs(b.event_date);
        if (da != null && db != null && (db - da) / 86400000 > 2) break;
      }
    }

    if (!partner) {
      out.push(a);
      used.add(ida);
      continue;
    }

    const nights = [a, partner].sort((x, y) => String(x.event_date || "").localeCompare(String(y.event_date || "")));
    const n1 = nights[0];
    const n2 = nights[1];
    const matches =
      (Number(n1.matches) || 0) + (Number(n2.matches) || 0) ||
      (n1.matches == null && n2.matches == null ? null : Number(n1.matches) || Number(n2.matches) || 0);

    const nightMeta: NightInfo[] = [
      { night: 1, event_id: String(n1.event_id), event_date: n1.event_date, event_name: n1.event_name, matches: n1.matches },
      { night: 2, event_id: String(n2.event_id), event_date: n2.event_date, event_name: n2.event_name, matches: n2.matches },
    ];

    const combined = {
      ...n1,
      event_id: n1.event_id,
      event_date: n1.event_date,
      event_end_date: n2.event_date || n1.event_end_date,
      matches,
      is_multi_night: true,
      night_count: 2,
      nights: nightMeta,
      display_subtitle: "Night 1 · Night 2",
    } as T;

    out.push(combined);
    used.add(String(n1.event_id));
    used.add(String(n2.event_id));
  }

  // Preserve caller-ish newest-first when dates exist
  return out.sort((a, b) => String(b.event_date || "").localeCompare(String(a.event_date || "")));
}

export function nightLabel(night: 1 | 2 | number): string {
  return `Night ${night}`;
}
