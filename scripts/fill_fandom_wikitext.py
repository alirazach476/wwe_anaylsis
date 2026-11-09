"""Parse Fandom wikitext Results/Matches bullets for the remaining empty events."""

from __future__ import annotations

import json
import re
from datetime import datetime

from rich.console import Console

from wwe_data.collectors.http_client import HttpClient
from wwe_data.config import get_settings
from wwe_data.models.match_schemas import (
    EventMatchBundle,
    RawMatchRecord,
    RawParticipantRecord,
)
from wwe_data.models.schemas import RawEventRecord, VerificationStatus
from wwe_data.pipeline.ids import make_match_id, make_wrestler_id
from wwe_data.pipeline.match_parse import (
    detect_title_match,
    parse_duration_to_seconds,
    parse_match_result_text,
    strip_champ_markers,
)
from wwe_data.pipeline.matches import (
    _load_partial_bundles,
    _write_partial_bundles,
    export_match_datasets,
)
from wwe_data.reports.completeness import write_completeness_report

console = Console()
API = "https://prowrestling.fandom.com/api.php"

PAGES = [
    (
        "2007-05-28",
        "Saturday Night's Main Event XXXIV",
        "https://prowrestling.fandom.com/wiki/Saturday_Night%27s_Main_Event_XXXIV",
    ),
    (
        "2008-07-28",
        "Saturday Night's Main Event XXXVI",
        "https://prowrestling.fandom.com/wiki/Saturday_Night%27s_Main_Event_XXXVI",
    ),
    (
        "2007-12-07",
        "Tribute to the Troops 2007",
        "https://prowrestling.fandom.com/wiki/Tribute_to_the_Troops_2007",
    ),
    (
        "2010-12-09",
        "Tribute to the Troops 2010",
        "https://prowrestling.fandom.com/wiki/Tribute_to_the_Troops_2010",
    ),
]


