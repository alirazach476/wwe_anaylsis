import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { EventCard } from "../components/EventCard";
import { EventArtwork } from "../components/EventArtwork";
import { BroadcastStatsStrip } from "../components/broadcast/BroadcastStatsStrip";
import { SeriesFamilyCard } from "../components/broadcast/SeriesFamilyCard";
import { PremiumSportsDataTable } from "../components/broadcast/PremiumSportsDataTable";
import {
  TOP_EVENT_SERIES,
  groupEventsByFamily,
  seriesSlug,
  sortEventsByPriority,
} from "../assets/eventPriority";
import { useFilters } from "../state/filters";
import { useEventTheme } from "../theme/EventThemeContext";
import { resolveEventTheme } from "../theme/eventThemes";
import { collapseMultiNightEvents } from "../utils/multiNightEvents";

export default function Events() {
  const { query } = useFilters();
  const { setEventIdentity, resetTheme } = useEventTheme();
  const [params, setParams] = useSearchParams();
  const qParam = params.get("q") || "";
  const view = params.get("view") === "all" ? "all" : "series";
  const [rawItems, setRawItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState(qParam);

  useEffect(() => {
    setQ(qParam);
  }, [qParam]);

  useEffect(() => {
    const { series: _series, ...rest } = query;
    api.events({ ...rest, q: q || undefined, limit: 500 }).then((r) => {
      let list = r.items;
      const seriesParam = params.get("series");
      if (seriesParam) {
        const key = seriesParam.toLowerCase();
        list = list.filter(
          (e) =>
            String(e.event_series || "").toLowerCase().includes(key) ||
            String(e.event_name || "").toLowerCase().includes(key)
        );
      }
      setRawItems(list);
      setTotal(seriesParam ? list.length : r.total);
      if (list[0]) setEventIdentity(list[0].event_series, list[0].event_name);
      else resetTheme();
    });
  }, [query, q, params, setEventIdentity, resetTheme]);

  const groups = useMemo(() => {
    return groupEventsByFamily(rawItems).map((g) => {
      const events = collapseMultiNightEvents(g.events);
      return {
        ...g,
        events,
        latest: events[0] || g.latest,
      };
    });
  }, [rawItems]);

  const featuredFamilies = useMemo(
    () => new Set<string>(TOP_EVENT_SERIES as unknown as string[]),
    []
  );
  const primaryGroups = useMemo(
    () => groups.filter((g) => featuredFamilies.has(g.family)),
    [groups, featuredFamilies]
  );
  const otherGroups = useMemo(
    () => groups.filter((g) => !featuredFamilies.has(g.family)),
    [groups, featuredFamilies]
  );

  const flatSorted = useMemo(
    () => sortEventsByPriority(collapseMultiNightEvents(rawItems)),
    [rawItems]
  );

  const kpiAttendance = useMemo(() => {
    const known = rawItems
      .map((e) => Number(e.attendance))
      .filter((n) => Number.isFinite(n) && n > 0);
    if (!known.length) return null;
    return Math.round(known.reduce((a, b) => a + b, 0) / known.length);
  }, [rawItems]);

  const knownAttendanceCount = useMemo(
    () => rawItems.filter((e) => Number.isFinite(Number(e.attendance)) && Number(e.attendance) > 0).length,
    [rawItems]
  );

  const yearSpark = useMemo(() => {
    const map = new Map<number, number>();
    for (const e of rawItems) {
      const y = Number(e.event_year);
      if (!Number.isFinite(y)) continue;
      map.set(y, (map.get(y) || 0) + 1);
    }
    return [...map.entries()].sort((a, b) => a[0] - b[0]).map(([, n]) => n);
  }, [rawItems]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <BroadcastStatsStrip
        stats={[
          { label: "Events", value: total, context: "In current filter / catalog" },
          {
            label: "Series families",
            value: groups.length,
            context: "Organized hubs + archives",
          },
          {
            label: "Avg attendance",
            value: kpiAttendance ?? "—",
            context:
              knownAttendanceCount > 0
                ? `Mean gate across ${knownAttendanceCount} events with figures`
                : "No attendance figures in filter",
          },
          {
            label: "Total matches",
            value: rawItems.reduce((a, e) => a + (Number(e.matches) || 0), 0),
            context: "Across loaded events",
            spark: yearSpark,
          },
        ]}
      />

      <section className="bc-chart-panel">
        <h3>Event explorer</h3>
        <p className="muted">
          {total} events · {groups.length} series families · browse hubs or every poster under its series header
        </p>
        <div className="filters" style={{ marginBottom: 10 }}>
          <button
            type="button"
            className={`tab${view === "series" ? " active" : ""}`}
            onClick={() => {
              const next = new URLSearchParams(params);
              next.delete("view");
              setParams(next);
            }}
          >
            Series hubs
          </button>
          <button
            type="button"
            className={`tab${view === "all" ? " active" : ""}`}
            onClick={() => {
              const next = new URLSearchParams(params);
              next.set("view", "all");
              setParams(next);
            }}
          >
            All events
          </button>
        </div>
        <div className="filters">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search event name…"
            style={{
              minWidth: 220,
              height: 40,
              borderRadius: 4,
              border: "1px solid var(--border-subtle)",
              background: "rgba(0,0,0,.35)",
              color: "#fff",
              padding: "0 12px",
            }}
          />
        </div>
      </section>

      {view === "series" ? (
        <>
          <section>
            <h3 className="series-section-title">Featured series</h3>
            <p className="muted" style={{ marginTop: 0 }}>
              Flagship PLEs — open a hub for every edition
            </p>
            <div className="event-poster-grid">
              {primaryGroups.map((g) => {
                const years = g.events
                  .map((e) => Number(e.event_year))
                  .filter((n) => !Number.isNaN(n));
                return (
                  <SeriesFamilyCard
                    key={g.family}
                    family={g.family}
                    count={g.events.length}
                    latest={g.latest}
                    yearFrom={years.length ? Math.min(...years) : null}
                    yearTo={years.length ? Math.max(...years) : null}
                  />
                );
              })}
            </div>
          </section>

          {otherGroups.length ? (
            <section>
              <h3 className="series-section-title">All other series</h3>
              <p className="muted" style={{ marginTop: 0 }}>
                Every remaining PLE family with its own archive hub
              </p>
              <div className="event-poster-grid">
                {otherGroups.map((g) => {
                  const years = g.events
                    .map((e) => Number(e.event_year))
                    .filter((n) => !Number.isNaN(n));
                  return (
                    <SeriesFamilyCard
                      key={g.family}
                      family={g.family}
                      count={g.events.length}
                      latest={g.latest}
                      yearFrom={years.length ? Math.min(...years) : null}
                      yearTo={years.length ? Math.max(...years) : null}
                    />
                  );
                })}
              </div>
            </section>
          ) : null}

          <section className="bc-chart-panel">
            <h3>Jump to series</h3>
            <div className="filters" style={{ flexWrap: "wrap" }}>
              {groups.map((g) => (
                <Link key={g.family} className="tab" to={`/series/${seriesSlug(g.family)}`}>
                  {g.family}
                </Link>
              ))}
            </div>
          </section>
        </>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
          {groups.map((g) => {
            const years = g.events
              .map((e) => Number(e.event_year))
              .filter((n) => !Number.isNaN(n));
            const span =
              years.length > 0
                ? `${Math.min(...years)}${years.length > 1 ? `–${Math.max(...years)}` : ""}`
                : "";
            return (
              <section key={g.family} className="series-event-block">
                <div className="series-event-block-head">
                  <div>
                    <h3 className="series-section-title">{g.family}</h3>
                    <p className="muted" style={{ margin: 0 }}>
                      {g.events.length} event{g.events.length === 1 ? "" : "s"}
                      {span ? ` · ${span}` : ""}
                    </p>
                  </div>
                  <Link className="btn ghost" to={`/series/${seriesSlug(g.family)}`}>
                    Open series →
                  </Link>
                </div>
                <div className="event-poster-grid">
                  {g.events.map((e) => (
                    <EventCard key={e.event_id} event={e} />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}

      {!rawItems.length && (
        <div className="bc-empty">
          <h4>No events</h4>
          <p>No events match the current filters.</p>
        </div>
      )}

      <PremiumSportsDataTable
        title="Event attendance board"
        variant="attendance"
        rows={flatSorted}
        rowKey={(e) => e.event_id}
        searchPlaceholder="Filter table…"
        searchFilter={(e, needle) =>
          [e.event_name, e.event_series, e.city, e.country, e.venue_name].join(" ").toLowerCase().includes(needle)
        }
        pageSize={30}
        columns={[
          {
            key: "event_date",
            header: "Date",
            sortValue: (e) => String(e.event_date || ""),
          },
          {
            key: "event_name",
            header: "Event",
            primary: true,
            render: (e) => {
              const t = resolveEventTheme(e.event_series, e.event_name);
              return (
                <div className="pst-cell-wrestler">
                  <EventArtwork
                    series={e.event_series}
                    eventName={e.event_name}
                    eventYear={e.event_year}
                    eventId={e.event_id}
                    size="sm"
                  />
                  <Link to={`/events/${e.event_id}`} style={{ color: t.accent }}>
                    {e.event_name}
                  </Link>
                </div>
              );
            },
          },
          { key: "event_year", header: "Year" },
          {
            key: "event_series",
            header: "Series",
            render: (e) => (
              <Link to={`/series/${seriesSlug(e.event_series || e.event_name || "other")}`} style={{ color: "inherit" }}>
                {e.event_series}
              </Link>
            ),
          },
          {
            key: "location",
            header: "Location",
            sortValue: (e) => [e.city, e.country].filter(Boolean).join(", "),
            render: (e) => [e.city, e.country].filter(Boolean).join(", ") || "—",
          },
          {
            key: "matches",
            header: "Matches",
            sortValue: (e) => Number(e.matches) || 0,
            render: (e) => e.matches ?? "—",
          },
          {
            key: "attendance",
            header: "Attendance",
            sortValue: (e) => {
              const n = Number(e.attendance);
              return Number.isFinite(n) && n > 0 ? n : -1;
            },
            render: (e) => {
              const n = Number(e.attendance);
              return Number.isFinite(n) && n > 0 ? n.toLocaleString() : "—";
            },
          },
        ]}
      />
    </div>
  );
}
