"""Fill missing match cards from WWE.com, then re-export datasets."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from wwe_data.collectors.wwe_com_matches import collect_missing_from_wwe
from wwe_data.config import get_settings
from wwe_data.models.match_schemas import EventMatchBundle
from wwe_data.pipeline.matches import (
    _load_partial_bundles,
    _write_partial_bundles,
    export_match_datasets,
    load_inventory,
)
from wwe_data.reports.completeness import write_completeness_report

console = Console()


def main() -> None:
    settings = get_settings()
    events = load_inventory()
    cache_path = settings.processed_dir / "match_bundles_partial.jsonl"

    existing = {b.event_id: b for b in _load_partial_bundles(cache_path)}
    console.print(f"Loaded {len(existing)} existing bundles")

    # Only attempt events currently empty / missing cards
    missing_events = [
        e
        for e in events
        if e.event_id not in existing
        or existing[e.event_id].collection_status in {"empty", "page_not_found", "error"}
        or not existing[e.event_id].matches
    ]
    console.print(f"Attempting WWE.com fill for {len(missing_events)} events...")

    new_bundles = collect_missing_from_wwe(missing_events)
    filled = 0
    still_missing = []
    for b in new_bundles:
        prev = existing.get(b.event_id)
        if b.matches:
            existing[b.event_id] = b
            filled += 1
            console.print(
                f"  OK {b.event_name}: {len(b.matches)} matches from {b.source_url}"
            )
        else:
            # Keep prior bundle but annotate WWE attempt
            if prev is None:
                existing[b.event_id] = b
            else:
                prev.error = (
                    f"{prev.error + '; ' if prev.error else ''}"
                    f"wwe.com: {b.collection_status} ({b.error})"
                )
                existing[b.event_id] = prev
            still_missing.append(
                f"{b.event_name}: {b.collection_status} — {b.error}"
            )
            console.print(f"  MISS {b.event_name}: {b.collection_status} — {b.error}")

    ordered = [existing[e.event_id] for e in events if e.event_id in existing]
    _write_partial_bundles(cache_path, list(existing.values()))
    paths = export_match_datasets(ordered, events)
    report = write_completeness_report(events, ordered)

    console.print(f"\nFilled from WWE.com: {filled}")
    console.print(f"Still missing: {len(still_missing)}")
    for row in still_missing:
        console.print(f"  - {row}")
    console.print(f"Completeness: {report}")
    console.print(f"Matches CSV: {paths.get('matches_csv')}")


if __name__ == "__main__":
    main()
