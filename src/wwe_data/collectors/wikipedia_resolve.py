"""Resolve Wikipedia article titles for WWE events via MediaWiki API."""

from __future__ import annotations

import re

from wwe_data.collectors.http_client import HttpClient
from wwe_data.models.schemas import RawEventRecord

API_URL = "https://en.wikipedia.org/w/api.php"

# Series overview pages that must not be used as a specific event card source
OVERVIEW_TITLES = {
    "saturday night's main event",
    "sunday night's main event",
    "tribute to the troops",
    "wwe tribute to the troops",
    "bad blood",
    "no mercy",
    "wargames",
    "war games",
    "survivor series",
    "royal rumble",
    "summerslam",
    "wrestlemania",
    "money in the bank",
    "elimination chamber",
}


def _candidate_titles(event: RawEventRecord) -> list[str]:
    name = re.sub(r"\s*\[.*?\]\s*", "", event.event_name).strip()
    year = event.event_year
    series = (event.event_series or "").strip()
    candidates: list[str] = []

    def add(title: str) -> None:
        title = re.sub(r"\s+", " ", title).strip()
        if title and title not in candidates:
            candidates.append(title)

    # Prefer year-qualified titles first
    add(f"{name} ({year})")
    if series:
        add(f"{series} ({year})")
    if "saturday night" in name.lower():
        # Prefer numbered episode page if present in name
        add(name)
        add(f"Saturday Night's Main Event ({year})")
    if "wargames" in name.lower() or "war games" in name.lower():
        add(f"Survivor Series ({year})")
        add(f"NXT WarGames ({year})")
    if year == 2000 and "wrestlemania" in name.lower():
        add("WrestleMania 2000")
    # Unqualified name last (often a disambiguation / overview)
    add(name)
    return candidates


def _is_overview_title(title: str, event: RawEventRecord) -> bool:
    t = title.strip().lower()
    if t in OVERVIEW_TITLES:
        return True
    # Overview if title has no year and equals bare series name
    if str(event.event_year) not in title:
        series = (event.event_series or "").strip().lower()
        if series and t == series:
            return True
        if t == event.event_name.strip().lower() and "(" not in title:
            # Bare event series name without edition markers
            if not re.search(r"\b(xx|xl|\d+)\b", t, re.I):
                if any(k in t for k in OVERVIEW_TITLES):
                    return True
    return False


def _score_title(title: str, event: RawEventRecord) -> int:
    score = 0
    blob = title.lower()
    if str(event.event_year) in title:
        score += 5
    if event.event_name.lower() in blob:
        score += 3
    series = (event.event_series or "").lower()
    if series and series in blob:
        score += 2
    if _is_overview_title(title, event):
        score -= 10
    return score


def resolve_event_page(client: HttpClient, event: RawEventRecord) -> str | None:
    """Return Wikipedia page title if found; None if unresolved."""
    candidates = _candidate_titles(event)
    found: list[str] = []

    if candidates:
        data = client.get_json(
            API_URL,
            params={
                "action": "query",
                "titles": "|".join(candidates[:10]),
                "format": "json",
                "formatversion": "2",
                "redirects": "1",
            },
        )
        pages = data.get("query", {}).get("pages", [])
        normalized: dict[str, str] = {}
        for r in data.get("query", {}).get("normalized", []) or []:
            normalized[r["from"]] = r["to"]
        for r in data.get("query", {}).get("redirects", []) or []:
            normalized[r["from"]] = r["to"]

        existing = {p["title"]: p for p in pages if not p.get("missing") and p.get("title")}
        for cand in candidates:
            target = normalized.get(cand, cand)
            page = existing.get(target) or existing.get(cand)
            if page:
                found.append(page["title"])

    # Search fallback
    for q in (
        f"\"{event.event_name}\" {event.event_year} WWE",
        f"{event.event_series or event.event_name} ({event.event_year})",
        f"{event.event_name} {event.event_year}",
    ):
        data = client.get_json(
            API_URL,
            params={
                "action": "query",
                "list": "search",
                "srsearch": q,
                "srlimit": 8,
                "format": "json",
            },
        )
        for hit in data.get("query", {}).get("search", []):
            found.append(hit["title"])

    # Rank and pick best non-overview
    ranked = sorted(set(found), key=lambda t: _score_title(t, event), reverse=True)
    for title in ranked:
        if _score_title(title, event) <= 0:
            continue
        if _is_overview_title(title, event):
            continue
        return title

    # Last resort: year-qualified only
    for title in ranked:
        if str(event.event_year) in title and not _is_overview_title(title, event):
            return title
    return None


def fetch_page_html(client: HttpClient, title: str) -> str:
    data = client.get_json(
        API_URL,
        params={
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json",
            "formatversion": "2",
        },
    )
    return data["parse"]["text"]
