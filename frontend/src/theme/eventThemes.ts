export type EventTheme = {
  themeName: string;
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  panel: string;
  glow: string;
  wordmark: string;
};

/** Matches official WWE web logo: black plate, white mark, red underline. */
const DEFAULT: EventTheme = {
  themeName: "WWE Legacy",
  primary: "#ff0000",
  secondary: "#000000",
  accent: "#ffffff",
  background: "radial-gradient(ellipse at 28% 0%, #3a0008 0%, #000000 52%), linear-gradient(165deg, #120003, #000000)",
  panel: "rgba(12,12,12,0.96)",
  glow: "rgba(255,0,0,0.42)",
  wordmark: "WWE",
};

const SERIES_THEMES: Record<string, EventTheme> = {
  wrestlemania: {
    themeName: "WrestleMania",
    primary: "#d4af37",
    secondary: "#0b0b0c",
    accent: "#f5e6b8",
    background: "radial-gradient(ellipse at 30% 0%, #3a2a08 0%, #0b0b0c 50%), linear-gradient(135deg,#1a1408,#050505)",
    panel: "rgba(22,18,10,0.94)",
    glow: "rgba(212,175,55,0.4)",
    wordmark: "WRESTLEMANIA",
  },
  "wrestlemania backlash": {
    themeName: "WrestleMania Backlash",
    primary: "#e11d2e",
    secondary: "#050506",
    accent: "#f5f5f5",
    background:
      "radial-gradient(ellipse at 50% 0%, #5a0a12 0%, #0a0506 48%), linear-gradient(160deg, #1a0508, #000)",
    panel: "rgba(18,8,10,0.95)",
    glow: "rgba(225,29,46,0.45)",
    wordmark: "BACKLASH",
  },
  "royal rumble": {
    themeName: "Royal Rumble",
    primary: "#ef4444",
    secondary: "#09090b",
    accent: "#fecaca",
    background: "radial-gradient(ellipse at top, #4a1018 0%, #09090b 55%)",
    panel: "rgba(24,10,12,0.94)",
    glow: "rgba(239,68,68,0.4)",
    wordmark: "ROYAL RUMBLE",
  },
  summerslam: {
    themeName: "SummerSlam",
    primary: "#38bdf8",
    secondary: "#071018",
    accent: "#fbbf24",
    background: "radial-gradient(ellipse at top right, #0c4a6e 0%, #071018 50%), linear-gradient(160deg,#0ea5e920,#000)",
    panel: "rgba(8,18,28,0.94)",
    glow: "rgba(56,189,248,0.35)",
    wordmark: "SUMMERSLAM",
  },
  "survivor series": {
    themeName: "Survivor Series",
    primary: "#dc2626",
    secondary: "#050505",
    accent: "#e5e5e5",
    background: "radial-gradient(ellipse at bottom, #3f0a0a 0%, #050505 60%)",
    panel: "rgba(16,8,8,0.95)",
    glow: "rgba(220,38,38,0.45)",
    wordmark: "SURVIVOR SERIES",
  },
  "money in the bank": {
    themeName: "Money in the Bank",
    primary: "#f59e0b",
    secondary: "#0c0a06",
    accent: "#fde68a",
    background: "radial-gradient(ellipse at top, #422006 0%, #0c0a06 55%)",
    panel: "rgba(20,16,8,0.94)",
    glow: "rgba(245,158,11,0.4)",
    wordmark: "MONEY IN THE BANK",
  },
  "hell in a cell": {
    themeName: "Hell in a Cell",
    primary: "#b91c1c",
    secondary: "#050505",
    accent: "#a3a3a3",
    background: "repeating-linear-gradient(90deg, #111 0 2px, #0a0a0a 2px 18px), radial-gradient(ellipse at center, #2a0505, #000)",
    panel: "rgba(12,12,12,0.95)",
    glow: "rgba(185,28,28,0.35)",
    wordmark: "HELL IN A CELL",
  },
  "elimination chamber": {
    themeName: "Elimination Chamber",
    primary: "#94a3b8",
    secondary: "#0b0f14",
    accent: "#e2e8f0",
    background: "radial-gradient(circle at 50% 20%, #334155 0%, #0b0f14 55%)",
    panel: "rgba(15,20,28,0.95)",
    glow: "rgba(148,163,184,0.35)",
    wordmark: "ELIMINATION CHAMBER",
  },
  "extreme rules": {
    themeName: "Extreme Rules",
    primary: "#ef4444",
    secondary: "#0a0505",
    accent: "#fca5a5",
    background: "radial-gradient(ellipse at top left, #5b1010 0%, #0a0505 55%)",
    panel: "rgba(20,8,8,0.95)",
    glow: "rgba(239,68,68,0.4)",
    wordmark: "EXTREME RULES",
  },
  "crown jewel": {
    themeName: "Crown Jewel",
    primary: "#fbbf24",
    secondary: "#120d04",
    accent: "#fff7d6",
    background: "radial-gradient(ellipse at top, #5b4308 0%, #120d04 55%)",
    panel: "rgba(24,18,8,0.95)",
    glow: "rgba(251,191,36,0.4)",
    wordmark: "CROWN JEWEL",
  },
  backlash: {
    themeName: "Backlash",
    primary: "#f97316",
    secondary: "#0c0805",
    accent: "#fdba74",
    background: "radial-gradient(ellipse at top, #7c2d12 0%, #0c0805 55%)",
    panel: "rgba(22,12,8,0.94)",
    glow: "rgba(249,115,22,0.35)",
    wordmark: "BACKLASH",
  },
  clash: {
    themeName: "Clash",
    primary: "#a855f7",
    secondary: "#0b0612",
    accent: "#e9d5ff",
    background: "radial-gradient(ellipse at top, #4c1d95 0%, #0b0612 55%)",
    panel: "rgba(18,10,28,0.94)",
    glow: "rgba(168,85,247,0.35)",
    wordmark: "CLASH",
  },
  "saturday night": {
    themeName: "SNME",
    primary: "#60a5fa",
    secondary: "#060a12",
    accent: "#dbeafe",
    background: "radial-gradient(ellipse at top, #1e3a8a 0%, #060a12 55%)",
    panel: "rgba(10,14,24,0.94)",
    glow: "rgba(96,165,250,0.35)",
    wordmark: "SNME",
  },
  "night of champions": {
    themeName: "Night of Champions",
    primary: "#facc15",
    secondary: "#0c0a04",
    accent: "#fef9c3",
    background: "radial-gradient(ellipse at top, #713f12 0%, #0c0a04 55%)",
    panel: "rgba(22,18,8,0.95)",
    glow: "rgba(250,204,21,0.4)",
    wordmark: "NIGHT OF CHAMPIONS",
  },
  wrestlepalooza: {
    themeName: "Wrestlepalooza",
    primary: "#f43f5e",
    secondary: "#0c0608",
    accent: "#fda4af",
    background: "radial-gradient(ellipse at top, #881337 0%, #0c0608 55%)",
    panel: "rgba(22,10,14,0.95)",
    glow: "rgba(244,63,94,0.4)",
    wordmark: "WRESTLEPALOOZA",
  },
  "fastlane": {
    themeName: "Fastlane",
    primary: "#22d3ee",
    secondary: "#041016",
    accent: "#a5f3fc",
    background: "radial-gradient(ellipse at top, #155e75 0%, #041016 55%)",
    panel: "rgba(8,18,24,0.95)",
    glow: "rgba(34,211,238,0.35)",
    wordmark: "FASTLANE",
  },
  "no mercy": {
    themeName: "No Mercy",
    primary: "#dc2626",
    secondary: "#0a0404",
    accent: "#fecaca",
    background: "radial-gradient(ellipse at top, #450a0a 0%, #0a0404 55%)",
    panel: "rgba(18,8,8,0.95)",
    glow: "rgba(220,38,38,0.4)",
    wordmark: "NO MERCY",
  },
  raw: {
    themeName: "Raw",
    primary: "#ef4444",
    secondary: "#0a0505",
    accent: "#fca5a5",
    background: "radial-gradient(ellipse at top, #7f1d1d 0%, #0a0505 55%)",
    panel: "rgba(20,8,8,0.94)",
    glow: "rgba(239,68,68,0.4)",
    wordmark: "RAW",
  },
  smackdown: {
    themeName: "SmackDown",
    primary: "#3b82f6",
    secondary: "#060a14",
    accent: "#93c5fd",
    background: "radial-gradient(ellipse at top, #1e3a8a 0%, #060a14 55%)",
    panel: "rgba(10,14,28,0.94)",
    glow: "rgba(59,130,246,0.4)",
    wordmark: "SMACKDOWN",
  },
};

