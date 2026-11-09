"""Collect Money in the Bank cash-in history via Wikipedia MediaWiki API."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from bs4 import BeautifulSoup

from wwe_data.collectors.http_client import HttpClient
from wwe_data.models.schemas import VerificationStatus
from wwe_data.pipeline.normalize import parse_wiki_date

API_URL = "https://en.wikipedia.org/w/api.php"
PAGE = "List of Money in the Bank ladder matches"
PAGE_URL = f"https://en.wikipedia.org/wiki/{PAGE.replace(' ', '_')}"


def _norm_name(value: str | None) -> str:
    text = re.sub(r"\[[^\]]*\]", "", value or "")
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    text = text.replace(".", "")
    return text


def _names_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    ta, tb = a.split(), b.split()
    # "Theory" ↔ "Austin Theory"
    if set(ta) <= set(tb) or set(tb) <= set(ta):
        return True
    return False


def _parse_cash_in_date(raw: str, year_hint: int | None = None) -> date | None:
    text = re.sub(r"\[[^\]]*\]", "", raw or "").strip()
    if not text:
        return None
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    # Fallback helper used elsewhere (needs year)
    if year_hint:
        return parse_wiki_date(text, year_hint)
    m = re.search(r"(\d{4})", text)
    if m:
        return parse_wiki_date(text, int(m.group(1)))
    return None


def _header_map(tr) -> dict[str, int]:
    headers = [c.get_text(" ", strip=True).lower() for c in tr.find_all(["th", "td"])]
    mapping: dict[str, int] = {}
    for i, h in enumerate(headers):
        if "case" in h and "holder" in h:
            mapping["holder"] = i
        elif h.startswith("championship") or h == "championship":
            mapping["championship"] = i
        elif h == "date":
            mapping["date"] = i
        elif h == "event":
            mapping["event"] = i
        elif "result" in h:
            mapping["results"] = i
        elif h == "location":
            mapping["location"] = i
        elif h in {"no", "no.", "#"}:
            mapping["no"] = i
    return mapping


def _cell(texts: list[str], idx: int | None) -> str | None:
    if idx is None or idx >= len(texts):
        return None
    return texts[idx] or None


def _infer_success(results: str | None) -> str | None:
    text = (results or "").lower()
    if not text:
        return None
    if re.search(r"\bwas defeated\b|\blost to\b|\bunsuccessful\b|\bfailed\b", text):
        return "unsuccessful"
    if "no contest" in text or re.search(r"\bdraw\b", text):
        return "no_contest"
    if re.search(r"\bdefeated\b|\bpinned\b|\bwon\b", text):
        return "successful"
    return None


def _infer_opponent(results: str | None) -> str | None:
    text = re.sub(r"\[[^\]]*\]", "", results or "").strip()
    m = re.search(
        r"was defeated by(?: defending champion)?\s+(.+?)(?:\s+after\b|\s+to win\b|\s+in a\b|$)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip(" .")
    m = re.search(
        r"Defeated\s+(.+?)(?:\s+after\b|\s+to win\b|\s+in a\b|$)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip(" .")
    m = re.search(
        r"Lost to\s+(.+?)(?:\s+after\b|\s+in a\b|$)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip(" .")
    return None


def parse_cash_in_tables(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    rows_out: list[dict[str, Any]] = []
    for table in soup.find_all("table", class_="wikitable"):
        first = table.find("tr")
        if not first:
            continue
        headers = _header_map(first)
        if "holder" not in headers or "date" not in headers or "results" not in headers:
            continue
        for tr in table.find_all("tr")[1:]:
            texts = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if len(texts) < 4:
                continue
            holder = _cell(texts, headers.get("holder"))
            if not holder or holder.lower() in {"case holder", "total"}:
                continue
            raw_date = _cell(texts, headers.get("date")) or ""
            cash_date = _parse_cash_in_date(raw_date)
            championship = _cell(texts, headers.get("championship"))
            event = _cell(texts, headers.get("event"))
            results = _cell(texts, headers.get("results"))
            location = _cell(texts, headers.get("location"))
            rows_out.append(
                {
                    "case_holder": re.sub(r"\[[^\]]*\]", "", holder).strip(),
                    "case_holder_norm": _norm_name(holder),
                    "championship": re.sub(r"\[[^\]]*\]", "", championship or "").strip() or None,
                    "cash_in_date": cash_date.isoformat() if cash_date else None,
                    "cash_in_event": re.sub(r"\[[^\]]*\]", "", event or "").strip() or None,
                    "cash_in_location": location,
                    "cash_in_opponent": _infer_opponent(results),
                    "cash_in_result": results,
                    "cash_in_outcome": _infer_success(results),
                    "championship_won": (
                        re.sub(r"\[[^\]]*\]", "", championship or "").strip() or None
                        if _infer_success(results) == "successful"
                        else None
                    ),
                    "source_url": PAGE_URL,
                    "verification_status": VerificationStatus.single_source.value,
                }
            )
    return rows_out


def fetch_mitb_cash_ins(client: HttpClient | None = None) -> list[dict[str, Any]]:
    client = client or HttpClient()
    data = client.get_json(
        API_URL,
        {
            "action": "parse",
            "page": PAGE,
            "prop": "text",
            "format": "json",
            "redirects": 1,
        },
    )
    html = data["parse"]["text"]["*"]
    return parse_cash_in_tables(html)


def enrich_mitb_winner_rows(
    mitb_rows: list[dict[str, Any]],
    cash_ins: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach the next unused cash-in for each ladder-match winner when dates align."""
    unused = sorted(
        [c for c in cash_ins if c.get("cash_in_date")],
        key=lambda r: r["cash_in_date"],
    )
    used: set[int] = set()
    enriched: list[dict[str, Any]] = []

    winners = sorted(
        mitb_rows,
        key=lambda r: (r.get("event_date") or "9999", r.get("winner") or ""),
    )
    for row in winners:
        out = dict(row)
        winner_norm = _norm_name(row.get("winner"))
        event_date = row.get("event_date")
        matched = None
        matched_idx = None
        for i, cash in enumerate(unused):
            if i in used:
                continue
            if not _names_match(cash["case_holder_norm"], winner_norm):
                continue
            if event_date and cash["cash_in_date"] and cash["cash_in_date"] < event_date:
                continue
            matched = cash
            matched_idx = i
            break
        if matched is not None and matched_idx is not None:
            used.add(matched_idx)
            out["cash_in_date"] = matched["cash_in_date"]
            out["cash_in_event"] = matched["cash_in_event"]
            out["cash_in_opponent"] = matched["cash_in_opponent"]
            out["cash_in_result"] = matched["cash_in_result"]
            out["championship_won"] = matched["championship_won"]
            out["cash_in_outcome"] = matched["cash_in_outcome"]
            out["cash_in_source_url"] = matched["source_url"]
            out["verification_status"] = VerificationStatus.verified.value
        else:
            out.setdefault("cash_in_outcome", None)
            out.setdefault("cash_in_source_url", None)
            # Keep needs_review when still unknown (transfer / unused / future)
            if not out.get("cash_in_date"):
                out["verification_status"] = VerificationStatus.needs_review.value
        enriched.append(out)
    return enriched
