import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { filterEventsByFamily, normalizeSeriesFamily, seriesFromSlug, seriesSlug } from "../assets/eventPriority";
import { EventCard } from "../components/EventCard";
import { BroadcastStatsStrip } from "../components/broadcast/BroadcastStatsStrip";
import { EventArtwork } from "../components/EventArtwork";
import { useFilters } from "../state/filters";
import { useEventTheme } from "../theme/EventThemeContext";
import { resolveEventTheme } from "../theme/eventThemes";
import { collapseMultiNightEvents } from "../utils/multiNightEvents";

export default function EventSeries() {
  const { seriesSlug: slugParam } = useParams();
  const family = seriesFromSlug(slugParam || "");
  const { setEventIdentity } = useEventTheme();
  const { filters, setFilters, query } = useFilters();
  const [items, setItems] = useState<any[]>([]);
  const [err, setErr] = useState("");

  // Keep global series filter in sync with this hub
  useEffect(() => {
    if (filters.series !== family) {
      setFilters((f) => ({ ...f, series: family }));
    }
  }, [family]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setErr("");
    setEventIdentity(family, family);
    api
      .events({
        year_from: query.year_from,
        year_to: query.year_to,
        country: query.country,
        limit: 500,
      })
      .then((r) => {
        // Prefer priority family rules; fall back to normalized series label match.
        const byFamily = filterEventsByFamily(r.items, family);
        if (byFamily.length) {
          setItems(byFamily);
          return;
        }
        const slugTarget = seriesSlug(family);
        setItems(
          r.items.filter((e) => {
            const label = normalizeSeriesFamily(e.event_series, e.event_name);
            return (
              seriesSlug(label) === slugTarget ||
              String(e.event_series || "").toLowerCase().includes(family.toLowerCase()) ||
              String(e.event_name || "").toLowerCase().includes(family.toLowerCase())
            );
          })
        );
      })
      .catch((e) => setErr(String(e)));
  }, [family, query.year_from, query.year_to, query.country, setEventIdentity]);

  const editions = useMemo(() => collapseMultiNightEvents(items), [items]);
  const theme = useMemo(() => resolveEventTheme(family, items[0]?.event_name || family), [family, items]);
  const years = useMemo(() => {
    const ys = items.map((e) => Number(e.event_year)).filter((n) => !Number.isNaN(n));
    return ys.length ? { from: Math.min(...ys), to: Math.max(...ys) } : null;
  }, [items]);
  const matchTotal = useMemo(
    () => items.reduce((a, e) => a + (Number(e.matches) || 0), 0),
    [items]
  );

  if (err) {
    return (
      <div className="bc-empty">
        <h4>Series unavailable</h4>
        <p>{err}</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <section className="event-hero" style={{ ["--event-primary" as string]: theme.primary }}>
        <div>
          <div className="event-hero-badge">{family} · Series archive</div>
          <h1>{family}</h1>
          <p className="muted" style={{ maxWidth: 520 }}>
            Every {family} event in the warehouse — two-night shows are combined as Night 1 · Night 2.
          </p>
          <div className="event-hero-strip">
            <span>
              <strong>Events</strong>
              {editions.length}
            </span>
            <span>
              <strong>Span</strong>
              {years ? `${years.from}–${years.to}` : "—"}
            </span>
            <span>
              <strong>Matches</strong>
              {matchTotal || "—"}
            </span>
          </div>
          <Link className="btn ghost" to="/events">
            ← All series
          </Link>
        </div>
        <div className="event-hero-art">
          <div className="event-hero-watermark">{theme.wordmark}</div>
          <EventArtwork
            series={family}
            eventName={items[0]?.event_name || family}
            eventYear={items[0]?.event_year}
            eventId={items[0]?.event_id}
            size="lg"
            driveTheme
          />
        </div>
      </section>

      <BroadcastStatsStrip
        stats={[
          { label: "Editions", value: editions.length, context: `${family} catalog (nights combined)` },
          { label: "First year", value: years?.from ?? "—", context: "Earliest in dataset" },
          { label: "Latest year", value: years?.to ?? "—", context: items[0]?.event_name || "—" },
          { label: "Total matches", value: matchTotal || "—", context: "Across editions" },
        ]}
      />

      {!editions.length ? (
        <div className="bc-empty">
          <h4>No events</h4>
          <p>No {family} events matched the current filters.</p>
        </div>
      ) : (
        <div className="event-poster-grid">
          {editions.map((e) => (
            <EventCard key={e.event_id} event={e} />
          ))}
        </div>
      )}

      <p className="muted" style={{ fontSize: "0.78rem" }}>
        Series key <code>{seriesSlug(family)}</code>
      </p>
    </div>
  );
}
