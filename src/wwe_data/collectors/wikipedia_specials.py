"""Allowlisted WWE television specials (Tribute to the Troops, etc.)."""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup

from wwe_data.collectors.http_client import HttpClient
from wwe_data.models.schemas import (
    CollectionLogRecord,
    EventStatus,
    EventType,
    RawEventRecord,
)
from wwe_data.pipeline.eligibility import EligibilityFilter
from wwe_data.pipeline.ids import make_collection_id, make_event_id
from wwe_data.pipeline.normalize import (
    canonicalize_event_name,
    infer_status,
    parse_location,
    parse_wiki_date,
)
from wwe_data.pipeline.series import SeriesRegistry

API_URL = "https://en.wikipedia.org/w/api.php"
PAGE = "List_of_WWE_television_specials"
SOURCE_URL = "https://en.wikipedia.org/wiki/List_of_WWE_television_specials"
SOURCE_NAME = "wikipedia_tv_specials"

# Only pull allowlisted specials — never weekly Raw/SmackDown/NXT episodes.
ALLOW_NAME = re.compile(
    r"(tribute to the troops|saturday night.?s main event|sunday night.?s main event|"
    r"wwe vs\.?\s*ecw|greatest royal rumble)",
    re.IGNORECASE,
)


def fetch_html(client: HttpClient | None = None) -> str:
    client = client or HttpClient()
    data = client.get_json(
        API_URL,
        params={
            "action": "parse",
            "page": PAGE,
            "prop": "text",
            "format": "json",
            "formatversion": "2",
        },
    )
    return data["parse"]["text"]


def parse_allowlisted_specials(
    html: str,
    *,
    start_year: int = 2000,
    end_year: int = 2027,
) -> list[RawEventRecord]:
    soup = BeautifulSoup(html, "lxml")
    eligibility = EligibilityFilter()
    registry = SeriesRegistry()
    records: list[RawEventRecord] = []
    now = datetime.utcnow()
    current_year: int | None = None

    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name in {"h2", "h3", "h4"}:
            m = re.search(r"\b(20\d{2}|19\d{2})\b", el.get_text(" ", strip=True))
            if m:
                current_year = int(m.group(0))
            continue
        if el.name != "table" or "wikitable" not in (el.get("class") or []):
            continue
        if current_year is None or not (start_year <= current_year <= end_year):
            continue

        header = el.find("tr")
        if not header:
            continue
        headers = [c.get_text(" ", strip=True).lower() for c in header.find_all(["th", "td"])]
        if not any("event" in h for h in headers):
            continue

        for tr in el.find_all("tr")[1:]:
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            event_name = cells[0]
            if not ALLOW_NAME.search(event_name):
                continue
            # Skip SNME here if dedicated collector already covers — still OK to include;
            # inventory dedupe will merge.
            date_text = cells[1] if len(cells) > 1 else ""
            event_date = parse_wiki_date(date_text, current_year)
            if not event_date:
                # Date may include "(aired ...)"
                event_date = parse_wiki_date(re.sub(r"\(.*?\)", "", date_text), current_year)
            if not event_date or not eligibility.in_window(event_date):
                continue

            venue = cells[2] if len(cells) > 2 else None
            location = cells[3] if len(cells) > 3 else None
            notes = cells[4] if len(cells) > 4 else None
            city, state, country = parse_location(location)

            series = registry.match(event_name)
            series_name = series.canonical_name if series else "Unclassified Eligible"
            event_name = canonicalize_event_name(event_name, event_date.year)

            records.append(
                RawEventRecord(
                    event_id=make_event_id(event_date, event_name),
                    event_name=event_name,
                    canonical_event_name=f"{series_name} ({event_date.year})",
                    event_series=series_name,
                    event_year=event_date.year,
                    event_date=event_date,
                    event_type=EventType.special,
                    event_status=EventStatus(infer_status(event_date)),
                    venue=venue,
                    city=city,
                    state_province=state,
                    country=country,
                    source_url=SOURCE_URL,
                    source_name=SOURCE_NAME,
                    notes=notes,
                    last_updated=now,
                    collection_timestamp=now,
                )
            )
    return records


def collect_wikipedia_specials(
    client: HttpClient | None = None,
    *,
    start_year: int = 2000,
    end_year: int = 2027,
) -> tuple[list[RawEventRecord], CollectionLogRecord]:
    client = client or HttpClient()
    now = datetime.utcnow()
    collection_id = make_collection_id(SOURCE_NAME, now.isoformat())
    try:
        html = fetch_html(client)
        records = parse_allowlisted_specials(
            html, start_year=start_year, end_year=end_year
        )
        return records, CollectionLogRecord(
            collection_id=collection_id,
            source_url=SOURCE_URL,
            collection_timestamp=now,
            records_collected=len(records),
            collection_status="success",
        )
    except Exception as exc:  # noqa: BLE001
        return [], CollectionLogRecord(
            collection_id=collection_id,
            source_url=SOURCE_URL,
            collection_timestamp=now,
            records_collected=0,
            errors=str(exc),
            collection_status="error",
        )
