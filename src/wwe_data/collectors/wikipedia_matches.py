"""Collect match cards from Wikipedia event pages (MediaWiki API)."""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup, Tag

from wwe_data.collectors.http_client import HttpClient
from wwe_data.collectors.wikipedia_resolve import fetch_page_html, resolve_event_page
from wwe_data.models.match_schemas import (
    EventMatchBundle,
    RawMatchRecord,
    RawParticipantRecord,
    SpecialRumbleEntrant,
)
from wwe_data.models.schemas import RawEventRecord, VerificationStatus
from wwe_data.pipeline.ids import make_match_id, make_wrestler_id
from wwe_data.pipeline.match_parse import (
    classify_special_match,
    detect_title_match,
    parse_duration_to_seconds,
    is_results_footnote,
    parse_match_result_text,
    strip_champ_markers,
)


def _header_map(row: Tag) -> dict[str, int]:
    cells = [c.get_text(" ", strip=True).lower() for c in row.find_all(["th", "td"])]
    mapping: dict[str, int] = {}
    for i, h in enumerate(cells):
        if h.startswith("no") or h in {"#", "match"}:
            mapping.setdefault("no", i)
        elif "result" in h:
            mapping["results"] = i
        elif "stipulation" in h:
            mapping["stipulations"] = i
        elif h.startswith("time") or h == "times":
            mapping["times"] = i
        elif "draw" in h or "entry" in h:
            mapping.setdefault("entry", i)
        elif "entrant" in h:
            mapping["entrant"] = i
        elif "order" in h and "elimin" in h:
            mapping["elim_order"] = i
        elif "eliminated by" in h:
            mapping["eliminated_by"] = i
        elif "elimination" in h and "order" not in h:
            mapping["elim_count"] = i
    return mapping


def _is_results_table(headers: dict[str, int]) -> bool:
    return "results" in headers and ("stipulations" in headers or "times" in headers)


def _is_rumble_table(headers: dict[str, int]) -> bool:
    return "entrant" in headers and ("elim_order" in headers or "entry" in headers)


def _cell(texts: list[str], idx: int | None) -> str | None:
    if idx is None or idx >= len(texts):
        return None
    val = texts[idx].strip()
    return val or None


def _parse_match_number(value: str | None) -> int | None:
    if not value:
        return None
    m = re.match(r"(\d+)", value.strip())
    return int(m.group(1)) if m else None


