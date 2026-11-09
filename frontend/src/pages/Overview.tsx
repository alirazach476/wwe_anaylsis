import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Plot from "react-plotly.js";
import { api } from "../api";
import { EventCard } from "../components/EventCard";
import { EventArtwork } from "../components/EventArtwork";
import { BroadcastStatsStrip } from "../components/broadcast/BroadcastStatsStrip";
import { useFilters } from "../state/filters";
import { useEventTheme } from "../theme/EventThemeContext";
import { plotlyLayout, accentColor } from "../theme/chartTheme";
import { resolveEventTheme } from "../theme/eventThemes";
import { pickFeaturedTopEvents, seriesSlug, TOP_EVENT_SERIES } from "../assets/eventPriority";

export default function Overview() {
  const { query } = useFilters();
  const { theme, setEventIdentity, resetTheme } = useEventTheme();
  const [data, setData] = useState<any>(null);
  const [catalog, setCatalog] = useState<any[]>([]);
  const [featured, setFeatured] = useState<any[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    setErr("");
    api.overview(query).then(setData).catch((e) => setErr(String(e)));
    api.events({ ...query, limit: 500 }).then((r) => {
      const items = r.items || [];
      setCatalog(items);
      const picks = pickFeaturedTopEvents(items, 11);
      setFeatured(picks);
      if (picks[0]) setEventIdentity(picks[0].event_series, picks[0].event_name);
      else resetTheme();
    });
  }, [query, setEventIdentity, resetTheme]);

  const hero = featured[0];
  const heroTheme = useMemo(
    () => resolveEventTheme(hero?.event_series, hero?.event_name),
    [hero]
  );
  const accent = accentColor(theme);

  const byYear = useMemo(() => {
    const map = new Map<number, { events: number; attendanceSum: number; matches: number; knownAtt: number }>();
    for (const e of catalog) {
      const y = Number(e.event_year);
      if (!Number.isFinite(y)) continue;
      const cur = map.get(y) || { events: 0, attendanceSum: 0, matches: 0, knownAtt: 0 };
      cur.events += 1;
      cur.matches += Number(e.matches) || 0;
      const att = Number(e.attendance);
      if (Number.isFinite(att) && att > 0) {
        cur.attendanceSum += att;
        cur.knownAtt += 1;
      }
      map.set(y, cur);
    }
    return [...map.entries()]
      .sort((a, b) => a[0] - b[0])
      .map(([year, v]) => ({
        year,
        events: v.events,
        matches: v.matches,
        avgAttendance: v.knownAtt > 0 ? Math.round(v.attendanceSum / v.knownAtt) : null,
      }));
  }, [catalog]);

  const bySeries = useMemo(() => {
    const map = new Map<string, { events: number; matches: number }>();
    for (const e of catalog) {
      const s = String(e.event_series || "Other");
      const cur = map.get(s) || { events: 0, matches: 0 };
      cur.events += 1;
      cur.matches += Number(e.matches) || 0;
      map.set(s, cur);
    }
    return [...map.entries()]
      .map(([series, v]) => ({ series, ...v }))
      .sort((a, b) => b.events - a.events)
      .slice(0, 14);
  }, [catalog]);

  const byCountry = useMemo(() => {
    const map = new Map<string, number>();
    for (const e of catalog) {
      const c = String(e.country || "Unknown");
      map.set(c, (map.get(c) || 0) + 1);
    }
    return [...map.entries()]
      .map(([country, count]) => ({ country, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 12);
  }, [catalog]);

  const attendanceLeaders = useMemo(
    () =>
      [...catalog]
        .filter((e) => Number(e.attendance) > 0)
        .sort((a, b) => Number(b.attendance) - Number(a.attendance))
        .slice(0, 12),
    [catalog]
  );

  const matchLoad = useMemo(() => {
    const vals = catalog.map((e) => Number(e.matches) || 0).filter((n) => n > 0);
    const buckets = new Map<string, number>();
    for (const n of vals) {
      const key = n <= 4 ? "1–4" : n <= 8 ? "5–8" : n <= 12 ? "9–12" : "13+";
      buckets.set(key, (buckets.get(key) || 0) + 1);
    }
    return ["1–4", "5–8", "9–12", "13+"].map((k) => ({ bucket: k, count: buckets.get(k) || 0 }));
  }, [catalog]);

  const scatter = useMemo(
    () =>
      catalog
        .filter((e) => Number(e.attendance) > 0 && Number(e.matches) > 0)
        .map((e) => ({
          attendance: Number(e.attendance),
          matches: Number(e.matches),
          name: e.event_name,
          year: e.event_year,
        })),
    [catalog]
  );

  if (err) return <div className="bc-empty"><h4>Overview unavailable</h4><p>{err}</p></div>;
  if (!data) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div className="bc-skeleton" style={{ height: 360 }} />
        <div className="bc-skeleton" style={{ height: 120 }} />
      </div>
    );
  }
  const k = data.kpis;
  const coverage =
    k.year_from != null && k.year_to != null ? `${k.year_from}–${k.year_to}` : "Unavailable";
  const yearSpark = (data.by_year || []).map((r: any) => Number(r.events) || 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <section className="event-hero" style={{ ["--event-primary" as string]: heroTheme.primary }}>
        <div>
          <div className="event-hero-badge">
            <img src="/branding/wwe-logo.png" alt="" width={18} height={18} />
            WWE Legacy Analytics
          </div>
          <h1>{hero?.event_name || "Premium Live Event Intelligence"}</h1>
          <p className="muted" style={{ maxWidth: 520 }}>
            Broadcast-grade historical analytics for WWE Premium Live Events — warehouse marts, year-specific logos, and match graphics.
          </p>
          <div className="event-hero-strip">
            {hero?.event_date ? (
              <span>
                <strong>Date</strong>
                {hero.event_date}
              </span>
            ) : null}
            {hero?.venue_name ? (
              <span>
                <strong>Venue</strong>
                {hero.venue_name}
              </span>
            ) : null}
            {hero?.city || hero?.country ? (
              <span>
                <strong>Location</strong>
                {[hero.city, hero.country].filter(Boolean).join(", ")}
              </span>
            ) : null}
            {hero?.matches != null ? (
              <span>
                <strong>Card</strong>
                {hero.matches} matches
              </span>
            ) : null}
          </div>
          {hero ? (
            <Link className="btn" to={`/events/${hero.event_id}`}>
              Open event analytics →
            </Link>
          ) : (
            <Link className="btn" to="/events">
              Explore all events →
            </Link>
          )}
        </div>
        <div className="event-hero-art">
          <div className="event-hero-watermark">{heroTheme.wordmark}</div>
          <EventArtwork
            series={hero?.event_series}
            eventName={hero?.event_name}
            eventYear={hero?.event_year}
            eventId={hero?.event_id}
            size="lg"
            driveTheme
          />
        </div>
      </section>

      <BroadcastStatsStrip
        stats={[
          { label: "PLE Events", value: k.total_events, context: "Filtered catalog", spark: yearSpark.slice(-12) },
          { label: "Matches", value: k.total_matches, context: "Recorded results" },
          { label: "Wrestlers", value: k.unique_wrestlers, context: "Distinct competitors" },
          { label: "Championships", value: k.total_championships ?? "—", context: "Title lineages tracked" },
          { label: "Title matches", value: k.championship_matches, context: "Stipulation share" },
          { label: "Venues", value: k.total_venues ?? "—", context: "Arenas & stadiums" },
          { label: "Countries", value: k.total_countries ?? "—", context: "Global footprint" },
          { label: "Coverage", value: coverage, context: "Historical window" },
        ]}
      />

      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
          <h3 style={{ margin: 0, fontFamily: "var(--font-display)", letterSpacing: "0.06em" }}>
            Top series
          </h3>
          <Link to="/events" className="muted" style={{ fontSize: "0.85rem" }}>
            Browse series hubs →
          </Link>
        </div>
        <div className="filters" style={{ marginBottom: 14 }}>
          {TOP_EVENT_SERIES.map((s) => (
            <Link key={s} className="tab" to={`/series/${seriesSlug(s)}`}>
              {s}
            </Link>
          ))}
        </div>
        <div className="event-poster-grid">
          {featured.map((e) => (
            <EventCard key={e.event_id} event={e} />
          ))}
        </div>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(320px,1fr))", gap: 14 }}>
        <div className="bc-chart-panel">
          <h3>Events & matches by year</h3>
          <p className="muted">Volume trend across the PLE calendar</p>
          <Plot
            data={[
              {
                x: data.by_year.map((r: any) => r.event_year),
                y: data.by_year.map((r: any) => r.events),
                type: "bar",
                name: "Events",
                marker: { color: accent },
                hovertemplate: "%{x}<br>%{y} events<extra></extra>",
              },
              {
                x: data.by_year.map((r: any) => r.event_year),
                y: data.by_year.map((r: any) => r.matches),
                type: "scatter",
                mode: "lines+markers",
                name: "Matches",
                yaxis: "y2",
                line: { color: theme.accent, width: 2 },
                hovertemplate: "%{x}<br>%{y} matches<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, {
              height: 340,
              yaxis2: { overlaying: "y", side: "right", gridcolor: "rgba(255,255,255,0.04)" },
            })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
        <div className="bc-chart-panel">
          <h3>Series distribution</h3>
          <p className="muted">Share of event families in the warehouse</p>
          <Plot
            data={[
              {
                labels: data.by_series.slice(0, 12).map((r: any) => r.event_series),
                values: data.by_series.slice(0, 12).map((r: any) => r.events),
                type: "pie",
                hole: 0.52,
                marker: {
                  colors: data.by_series.slice(0, 12).map((r: any) => resolveEventTheme(r.event_series).primary),
                },
                textinfo: "label+percent",
                textposition: "inside",
                hovertemplate: "<b>%{label}</b><br>%{value} events (%{percent})<extra></extra>",
              },
            ]}
            layout={plotlyLayout(theme, { height: 340, showlegend: false, margin: { t: 10, b: 10, l: 10, r: 10 } })}
            style={{ width: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
      </div>

      <section style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div>
          <h3 style={{ margin: 0, fontFamily: "var(--font-display)", letterSpacing: "0.06em" }}>
            Catalog insights
          </h3>
          <p className="muted" style={{ marginTop: 6 }}>
            Event density, gates, geography, and card size across the loaded PLE catalog
          </p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(320px,1fr))", gap: 14 }}>
          <div className="bc-chart-panel">
            <h3>Events per year</h3>
            <p className="muted">Catalog density across the timeline</p>
            <Plot
              data={[
                {
                  x: byYear.map((r) => r.year),
                  y: byYear.map((r) => r.events),
                  type: "bar",
                  marker: { color: accent },
                  hovertemplate: "<b>%{x}</b><br>%{y} events<extra></extra>",
                },
              ]}
              layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 40, l: 44, r: 10 } })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          </div>

          <div className="bc-chart-panel">
            <h3>Avg attendance by year</h3>
            <p className="muted">Mean gate per event (zeros / missing excluded)</p>
            <Plot
              data={[
                {
                  x: byYear.map((r) => r.year),
                  y: byYear.map((r) => r.avgAttendance),
                  type: "scatter",
                  mode: "lines+markers",
                  fill: "tozeroy",
                  line: { color: accent, width: 2.5 },
                  marker: { size: 5 },
                  hovertemplate: "<b>%{x}</b><br>Avg %{y:,}<extra></extra>",
                },
              ]}
              layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 40, l: 56, r: 10 } })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          </div>

          <div className="bc-chart-panel">
            <h3>Events by series</h3>
            <p className="muted">Which families appear most often</p>
            <Plot
              data={[
                {
                  x: bySeries.map((r) => r.events),
                  y: bySeries.map((r) => r.series),
                  type: "bar",
                  orientation: "h",
                  marker: { color: accent },
                  hovertemplate: "<b>%{y}</b><br>%{x} events<extra></extra>",
                },
              ]}
              layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 40, l: 120, r: 16 } })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          </div>

          <div className="bc-chart-panel">
            <h3>Countries</h3>
            <p className="muted">Where PLEs have been staged</p>
            <Plot
              data={[
                {
                  labels: byCountry.map((r) => r.country),
                  values: byCountry.map((r) => r.count),
                  type: "pie",
                  hole: 0.5,
                  textinfo: "label+percent",
                  hovertemplate: "<b>%{label}</b><br>%{value} events<extra></extra>",
                  marker: {
                    colors: [accent, theme.accent, "#71717a", "#d4af37", "#38bdf8", "#f472b6", "#22c55e", "#a855f7"],
                  },
                },
              ]}
              layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 10, l: 10, r: 10 }, showlegend: false })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          </div>

          <div className="bc-chart-panel">
            <h3>Card size mix</h3>
            <p className="muted">How many matches typical events carry</p>
            <Plot
              data={[
                {
                  x: matchLoad.map((r) => r.bucket),
                  y: matchLoad.map((r) => r.count),
                  type: "bar",
                  marker: { color: theme.accent },
                  hovertemplate: "<b>%{x} matches</b><br>%{y} events<extra></extra>",
                },
              ]}
              layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 40, l: 44, r: 10 } })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          </div>

          <div className="bc-chart-panel">
            <h3>Top gates</h3>
            <p className="muted">Highest reported attendance</p>
            <Plot
              data={[
                {
                  x: attendanceLeaders.map((e) => e.attendance),
                  y: attendanceLeaders.map((e) => e.event_name),
                  type: "bar",
                  orientation: "h",
                  marker: { color: accent },
                  hovertemplate: "<b>%{y}</b><br>%{x:,}<extra></extra>",
                },
              ]}
              layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 40, l: 140, r: 16 } })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          </div>

          <div className="bc-chart-panel">
            <h3>Matches booked by series</h3>
            <p className="muted">Total bout volume inside each family</p>
            <Plot
              data={[
                {
                  x: bySeries.map((r) => r.series),
                  y: bySeries.map((r) => r.matches),
                  type: "bar",
                  marker: { color: accent },
                  hovertemplate: "<b>%{x}</b><br>%{y} matches<extra></extra>",
                },
              ]}
              layout={plotlyLayout(theme, { height: 320, margin: { t: 10, b: 90, l: 44, r: 10 } })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          </div>

          <div className="bc-chart-panel">
            <h3>Attendance vs card size</h3>
            <p className="muted">Does a bigger gate track with more matches?</p>
            <Plot
              data={[
                {
                  x: scatter.map((r) => r.matches),
                  y: scatter.map((r) => r.attendance),
                  text: scatter.map((r) => `${r.name} (${r.year})`),
                  type: "scatter",
                  mode: "markers",
                  marker: { color: accent, size: 8, opacity: 0.75 },
                  hovertemplate: "<b>%{text}</b><br>%{x} matches · %{y:,} attendance<extra></extra>",
                },
              ]}
              layout={plotlyLayout(theme, {
                height: 320,
                margin: { t: 10, b: 48, l: 56, r: 10 },
                xaxis: { title: { text: "Matches" }, gridcolor: "rgba(255,255,255,0.06)" },
                yaxis: { title: { text: "Attendance" }, gridcolor: "rgba(255,255,255,0.06)" },
              })}
              style={{ width: "100%" }}
              config={{ displayModeBar: false, responsive: true }}
            />
          </div>
        </div>
      </section>
    </div>
  );
}
