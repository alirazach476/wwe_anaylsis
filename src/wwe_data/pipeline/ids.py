"""Stable ID generation — never invents content, only hashes known fields."""

from __future__ import annotations

import hashlib
import re
from datetime import date


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:80]


def make_event_id(event_date: date, event_name: str) -> str:
    """Deterministic event_id from date + normalized name."""
    base = f"{event_date.isoformat()}_{slugify(event_name)}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
    return f"evt_{event_date.strftime('%Y%m%d')}_{slugify(event_name)[:40]}_{digest}"


def make_collection_id(source_name: str, timestamp_iso: str) -> str:
    raw = f"{source_name}|{timestamp_iso}"
    return f"col_{hashlib.sha1(raw.encode()).hexdigest()[:16]}"


def make_match_id(event_id: str, match_number: int | None, result_text: str) -> str:
    raw = f"{event_id}|{match_number}|{slugify(result_text)[:120]}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    num = match_number if match_number is not None else 0
    return f"mtc_{digest}_{num}"


def make_wrestler_id(canonical_name: str) -> str:
    return f"wrs_{slugify(canonical_name)[:60]}_{hashlib.sha1(canonical_name.lower().encode()).hexdigest()[:8]}"


def make_championship_id(name: str) -> str:
    return f"chp_{slugify(name)[:60]}_{hashlib.sha1(name.lower().encode()).hexdigest()[:8]}"


def make_team_id(team_name: str) -> str:
    return f"tem_{slugify(team_name)[:60]}_{hashlib.sha1(team_name.lower().encode()).hexdigest()[:8]}"