def clean_wiki_links(text: str) -> str:
    text = re.sub(r"\[\[[^|\]]*\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"\s+", " ", text).strip(" ;*")
    return text


def parse_wikitext_results(wikitext: str) -> list[tuple[str, str | None, str | None]]:
    # Prefer Results or Matches section
    m = re.search(
        r"==\s*(Results|Matches)\s*==(.+?)(?:\n==[^=]|\Z)",
        wikitext,
        re.S | re.I,
    )
    chunk = m.group(2) if m else wikitext
    rows: list[tuple[str, str | None, str | None]] = []
    for line in chunk.splitlines():
        line = line.strip()
        if not line.startswith("*"):
            continue
        if line.lower().startswith("*'''also") or "segment" in line.lower():
            continue
        raw = line.lstrip("*").strip()
        # duration in trailing (m:ss)
        dur = None
        dm = re.search(r"\((\d{1,2}:\d{2})\)\s*$", raw)
        if dm:
            dur = dm.group(1)
            raw = raw[: dm.start()].strip()
        # stipulation: "in a X match"
        stip = None
        sm = re.search(r"\bin an?\s+(.+?match.*?)\s*$", raw, re.I)
        if sm:
            stip = clean_wiki_links(sm.group(1))
        result = clean_wiki_links(raw)
        # Drop leading Dark Match label into stipulation
        if result.lower().startswith("dark match"):
            result = re.sub(r"(?i)^dark match:\s*", "", result)
            stip = (stip + "; " if stip else "") + "Dark match"
        if not re.search(r"defeated|def\.|ended in|won a", result, re.I):
            continue
        rows.append((result, stip, dur))
    return rows


def bundle_from_rows(
    event: RawEventRecord, rows: list[tuple[str, str | None, str | None]], source_url: str
) -> EventMatchBundle:
    matches: list[RawMatchRecord] = []
    participants: list[RawParticipantRecord] = []
    for i, (result, stip, dur) in enumerate(rows, start=1):
        parsed = parse_match_result_text(result)
        if re.search(r"ended in a no[- ]?contest|no contest", result, re.I):
            # participants both sides if "A vs. B ended in"
            vm = re.match(r"(.+?)\s+vs\.?\s+(.+?)\s+ended in", result, re.I)
            if vm:
                parsed = {
                    "winner": None,
                    "loser": None,
                    "winners": re.split(r"\s+&\s+|\s+and\s+", strip_champ_markers(vm.group(1))),
                    "losers": re.split(r"\s+&\s+|\s+and\s+", strip_champ_markers(vm.group(2))),
                    "outcome": "no_contest",
                    "is_draw": True,
                }
        mid = make_match_id(event.event_id, i, result)
        matches.append(
            RawMatchRecord(
                match_id=mid,
                event_id=event.event_id,
                match_number=i,
                match_type=stip,
                match_stipulation=stip,
                match_duration_seconds=parse_duration_to_seconds(dur),
                match_result=result,
                winner=parsed.get("winner"),
                loser=parsed.get("loser"),
                is_title_match=detect_title_match(stip, result),
                is_main_event=(i == len(rows)),
                is_preshow=False,
                match_status="no_contest"
                if (parsed.get("outcome") == "no_contest")
                else "completed",
                source_url=source_url,
                verification_status=VerificationStatus.single_source,
            )
        )
        for names, label in (
            (parsed.get("winners") or [], "win" if parsed.get("outcome") != "no_contest" else "no_contest"),
            (parsed.get("losers") or [], "loss" if parsed.get("outcome") != "no_contest" else "no_contest"),
        ):
            for name in names:
                name = strip_champ_markers(name.strip())
                if len(name) < 2:
                    continue
                participants.append(
                    RawParticipantRecord(
                        match_id=mid,
                        wrestler_id=make_wrestler_id(name),
                        ring_name=name,
                        participant_role="competitor",
                        result=label,
                    )
                )
    return EventMatchBundle(
        event_id=event.event_id,
        event_name=event.event_name,
        source_url=source_url,
        wiki_page=source_url,
        matches=matches,
        participants=participants,
        collection_status="success" if matches else "empty",
        collected_at=datetime.utcnow(),
    )


def main() -> None:
    settings = get_settings()
    client = HttpClient()
    inv = [
        RawEventRecord.model_validate(r)
        for r in json.loads(
            (settings.processed_dir / "events_inventory.json").read_text(encoding="utf-8")
        )
    ]
    by_date = {e.event_date.isoformat(): e for e in inv}
    existing = {
        b.event_id: b
        for b in _load_partial_bundles(settings.processed_dir / "match_bundles_partial.jsonl")
    }

    for event_date, title, url in PAGES:
        event = by_date[event_date]
        data = client.get_json(
            API,
            params={"action": "parse", "page": title, "prop": "wikitext", "format": "json"},
            use_cache=False,
        )
        wt = data["parse"]["wikitext"]["*"]
        rows = parse_wikitext_results(wt)
        bundle = bundle_from_rows(event, rows, url)
        existing[event.event_id] = bundle
        console.print(f"{event.event_name}: {len(bundle.matches)} matches")
        for m in bundle.matches:
            console.print(f"  - {m.match_result}")

    ordered = [existing[e.event_id] for e in inv if e.event_id in existing]
    _write_partial_bundles(
        settings.processed_dir / "match_bundles_partial.jsonl", list(existing.values())
    )
    export_match_datasets(ordered, inv)
    report = write_completeness_report(inv, ordered)

    # Verify key specials
    console.print("\nKey specials check:")
    for e in inv:
        if e.event_name in {
            "WWE Raw Premiere on Netflix",
            "John Cena's Final SmackDown",
            "John Cena's Final Raw",
            "Raw: Roman Reigns vs. Penta",
        }:
            b = existing.get(e.event_id)
            console.print(f"{e.event_name}: {len(b.matches) if b else 0} matches")
            if b:
                for m in b.matches:
                    console.print(f"  - {m.match_result}")
    console.print(f"Completeness: {report}")


if __name__ == "__main__":
    main()
