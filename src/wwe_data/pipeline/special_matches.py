"""Derive special-match datasets from collected match/participant rows."""

from __future__ import annotations

from wwe_data.models.match_schemas import (
    RawMatchRecord,
    RawParticipantRecord,
    SpecialMitbCashIn,
    SpecialRumbleEntrant,
)
from wwe_data.models.schemas import RawEventRecord, VerificationStatus


def extract_mitb_winners(
    matches: list[RawMatchRecord],
    events_by_id: dict[str, RawEventRecord],
) -> list[dict]:
    """MITB ladder match winners — cash-in details left null unless sourced later."""
    rows = []
    for m in matches:
        if m.special_match_kind != "money_in_the_bank" and not (
            m.match_stipulation
            and "money in the bank" in m.match_stipulation.lower()
            and "ladder" in (m.match_stipulation or "").lower()
        ):
            continue
        event = events_by_id.get(m.event_id)
        rows.append(
            {
                "match_id": m.match_id,
                "event_id": m.event_id,
                "event_name": event.event_name if event else None,
                "event_date": event.event_date.isoformat() if event else None,
                "winner": m.winner,
                "match_result": m.match_result,
                "stipulation": m.match_stipulation,
                "source_url": m.source_url,
                # Cash-in fields intentionally null until a dedicated cash-in source pass
                "cash_in_date": None,
                "cash_in_event": None,
                "cash_in_opponent": None,
                "cash_in_result": None,
                "championship_won": None,
                "verification_status": VerificationStatus.needs_review.value,
            }
        )
    return rows


def extract_survivor_series_rows(
    matches: list[RawMatchRecord],
    participants: list[RawParticipantRecord],
    events_by_id: dict[str, RawEventRecord],
) -> list[dict]:
    by_match = {m.match_id: m for m in matches}
    part_by_match: dict[str, list[RawParticipantRecord]] = {}
    for p in participants:
        part_by_match.setdefault(p.match_id, []).append(p)

    rows = []
    for m in matches:
        stip = (m.match_stipulation or "").lower()
        if m.special_match_kind != "survivor_series" and not (
            "survivor series" in stip or "wargames" in stip or "war games" in stip
        ):
            continue
        event = events_by_id.get(m.event_id)
        members = part_by_match.get(m.match_id, [])
        rows.append(
            {
                "match_id": m.match_id,
                "event_id": m.event_id,
                "event_name": event.event_name if event else None,
                "event_date": event.event_date.isoformat() if event else None,
                "match_format": m.match_stipulation,
                "winning_side": m.winner,
                "losing_side": m.loser,
                "survivors": "; ".join(
                    p.ring_name for p in members if p.result in {"win", "survivor", "winner"}
                )
                or m.winner,
                "participants": "; ".join(p.ring_name for p in members),
                "source_url": m.source_url,
            }
        )
    return rows


def extract_chamber_rows(
    matches: list[RawMatchRecord],
    participants: list[RawParticipantRecord],
    events_by_id: dict[str, RawEventRecord],
) -> list[dict]:
    part_by_match: dict[str, list[RawParticipantRecord]] = {}
    for p in participants:
        part_by_match.setdefault(p.match_id, []).append(p)

    rows = []
    for m in matches:
        stip = (m.match_stipulation or "").lower()
        if m.special_match_kind != "elimination_chamber" and "elimination chamber" not in stip:
            continue
        event = events_by_id.get(m.event_id)
        members = part_by_match.get(m.match_id, [])
        rows.append(
            {
                "match_id": m.match_id,
                "event_id": m.event_id,
                "event_name": event.event_name if event else None,
                "event_date": event.event_date.isoformat() if event else None,
                "winner": m.winner,
                "championship_at_stake": m.match_stipulation if m.is_title_match else None,
                "participants": "; ".join(p.ring_name for p in members) or None,
                "entry_order": None,  # often not in main results table — left null
                "elimination_order": None,
                "starting_competitors": None,
                "source_url": m.source_url,
                "verification_status": VerificationStatus.needs_review.value,
            }
        )
    return rows


def rumble_to_rows(entrants: list[SpecialRumbleEntrant]) -> list[dict]:
    return [e.model_dump(mode="json") for e in entrants]
