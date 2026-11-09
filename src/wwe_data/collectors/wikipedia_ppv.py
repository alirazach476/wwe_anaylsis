"""Collect WWE PPV/PLE inventory via MediaWiki API HTML parse (permitted)."""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup, Tag

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
    parse_attendance,
    parse_location,
    parse_wiki_date,
    parse_wiki_end_date,
)
from wwe_data.pipeline.series import SeriesRegistry

API_URL = "https://en.wikipedia.org/w/api.php"
PAGE = "List_of_WWE_pay-per-view_and_livestreaming_supercards"
SOURCE_URL = (
    "https://en.wikipedia.org/wiki/List_of_WWE_pay-per-view_and_livestreaming_supercards"
)
SOURCE_NAME = "wikipedia_ppv_list"

_ATTENDANCE_LIKE = re.compile(r"^[\d,]+(?:\s*\(.*\))?$")
_VENUE_LIKE = re.compile(
    r"Arena|Stadium|Center|Centre|Garden|Coliseum|Dome|Forum|Field|Park|Hall|Theatre|Theater",
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


def _year_from_heading(text: str) -> int | None:
    m = re.search(r"\b(19|20)\d{2}\b", text)
    return int(m.group(0)) if m else None


def _parse_brand_from_notes(notes: str | None) -> str | None:
    if not notes:
        return None
    brands = []
    for brand in ("Raw", "SmackDown", "ECW", "NXT"):
        if re.search(rf"\b{brand}\b", notes, re.IGNORECASE):
            brands.append(brand)
    return "/".join(brands) if brands else None


def _looks_like_event_name(name: str) -> bool:
    if not name or len(name) < 2:
        return False
    if _ATTENDANCE_LIKE.match(name.strip()):
        return False
    if name.strip().isdigit():
        return False
    # Pure venue / city continuation rows
    if _VENUE_LIKE.search(name) and not re.search(
        r"Wrestle|Slam|Rumble|Survivor|Mania|Mercy|Bash|Chamber|Backlash|Crown|Clash|"
        r"Night|Series|Rules|Vengeance|Judgment|Armageddon|Payback|Fastlane|TLC|"
        r"Hell|Invasion|Stomping|Spectacle|Heat|Arrival|Roadblock|Evolution",
        name,
        re.IGNORECASE,
    ):
        return False
    return True


def _expand_rowspans(table: Tag) -> list[list[str]]:
    """Expand HTML rowspans/colspans into a rectangular grid of cell texts."""
    rows_raw = table.find_all("tr")
    if not rows_raw:
        return []

    grid: list[list[str | None]] = []
    # occupied[row][col] = True if filled by prior rowspan
    spans: dict[tuple[int, int], str] = {}

    for r_idx, tr in enumerate(rows_raw):
        cells = tr.find_all(["td", "th"])
        row: list[str | None] = []
        c_idx = 0
        cell_i = 0
        while cell_i < len(cells) or (r_idx, c_idx) in spans:
            if (r_idx, c_idx) in spans:
                row.append(spans[(r_idx, c_idx)])
                c_idx += 1
                continue
            cell = cells[cell_i]
            cell_i += 1
            text = cell.get_text(" ", strip=True)
            rowspan = int(cell.get("rowspan", 1) or 1)
            colspan = int(cell.get("colspan", 1) or 1)
            for _ in range(colspan):
                row.append(text)
                if rowspan > 1:
                    for extra in range(1, rowspan):
                        spans[(r_idx + extra, c_idx)] = text
                c_idx += 1
        grid.append(row)

    # Normalize to strings
    return [[(c or "") for c in row] for row in grid]


def parse_events_from_html(
    html: str,
    *,
    start_year: int = 2000,
    end_year: int = 2027,
    eligibility: EligibilityFilter | None = None,
    registry: SeriesRegistry | None = None,
) -> list[RawEventRecord]:
    eligibility = eligibility or EligibilityFilter()
    registry = registry or SeriesRegistry()
    soup = BeautifulSoup(html, "lxml")
    records: list[RawEventRecord] = []
    now = datetime.utcnow()
    current_year: int | None = None
    seen_keys: set[tuple[str, str]] = set()

    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name in {"h2", "h3", "h4"}:
            year = _year_from_heading(el.get_text(" ", strip=True))
            if year is not None:
                current_year = year
            continue

        if el.name != "table":
            continue
        classes = el.get("class") or []
        if "wikitable" not in classes:
            continue
        if current_year is None or current_year < start_year or current_year > end_year:
            continue

        grid = _expand_rowspans(el)
        if not grid:
            continue
        header_cells = [h.lower() for h in grid[0]]
        if not any(h == "date" or h.startswith("date") for h in header_cells):
            continue
        if not any("event" in h for h in header_cells):
            continue

        event_idx = next(
            (i for i, h in enumerate(header_cells) if h == "event" or h.startswith("event")),
            1,
        )
        date_idx = next(
            (i for i, h in enumerate(header_cells) if h == "date" or h.startswith("date")),
            0,
        )

        def col_from(texts: list[str], name: str) -> str | None:
            for i, h in enumerate(header_cells):
                if name in h and i < len(texts):
                    return texts[i] or None
            return None

        for texts in grid[1:]:
            if date_idx >= len(texts) or event_idx >= len(texts):
                continue
            date_text = texts[date_idx]
            if not date_text or "branded event" in date_text.lower():
                continue
            if date_text.lower() in {"date"}:
                continue

            event_date = parse_wiki_date(date_text, current_year)
            if not event_date:
                continue

            event_name = canonicalize_event_name(texts[event_idx], current_year)
            if not _looks_like_event_name(event_name):
                continue

            venue = col_from(texts, "venue")
            location = col_from(texts, "location")
            attendance = parse_attendance(col_from(texts, "attendance"))
            notes = col_from(texts, "notes")
            city, state, country = parse_location(location)
            end_date = parse_wiki_end_date(date_text, current_year)

            if not eligibility.is_eligible(event_name, event_date, notes):
                continue

            key = (event_date.isoformat(), event_name.lower())
            if key in seen_keys:
                continue
            seen_keys.add(key)

            series = registry.match(event_name)
            if series:
                series_name = series.canonical_name
                try:
                    event_type = EventType(series.event_type)
                except ValueError:
                    event_type = EventType.other
            else:
                series_name = "Unclassified Eligible"
                event_type = EventType.other

            if current_year < 2022 and series and series.event_type == "ppv":
                event_type = EventType.ppv

            status = EventStatus(infer_status(event_date))
            records.append(
                RawEventRecord(
                    event_id=make_event_id(event_date, event_name),
                    event_name=event_name,
                    canonical_event_name=(
                        f"{series_name} ({event_date.year})"
                        if series_name != "Unclassified Eligible"
                        else event_name
                    ),
                    event_series=series_name,
                    event_year=event_date.year,
                    event_date=event_date,
                    event_end_date=end_date,
                    event_type=event_type,
                    event_status=status,
                    venue=venue,
                    city=city,
                    state_province=state,
                    country=country,
                    attendance=attendance,
                    brand=_parse_brand_from_notes(notes),
                    source_url=SOURCE_URL,
                    source_name=SOURCE_NAME,
                    notes=notes,
                    last_updated=now,
                    collection_timestamp=now,
                )
            )
    return records


def collect_wikipedia_ppv(
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
        records = parse_events_from_html(
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
