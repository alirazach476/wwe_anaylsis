"""Build the master event inventory (phase 1) — no match scraping."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console

from wwe_data.collectors.http_client import HttpClient
from wwe_data.collectors.secondary_sources import audit_secondary_robots
from wwe_data.collectors.wikipedia_ppv import collect_wikipedia_ppv
from wwe_data.collectors.wikipedia_snme import collect_wikipedia_snme
from wwe_data.collectors.wikipedia_specials import collect_wikipedia_specials
from wwe_data.config import get_settings
from wwe_data.models.schemas import CollectionLogRecord, RawEventRecord
from wwe_data.pipeline.dedupe import merge_event_records
from wwe_data.reports.coverage import write_coverage_report

console = Console()


def build_inventory(
    *,
    start_year: int | None = None,
    end_year: int | None = None,
    use_cache: bool = True,
) -> tuple[list[RawEventRecord], list[CollectionLogRecord]]:
    settings = get_settings()
    start_year = start_year or settings.start_year
    end_year = end_year or settings.end_year
    client = HttpClient()
    # HttpClient caches by default; callers can clear cache dir if needed
    _ = use_cache

    all_records: list[RawEventRecord] = []
    logs: list[CollectionLogRecord] = []

    console.print("[bold]Collecting Wikipedia PPV/PLE list...[/bold]")
    recs, log = collect_wikipedia_ppv(
        client, start_year=start_year, end_year=end_year
    )
    all_records.extend(recs)
    logs.append(log)
    console.print(f"  -> {log.records_collected} records ({log.collection_status})")

    console.print("[bold]Collecting Saturday Night's Main Event...[/bold]")
    recs, log = collect_wikipedia_snme(
        client, start_year=start_year, end_year=end_year
    )
    all_records.extend(recs)
    logs.append(log)
    console.print(f"  -> {log.records_collected} records ({log.collection_status})")

    console.print("[bold]Collecting allowlisted TV specials...[/bold]")
    recs, log = collect_wikipedia_specials(
        client, start_year=start_year, end_year=end_year
    )
    all_records.extend(recs)
    logs.append(log)
    console.print(f"  -> {log.records_collected} records ({log.collection_status})")

    console.print("[bold]Auditing secondary-source robots.txt...[/bold]")
    robots = audit_secondary_robots(client)
    for r in robots:
        console.print(
            f"  -> {r.source_name}: can_fetch={r.can_fetch} ({r.detail})"
        )

    console.print("[bold]Deduplicating inventory...[/bold]")
    merged = merge_event_records(all_records)
    console.print(f"  -> {len(all_records)} raw -> {len(merged)} unique events")
    return merged, logs


def export_inventory(
    records: list[RawEventRecord],
    logs: list[CollectionLogRecord],
    output_dir: Path | None = None,
) -> dict[str, Path]:
    settings = get_settings()
    out = output_dir or settings.processed_dir
    out.mkdir(parents=True, exist_ok=True)
    exports = settings.exports_dir
    exports.mkdir(parents=True, exist_ok=True)

    rows = [r.model_dump(mode="json") for r in records]
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["event_date", "event_name"]).reset_index(drop=True)

    paths: dict[str, Path] = {}
    csv_path = exports / "events_inventory.csv"
    parquet_path = exports / "events_inventory.parquet"
    json_path = out / "events_inventory.json"
    logs_path = out / "collection_logs.json"

    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(parquet_path, index=False)
        paths["parquet"] = parquet_path
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]Parquet export skipped: {exc}[/yellow]")

    json_path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    logs_path.write_text(
        json.dumps([l.model_dump(mode="json") for l in logs], indent=2, default=str),
        encoding="utf-8",
    )
    paths.update({"csv": csv_path, "json": json_path, "logs": logs_path})

    # Stamp collection time on dataset
    stamp = {
        "last_collection_timestamp": datetime.utcnow().isoformat() + "Z",
        "event_count": len(records),
        "window": {
            "start_year": settings.start_year,
            "end_year": settings.end_year,
        },
        "phase": "event_inventory",
        "match_scraping": "deferred_until_inventory_review",
    }
    stamp_path = out / "dataset_stamp.json"
    stamp_path.write_text(json.dumps(stamp, indent=2), encoding="utf-8")
    paths["stamp"] = stamp_path
    return paths


def main() -> None:
    records, logs = build_inventory()
    paths = export_inventory(records, logs)
    report_path = write_coverage_report(records, logs)
    console.print("\n[green]Inventory phase complete.[/green]")
    for k, p in paths.items():
        console.print(f"  {k}: {p}")
    console.print(f"  coverage: {report_path}")
    console.print(
        "\n[bold yellow]STOP:[/bold yellow] Match scraping is deferred until "
        "this inventory and coverage audit are reviewed."
    )


if __name__ == "__main__":
    main()
