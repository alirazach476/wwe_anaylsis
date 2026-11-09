import { Link } from "react-router-dom";
import { resolveEventTheme } from "../../theme/eventThemes";
import { isUpcomingEvent } from "../../utils/wrestlerNames";
import { EventArtwork } from "../EventArtwork";

export function EventPosterCard({ event }: { event: any }) {
  const theme = resolveEventTheme(event.event_series, event.event_name);
  const upcoming = isUpcomingEvent(event);
  return (
    <Link
      to={`/events/${event.event_id}`}
      className={`event-poster${upcoming ? " is-upcoming" : ""}`}
      style={{ ["--card-accent" as string]: theme.primary }}
    >
      <div className="event-poster-accent" />
      <div className="event-poster-art">
        <EventArtwork
          series={event.event_series}
          eventName={event.event_name}
          eventYear={event.event_year}
          eventId={event.event_id}
          size="md"
        />
      </div>
      <div className="event-poster-wash" />
      <div className="event-poster-meta">
        <div className="event-poster-year">{event.event_year}</div>
        <h4>{event.event_name}</h4>
        {upcoming ? <div className="coming-soon-badge">Coming Soon</div> : null}
        <div className="event-poster-foot">
          {event.event_date ? <span>{event.event_date}</span> : null}
          {event.venue_name ? <span>{event.venue_name}</span> : null}
          <span>{[event.city, event.country].filter(Boolean).join(", ") || "Location TBA"}</span>
          <span>
            {upcoming
              ? "Coming Soon"
              : event.matches != null
                ? `${event.matches} matches`
                : "Matches n/a"}
          </span>
        </div>
      </div>
    </Link>
  );
}