/** Longer / more specific keys first so "wrestlemania backlash" beats "wrestlemania". */
const THEME_KEYS = Object.keys(SERIES_THEMES).sort((a, b) => b.length - a.length);

export function resolveEventTheme(series?: string | null, eventName?: string | null): EventTheme {
  const hay = `${series || ""} ${eventName || ""}`.toLowerCase();
  for (const key of THEME_KEYS) {
    if (hay.includes(key)) return SERIES_THEMES[key];
  }
  return DEFAULT;
}

export function applyThemeToDocument(theme: EventTheme) {
  const root = document.documentElement;
  root.style.setProperty("--event-primary", theme.primary);
  root.style.setProperty("--event-secondary", theme.secondary);
  root.style.setProperty("--event-accent", theme.accent);
  root.style.setProperty("--event-panel", theme.panel);
  root.style.setProperty("--event-glow", theme.glow);
  root.style.setProperty("--event-bg", theme.background);
  root.style.setProperty("--brand-red", theme.primary);
  root.style.setProperty("--bg-base", theme.secondary);
  root.style.setProperty("--bg-elevated", `color-mix(in srgb, ${theme.secondary} 70%, #1a1a1e)`);
  root.style.setProperty("--bg-panel", theme.panel);
  root.dataset.eventTheme = theme.themeName;
  document.body.style.background = theme.background;
}

export { DEFAULT as DEFAULT_THEME };
