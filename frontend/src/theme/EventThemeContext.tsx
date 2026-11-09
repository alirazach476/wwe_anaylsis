import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { applyThemeToDocument, DEFAULT_THEME, resolveEventTheme, type EventTheme } from "./eventThemes";
import { extractLogoPalette } from "./logoPalette";

type Ctx = {
  theme: EventTheme;
  setEventIdentity: (series?: string | null, eventName?: string | null) => void;
  applyLogoTheme: (logoSrc: string | null | undefined, base?: EventTheme) => void;
  resetTheme: () => void;
};

const EventThemeContext = createContext<Ctx | null>(null);

function sameTheme(a: EventTheme, b: EventTheme) {
  return (
    a.themeName === b.themeName &&
    a.primary === b.primary &&
    a.secondary === b.secondary &&
    a.accent === b.accent &&
    a.background === b.background
  );
}

export function EventThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<EventTheme>(DEFAULT_THEME);
  const themeRef = useRef(theme);
  themeRef.current = theme;
  const logoReq = useRef(0);

  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  const setEventIdentity = useCallback((series?: string | null, eventName?: string | null) => {
    const next = resolveEventTheme(series, eventName);
    if (!sameTheme(themeRef.current, next)) setTheme(next);
  }, []);

  const applyLogoTheme = useCallback((logoSrc: string | null | undefined, base?: EventTheme) => {
    if (!logoSrc) return;
    const req = ++logoReq.current;
    const foundation = base || themeRef.current;
    extractLogoPalette(logoSrc).then((palette) => {
      if (req !== logoReq.current || !palette) return;
      const next: EventTheme = {
        ...foundation,
        primary: palette.primary,
        secondary: palette.secondary,
        accent: palette.accent,
        glow: palette.glow,
        background: palette.background,
        panel: palette.panel,
        themeName: `${foundation.themeName} · logo`,
      };
      if (!sameTheme(themeRef.current, next)) setTheme(next);
    });
  }, []);

  const resetTheme = useCallback(() => {
    logoReq.current += 1;
    if (!sameTheme(themeRef.current, DEFAULT_THEME)) setTheme(DEFAULT_THEME);
  }, []);

  const value = useMemo<Ctx>(
    () => ({ theme, setEventIdentity, applyLogoTheme, resetTheme }),
    [theme, setEventIdentity, applyLogoTheme, resetTheme]
  );

  return <EventThemeContext.Provider value={value}>{children}</EventThemeContext.Provider>;
}

export function useEventTheme() {
  const ctx = useContext(EventThemeContext);
  if (!ctx) throw new Error("EventThemeProvider missing");
  return ctx;
}
