"""Deduplicate and merge multi-source event inventory records."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from wwe_data.models.schemas import RawEventRecord, VerificationStatus


def _normalize_name_for_dedupe(name: str) -> str:
    """Collapse SNME numbering / light punctuation for same-day duplicates."""
    import re

    text = name.lower().strip()
    text = re.sub(r"saturday night.?s main event(?:\s+[ivxlcdm]+)?", "saturday nights main event", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _merge_key(record: RawEventRecord) -> tuple:
    """Soft key for near-duplicate detection across sources."""
    return (record.event_date.isoformat(), _normalize_name_for_dedupe(record.event_name))


def _prefer(a: str | None, b: str | None) -> str | None:
    if a and not b:
        return a
    if b and not a:
        return b
    if a and b and a != b:
        # Keep first; conflict flagged at verification level
        return a
    return a or b


def merge_event_records(records: list[RawEventRecord]) -> list[RawEventRecord]:
    grouped: dict[tuple, list[RawEventRecord]] = defaultdict(list)
    for rec in records:
        grouped[_merge_key(rec)].append(rec)

    merged: list[RawEventRecord] = []
    now = datetime.utcnow()
    for _, group in sorted(grouped.items(), key=lambda x: x[0][0]):
        primary = group[0]
        sources = {r.source_name for r in group}
        conflict_fields = []
        for other in group[1:]:
            for field in ("venue", "city", "attendance", "country"):
                av = getattr(primary, field)
                bv = getattr(other, field)
                if av and bv and av != bv:
                    conflict_fields.append(field)
                setattr(primary, field, _prefer(av, bv))

        if len(sources) > 1 and not conflict_fields:
            primary.verification_status = VerificationStatus.verified
        elif conflict_fields:
            primary.verification_status = VerificationStatus.conflict
            note = f"Conflict on: {', '.join(sorted(set(conflict_fields)))}"
            primary.notes = f"{primary.notes + '; ' if primary.notes else ''}{note}"
        else:
            primary.verification_status = VerificationStatus.single_source

        primary.last_updated = now
        # Keep deterministic event_id from primary
        merged.append(primary)
    return merged
