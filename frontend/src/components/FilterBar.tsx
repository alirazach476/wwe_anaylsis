import { useNavigate, useLocation } from "react-router-dom";
import { seriesSlug, TOP_EVENT_SERIES } from "../assets/eventPriority";
import { useFilters } from "../state/filters";
import { FilterSelect } from "./FilterSelect";

export function FilterBar() {
  const { filters, setFilters, meta } = useFilters();
  const navigate = useNavigate();
  const location = useLocation();

  function onSeriesChange(value: string) {
    const series = value || undefined;
    setFilters((f) => ({ ...f, series }));

    if (!series) {
      if (location.pathname.startsWith("/series/")) navigate("/events");
      return;
    }

    const top = TOP_EVENT_SERIES.find(
      (s) => s.toLowerCase() === series.toLowerCase() || series.toLowerCase().includes(s.toLowerCase())
    );
    if (top) {
      navigate(`/series/${seriesSlug(top)}`);
      return;
    }

    navigate(`/events?view=all&series=${encodeURIComponent(series)}`);
  }

  return (
    <div className="filters filter-bar">
      <FilterSelect
        ariaLabel="Year from"
        placeholder="Year from"
        value={filters.yearFrom != null ? String(filters.yearFrom) : ""}
        options={meta.years.map((y) => ({ value: String(y), label: String(y) }))}
        onChange={(v) => setFilters((f) => ({ ...f, yearFrom: v ? Number(v) : undefined }))}
      />
      <FilterSelect
        ariaLabel="Year to"
        placeholder="Year to"
        value={filters.yearTo != null ? String(filters.yearTo) : ""}
        options={meta.years.map((y) => ({ value: String(y), label: String(y) }))}
        onChange={(v) => setFilters((f) => ({ ...f, yearTo: v ? Number(v) : undefined }))}
      />
      <FilterSelect
        ariaLabel="Series"
        placeholder="All series"
        value={filters.series ?? ""}
        options={meta.series.map((s) => ({ value: s, label: s }))}
        onChange={onSeriesChange}
      />
      <FilterSelect
        ariaLabel="Country"
        placeholder="All countries"
        value={filters.country ?? ""}
        options={meta.countries.map((c) => ({ value: c, label: c }))}
        onChange={(v) => setFilters((f) => ({ ...f, country: v || undefined }))}
      />
      <FilterSelect
        ariaLabel="Match type"
        placeholder="All match types"
        value={filters.matchType ?? ""}
        options={meta.match_types.map((t) => ({ value: t, label: t }))}
        onChange={(v) => setFilters((f) => ({ ...f, matchType: v || undefined }))}
      />
      <button
        type="button"
        className="btn ghost"
        onClick={() => {
          setFilters({});
          if (location.pathname.startsWith("/series/")) navigate("/events");
        }}
      >
        Reset
      </button>
    </div>
  );
}
