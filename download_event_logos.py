#!/usr/bin/env python3
"""
download_event_logos.py — Year-specific WWE PLE logos from Wikimedia Commons.

Discovers events from the local warehouse/exports dataset, searches Commons for
`{event_name} {year} WWE logo`, scores candidates, downloads relevant images,
and writes a frontend-consumable manifest.

Examples:
  python download_event_logos.py
  python download_event_logos.py --event "WrestleMania" --year 2002
  python download_event_logos.py --retry-missing
  python download_event_logos.py --review
  python download_event_logos.py --force
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, unquote, urlparse

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
# Served by Vite as /assets/wwe/events/...
ASSETS_ROOT = ROOT / "frontend" / "public" / "assets" / "wwe" / "events"
MANIFEST_PATH = ASSETS_ROOT / "event_logo_manifest.json"
REVIEW_CSV = ROOT / "event_logo_review.csv"
ERROR_LOG = ROOT / "logs" / "event_logo_download_errors.log"

DEFAULT_CSV = ROOT / "data" / "warehouse" / "marts" / "mart_event_analytics.csv"
EXPORTS_EVENTS = ROOT / "data" / "exports" / "events.csv"
SQLITE_CANDIDATES = [
    ROOT / "data" / "processed" / "wwe_analytics.sqlite",
    ROOT / "data" / "processed" / "wwe_history.sqlite",
]

USER_AGENT = (
    "WWE-PLE-Analytics/1.0 (educational historical analytics; "
    "event logo archival; contact=local)"
)
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WP_API = "https://en.wikipedia.org/w/api.php"
_COMMONS_AVAILABLE: bool | None = None

# Minimum score to auto-accept a download
ACCEPT_THRESHOLD = 24
# Below this → needs_review / missing
REVIEW_THRESHOLD = 14

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})

log = logging.getLogger("event_logos")


@dataclass
class EventRecord:
    event_id: str
    event_name: str
    event_year: int
    event_series: str
    event_family: str


@dataclass
class Candidate:
    file_title: str
    image_url: str
    page_url: str
    mime: str | None = None
    width: int | None = None
    height: int | None = None
    license_name: str | None = None
    license_url: str | None = None
    author: str | None = None
    source_info: str | None = None
    relevance_score: float = 0.0
    reasons: list[str] = field(default_factory=list)


@dataclass
class ManifestRow:
    event_id: str
    event_name: str
    event_year: int
    event_family: str
    local_logo_path: str | None
    source_file_title: str | None
    source_page_url: str | None
    original_image_url: str | None
    license_name: str | None
    license_url: str | None
    author: str | None
    search_query: str
    relevance_score: float | None
    download_status: str
    needs_manual_review: bool


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------


def slug_family(series: str | None, name: str | None = None) -> str:
    hay = f"{series or ''} {name or ''}".lower()
    mapping = [
        ("wrestlemania", "wrestlemania"),
        ("greatest royal rumble", "greatest-royal-rumble"),
        ("royal rumble", "royal-rumble"),
        ("summerslam", "summerslam"),
        ("survivor series", "survivor-series"),
        ("money in the bank", "money-in-the-bank"),
        ("hell in a cell", "hell-in-a-cell"),
        ("elimination chamber", "elimination-chamber"),
        ("extreme rules", "extreme-rules"),
        ("crown jewel", "crown-jewel"),
        ("backlash", "backlash"),
        ("clash at the castle", "clash-at-the-castle"),
        ("clash of champions", "clash-of-champions"),
        ("clash in paris", "clash-in-paris"),
        ("clash in italy", "clash-in-italy"),
        ("saturday night", "saturday-night-main-event"),
        ("night of champions", "night-of-champions"),
        ("no way out", "no-way-out"),
        ("no mercy", "no-mercy"),
        ("tlc", "tlc"),
        ("judgment day", "judgment-day"),
        ("payback", "payback"),
        ("fastlane", "fastlane"),
        ("battleground", "battleground"),
        ("great american bash", "great-american-bash"),
        ("king of the ring", "king-of-the-ring"),
        ("king and queen", "king-and-queen-of-the-ring"),
        ("one night stand", "one-night-stand"),
        ("tribute to the troops", "tribute-to-the-troops"),
    ]
    for needle, slug in mapping:
        if needle in hay:
            return slug
    raw = (series or name or "other").lower()
    return re.sub(r"[^a-z0-9]+", "-", raw).strip("-") or "other"


def file_stem(event_name: str, year: int, family: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", event_name.lower()).strip("_")
    # Prefer family_year when name already embeds the year
    if str(year) in base:
        return f"{family.replace('-', '_')}_{year}"
    return f"{base}_{year}"


def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    rename: dict[str, str] = {}
    for want, aliases in {
        "event_id": ["event_id", "id"],
        "event_name": ["event_name", "name", "canonical_event_name", "title"],
        "event_year": ["event_year", "year"],
        "event_series": ["event_series", "series", "family"],
    }.items():
        for a in aliases:
            if a in cols:
                rename[cols[a]] = want
                break
    out = df.rename(columns=rename)
    need = {"event_name", "event_year"}
    if not need.issubset(out.columns):
        raise ValueError(f"Dataset missing columns {need - set(out.columns)}")
    if "event_id" not in out.columns:
        out["event_id"] = out.apply(
            lambda r: f"evt_{r['event_year']}_{re.sub(r'[^a-z0-9]+', '-', str(r['event_name']).lower()).strip('-')}",
            axis=1,
        )
    if "event_series" not in out.columns:
        out["event_series"] = out["event_name"]
    out["event_year"] = pd.to_numeric(out["event_year"], errors="coerce")
    out = out.dropna(subset=["event_year", "event_name"])
    out["event_year"] = out["event_year"].astype(int)
    out["event_name"] = out["event_name"].astype(str).str.strip()
    out["event_series"] = out["event_series"].astype(str).str.strip()
    out["event_id"] = out["event_id"].astype(str).str.strip()
    return out


def load_events(path: Path | None = None) -> list[EventRecord]:
    frames: list[pd.DataFrame] = []
    candidates = [path] if path else [DEFAULT_CSV, EXPORTS_EVENTS]
    for p in candidates:
        if p and p.exists():
            if p.suffix.lower() == ".csv":
                frames.append(_normalize_frame(pd.read_csv(p)))
                break
            if p.suffix.lower() == ".json":
                frames.append(_normalize_frame(pd.read_json(p)))
                break

    if not frames:
        for db in SQLITE_CANDIDATES:
            if not db.exists():
                continue
            con = sqlite3.connect(db)
            try:
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", con)["name"].tolist()
                for t in ("mart_event_analytics", "events", "dim_events"):
                    if t in tables:
                        frames.append(_normalize_frame(pd.read_sql(f"SELECT * FROM {t}", con)))
                        break
            finally:
                con.close()
            if frames:
                break

    if not frames:
        raise FileNotFoundError("No event dataset found (CSV/JSON/SQLite).")

    df = frames[0]
    # Deduplicate by event_id preferentially, else name+year
    if df["event_id"].duplicated().any():
        df = df.drop_duplicates(subset=["event_id"], keep="first")
    df = df.drop_duplicates(subset=["event_name", "event_year"], keep="first")
    df = df.sort_values(["event_year", "event_name"])

    records: list[EventRecord] = []
    for _, row in df.iterrows():
        series = str(row["event_series"])
        name = str(row["event_name"])
        records.append(
            EventRecord(
                event_id=str(row["event_id"]),
                event_name=name,
                event_year=int(row["event_year"]),
                event_series=series,
                event_family=slug_family(series, name),
            )
        )
    return records


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def request_json(url: str, params: dict[str, Any], retries: int = 5) -> dict[str, Any]:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=45)
            if r.status_code == 429:
                wait = min(60, 2 ** attempt * 3)
                log.warning("429 rate limit — sleeping %ss", wait)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001
            last = exc
            wait = min(40, 2 ** attempt)
            log.warning("API error (%s) — retry in %ss", exc, wait)
            time.sleep(wait)
    raise RuntimeError(f"API failed: {last}")


def download_bytes(url: str, retries: int = 5) -> tuple[bytes, str] | None:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=60, allow_redirects=True)
            if r.status_code == 429:
                time.sleep(min(60, 2 ** attempt * 3))
                continue
            if r.status_code >= 400:
                return None
            ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            data = r.content
            if "text/html" in ctype or data[:15].lstrip().lower().startswith((b"<!doctype", b"<html")):
                log.error("Got HTML instead of image for %s", url)
                return None
            if not _looks_like_image(data, ctype):
                log.error("Invalid image signature for %s (%s)", url, ctype)
                return None
            return data, ctype
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(min(30, 2 ** attempt))
    log.error("Download failed for %s: %s", url, last)
    return None


def _looks_like_image(data: bytes, ctype: str) -> bool:
    if len(data) < 64:
        return False
    sigs = [
        (b"\x89PNG\r\n\x1a\n", "png"),
        (b"\xff\xd8\xff", "jpeg"),
        (b"GIF87a", "gif"),
        (b"GIF89a", "gif"),
        (b"RIFF", "webp"),  # weak; check WEBP later
        (b"<?xml", "svg"),
        (b"<svg", "svg"),
    ]
    for sig, _ in sigs:
        if data.startswith(sig) or data.lstrip().startswith(sig):
            return True
    if "svg" in ctype and b"<svg" in data[:2000].lower():
        return True
    if data[8:12] == b"WEBP":
        return True
    return False


def ext_for(mime: str | None, url: str, title: str) -> str:
    if mime:
        m = mime.lower()
        if "svg" in m:
            return ".svg"
        if "png" in m:
            return ".png"
        if "jpeg" in m or "jpg" in m:
            return ".jpg"
        if "webp" in m:
            return ".webp"
        if "gif" in m:
            return ".gif"
    for cand in (title, urlparse(url).path):
        low = unquote(cand).lower()
        for e in (".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif"):
            if low.endswith(e):
                return ".jpg" if e == ".jpeg" else e
    return ".png"


# ---------------------------------------------------------------------------
# Commons search + scoring
# ---------------------------------------------------------------------------


def search_query(event: EventRecord) -> str:
    # Prefer clean series + year when event_name already has year/noise
    name = event.event_series if event.event_series and event.event_series.lower() not in {"other", "nan"} else event.event_name
    # Strip trailing year from series name duplicates
    name = re.sub(rf"\b{event.event_year}\b", "", name).strip()
    name = re.sub(r"\s+", " ", name)
    return f"{name} {event.event_year} WWE logo"


def request_json_fast_fail(url: str, params: dict[str, Any], retries: int = 2) -> dict[str, Any] | None:
    """Like request_json but fails fast on DNS / connection errors (e.g. commons.wikimedia.org)."""
    for attempt in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=25)
            if r.status_code == 429:
                time.sleep(min(30, 2 ** attempt * 3))
                continue
            if r.status_code >= 400:
                return None
            return r.json()
        except requests.exceptions.RequestException as exc:
            log.warning("API unreachable %s (%s)", urlparse(url).hostname, exc.__class__.__name__)
            return None
    return None


def _page_title_relevant(title: str, event: EventRecord) -> bool:
    """Only accept the edition article for this year — never the series hub or other years."""
    t = title.lower().strip()
    year = str(event.event_year)
    name = event.event_name.lower().strip()
    series = event.event_series.lower().strip()

    # Exact event name (e.g. "WrestleMania X8")
    if t == name or t == "wwe " + name:
        return True
    # Explicit year edition pages
    edition_titles = {
        f"{series} ({year})",
        f"wwe {series} ({year})",
        f"{name} ({year})",
        f"wwe {name} ({year})",
    }
    if t in edition_titles:
        return True
    if year in t and series in t:
        # Reject if another year also appears
        other = [y for y in re.findall(r"(?:19|20)\d{2}", t) if y != year]
        return not other
    # Series hub alone (e.g. "SummerSlam", "WrestleMania") — too noisy
    if t in {series, f"wwe {series}", f"{series} (professional wrestling)"}:
        return False
    # Other editions: WrestleMania XIX while seeking X8
    if name and name != series:
        # Require the distinctive edition token from event_name
        tokens = [tok for tok in re.split(r"[^a-z0-9]+", name) if tok and tok not in re.split(r"[^a-z0-9]+", series)]
        if tokens and all(tok in t for tok in tokens):
            return True
    return False


def wiki_page_title_candidates(event: EventRecord) -> list[str]:
    """Year-specific Wikipedia article titles to mine for logos/posters."""
    titles: list[str] = []
    name = event.event_name.strip()
    series = event.event_series.strip()
    year = event.event_year
    for t in (
        name,
        f"{series} ({year})",
        f"{name} ({year})",
        f"WWE {series} ({year})",
        f"WWE {name}",
    ):
        t = re.sub(r"\s+", " ", t).strip()
        if t and t not in titles and _page_title_relevant(t, event):
            titles.append(t)
    # Narrow search: series + year only; filter strictly
    data = request_json_fast_fail(
        WP_API,
        {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f"\"{series}\" {year}",
            "srnamespace": 0,
            "srlimit": 8,
        },
    )
    if data:
        for hit in data.get("query", {}).get("search", []):
            t = hit.get("title")
            if t and t not in titles and _page_title_relevant(t, event):
                titles.append(t)
    return titles[:6]


def files_from_wikipedia_pages(event: EventRecord) -> list[str]:
    """Collect File: titles from year-specific Wikipedia event articles only."""
    titles = wiki_page_title_candidates(event)
    if not titles:
        return []
    data = request_json_fast_fail(
        WP_API,
        {
            "action": "query",
            "format": "json",
            "titles": "|".join(titles),
            "prop": "pageimages|images|info",
            "pithumbsize": 1200,
            "pilicense": "any",
            "imlimit": 40,
            "redirects": 1,
        },
    )
    files: list[str] = []
    if not data:
        return files

    # Map redirects so we know final titles
    redirect_to: dict[str, str] = {}
    for row in data.get("query", {}).get("redirects", []):
        redirect_to[row["from"]] = row["to"]

    for page in data.get("query", {}).get("pages", {}).values():
        if page.get("missing") is not None:
            continue
        page_title = page.get("title") or ""
        if not _page_title_relevant(page_title, event):
            log.info("  skip unrelated wiki page: %s", page_title)
            continue
        pi = page.get("pageimage")
        if pi:
            ft = pi if str(pi).startswith("File:") else f"File:{pi}"
            if ft not in files:
                files.insert(0, ft)  # prefer infobox/lead image
        for img in page.get("images") or []:
            t = img.get("title")
            if not t or t in files:
                continue
            low = t.lower()
            if any(
                x in low
                for x in (
                    "commons-logo",
                    "wikidata",
                    "edit-clear",
                    "question_book",
                    "padlock",
                    "ambox",
                    "flag of",
                    "crystal_clear",
                    "symbol_support",
                )
            ):
                continue
            files.append(t)
    return files[:25]


def commons_reachable() -> bool:
    global _COMMONS_AVAILABLE
    if _COMMONS_AVAILABLE is not None:
        return _COMMONS_AVAILABLE
    try:
        r = SESSION.get(COMMONS_API, params={"action": "query", "format": "json", "meta": "siteinfo"}, timeout=8)
        _COMMONS_AVAILABLE = r.status_code == 200
    except requests.exceptions.RequestException:
        _COMMONS_AVAILABLE = False
    if not _COMMONS_AVAILABLE:
        log.warning("Commons API unreachable — using English Wikipedia pages only")
    return _COMMONS_AVAILABLE


def commons_search(query: str, limit: int = 12) -> list[str]:
    """Return File: titles from Commons when available."""
    titles: list[str] = []
    if not commons_reachable():
        return titles
    data = request_json_fast_fail(
        COMMONS_API,
        {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srnamespace": 6,
            "srlimit": limit,
        },
        retries=1,
    )
    if not data:
        return titles
    for hit in data.get("query", {}).get("search", []):
        t = hit.get("title")
        if t and t not in titles:
            titles.append(t)
    return titles


def imageinfo_batch(file_titles: list[str]) -> list[Candidate]:
    if not file_titles:
        return []
    out: list[Candidate] = []
    # Chunk to avoid oversized requests / partial failures
    for i in range(0, min(len(file_titles), 20), 5):
        chunk = file_titles[i : i + 5]
        data = request_json_fast_fail(
            WP_API,
            {
                "action": "query",
                "format": "json",
                "titles": "|".join(chunk),
                "prop": "imageinfo",
                "iiprop": "url|mime|size|extmetadata",
                "iiurlwidth": 1600,
            },
            retries=3,
        )
        if not data:
            time.sleep(1.0)
            continue
        for page in data.get("query", {}).get("pages", {}).values():
            if page.get("missing") is not None:
                continue
            infos = page.get("imageinfo") or []
            if not infos:
                continue
            ii = infos[0]
            meta = ii.get("extmetadata") or {}
            license_name = (meta.get("LicenseShortName") or meta.get("License") or {}).get("value")
            license_url = (meta.get("LicenseUrl") or {}).get("value")
            author = (meta.get("Artist") or meta.get("Credit") or {}).get("value")
            if author:
                author = re.sub(r"<[^>]+>", "", author).strip()
            source_info = (meta.get("Attribution") or meta.get("Credit") or {}).get("value")
            if source_info:
                source_info = re.sub(r"<[^>]+>", "", str(source_info)).strip()
            url = ii.get("url") or ii.get("thumburl")
            if not url:
                continue
            title = page.get("title") or ""
            page_url = f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
            out.append(
                Candidate(
                    file_title=title,
                    image_url=url,
                    page_url=page_url,
                    mime=ii.get("mime"),
                    width=ii.get("width"),
                    height=ii.get("height"),
                    license_name=license_name,
                    license_url=license_url,
                    author=author,
                    source_info=source_info,
                )
            )
        time.sleep(0.35)
    return out


def score_candidate(cand: Candidate, event: EventRecord) -> Candidate:
    title = unquote(cand.file_title).lower()
    series = event.event_series.lower()
    name = event.event_name.lower()
    year = str(event.event_year)
    score = 0.0
    reasons: list[str] = []
    series_tokens = [t for t in re.split(r"[^a-z0-9]+", series) if len(t) > 2]
    name_tokens = [t for t in re.split(r"[^a-z0-9]+", name) if len(t) > 2]

    # Logo keywords (strong preference)
    if any(k in title for k in ("logo", "wordmark", "logotype")):
        score += 18
        reasons.append("logo_keyword")
    # Official event posters are acceptable year-specific artwork when no logo exists
    if "poster" in title or "promotional" in title:
        if year in title or any(t in title for t in series_tokens if len(t) > 3):
            score += 4
            reasons.append("year_event_poster")
        else:
            score -= 8
            reasons.append("poster_penalty")

    # Year match / mismatch
    years_in_title = re.findall(r"(19|20)\d{2}", title)
    if year in title:
        score += 16
        reasons.append("year_match")
    elif years_in_title and year not in years_in_title:
        score -= 22
        reasons.append("wrong_year")

    # Roman / branded event codes often appear without the calendar year (e.g. WMX8)
    compact_name = re.sub(r"[^a-z0-9]+", "", name)
    compact_title = re.sub(r"[^a-z0-9]+", "", title)
    if compact_name and len(compact_name) >= 6 and compact_name in compact_title:
        score += 18
        reasons.append("exact_event_name")
    # Strongly prefer filenames that include the calendar year for this event
    if year in title and any(tok in title for tok in series_tokens if len(tok) > 3):
        score += 8
        reasons.append("series_year_in_filename")
    hit = sum(1 for t in series_tokens if t in title)
    if hit:
        score += min(14, hit * 4)
        reasons.append("series_tokens")
    if any(t in title for t in name_tokens if t not in {"wwe", "the", "and"}):
        score += 6
        reasons.append("name_tokens")

    # WWE relevance
    if "wwe" in title or "wwf" in title:
        score += 6
        reasons.append("wwe_mark")

    # Format
    mime = (cand.mime or "").lower()
    if "svg" in mime or title.endswith(".svg"):
        score += 6
        reasons.append("svg")
    elif "png" in mime or title.endswith(".png"):
        score += 4
        reasons.append("png")
    elif "jpeg" in mime or title.endswith((".jpg", ".jpeg")):
        score += 1

    # Dimensions
    w, h = cand.width or 0, cand.height or 0
    if w and h:
        if w >= 300 and h >= 80:
            score += 5
            reasons.append("good_dims")
        if w < 80 or h < 40:
            score -= 8
            reasons.append("tiny")
        # Tall posters
        if h > w * 1.4 and "logo" not in title:
            score -= 6
            reasons.append("portrait_poster")

    # Penalties for unrelated content
    for bad in (
        "portrait",
        "wrestler",
        "arena",
        "crowd",
        "ticket",
        "fan art",
        "fanart",
        "2k",
        "video game",
        "network logo",
        "raw logo",
        "smackdown logo",
    ):
        if bad in title and bad.split()[0] not in series:
            score -= 12
            reasons.append(f"penalize_{bad.replace(' ', '_')}")

    # Generic WWE-only logos (no event)
    if re.search(r"\bwwe[_ -]?logo\b", title) and not any(t in title for t in series_tokens):
        score -= 14
        reasons.append("generic_wwe_logo")

    cand.relevance_score = score
    cand.reasons = reasons
    return cand


def pick_best(cands: list[Candidate], event: EventRecord) -> Candidate | None:
    scored = [score_candidate(c, event) for c in cands]
    scored.sort(key=lambda c: c.relevance_score, reverse=True)
    return scored[0] if scored else None


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"generated_by": "download_event_logos.py", "items": []}


def save_manifest(items: list[ManifestRow]) -> None:
    ASSETS_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_by": "download_event_logos.py",
        "source": "Wikimedia Commons MediaWiki API",
        "count": len(items),
        "items": [asdict(i) for i in items],
        "by_event_id": {
            i.event_id: i.local_logo_path
            for i in items
            if i.local_logo_path and i.download_status == "downloaded"
        },
    }
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_review_csv(rows: list[dict[str, Any]]) -> None:
    fields = [
        "event_name",
        "year",
        "event_id",
        "candidate_file_title",
        "candidate_image_url",
        "source_page",
        "license",
        "relevance_score",
        "review_status",
        "reasons",
    ]
    with REVIEW_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def setup_logging() -> None:
    ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(ERROR_LOG, encoding="utf-8"),
        ],
    )


# ---------------------------------------------------------------------------
# Core download loop
# ---------------------------------------------------------------------------


def dest_path(event: EventRecord, ext: str) -> Path:
    folder = ASSETS_ROOT / event.event_family
    folder.mkdir(parents=True, exist_ok=True)
    stem = file_stem(event.event_name, event.event_year, event.event_family)
    return folder / f"{stem}{ext}"


def process_event(
    event: EventRecord,
    *,
    force: bool = False,
    existing: dict[str, ManifestRow] | None = None,
) -> tuple[ManifestRow, list[dict[str, Any]]]:
    query = search_query(event)
    review_rows: list[dict[str, Any]] = []
    existing = existing or {}

    # Skip if already downloaded (unless force)
    prev = existing.get(event.event_id)
    if prev and prev.local_logo_path and prev.download_status == "downloaded" and not force:
        # Resolve under frontend/public (paths stored as /assets/...)
        public_file = ROOT / "frontend" / "public" / prev.local_logo_path.lstrip("/")
        if public_file.exists() and public_file.stat().st_size > 200:
            log.info("SKIP cached %s %s", event.event_name, event.event_year)
            return prev, review_rows

    log.info("SEARCH %s (%s) — %s", event.event_name, event.event_year, query)
    # Prefer year-specific Wikipedia event pages (works when Commons DNS is blocked)
    titles = files_from_wikipedia_pages(event)
    time.sleep(0.5)
    for t in commons_search(query):
        if t not in titles:
            titles.append(t)
    # Secondary Commons/enwiki file search
    if len(titles) < 4:
        alt_q = f"{event.event_name} {event.event_year} logo"
        for t in commons_search(alt_q):
            if t not in titles:
                titles.append(t)
        time.sleep(0.6)

    cands = imageinfo_batch(titles)
    time.sleep(0.6)
    for c in cands:
        score_candidate(c, event)
        review_rows.append(
            {
                "event_name": event.event_name,
                "year": event.event_year,
                "event_id": event.event_id,
                "candidate_file_title": c.file_title,
                "candidate_image_url": c.image_url,
                "source_page": c.page_url,
                "license": c.license_name or "",
                "relevance_score": round(c.relevance_score, 2),
                "review_status": "candidate",
                "reasons": ",".join(c.reasons),
            }
        )

    best = pick_best(cands, event) if cands else None
    if not best or best.relevance_score < REVIEW_THRESHOLD:
        status = "missing" if not best else "needs_review"
        log.info("  → %s (best=%.1f)", status, best.relevance_score if best else -1)
        if best:
            for r in review_rows:
                if r["candidate_file_title"] == best.file_title:
                    r["review_status"] = "needs_review"
        return (
            ManifestRow(
                event_id=event.event_id,
                event_name=event.event_name,
                event_year=event.event_year,
                event_family=event.event_family,
                local_logo_path=None,
                source_file_title=best.file_title if best else None,
                source_page_url=best.page_url if best else None,
                original_image_url=best.image_url if best else None,
                license_name=best.license_name if best else None,
                license_url=best.license_url if best else None,
                author=best.author if best else None,
                search_query=query,
                relevance_score=best.relevance_score if best else None,
                download_status=status,
                needs_manual_review=True,
            ),
            review_rows,
        )

    if best.relevance_score < ACCEPT_THRESHOLD:
        for r in review_rows:
            if r["candidate_file_title"] == best.file_title:
                r["review_status"] = "needs_review"
        return (
            ManifestRow(
                event_id=event.event_id,
                event_name=event.event_name,
                event_year=event.event_year,
                event_family=event.event_family,
                local_logo_path=None,
                source_file_title=best.file_title,
                source_page_url=best.page_url,
                original_image_url=best.image_url,
                license_name=best.license_name,
                license_url=best.license_url,
                author=best.author,
                search_query=query,
                relevance_score=best.relevance_score,
                download_status="needs_review",
                needs_manual_review=True,
            ),
            review_rows,
        )

    ext = ext_for(best.mime, best.image_url, best.file_title)
    dest = dest_path(event, ext)
    if dest.exists() and dest.stat().st_size > 200 and not force:
        rel = f"/assets/wwe/events/{event.event_family}/{dest.name}"
        log.info("  → exists %s", dest.name)
        for r in review_rows:
            if r["candidate_file_title"] == best.file_title:
                r["review_status"] = "accepted_cached"
        return (
            ManifestRow(
                event_id=event.event_id,
                event_name=event.event_name,
                event_year=event.event_year,
                event_family=event.event_family,
                local_logo_path=rel,
                source_file_title=best.file_title,
                source_page_url=best.page_url,
                original_image_url=best.image_url,
                license_name=best.license_name,
                license_url=best.license_url,
                author=best.author,
                search_query=query,
                relevance_score=best.relevance_score,
                download_status="downloaded",
                needs_manual_review=False,
            ),
            review_rows,
        )

    blob = download_bytes(best.image_url)
    if not blob:
        log.error("  → download_failed %s", best.image_url)
        for r in review_rows:
            if r["candidate_file_title"] == best.file_title:
                r["review_status"] = "download_failed"
        return (
            ManifestRow(
                event_id=event.event_id,
                event_name=event.event_name,
                event_year=event.event_year,
                event_family=event.event_family,
                local_logo_path=None,
                source_file_title=best.file_title,
                source_page_url=best.page_url,
                original_image_url=best.image_url,
                license_name=best.license_name,
                license_url=best.license_url,
                author=best.author,
                search_query=query,
                relevance_score=best.relevance_score,
                download_status="failed",
                needs_manual_review=True,
            ),
            review_rows,
        )

    data, ctype = blob
    # Adjust extension from actual content-type when possible
    ext = ext_for(ctype or best.mime, best.image_url, best.file_title)
    dest = dest_path(event, ext)
    dest.write_bytes(data)
    rel = f"/assets/wwe/events/{event.event_family}/{dest.name}"
    log.info("  → saved %s (score=%.1f)", dest.name, best.relevance_score)
    for r in review_rows:
        if r["candidate_file_title"] == best.file_title:
            r["review_status"] = "accepted"
    return (
        ManifestRow(
            event_id=event.event_id,
            event_name=event.event_name,
            event_year=event.event_year,
            event_family=event.event_family,
            local_logo_path=rel,
            source_file_title=best.file_title,
            source_page_url=best.page_url,
            original_image_url=best.image_url,
            license_name=best.license_name,
            license_url=best.license_url,
            author=best.author,
            search_query=query,
            relevance_score=best.relevance_score,
            download_status="downloaded",
            needs_manual_review=False,
        ),
        review_rows,
    )


def manifest_index(data: dict[str, Any]) -> dict[str, ManifestRow]:
    out: dict[str, ManifestRow] = {}
    for raw in data.get("items", []):
        try:
            out[raw["event_id"]] = ManifestRow(**raw)
        except TypeError:
            continue
    return out


def filter_events(
    events: list[EventRecord],
    *,
    event_filter: str | None,
    year: int | None,
    retry_missing: bool,
    existing: dict[str, ManifestRow],
) -> list[EventRecord]:
    selected = events
    if event_filter:
        ef = event_filter.lower()
        selected = [
            e
            for e in selected
            if ef in e.event_name.lower() or ef in e.event_series.lower() or ef in e.event_family
        ]
    if year is not None:
        selected = [e for e in selected if e.event_year == year]
    if retry_missing:
        selected = [
            e
            for e in selected
            if e.event_id not in existing
            or existing[e.event_id].download_status in {"missing", "failed", "needs_review"}
            or not existing[e.event_id].local_logo_path
        ]
    return selected


def print_report(items: list[ManifestRow], review_n: int, dup_n: int) -> None:
    total = len(items)
    ok = sum(1 for i in items if i.download_status == "downloaded")
    missing = sum(1 for i in items if i.download_status == "missing")
    review = sum(1 for i in items if i.download_status == "needs_review" or i.needs_manual_review)
    failed = sum(1 for i in items if i.download_status == "failed")
    print("\n========== EVENT LOGO DOWNLOAD REPORT ==========")
    print(f"Total unique events discovered : {total}")
    print(f"Successful downloads           : {ok}")
    print(f"Missing logos                  : {missing}")
    print(f"Images requiring review        : {review}")
    print(f"Failed downloads               : {failed}")
    print(f"Duplicate candidates recorded  : {dup_n}")
    print(f"Review CSV rows                : {review_n}")
    print(f"Manifest                       : {MANIFEST_PATH}")
    print(f"Assets root                    : {ASSETS_ROOT}")
    print("================================================\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download year-specific WWE PLE logos from Wikimedia Commons")
    parser.add_argument("--event", help="Filter by event name/series substring")
    parser.add_argument("--year", type=int, help="Filter by event year")
    parser.add_argument("--retry-missing", action="store_true", help="Only retry missing/failed/needs_review")
    parser.add_argument("--review", action="store_true", help="Regenerate review report from manifest + light re-search")
    parser.add_argument("--force", action="store_true", help="Replace existing downloaded images")
    parser.add_argument("--dataset", type=Path, help="Optional CSV/JSON path")
    parser.add_argument("--limit", type=int, help="Process at most N events (debug)")
    parser.add_argument("--sleep", type=float, default=1.2, help="Polite delay between events")
    args = parser.parse_args(argv)

    setup_logging()
    ASSETS_ROOT.mkdir(parents=True, exist_ok=True)

    events = load_events(args.dataset)
    log.info("Loaded %s unique events from dataset", len(events))

    existing_data = load_manifest()
    existing = manifest_index(existing_data)

    if args.review and not args.event and args.year is None and not args.retry_missing and not args.force:
        # Regenerate review CSV by re-scoring top Commons hits without downloading
        review_rows: list[dict[str, Any]] = []
        for event in events:
            query = search_query(event)
            titles = commons_search(query, limit=8)
            cands = imageinfo_batch(titles)
            for c in cands:
                score_candidate(c, event)
                review_rows.append(
                    {
                        "event_name": event.event_name,
                        "year": event.event_year,
                        "event_id": event.event_id,
                        "candidate_file_title": c.file_title,
                        "candidate_image_url": c.image_url,
                        "source_page": c.page_url,
                        "license": c.license_name or "",
                        "relevance_score": round(c.relevance_score, 2),
                        "review_status": "candidate",
                        "reasons": ",".join(c.reasons),
                    }
                )
            time.sleep(args.sleep)
        write_review_csv(review_rows)
        # Keep existing manifest items
        items = list(existing.values()) if existing else []
        if not items:
            items = [
                ManifestRow(
                    event_id=e.event_id,
                    event_name=e.event_name,
                    event_year=e.event_year,
                    event_family=e.event_family,
                    local_logo_path=None,
                    source_file_title=None,
                    source_page_url=None,
                    original_image_url=None,
                    license_name=None,
                    license_url=None,
                    author=None,
                    search_query=search_query(e),
                    relevance_score=None,
                    download_status="missing",
                    needs_manual_review=True,
                )
                for e in events
            ]
        print_report(items, len(review_rows), 0)
        return 0

    selected = filter_events(
        events,
        event_filter=args.event,
        year=args.year,
        retry_missing=args.retry_missing,
        existing=existing,
    )
    if args.limit:
        selected = selected[: args.limit]

    # Merge results into full inventory
    results: dict[str, ManifestRow] = dict(existing)
    # Ensure every discovered event appears in the final report
    for e in events:
        if e.event_id not in results:
            results[e.event_id] = ManifestRow(
                event_id=e.event_id,
                event_name=e.event_name,
                event_year=e.event_year,
                event_family=e.event_family,
                local_logo_path=None,
                source_file_title=None,
                source_page_url=None,
                original_image_url=None,
                license_name=None,
                license_url=None,
                author=None,
                search_query=search_query(e),
                relevance_score=None,
                download_status="pending",
                needs_manual_review=True,
            )

    all_review: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    dup_candidates = 0

    log.info("Processing %s events…", len(selected))
    for i, event in enumerate(selected, 1):
        print(f"[{i}/{len(selected)}] {event.event_name} ({event.event_year})")
        try:
            row, reviews = process_event(event, force=args.force, existing=existing)
        except Exception as exc:  # noqa: BLE001
            log.exception("Unhandled error for %s: %s", event.event_id, exc)
            row = ManifestRow(
                event_id=event.event_id,
                event_name=event.event_name,
                event_year=event.event_year,
                event_family=event.event_family,
                local_logo_path=None,
                source_file_title=None,
                source_page_url=None,
                original_image_url=None,
                license_name=None,
                license_url=None,
                author=None,
                search_query=search_query(event),
                relevance_score=None,
                download_status="failed",
                needs_manual_review=True,
            )
            reviews = []

        # Duplicate image detection across review candidates
        for r in reviews:
            url = r.get("candidate_image_url") or ""
            h = hashlib.sha1(url.encode("utf-8")).hexdigest()
            if h in seen_hashes:
                dup_candidates += 1
                r["review_status"] = f"{r.get('review_status')}|duplicate_url"
            else:
                seen_hashes.add(h)
        all_review.extend(reviews)
        results[event.event_id] = row
        time.sleep(args.sleep)

    # Mark untouched pending as missing in this run's full inventory sense
    items = sorted(results.values(), key=lambda x: (x.event_year, x.event_name))
    for it in items:
        if it.download_status == "pending":
            it.download_status = "missing"

    save_manifest(items)
    write_review_csv(all_review)
    print_report(items, len(all_review), dup_candidates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
