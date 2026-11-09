import { useEffect, useState } from "react";
import { seriesLogoUrl } from "../assets/assetManifest";
import { loadEventLogoManifest, logoPathFromManifest, type EventLogoManifest } from "../assets/eventLogoLookup";
import { resolveEventTheme } from "../theme/eventThemes";
import { useEventTheme } from "../theme/EventThemeContext";

export function EventArtwork({
  series,
  eventName,
  eventYear,
  eventId,
  size = "md",
  driveTheme = false,
}: {
  series?: string | null;
  eventName?: string | null;
  eventYear?: number | string | null;
  eventId?: string | null;
  size?: "sm" | "md" | "lg";
  /** When true, sample logo colors and paint the page theme to match. */
  driveTheme?: boolean;
}) {
  const theme = resolveEventTheme(series, eventName);
  const { applyLogoTheme } = useEventTheme();
  const [manifest, setManifest] = useState<EventLogoManifest | null>(null);
  const [ready, setReady] = useState(false);
  const yearSpecific = logoPathFromManifest(manifest, { eventId, eventName, eventYear, series });
  const fallback = seriesLogoUrl(series, eventName);
  const src = yearSpecific || (ready ? fallback : null);
  const [failed, setFailed] = useState(false);
  const maxH = size === "lg" ? 260 : size === "sm" ? 72 : 190;

  useEffect(() => {
    loadEventLogoManifest()
      .then((m) => {
        setManifest(m);
      })
      .finally(() => setReady(true));
  }, [eventId, eventName, eventYear, series]);

  useEffect(() => {
    setFailed(false);
  }, [src]);

  useEffect(() => {
    if (!driveTheme || !src || failed) return;
    applyLogoTheme(src, theme);
  }, [driveTheme, src, failed, applyLogoTheme, theme]);

  if (!src || failed) {
    return (
      <div className="event-wordmark" style={{ fontSize: size === "lg" ? undefined : "1.6rem", color: theme.accent }}>
        {theme.wordmark}
      </div>
    );
  }

  return (
    <img
      className="event-logo-img"
      src={src}
      alt={`${eventName || series || theme.themeName} logo`}
      style={{ maxHeight: maxH, objectFit: "contain" }}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
