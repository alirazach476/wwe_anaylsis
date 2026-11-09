"""Collect match results from permitted WWE.com show pages for missing events."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

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
    parse_match_result_text,
    strip_champ_markers,
)

DEF_LINE = re.compile(
    r"^(?P<line>.+?\s(?:def\.|defeated)\s+.+?)(?:\s*[–—-]\s*.*)?$",
    re.IGNORECASE,
)
NARRATIVE_DEF = re.compile(
    r"([A-Z][^.]{2,120}?)\s+defeated\s+([^.!]{2,120}?)(?:\.|,| in a | while )",
    re.IGNORECASE,
)


def load_url_map(path: Path | None = None) -> list[dict]:
    settings = get_settings()
    path = path or (settings.config_dir / "wwe_missing_event_urls.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("events", [])


def _clean_heading_noise(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bPHOTOS\b|\bWATCH\b|\bvia Submission\b", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" -–—")
    return text


def _normalize_result_candidate(raw: str) -> str | None:
    cleaned = _clean_heading_noise(raw)
    cleaned = re.sub(r"\(\s*\|\s*\)", "", cleaned).strip()
    cleaned = re.sub(r"\s*\(\s*\)\s*", " ", cleaned).strip()
    # Note: do not use \b after def. — '.' is non-word so \bdef\.\b never matches
    if not re.search(r"\bdef\.|\bdefeated\b", cleaned, re.I):
        return None
    # Trim trailing junk after result
    m = re.search(
        r"(.+?\s(?:def\.|defeated)\s+.+?)(?:\s+Catch WWE|\s+View photos|\.|$)",
        cleaned,
        re.I,
    )
    candidate = _clean_heading_noise(m.group(1) if m else cleaned)
    candidate = re.sub(r"\s*\(\s*\)\s*$", "", candidate).strip()
    if not (8 < len(candidate) < 240):
        return None
    if re.search(r"\bcanceled\b|\bcancelled\b", candidate, re.I):
        return None
    return candidate


def extract_result_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    lines: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        candidate = _normalize_result_candidate(raw)
        if not candidate:
            return
        key = candidate.lower()
        if key in seen:
            return
        seen.add(key)
        lines.append(candidate)

    # Headings / emphasis / list / anchors (WWE often puts results in <a> or <strong>)
    for el in soup.find_all(["h1", "h2", "h3", "h4", "strong", "b", "li", "p", "a"]):
        add(el.get_text(" ", strip=True))

    # Direct text nodes (split across tags on some pages)
    for el in soup.find_all(string=True):
        text = str(el).strip()
        if "def." in text.lower() or "defeated" in text.lower():
            parent_text = el.parent.get_text(" ", strip=True) if el.parent else text
            add(parent_text)

    # Narrative fallback for older recap articles
    if len(lines) < 2:
        text = soup.get_text(" ", strip=True)
        for m in NARRATIVE_DEF.finditer(text):
            winner = _clean_heading_noise(m.group(1))
            loser = _clean_heading_noise(m.group(2))
            if len(winner) > 100 or len(loser) > 100:
                continue
            add(f"{winner} defeated {loser}")

    return lines


def bundle_from_result_lines(
    event: RawEventRecord,
    result_lines: list[str],
    source_url: str,
) -> EventMatchBundle:
    matches: list[RawMatchRecord] = []
    participants: list[RawParticipantRecord] = []
    now = datetime.utcnow()

    for i, line in enumerate(result_lines, start=1):
        # Skip canceled
        if re.search(r"\bcanceled\b|\bcancelled\b", line, re.I):
            continue
        parsed = parse_match_result_text(line)
        stip = None
        m_stip = re.search(r"\(([^)]+)\)\s*$", line)
        if m_stip:
            stip = m_stip.group(1)
        match_id = make_match_id(event.event_id, i, line)
        is_title = detect_title_match(stip, line)
        match = RawMatchRecord(
            match_id=match_id,
            event_id=event.event_id,
            match_number=i,
            match_type=stip,
            match_stipulation=stip,
            match_result=line,
            winner=parsed["winner"],
            loser=parsed["loser"],
            is_title_match=is_title,
            is_main_event=(i == len(result_lines)),
            is_preshow=False,
            match_status="completed",
            source_url=source_url,
            verification_status=VerificationStatus.single_source,
        )
        matches.append(match)
        for names, label in ((parsed["winners"], "win"), (parsed["losers"], "loss")):
            for ring_name in names:
                ring_name = strip_champ_markers(ring_name)
                if not ring_name or len(ring_name) < 2:
                    continue
                participants.append(
                    RawParticipantRecord(
                        match_id=match_id,
                        wrestler_id=make_wrestler_id(ring_name),
                        ring_name=ring_name,
                        participant_role="competitor",
                        result=label,
                    )
                )

    return EventMatchBundle(
        event_id=event.event_id,
        event_name=event.event_name,
        source_url=source_url,
        matches=matches,
        participants=participants,
        collection_status="success" if matches else "empty",
        error=None if matches else "No parseable results on WWE.com page",
        collected_at=now,
    )


def collect_missing_from_wwe(
    events: list[RawEventRecord],
    client: HttpClient | None = None,
) -> list[EventMatchBundle]:
    client = client or HttpClient()
    client.settings.request_delay_seconds = max(client.settings.request_delay_seconds, 0.7)
    url_rows = load_url_map()
    by_date = {r["event_date"]: r for r in url_rows}
    events_by_date = {e.event_date.isoformat(): e for e in events}

    bundles: list[EventMatchBundle] = []
    for row in url_rows:
        event = events_by_date.get(row["event_date"])
        if event is None:
            continue
        url = row.get("source_url")
        if not url:
            bundles.append(
                EventMatchBundle(
                    event_id=event.event_id,
                    event_name=event.event_name,
                    collection_status="page_not_found",
                    error=row.get("notes") or "No WWE.com URL configured",
                )
            )
            continue
        try:
            # Bypass cache — WWE pages are large/dynamic; prefer fresh permitted fetch
            html = client.get_text(url, use_cache=False)
            lines = extract_result_lines(html)
            bundle = bundle_from_result_lines(event, lines, url)
            bundles.append(bundle)
        except Exception as exc:  # noqa: BLE001
            bundles.append(
                EventMatchBundle(
                    event_id=event.event_id,
                    event_name=event.event_name,
                    source_url=url,
                    collection_status="error",
                    error=str(exc),
                )
            )
    return bundles
