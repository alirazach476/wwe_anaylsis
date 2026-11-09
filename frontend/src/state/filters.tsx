import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../api";

export type Filters = {
  yearFrom?: number;
  yearTo?: number;
  series?: string;
  country?: string;
  matchType?: string;
};

type Ctx = {
  filters: Filters;
  setFilters: React.Dispatch<React.SetStateAction<Filters>>;
  meta: { years: number[]; series: string[]; countries: string[]; match_types: string[] };
  query: Record<string, string | number | undefined>;
};

const FilterContext = createContext<Ctx | null>(null);

export function FilterProvider({ children }: { children: React.ReactNode }) {
  const [filters, setFilters] = useState<Filters>({});
  const [meta, setMeta] = useState({ years: [] as number[], series: [] as string[], countries: [] as string[], match_types: [] as string[] });

  useEffect(() => {
    api.meta().then(setMeta).catch(() => undefined);
  }, []);

  const query = useMemo(
    () => ({
      year_from: filters.yearFrom,
      year_to: filters.yearTo,
      series: filters.series,
      country: filters.country,
      match_type: filters.matchType,
    }),
    [filters]
  );

  return (
    <FilterContext.Provider value={{ filters, setFilters, meta, query }}>
      {children}
    </FilterContext.Provider>
  );
}

export function useFilters() {
  const ctx = useContext(FilterContext);
  if (!ctx) throw new Error("FilterProvider missing");
  return ctx;
}
