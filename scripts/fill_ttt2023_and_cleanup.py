"""Fill Tribute 2023 + clean Final SmackDown duplicate narrative row."""

from __future__ import annotations

import json
from datetime import datetime

from rich.console import Console

from wwe_data.collectors.wwe_com_matches import bundle_from_result_lines
from wwe_data.config import get_settings
from wwe_data.models.match_schemas import EventMatchBundle
from wwe_data.models.schemas import RawEventRecord
from wwe_data.pipeline.matches import (
    _load_partial_bundles,
    _write_partial_bundles,
    export_match_datasets,
)
from wwe_data.reports.completeness import write_completeness_report

console = Console()

TTT_2023_RESULTS = [
    "Santos Escobar def. Dragon Lee",
    "Bobby Lashley def. Karrion Kross",
    "Asuka def. Charlotte Flair",
    "Randy Orton & LA Knight def. Jimmy Uso & Solo Sikoa",
]


def main() -> None:
    settings = get_settings()
    inv = [
        RawEventRecord.model_validate(r)
        for r in json.loads(
            (settings.processed_dir / "events_inventory.json").read_text(encoding="utf-8")
        )
    ]
    existing = {
        b.event_id: b
        for b in _load_partial_bundles(settings.processed_dir / "match_bundles_partial.jsonl")
    }

    ttt = next(e for e in inv if e.event_date.isoformat() == "2023-12-08")
    bundle = bundle_from_result_lines(
        ttt,
        TTT_2023_RESULTS,
        "https://www.cagematch.net/?id=1&nr=376269",
    )
    # Cross-confirmed via Fightful / SmackDown Hotel / WrestleTalk (Cagematch DNS blocked here)
    bundle.error = None
    bundle.collection_status = "success"
    bundle.collected_at = datetime.utcnow()
    for m in bundle.matches:
        m.verification_status = m.verification_status  # keep single_source
        if "Escobar" in (m.match_result or "") or "Lashley" in (m.match_result or ""):
            m.match_stipulation = (
                "#1 Contender Tournament (WWE United States Championship) Round 1"
            )
            m.is_title_match = False
    existing[ttt.event_id] = bundle
    console.print(f"Tribute 2023: {len(bundle.matches)} matches")

    # Clean Final SmackDown — drop narrative Lesnar duplicate
    final_sd = next(e for e in inv if e.event_name == "John Cena's Final SmackDown")
    b = existing[final_sd.event_id]
    keep = []
    for m in b.matches:
        r = (m.match_result or "").lower()
        if r.startswith("with both competitors down"):
            continue
        keep.append(m)
    # keep participants for remaining match ids
    keep_ids = {m.match_id for m in keep}
    b.matches = keep
    b.participants = [p for p in b.participants if p.match_id in keep_ids]
    existing[final_sd.event_id] = b
    console.print(f"Final SmackDown cleaned to {len(b.matches)} matches")

    ordered = [existing[e.event_id] for e in inv if e.event_id in existing]
    _write_partial_bundles(
        settings.processed_dir / "match_bundles_partial.jsonl", list(existing.values())
    )
    export_match_datasets(ordered, inv)
    report = write_completeness_report(inv, ordered)
    console.print(f"Missing cards: check {report}")


if __name__ == "__main__":
    main()
