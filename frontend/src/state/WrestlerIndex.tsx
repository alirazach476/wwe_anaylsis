import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../api";
import { cleanWrestlerName, wrestlerNameKey } from "../utils/wrestlerNames";

type Entry = { wrestler_id: string; canonical_name: string; matches: number };

type Ctx = {
  ready: boolean;
  resolveId: (name?: string | null, preferredId?: string | null) => string | null;
  resolveName: (name?: string | null) => string;
};

const WrestlerIndexContext = createContext<Ctx>({
  ready: false,
  resolveId: () => null,
  resolveName: (n) => cleanWrestlerName(n) || String(n || ""),
});

export function WrestlerIndexProvider({ children }: { children: ReactNode }) {
  const [byKey, setByKey] = useState<Map<string, Entry>>(new Map());
  const [byId, setById] = useState<Map<string, Entry>>(new Map());
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .wrestlers({ limit: 5000 })
      .then((r) => {
        if (cancelled) return;
        const keyMap = new Map<string, Entry>();
        const idMap = new Map<string, Entry>();
        for (const w of r.items || []) {
          const id = String(w.wrestler_id || "");
          const name = cleanWrestlerName(w.canonical_name) || String(w.canonical_name || "");
          if (!id || !name) continue;
          const entry: Entry = {
            wrestler_id: id,
            canonical_name: name,
            matches: Number(w.matches) || 0,
          };
          idMap.set(id, entry);
          const key = wrestlerNameKey(name);
          if (!key) continue;
          const prev = keyMap.get(key);
          if (!prev || entry.matches > prev.matches) keyMap.set(key, entry);
        }
        setByKey(keyMap);
        setById(idMap);
        setReady(true);
      })
      .catch(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<Ctx>(
    () => ({
      ready,
      resolveName: (name) => {
        const cleaned = cleanWrestlerName(name);
        if (!cleaned) return String(name || "");
        const hit = byKey.get(wrestlerNameKey(cleaned));
        return hit?.canonical_name || cleaned;
      },
      resolveId: (name, preferredId) => {
        if (preferredId) {
          const pref = String(preferredId);
          // Prefer preferred id only if it looks like a real roster id (not and- junk)
          if (byId.has(pref) && !/wrs_and-/i.test(pref)) return pref;
          const fromPref = byId.get(pref);
          if (fromPref) {
            const remapped = byKey.get(wrestlerNameKey(fromPref.canonical_name));
            if (remapped) return remapped.wrestler_id;
          }
        }
        const cleaned = cleanWrestlerName(name);
        if (!cleaned) return null;
        return byKey.get(wrestlerNameKey(cleaned))?.wrestler_id || null;
      },
    }),
    [ready, byKey, byId]
  );

  return <WrestlerIndexContext.Provider value={value}>{children}</WrestlerIndexContext.Provider>;
}

export function useWrestlerIndex() {
  return useContext(WrestlerIndexContext);
}
