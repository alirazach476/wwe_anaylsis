import type { Layout } from "plotly.js";
import type { EventTheme } from "./eventThemes";

export function plotlyLayout(theme: EventTheme, extra: Partial<Layout> = {}): Partial<Layout> {
  return {
    paper_bgcolor: "transparent",
    plot_bgcolor: "rgba(0,0,0,0.15)",
    font: { color: "#c5c6c8", family: "Bebas Neue, Manrope, Segoe UI, sans-serif", size: 12 },
    margin: { t: 28, r: 24, l: 48, b: 52 },
    colorway: [theme.primary, theme.accent, "#71717a", "#f4f4f5", "#7f1d1d", "#d4af37"],
    legend: {
      orientation: "h",
      bgcolor: "transparent",
      font: { family: "Manrope, Segoe UI, sans-serif", size: 11, color: "#a1a1aa" },
      y: 1.12,
    },
    hoverlabel: {
      bgcolor: "#0e0e12",
      bordercolor: theme.primary,
      font: { family: "Manrope, Segoe UI, sans-serif", size: 12, color: "#f4f4f5" },
    },
    xaxis: {
      gridcolor: "rgba(255,255,255,0.06)",
      zerolinecolor: "rgba(255,255,255,0.1)",
      tickfont: { family: "Manrope, Segoe UI, sans-serif", size: 11 },
    },
    yaxis: {
      gridcolor: "rgba(255,255,255,0.06)",
      zerolinecolor: "rgba(255,255,255,0.1)",
      tickfont: { family: "Manrope, Segoe UI, sans-serif", size: 11 },
    },
    transition: { duration: 280, easing: "cubic-in-out" },
    ...extra,
  };
}

export function accentColor(theme: EventTheme) {
  return theme.primary;
}
