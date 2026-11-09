"""Coverage audit for the event inventory phase."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.table import Table

from wwe_data.config import get_settings, load_eligibility
from wwe_data.models.schemas import CollectionLogRecord, CoverageMetrics, RawEventRecord
from wwe_data.pipeline.series import SeriesRegistry

console = Console()


def compute_coverage(
    records: list[RawEventRecord],
    logs: list[CollectionLogRecord] | None = None,
) -> CoverageMetrics:
    settings = get_settings()
    registry = SeriesRegistry()
    eligibility = load_eligibility()
    must_consider = set(eligibility.get("include", {}).get("must_consider_series", []))

    by_year: dict[int, int] = Counter(r.event_year for r in records)
    years = list(range(settings.start_year, settings.end_year + 1))
    # Coverage % by year: collected / max(collected, 1) for years with data;
    # for future years with zero announced events, mark 0 with note (not fabricated).
    coverage_by_year: dict[str, float] = {}
    for y in years:
        count = by_year.get(y, 0)
        # Without an external expected denominator, report relative density later;
        # here: 100% if we have at least one eligible collected event for past/current
        # years that historically always had PPVs, else 0 for empty future years.
        if count > 0:
            coverage_by_year[str(y)] = 100.0
        else:
            coverage_by_year[str(y)] = 0.0

    by_series: dict[str, dict[str, int | float]] = {}
    series_counts = Counter(r.event_series or "Unclassified Eligible" for r in records)
    for series_name, count in sorted(series_counts.items()):
        by_series[series_name] = {
            "events": count,
            "years_represented": len(
                {r.event_year for r in records if (r.event_series or "") == series_name}
            ),
        }

    present_series = set(series_counts)
    # Alias / naming equivalents so coverage does not false-flag known series
    series_aliases = {
        "Day 1": {"Day 1", "New Year's Revolution"},
        "Great American Bash": {"Great American Bash", "The Great American Bash", "The Bash"},
        "The Bash": {"The Bash", "The Great American Bash", "Great American Bash"},
        "TLC": {"TLC", "TLC: Tables, Ladders & Chairs"},
        "One Night Stand": {"One Night Stand", "ECW One Night Stand"},
    }
    missing_from_registry = []
    for name in sorted(must_consider):
        aliases = series_aliases.get(name, {name})
        if present_series.isdisjoint(aliases):
            missing_from_registry.append(name)
    unclassified = sorted(
        r.event_name
        for r in records
        if (r.event_series or "") == "Unclassified Eligible"
    )
    needs_review = sum(
        1
        for r in records
        if r.verification_status.value in {"conflict", "needs_review", "unverified"}
    )

    notes = [
        "Phase 1 inventory only — match cards not yet collected.",
        "Unannounced future events are not fabricated; empty future years are expected.",
        "Secondary archives (SDH, OWoW, WrestlingOracle) pending after inventory review.",
        f"Collection logs: {len(logs or [])}",
    ]

    return CoverageMetrics(
        total_eligible_events=len(records),
        total_events_collected=len(records),
        total_matches_collected=0,
        total_unique_wrestlers=0,
        total_championship_matches=0,
        total_title_changes=0,
        events_missing_match_cards=len(records),  # all, until match phase
        events_missing_results=len(records),
        records_requiring_manual_verification=needs_review
        + len(
            [
                r
                for r in records
                if r.verification_status.value == "conflict"
            ]
        ),
        coverage_by_year=coverage_by_year,
        coverage_by_series=by_series,
        missing_series_from_registry=missing_from_registry,
        unclassified_events=unclassified,
        notes=notes,
    )


def write_coverage_report(
    records: list[RawEventRecord],
    logs: list[CollectionLogRecord] | None = None,
    output_dir: Path | None = None,
) -> Path:
    settings = get_settings()
    out = output_dir or settings.reports_dir
    out.mkdir(parents=True, exist_ok=True)

    metrics = compute_coverage(records, logs)
    report = metrics.model_dump(mode="json")

    # Extra audit tables
    year_counts = (
        pd.DataFrame([{"year": r.event_year, "event": r.event_name} for r in records])
        .groupby("year")
        .size()
        .rename("events")
        .reset_index()
        if records
        else pd.DataFrame(columns=["year", "events"])
    )

    series_df = (
        pd.DataFrame(
            [
                {
                    "series": k,
                    "events": v["events"],
                    "years_represented": v["years_represented"],
                }
                for k, v in metrics.coverage_by_series.items()
            ]
        )
        .sort_values("events", ascending=False)
        if metrics.coverage_by_series
        else pd.DataFrame()
    )

    json_path = out / "coverage_audit.json"
    md_path = out / "coverage_audit.md"
    year_csv = out / "coverage_by_year.csv"
    series_csv = out / "coverage_by_series.csv"

    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    year_counts.to_csv(year_csv, index=False)
    series_df.to_csv(series_csv, index=False)

    md = _render_markdown(metrics, year_counts, series_df)
    md_path.write_text(md, encoding="utf-8")

    _print_summary(metrics, year_counts)
    return md_path


def _render_markdown(
    metrics: CoverageMetrics,
    year_counts: pd.DataFrame,
    series_df: pd.DataFrame,
) -> str:
    lines = [
        "# WWE Event Inventory Coverage Audit",
        "",
        f"_Generated: {metrics.collection_timestamp.isoformat()}Z_",
        "",
        "## Summary",
        "",
        f"- **Total eligible events collected:** {metrics.total_events_collected}",
        f"- **Total matches collected:** {metrics.total_matches_collected} (deferred)",
        f"- **Unique wrestlers:** {metrics.total_unique_wrestlers} (deferred)",
        f"- **Championship matches:** {metrics.total_championship_matches} (deferred)",
        f"- **Title changes:** {metrics.total_title_changes} (deferred)",
        f"- **Events missing match cards:** {metrics.events_missing_match_cards}",
        f"- **Events missing results:** {metrics.events_missing_results}",
        f"- **Records requiring manual verification:** {metrics.records_requiring_manual_verification}",
        "",
        "## Notes",
        "",
    ]
    for note in metrics.notes:
        lines.append(f"- {note}")

    lines += ["", "## Events per year", "", "| Year | Events |", "| --- | ---: |"]
    if not year_counts.empty:
        for _, row in year_counts.iterrows():
            lines.append(f"| {int(row['year'])} | {int(row['events'])} |")

    lines += ["", "## Coverage by series", "", "| Series | Events | Years |", "| --- | ---: | ---: |"]
    if not series_df.empty:
        for _, row in series_df.iterrows():
            lines.append(
                f"| {row['series']} | {int(row['events'])} | {int(row['years_represented'])} |"
            )

    lines += ["", "## Must-consider series not yet observed", ""]
    if metrics.missing_series_from_registry:
        for name in metrics.missing_series_from_registry:
            lines.append(f"- {name}")
    else:
        lines.append("- None — all must-consider series appear at least once.")

    lines += ["", "## Unclassified eligible events", ""]
    if metrics.unclassified_events:
        for name in metrics.unclassified_events:
            lines.append(f"- {name}")
    else:
        lines.append("- None")

    lines += [
        "",
        "## Gate",
        "",
        "**Do not proceed to match scraping until this inventory is reviewed** "
        "and missing event-series gaps are addressed in `config/event_series_registry.yaml`.",
        "",
    ]
    return "\n".join(lines)


def _print_summary(metrics: CoverageMetrics, year_counts: pd.DataFrame) -> None:
    table = Table(title="Inventory Coverage Summary")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Eligible events collected", str(metrics.total_events_collected))
    table.add_row("Matches collected", str(metrics.total_matches_collected))
    table.add_row("Missing match cards", str(metrics.events_missing_match_cards))
    table.add_row(
        "Needs verification", str(metrics.records_requiring_manual_verification)
    )
    table.add_row(
        "Missing must-consider series",
        str(len(metrics.missing_series_from_registry)),
    )
    table.add_row("Unclassified events", str(len(metrics.unclassified_events)))
    console.print(table)

    if not year_counts.empty:
        yt = Table(title="Events by Year")
        yt.add_column("Year")
        yt.add_column("Events", justify="right")
        for _, row in year_counts.iterrows():
            yt.add_row(str(int(row["year"])), str(int(row["events"])))
        console.print(yt)


def main() -> None:
    settings = get_settings()
    inv = settings.processed_dir / "events_inventory.json"
    if not inv.exists():
        console.print("[red]No inventory found. Run: python -m wwe_data.pipeline.inventory[/red]")
        return
    records = [
        RawEventRecord.model_validate(row)
        for row in json.loads(inv.read_text(encoding="utf-8"))
    ]
    write_coverage_report(records)


if __name__ == "__main__":
    main()
