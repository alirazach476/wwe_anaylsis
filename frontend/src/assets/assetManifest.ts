/** Centralized branding + event artwork. Logos come from Wikipedia-sourced local files. */

import { EVENT_LOGO_BY_SERIES, EVENT_LOGOS } from "./eventLogoManifest.generated";

export const BRAND = {
  siteName: "WWE Legacy Analytics",
  tagline: "Premium Live Event Intelligence",
  logoSvg: "/branding/wwe-logo.svg",
  logoPng: "/branding/wwe-logo.png",
  logoMark: "/branding/wwe-logo-mark.svg",
  favicon: "/branding/wwe-logo-mark.svg",
};

export { EVENT_LOGOS, EVENT_LOGO_BY_SERIES };

export function seriesSlug(series?: string | null, eventName?: string | null): string {
  const hay = `${series || ""} ${eventName || ""}`.toLowerCase();
  if (hay.includes("wrestlemania")) return "wrestlemania";
  if (hay.includes("greatest royal rumble")) return "greatest-royal-rumble";
  if (hay.includes("royal rumble")) return "royal-rumble";
  if (hay.includes("summerslam")) return "summerslam";
  if (hay.includes("survivor series") && hay.includes("wargames")) return "survivor-series-wargames";
  if (hay.includes("survivor series")) return "survivor-series";
  if (hay.includes("money in the bank")) return "money-in-the-bank";
  if (hay.includes("hell in a cell")) return "hell-in-a-cell";
  if (hay.includes("elimination chamber")) return "elimination-chamber";
  if (hay.includes("extreme rules")) return "extreme-rules";
  if (hay.includes("crown jewel")) return "crown-jewel";
  if (hay.includes("backlash")) return "backlash";
  if (hay.includes("clash at the castle")) return "clash-at-the-castle";
  if (hay.includes("clash in paris")) return "clash-in-paris";
  if (hay.includes("clash in italy")) return "clash-in-italy";
  if (hay.includes("clash of champions")) return "clash-of-champions";
  if (hay.includes("saturday night")) return "saturday-night-s-main-event";
  if (hay.includes("sunday night")) return "sunday-night-s-main-event";
  if (hay.includes("great american bash") || hay.includes("the bash")) return "the-great-american-bash";
  if (hay.includes("wwe vs") && hay.includes("ecw")) return "wwe-vs-ecw-head-to-head";
  const raw = (series || eventName || "").toLowerCase().trim();
  return raw.replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "wwe";
}

export function seriesLogoUrl(series?: string | null, eventName?: string | null): string | null {
  if (series && EVENT_LOGO_BY_SERIES[series]) return EVENT_LOGO_BY_SERIES[series];
  const slug = seriesSlug(series, eventName);
  return EVENT_LOGOS[slug]?.path || null;
}

export function initials(name?: string | null): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
