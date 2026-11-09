import { Link } from "react-router-dom";
import { seriesSlug } from "../../assets/eventPriority";
import { resolveEventTheme } from "../../theme/eventThemes";
import { EventArtwork } from "../EventArtwork";

export function SeriesFamilyCard({
  family,
  count,
  latest,
  yearFrom,
  yearTo,
}: {
  family: string;
  count: number;
  latest?: any;
  yearFrom?: number | null;
  yearTo?: number | null;
}) {
  const theme = resolveEventTheme(family, latest?.event_name || family);
  const href = family === "Other Events" ? "/events?view=all" : `/series/${seriesSlug(family)}`;
  const span =
    yearFrom && yearTo ? `${yearFrom}–${yearTo}` : yearFrom ? String(yearFrom) : "Archive";

  return (
    <Link
      to={href}
      className="event-poster series-family-card"
      style={{ ["--card-accent" as string]: theme.primary, minHeight: 300 }}
    >
      <div className="event-poster-accent" />
      <div className="event-poster-art">
        <EventArtwork
          series={family}
          eventName={latest?.event_name || family}
          eventYear={latest?.event_year}
          eventId={latest?.event_id}
          size="md"
        />
      </div>
      <div className="event-poster-wash" />
      <div className="event-poster-meta">
        <div className="event-poster-year">{span}</div>
        <h4>{family}</h4>
        <div className="event-poster-foot">
          <span>{count} events</span>
          {latest?.event_name ? <span>Latest: {latest.event_name}</span> : null}
          <span>Open series →</span>
        </div>
      </div>
    </Link>
  );
}
