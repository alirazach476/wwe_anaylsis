"""Name / location / date normalization helpers."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def clean_wiki_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value
    # Strip wiki markup remnants
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip("| ").strip()
    return text or None


def parse_attendance(value: str | None) -> Optional[int]:
    if not value:
        return None
    text = clean_wiki_text(value) or ""
    # Prefer first integer-looking token; ignore combined multi-venue notes
    m = re.search(r"([\d,]+)", text.replace("\xa0", " "))
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None


def parse_location(location: str | None) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Return city, state_province, country from a Wikipedia location cell."""
    text = clean_wiki_text(location)
    if not text:
        return None, None, None

    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return None, None, None

    # Heuristics for common patterns
    if len(parts) == 1:
        return parts[0], None, None
    if len(parts) == 2:
        # "City, Country" or "City, State"
        second = parts[1]
        if second.lower() in {
            "canada",
            "england",
            "scotland",
            "wales",
            "ireland",
            "mexico",
            "japan",
            "australia",
            "germany",
            "france",
            "italy",
            "spain",
            "saudi arabia",
            "united arab emirates",
            "puerto rico",
            "india",
            "china",
            "south korea",
            "brazil",
            "iraq",
            "kuwait",
            "qatar",
        }:
            return parts[0], None, second
        return parts[0], second, "United States"
    # City, State, Country or City, Province, Country
    return parts[0], parts[1], parts[2] if len(parts) > 2 else None


def parse_wiki_date(cell: str, year: int) -> date | None:
    """Parse Wikipedia date cells like 'January 23' or 'April 18 – April 19'."""
    text = clean_wiki_text(cell) or ""
    # Drop parenthetical air dates for inventory primary date: use event date when present
    # e.g. "December 7 (aired December 25)" -> December 7
    text = re.sub(r"\(aired.*?\)", "", text, flags=re.IGNORECASE).strip()
    # Multi-day: take start
    if "–" in text or " - " in text or "—" in text:
        text = re.split(r"[–—]| - ", text)[0].strip()

    m = re.match(
        r"(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2})(?:\s*,\s*(?P<year>\d{4}))?",
        text,
    )
    if not m:
        return None
    month_name = m.group("month").lower()
    if month_name not in MONTHS:
        return None
    y = int(m.group("year") or year)
    d = int(m.group("day"))
    try:
        return date(y, MONTHS[month_name], d)
    except ValueError:
        return None


def parse_wiki_end_date(cell: str, year: int) -> date | None:
    text = clean_wiki_text(cell) or ""
    text = re.sub(r"\(aired.*?\)", "", text, flags=re.IGNORECASE).strip()
    parts = re.split(r"[–—]| - ", text)
    if len(parts) < 2:
        return None
    end = parts[1].strip()
    # End may be "April 19" or just "19"
    m = re.match(
        r"(?:(?P<month>[A-Za-z]+)\s+)?(?P<day>\d{1,2})(?:\s*,\s*(?P<year>\d{4}))?",
        end,
    )
    if not m:
        return None
    start = parse_wiki_date(cell, year)
    month_name = (m.group("month") or "").lower()
    if month_name and month_name in MONTHS:
        month = MONTHS[month_name]
    elif start:
        month = start.month
    else:
        return None
    y = int(m.group("year") or year)
    try:
        return date(y, month, int(m.group("day")))
    except ValueError:
        return None


def canonicalize_event_name(name: str, year: int | None = None) -> str:
    text = clean_wiki_text(name) or name
    text = re.sub(r"\s+", " ", text).strip()
    # Normalize common variants
    replacements = {
        r"^WWF\s+": "WWE ",
        r"Tables, Ladders (&|and) Chairs": "TLC: Tables, Ladders & Chairs",
        r"TLC:\s*Tables, Ladders and Chairs": "TLC: Tables, Ladders & Chairs",
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


def infer_status(event_date: date, today: date | None = None) -> str:
    today = today or date.today()
    if event_date > today:
        return "announced"
    return "completed"


def utc_now() -> datetime:
    return datetime.utcnow()
