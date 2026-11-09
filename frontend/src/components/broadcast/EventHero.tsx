import { Link } from "react-router-dom";
import { seriesSlug } from "../../assets/eventPriority";
import { useEventTheme } from "../../theme/EventThemeContext";
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

  return (
    <section className="event-hero">
      <div>
        <div className="event-hero-badge">{theme.themeName} · Event microsite</div>
        <h1>{event.event_name}</h1>
        <div className="event-hero-strip">
          <span>
            <strong>Year</strong>
            {event.event_year ?? "—"}
          </span>
          <span>
            <strong>Date</strong>
            {event.event_date || "TBA"}
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
            {matches != null ? `${matches} matches` : "—"}
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
