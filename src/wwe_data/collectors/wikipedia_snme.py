"""Collect Saturday Night's Main Event specials (2000–2027) via MediaWiki HTML."""

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
from wwe_data.pipeline.ids import make_collection_id, make_event_id
from wwe_data.pipeline.normalize import (
    canonicalize_event_name,
    infer_status,
    parse_location,
    parse_wiki_date,
)

API_URL = "https://en.wikipedia.org/w/api.php"
PAGE = "Saturday_Night's_Main_Event"
SOURCE_URL = "https://en.wikipedia.org/wiki/Saturday_Night%27s_Main_Event"
SOURCE_NAME = "wikipedia_snme"


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


def parse_snme_events(
    html: str,
    *,
    start_year: int = 2000,
    end_year: int = 2027,
) -> list[RawEventRecord]:
    soup = BeautifulSoup(html, "lxml")
    records: list[RawEventRecord] = []
    now = datetime.utcnow()

    for table in soup.find_all("table", class_="wikitable"):
        header_row = table.find("tr")
        if not header_row:
            continue
        headers = [c.get_text(" ", strip=True).lower() for c in header_row.find_all(["th", "td"])]
        if not any("episode" in h or "event" in h for h in headers):
            continue

        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 3:
                continue
            texts = [c.get_text(" ", strip=True) for c in cells]
            joined = " | ".join(texts)
            if "main event" not in joined.lower() and "saturday night" not in joined.lower():
                continue

            # Episode / event name
            name = texts[0]
            if "main event" not in name.lower():
                name = next(
                    (t for t in texts if "main event" in t.lower() or "saturday night" in t.lower()),
                    name,
                )
            if "main event" not in name.lower() and "saturday night" not in name.lower():
                continue

            event_date = None
            for cell in texts[1:6]:
                ym = re.search(
                    r"(January|February|March|April|May|June|July|August|September|"
                    r"October|November|December)\s+\d{1,2},\s*(\d{4})",
                    cell,
                    re.IGNORECASE,
                )
                if ym:
                    event_date = parse_wiki_date(ym.group(0), int(ym.group(2)))
                    if event_date:
                        break
                # Date without comma year already handled; try Month Day Year variants
                ym2 = re.search(
                    r"(January|February|March|April|May|June|July|August|September|"
                    r"October|November|December)\s+\d{1,2}\s+(\d{4})",
                    cell,
                    re.IGNORECASE,
                )
                if ym2:
                    event_date = parse_wiki_date(
                        f"{ym2.group(1)} {ym2.group(0).split()[1]}, {ym2.group(2)}",
                        int(ym2.group(2)),
                    )
                    if event_date:
                        break

            if not event_date or not (start_year <= event_date.year <= end_year):
                continue

            venue = None
            city = state = country = None
            for cell in texts:
                if re.search(
                    r"Arena|Center|Garden|Coliseum|Stadium|Dome|Forum|Centre",
                    cell,
                ):
                    venue = cell
                if "," in cell and not re.search(r"\bvs\.?\b", cell, re.IGNORECASE):
                    c, s, co = parse_location(cell)
                    if c and re.match(r"^[A-Za-z].*", c) and not city:
                        # Avoid treating episode titles as locations
                        if "main event" not in cell.lower():
                            city, state, country = c, s, co

            event_name = canonicalize_event_name(name, event_date.year)
            records.append(
                RawEventRecord(
                    event_id=make_event_id(event_date, event_name),
                    event_name=event_name,
                    canonical_event_name=f"Saturday Night's Main Event ({event_date.year})",
                    event_series="Saturday Night's Main Event",
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
                    last_updated=now,
                    collection_timestamp=now,
                )
            )
    return records


def collect_wikipedia_snme(
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
        records = parse_snme_events(html, start_year=start_year, end_year=end_year)
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
