import { Link } from "react-router-dom";
import { resolveEventTheme } from "../../theme/eventThemes";
import { isUpcomingEvent } from "../../utils/wrestlerNames";
import { EventArtwork } from "../EventArtwork";

export function EventPosterCard({ event }: { event: any }) {
  const theme = resolveEventTheme(event.event_series, event.event_name);
  const upcoming = isUpcomingEvent(event);
  const multi = Boolean(event.is_multi_night && (event.nights?.length || 0) >= 2);
  const dateLabel = multi
    ? [event.event_date, event.event_end_date || event.nights?.[1]?.event_date].filter(Boolean).join(" · ")
    : event.event_date;
  return (
    <Link
      to={`/events/${event.event_id}`}
      className={`event-poster${upcoming ? " is-upcoming" : ""}${multi ? " is-multi-night" : ""}`}
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
        {multi ? <div className="coming-soon-badge multi-night">Night 1 · Night 2</div> : null}
        {upcoming ? <div className="coming-soon-badge">Coming Soon</div> : null}
        <div className="event-poster-foot">
          {dateLabel ? <span>{dateLabel}</span> : null}
          {event.venue_name ? <span>{event.venue_name}</span> : null}
          <span>{[event.city, event.country].filter(Boolean).join(", ") || "Location TBA"}</span>
          <span>
            {upcoming
              ? "Coming Soon"
              : event.matches != null
                ? `${event.matches} matches${multi ? " (2 nights)" : ""}`
                : "Matches n/a"}
          </span>
        </div>
      </div>
    </Link>
  );
}
