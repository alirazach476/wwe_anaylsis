import { Link } from "react-router-dom";
import { seriesSlug } from "../../assets/eventPriority";
import { useEventTheme } from "../../theme/EventThemeContext";
import { isUpcomingEvent } from "../../utils/wrestlerNames";
import { EventArtwork } from "../EventArtwork";

export function EventHero({
  event,
  matchCount,
  backTo = "/events",
  backLabel = "← All series",
}: {
  event: any;
  matchCount?: number;
  backTo?: string;
  backLabel?: string;
}) {
  const { theme } = useEventTheme();
  const matches = matchCount ?? event.matches ?? event.match_count;
  const family = event.event_series || theme.themeName;
  const seriesPath = `/series/${seriesSlug(family)}`;
  const upcoming = isUpcomingEvent({ ...event, matches: Number(matches) || 0 });
  const multi = Boolean(event.is_multi_night && (event.nights?.length || 0) >= 2);
  const nightNumber = Number(event.night_number) || null;
  const nightDates = (event.nights || [])
    .map((n: any) => n.event_date)
    .filter(Boolean)
    .join(" · ");

  return (
    <section className="event-hero">
      <div>
        <div className="event-hero-badge">{theme.themeName} · Event microsite</div>
        <h1>
          {event.event_name}
          {multi && nightNumber ? <span className="event-hero-night"> · Night {nightNumber}</span> : null}
        </h1>
        {multi ? <div className="coming-soon-badge hero multi-night">Night 1 · Night 2</div> : null}
        {upcoming ? <div className="coming-soon-badge hero">Coming Soon</div> : null}
        <div className="event-hero-strip">
          <span>
            <strong>Year</strong>
            {event.event_year ?? "—"}
          </span>
          <span>
            <strong>Date</strong>
            {multi && nightDates ? nightDates : event.event_date || "TBA"}
          </span>
          <span>
            <strong>Venue</strong>
            {event.venue_name || "TBA"}
          </span>
          <span>
            <strong>Location</strong>
            {[event.city, event.country].filter(Boolean).join(", ") || "TBA"}
          </span>
          <span>
            <strong>Attendance</strong>
            {Number(event.attendance) > 0 ? Number(event.attendance).toLocaleString() : "Unavailable"}
          </span>
          <span>
            <strong>Card</strong>
            {upcoming ? "Coming Soon" : matches != null ? `${matches} matches` : "—"}
          </span>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <Link className="btn ghost" to={backTo}>
            {backLabel}
          </Link>
          <Link className="btn" to={seriesPath}>
            All {family} →
          </Link>
        </div>
      </div>
      <div className="event-hero-art">
        <div className="event-hero-watermark">{theme.wordmark}</div>
        <EventArtwork
          series={event.event_series}
          eventName={event.event_name}
          eventYear={event.event_year}
          eventId={event.event_id}
          size="lg"
          driveTheme
        />
      </div>
    </section>
  );
}
