const BASE = "";

async function get<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const url = new URL(path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "" && v !== null) url.searchParams.set(k, String(v));
    });
  }
  const res = await fetch(`${BASE}${url.pathname}${url.search}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  overview: (p?: Record<string, string | number | undefined>) =>
    get<{ kpis: Record<string, number>; by_year: any[]; by_country: any[]; by_series: any[] }>(
      "/api/analytics/overview",
      p
    ),
  events: (p?: Record<string, string | number | undefined>) =>
    get<{ total: number; items: any[] }>("/api/events", p),
  event: (id: string) => get<any>(`/api/events/${id}`),
  wrestlers: (p?: Record<string, string | number | undefined>) =>
    get<{ total: number; items: any[] }>("/api/wrestlers", p),
  wrestler: (id: string) => get<any>(`/api/wrestlers/${id}`),
  matches: (p?: Record<string, string | number | boolean | undefined>) =>
    get<{ total: number; items: any[] }>("/api/matches", p),
  matchAnalytics: () => get<any>("/api/analytics/matches"),
  championships: () => get<any>("/api/analytics/championships"),
  historicalRecords: () => get<any>("/api/analytics/historical-records"),
  rumble: () => get<any>("/api/analytics/royal-rumble"),
  mitb: () => get<any>("/api/analytics/money-in-the-bank"),
  attendance: () => get<any>("/api/analytics/attendance"),
  global: () => get<any>("/api/analytics/global"),
  ml: () => get<any>("/api/analytics/ml"),
  meta: () => get<{ years: number[]; series: string[]; countries: string[]; match_types: string[] }>("/api/filters/meta"),
};
