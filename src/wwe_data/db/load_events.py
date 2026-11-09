"""Load event inventory into PostgreSQL (optional until DB is available)."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from sqlalchemy.dialects.postgresql import insert

from wwe_data.config import get_settings
from wwe_data.db.models import CollectionLog, Event, EventSource
from wwe_data.db.session import create_all, get_session
from wwe_data.models.schemas import RawEventRecord

console = Console()


def load_inventory_to_postgres(
    inventory_path: Path | None = None,
    logs_path: Path | None = None,
) -> int:
    settings = get_settings()
    inventory_path = inventory_path or (
        settings.processed_dir / "events_inventory.json"
    )
    logs_path = logs_path or (settings.processed_dir / "collection_logs.json")
    if not inventory_path.exists():
        raise FileNotFoundError(f"Missing inventory: {inventory_path}")

    create_all()
    records = [
        RawEventRecord.model_validate(row)
        for row in json.loads(inventory_path.read_text(encoding="utf-8"))
    ]
    session = get_session()
    try:
        for rec in records:
            stmt = insert(Event).values(
                event_id=rec.event_id,
                event_name=rec.event_name,
                canonical_event_name=rec.canonical_event_name,
                event_series=rec.event_series,
                event_year=rec.event_year,
                event_date=rec.event_date,
                event_end_date=rec.event_end_date,
                event_type=rec.event_type.value,
                event_status=rec.event_status.value,
                venue=rec.venue,
                city=rec.city,
                state_province=rec.state_province,
                country=rec.country,
                attendance=rec.attendance,
                broadcast_platform=rec.broadcast_platform,
                brand=rec.brand,
                official_url=rec.official_url,
                source_url=rec.source_url,
                verification_status=rec.verification_status.value,
                last_updated=rec.last_updated,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["event_id"],
                set_={
                    "event_name": stmt.excluded.event_name,
                    "canonical_event_name": stmt.excluded.canonical_event_name,
                    "event_series": stmt.excluded.event_series,
                    "venue": stmt.excluded.venue,
                    "city": stmt.excluded.city,
                    "attendance": stmt.excluded.attendance,
                    "verification_status": stmt.excluded.verification_status,
                    "last_updated": stmt.excluded.last_updated,
                },
            )
            session.execute(stmt)
            session.add(
                EventSource(
                    event_id=rec.event_id,
                    source_name=rec.source_name,
                    source_url=rec.source_url,
                    source_type="archive",
                    retrieved_at=rec.collection_timestamp,
                    verification_status=rec.verification_status.value,
                )
            )

        if logs_path.exists():
            for row in json.loads(logs_path.read_text(encoding="utf-8")):
                session.merge(
                    CollectionLog(
                        collection_id=row["collection_id"],
                        source_url=row["source_url"],
                        collection_timestamp=row["collection_timestamp"],
                        records_collected=row.get("records_collected", 0),
                        errors=row.get("errors"),
                        collection_status=row.get("collection_status", "success"),
                    )
                )
        session.commit()
        console.print(f"[green]Loaded {len(records)} events into PostgreSQL[/green]")
        return len(records)
    finally:
        session.close()


if __name__ == "__main__":
    load_inventory_to_postgres()
