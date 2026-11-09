"""Phase 2 data completeness report."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from wwe_data.config import get_settings
from wwe_data.models.match_schemas import EventMatchBundle
from wwe_data.models.schemas import RawEventRecord
from wwe_data.pipeline.championships import build_championship_tables
from wwe_data.pipeline.wrestlers import build_wrestler_tables

console = Console()


def write_completeness_report(
    events: list[RawEventRecord],
    bundles: list[EventMatchBundle],
    output_dir: Path | None = None,
) -> Path:
    settings = get_settings()
    out = output_dir or settings.reports_dir
    out.mkdir(parents=True, exist_ok=True)

    by_id = {b.event_id: b for b in bundles}
    matches = [m for b in bundles for m in b.matches]
    participants = [p for b in bundles for p in b.participants]
    wrestlers, _ = build_wrestler_tables(participants)
    championships, match_champs = build_championship_tables(matches)
    title_changes = sum(1 for c in match_champs if c.title_change)

    missing_cards = []
    missing_results = []
    for e in events:
        b = by_id.get(e.event_id)
        if e.event_status.value == "announced":
            continue
        if not b or b.collection_status in {"page_not_found", "empty", "error"} or not b.matches:
            missing_cards.append(f"{e.event_date} | {e.event_name} | {b.collection_status if b else 'not_collected'}")
            continue
        # Matches present but any without result text
        if any(not m.match_result for m in b.matches):
            missing_results.append(f"{e.event_date} | {e.event_name}")

    status_counts = Counter(b.collection_status for b in bundles)
    matches_by_year: dict[int, int] = defaultdict(int)
    events_with_matches_by_year: dict[int, int] = defaultdict(int)
    events_by_year: dict[int, int] = Counter(e.event_year for e in events)
    for e in events:
        b = by_id.get(e.event_id)
        if b and b.matches:
            events_with_matches_by_year[e.event_year] += 1
            matches_by_year[e.event_year] += len(b.matches)

    coverage_by_year = {
        str(y): round(100.0 * events_with_matches_by_year.get(y, 0) / c, 1)
        if c
        else 0.0
        for y, c in sorted(events_by_year.items())
    }

    series_stats: dict[str, dict[str, int | float]] = {}
    for e in events:
        series = e.event_series or "Unclassified"
        slot = series_stats.setdefault(series, {"events": 0, "with_matches": 0})
        slot["events"] = int(slot["events"]) + 1
        b = by_id.get(e.event_id)
        if b and b.matches:
            slot["with_matches"] = int(slot["with_matches"]) + 1
    for series, slot in series_stats.items():
        ev = int(slot["events"])
        wm = int(slot["with_matches"])
        slot["coverage_pct"] = round(100.0 * wm / ev, 1) if ev else 0.0

    needs_review = sum(
        1
        for b in bundles
        if b.collection_status in {"page_not_found", "empty", "error"}
    )

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_eligible_events": len(events),
        "total_events_collected": len(events),
        "total_matches_collected": len(matches),
        "total_unique_wrestlers": len(wrestlers),
        "total_championship_matches": sum(1 for m in matches if m.is_title_match),
        "total_title_changes": title_changes,
        "events_missing_match_cards": len(missing_cards),
        "events_missing_results": len(missing_results),
        "records_requiring_manual_verification": needs_review,
        "collection_status_counts": dict(status_counts),
        "coverage_by_year": coverage_by_year,
        "coverage_by_series": series_stats,
        "events_missing_match_cards_list": missing_cards,
        "royal_rumble_entrant_rows": sum(len(b.rumble_entrants) for b in bundles),
        "notes": [
            "Primary match source: Wikipedia MediaWiki API",
            "Cash-in / chamber entry-order details left null when not on event page",
            "No fabricated match results",
        ],
    }

    json_path = out / "completeness_report.json"
    md_path = out / "completeness_report.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    lines = [
        "# WWE Dataset Completeness Report (Phase 2)",
        "",
        f"_Generated: {report['generated_at']}_",
        "",
        "## Summary",
        "",
        f"- **Total eligible events:** {report['total_eligible_events']}",
        f"- **Total events collected:** {report['total_events_collected']}",
        f"- **Total matches collected:** {report['total_matches_collected']}",
        f"- **Total unique wrestlers:** {report['total_unique_wrestlers']}",
        f"- **Championship matches:** {report['total_championship_matches']}",
        f"- **Title changes (inferred):** {report['total_title_changes']}",
        f"- **Events missing match cards:** {report['events_missing_match_cards']}",
        f"- **Events missing results:** {report['events_missing_results']}",
        f"- **Records requiring manual verification:** {report['records_requiring_manual_verification']}",
        f"- **Royal Rumble entrant rows:** {report['royal_rumble_entrant_rows']}",
        "",
        "## Collection status",
        "",
    ]
    for k, v in sorted(status_counts.items()):
        lines.append(f"- `{k}`: {v}")

    lines += ["", "## Coverage by year", "", "| Year | Event match coverage % | Matches |", "| --- | ---: | ---: |"]
    for y, pct in coverage_by_year.items():
        lines.append(f"| {y} | {pct} | {matches_by_year.get(int(y), 0)} |")

    lines += ["", "## Events missing match cards", ""]
    if missing_cards:
        for row in missing_cards:
            lines.append(f"- {row}")
    else:
        lines.append("- None")

    lines += ["", "## Notes", ""]
    for n in report["notes"]:
        lines.append(f"- {n}")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    table = Table(title="Completeness Summary")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for label, key in [
        ("Events", "total_eligible_events"),
        ("Matches", "total_matches_collected"),
        ("Wrestlers", "total_unique_wrestlers"),
        ("Title matches", "total_championship_matches"),
        ("Title changes", "total_title_changes"),
        ("Missing match cards", "events_missing_match_cards"),
        ("Needs verification", "records_requiring_manual_verification"),
    ]:
        table.add_row(label, str(report[key]))
    console.print(table)
    return md_path
