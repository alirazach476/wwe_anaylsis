"""Phase 2 pipeline: collect match cards for the event inventory."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.progress import Progress

from wwe_data.collectors.http_client import HttpClient
from wwe_data.collectors.wikipedia_matches import collect_event_matches
from wwe_data.config import get_settings
from wwe_data.models.match_schemas import EventMatchBundle
from wwe_data.models.schemas import CollectionLogRecord, RawEventRecord
from wwe_data.pipeline.championships import build_championship_tables
from wwe_data.pipeline.ids import make_collection_id
from wwe_data.pipeline.special_matches import (
    extract_chamber_rows,
    extract_mitb_winners,
    extract_survivor_series_rows,
    rumble_to_rows,
)
from wwe_data.pipeline.wrestlers import build_wrestler_tables
from wwe_data.reports.completeness import write_completeness_report

console = Console()


def load_inventory(path: Path | None = None) -> list[RawEventRecord]:
    settings = get_settings()
    path = path or (settings.processed_dir / "events_inventory.json")
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [RawEventRecord.model_validate(r) for r in rows]


def _load_partial_bundles(cache_path: Path) -> list[EventMatchBundle]:
    bundles: list[EventMatchBundle] = []
    if not cache_path.exists():
        return bundles
    with cache_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            bundles.append(EventMatchBundle.model_validate(json.loads(line)))
    return bundles


def _write_partial_bundles(cache_path: Path, bundles: list[EventMatchBundle]) -> None:
    with cache_path.open("w", encoding="utf-8") as fh:
        for b in bundles:
            fh.write(b.model_dump_json() + "\n")


def collect_all_matches(
    events: list[RawEventRecord] | None = None,
    *,
    limit: int | None = None,
    resume: bool = True,
    retry_failed: bool = False,
) -> list[EventMatchBundle]:
    settings = get_settings()
    events = events or load_inventory()
    if limit is not None:
        events = events[:limit]

    client = HttpClient()
    # Polite pacing to reduce 429s on long runs
    client.settings.request_delay_seconds = max(
        client.settings.request_delay_seconds, 0.6
    )

    cache_path = settings.processed_dir / "match_bundles_partial.jsonl"
    by_id: dict[str, EventMatchBundle] = {}

    if resume and cache_path.exists():
        for b in _load_partial_bundles(cache_path):
            by_id[b.event_id] = b
        console.print(f"Loaded {len(by_id)} cached event bundles")

    def needs_collect(event_id: str) -> bool:
        if event_id not in by_id:
            return True
        if not retry_failed:
            return False
        b = by_id[event_id]
        status = b.collection_status
        if status in {"error", "empty", "page_not_found"}:
            return True
        if status == "success" and not b.matches:
            return True
        # Recollect suspicious oversized cards (series overview mis-resolve)
        if len(b.matches) > 40:
            return True
        if b.wiki_page and b.wiki_page.lower() in {
            "saturday night's main event",
            "sunday night's main event",
            "bad blood",
            "no mercy",
            "wargames",
            "wwe tribute to the troops",
        }:
            return True
        return False

    remaining = [e for e in events if needs_collect(e.event_id)]
    console.print(f"Collecting matches for {len(remaining)} events...")

    with Progress() as progress:
        task = progress.add_task("matches", total=len(remaining))
        for event in remaining:
            bundle = collect_event_matches(event, client)
            by_id[event.event_id] = bundle
            # Persist incrementally (rewrite keeps successes + new results)
            _write_partial_bundles(cache_path, list(by_id.values()))
            progress.advance(task)
            # Brief pause between events after errors cool down the API
            if bundle.collection_status == "error":
                time.sleep(2.0)

    # Preserve event order
    return [by_id[e.event_id] for e in events if e.event_id in by_id]


def _df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def export_match_datasets(
    bundles: list[EventMatchBundle],
    events: list[RawEventRecord],
) -> dict[str, Path]:
    settings = get_settings()
    exports = settings.exports_dir
    processed = settings.processed_dir
    exports.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    matches = [m for b in bundles for m in b.matches]
    participants = [p for b in bundles for p in b.participants]
    rumble = [r for b in bundles for r in b.rumble_entrants]
    events_by_id = {e.event_id: e for e in events}

    wrestlers, aliases = build_wrestler_tables(participants)
    championships, match_champs = build_championship_tables(matches)
    mitb = extract_mitb_winners(matches, events_by_id)
    survivor = extract_survivor_series_rows(matches, participants, events_by_id)
    chamber = extract_chamber_rows(matches, participants, events_by_id)

    datasets = {
        "matches": [m.model_dump(mode="json") for m in matches],
        "match_participants": [p.model_dump(mode="json") for p in participants],
        "wrestlers": [w.model_dump(mode="json") for w in wrestlers],
        "wrestler_aliases": [a.model_dump(mode="json") for a in aliases],
        "championships": [c.model_dump(mode="json") for c in championships],
        "match_championships": [c.model_dump(mode="json") for c in match_champs],
        "special_royal_rumble": rumble_to_rows(rumble),
        "special_money_in_the_bank": mitb,
        "special_survivor_series": survivor,
        "special_elimination_chamber": chamber,
        "event_match_status": [
            {
                "event_id": b.event_id,
                "event_name": b.event_name,
                "wiki_page": b.wiki_page,
                "source_url": b.source_url,
                "match_count": len(b.matches),
                "collection_status": b.collection_status,
                "error": b.error,
            }
            for b in bundles
        ],
    }

    paths: dict[str, Path] = {}
    for name, rows in datasets.items():
        df = _df(rows)
        csv_path = exports / f"{name}.csv"
        parquet_path = exports / f"{name}.parquet"
        json_path = processed / f"{name}.json"
        df.to_csv(csv_path, index=False)
        json_path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
        try:
            df.to_parquet(parquet_path, index=False)
            paths[f"{name}_parquet"] = parquet_path
        except Exception:
            pass
        paths[f"{name}_csv"] = csv_path
        paths[f"{name}_json"] = json_path

    stamp = {
        "last_collection_timestamp": datetime.utcnow().isoformat() + "Z",
        "phase": "match_collection",
        "events_processed": len(bundles),
        "matches": len(matches),
        "participants": len(participants),
        "wrestlers": len(wrestlers),
        "championship_links": len(match_champs),
        "rumble_entrant_rows": len(rumble),
    }
    stamp_path = processed / "dataset_stamp_matches.json"
    stamp_path.write_text(json.dumps(stamp, indent=2), encoding="utf-8")
    paths["stamp"] = stamp_path

    # Collection log
    log = CollectionLogRecord(
        collection_id=make_collection_id("wikipedia_matches", stamp["last_collection_timestamp"]),
        source_url="https://en.wikipedia.org/w/api.php",
        records_collected=len(matches),
        collection_status="success",
    )
    log_path = processed / "collection_logs_matches.json"
    log_path.write_text(
        json.dumps([log.model_dump(mode="json")], indent=2, default=str),
        encoding="utf-8",
    )
    paths["logs"] = log_path
    return paths


def main(limit: int | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Phase 2 match collection")
    parser.add_argument("--limit", type=int, default=None, help="Process only N events")
    parser.add_argument("--fresh", action="store_true", help="Ignore partial cache")
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry events that previously errored / had empty cards",
    )
    args = parser.parse_args()
    limit = args.limit if args.limit is not None else limit

    settings = get_settings()
    if args.fresh:
        partial = settings.processed_dir / "match_bundles_partial.jsonl"
        if partial.exists():
            partial.unlink()

    events = load_inventory()
    bundles = collect_all_matches(
        events,
        limit=limit,
        resume=not args.fresh,
        retry_failed=args.retry_failed,
    )
    # If limit used, only report on those events
    event_subset = events[:limit] if limit else events
    # Filter bundles to subset event ids when limited
    if limit:
        ids = {e.event_id for e in event_subset}
        bundles = [b for b in bundles if b.event_id in ids]

    paths = export_match_datasets(bundles, event_subset)
    report = write_completeness_report(event_subset, bundles)
    console.print("\n[green]Phase 2 match collection complete.[/green]")
    console.print(f"  matches csv: {paths.get('matches_csv')}")
    console.print(f"  completeness: {report}")


if __name__ == "__main__":
    main()