def parse_results_tables(html: str, event: RawEventRecord, page_url: str) -> EventMatchBundle:
    soup = BeautifulSoup(html, "lxml")
    matches: list[RawMatchRecord] = []
    participants: list[RawParticipantRecord] = []
    rumble_rows: list[SpecialRumbleEntrant] = []
    now = datetime.utcnow()

    tables = soup.find_all("table", class_="wikitable")
    results_tables = []
    rumble_tables = []
    for table in tables:
        first = table.find("tr")
        if not first:
            continue
        headers = _header_map(first)
        if _is_rumble_table(headers):
            rumble_tables.append((table, headers))
        elif _is_results_table(headers):
            results_tables.append((table, headers))

    for table, headers in results_tables:
        rows = table.find_all("tr")[1:]
        # Main event = last numbered match in this table (skip kickoff if labeled)
        numbered = []
        parsed_rows = []
        for tr in rows:
            texts = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if len(texts) < 2:
                continue
            result_text = _cell(texts, headers.get("results"))
            if not result_text:
                continue
            # Skip dark match footnotes / color keys / (c) legends
            if is_results_footnote(result_text):
                continue
            match_no = _parse_match_number(_cell(texts, headers.get("no")))
            stip = _cell(texts, headers.get("stipulations"))
            duration = parse_duration_to_seconds(_cell(texts, headers.get("times")))
            is_preshow = bool(
                stip and re.search(r"pre.?show|kickoff|countdown", stip, re.I)
            ) or bool(re.search(r"pre.?show|kickoff", result_text, re.I))
            parsed_rows.append((match_no, result_text, stip, duration, is_preshow))
            if match_no is not None and not is_preshow:
                numbered.append(match_no)

        main_no = max(numbered) if numbered else None

        for match_no, result_text, stip, duration, is_preshow in parsed_rows:
            parsed = parse_match_result_text(result_text)
            special = classify_special_match(stip, result_text)
            match_id = make_match_id(event.event_id, match_no, result_text)
            is_title = detect_title_match(stip, result_text)
            match = RawMatchRecord(
                match_id=match_id,
                event_id=event.event_id,
                match_number=match_no,
                match_name=None,
                match_type=stip,
                match_stipulation=stip,
                match_duration_seconds=duration,
                match_result=result_text,
                winner=parsed["winner"],
                loser=parsed["loser"],
                is_title_match=is_title,
                is_main_event=(match_no == main_no) if main_no is not None else None,
                is_preshow=is_preshow,
                match_status="completed" if event.event_status.value == "completed" else "announced",
                source_url=page_url,
                verification_status=VerificationStatus.single_source,
                special_match_kind=special,
            )
            matches.append(match)

            for role_side, names, result_label in (
                ("winner", parsed["winners"], "win"),
                ("loser", parsed["losers"], "loss"),
            ):
                for ring_name in names:
                    ring_name = strip_champ_markers(ring_name)
                    if not ring_name or len(ring_name) < 2:
                        continue
                    # Skip pure method words
                    if ring_name.lower() in {"pinfall", "submission", "disqualification"}:
                        continue
                    wid = make_wrestler_id(ring_name)
                    participants.append(
                        RawParticipantRecord(
                            match_id=match_id,
                            wrestler_id=wid,
                            ring_name=ring_name,
                            participant_role="competitor",
                            result=result_label,
                        )
                    )

    # Royal Rumble entrant tables (men's + women's each get their own card match)
    rumble_card_matches = [m for m in matches if m.special_match_kind == "royal_rumble"]
    for table_idx, (table, headers) in enumerate(rumble_tables):
        # Prefer 1:1 table → rumble match assignment; fall back to first match only if needed
        rumble_match = (
            rumble_card_matches[table_idx]
            if table_idx < len(rumble_card_matches)
            else (rumble_card_matches[0] if rumble_card_matches else None)
        )
        match_id = rumble_match.match_id if rumble_match else make_match_id(
            event.event_id, 99 + table_idx, "royal rumble entrants"
        )
        if rumble_match is None:
            # Create placeholder match row from rumble table alone
            matches.append(
                RawMatchRecord(
                    match_id=match_id,
                    event_id=event.event_id,
                    match_number=None,
                    match_type="Royal Rumble match",
                    match_stipulation="Royal Rumble match",
                    match_result=None,
                    is_title_match=False,
                    is_main_event=True,
                    is_preshow=False,
                    match_status="completed",
                    source_url=page_url,
                    special_match_kind="royal_rumble",
                )
            )

        entrants: list[SpecialRumbleEntrant] = []
        for tr in table.find_all("tr")[1:]:
            texts = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            entrant = _cell(texts, headers.get("entrant"))
            if not entrant:
                continue
            entrant = strip_champ_markers(entrant)
            entry = _parse_match_number(_cell(texts, headers.get("entry")))
            elim_raw = _cell(texts, headers.get("elim_order"))
            elim_order = None
            is_winner = False
            if elim_raw:
                if re.search(r"winner", elim_raw, re.I):
                    is_winner = True
                else:
                    elim_order = _parse_match_number(elim_raw)
            eliminated_by = _cell(texts, headers.get("eliminated_by"))
            if eliminated_by and eliminated_by in {"—", "-", ""}:
                eliminated_by = None
            time_s = parse_duration_to_seconds(_cell(texts, headers.get("times")))
            elim_count = _parse_match_number(_cell(texts, headers.get("elim_count")))
            wid = make_wrestler_id(entrant)
            entrants.append(
                SpecialRumbleEntrant(
                    match_id=match_id,
                    event_id=event.event_id,
                    entrant=entrant,
                    wrestler_id=wid,
                    entry_number=entry,
                    elimination_order=elim_order,
                    eliminated_by=eliminated_by,
                    time_in_match_seconds=time_s,
                    eliminations_made=elim_count,
                    is_winner=is_winner,
                )
            )
            participants.append(
                RawParticipantRecord(
                    match_id=match_id,
                    wrestler_id=wid,
                    ring_name=entrant,
                    participant_role="competitor",
                    result="winner" if is_winner else ("eliminated" if elim_order else None),
                    entry_number=entry,
                    elimination_order=elim_order,
                    eliminated_by=eliminated_by,
                    time_in_match_seconds=time_s,
                )
            )

        # Final four = last four eliminated + winner, or lowest elimination orders remaining
        if entrants:
            winner = next((e for e in entrants if e.is_winner), None)
            eliminated = sorted(
                [e for e in entrants if e.elimination_order is not None],
                key=lambda e: e.elimination_order or 0,
            )
            final_four_ids = set()
            if winner:
                final_four_ids.add(winner.wrestler_id)
            # Last three eliminated before winner
            for e in reversed(eliminated[-3:]):
                final_four_ids.add(e.wrestler_id)
            for e in entrants:
                e.is_final_four = e.wrestler_id in final_four_ids
                if e.is_winner and rumble_match and not rumble_match.winner:
                    rumble_match.winner = e.entrant
            rumble_rows.extend(entrants)

    return EventMatchBundle(
        event_id=event.event_id,
        event_name=event.event_name,
        source_url=page_url,
        matches=matches,
        participants=participants,
        rumble_entrants=rumble_rows,
        collection_status="success" if matches else "empty",
        collected_at=now,
    )


def collect_event_matches(
    event: RawEventRecord,
    client: HttpClient | None = None,
) -> EventMatchBundle:
    client = client or HttpClient()
    # Do not invent cards for unannounced/empty future events
    if event.event_status.value == "announced":
        return EventMatchBundle(
            event_id=event.event_id,
            event_name=event.event_name,
            collection_status="skipped_announced",
            error="Future/announced event — match card not fabricated",
        )

    try:
        title = resolve_event_page(client, event)
        if not title:
            return EventMatchBundle(
                event_id=event.event_id,
                event_name=event.event_name,
                collection_status="page_not_found",
                error="Wikipedia page not resolved",
            )
        page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        html = fetch_page_html(client, title)
        bundle = parse_results_tables(html, event, page_url)
        bundle.wiki_page = title
        bundle.source_url = page_url
        # Guard: overview pages can yield hundreds of unrelated rows
        if len(bundle.matches) > 40:
            bundle.matches = []
            bundle.participants = []
            bundle.rumble_entrants = []
            bundle.collection_status = "empty"
            bundle.error = (
                f"Rejected oversized card ({title}) — likely series overview page"
            )
        return bundle
    except Exception as exc:  # noqa: BLE001
        return EventMatchBundle(
            event_id=event.event_id,
            event_name=event.event_name,
            collection_status="error",
            error=str(exc),
        )
