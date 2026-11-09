"""Inventory integrity checks used by tests and coverage."""

from __future__ import annotations

from wwe_data.models.schemas import RawEventRecord


def assert_unique_event_ids(records: list[RawEventRecord]) -> None:
    ids = [r.event_id for r in records]
    assert len(ids) == len(set(ids)), "Duplicate event_id values found"


def assert_dates_in_window(
    records: list[RawEventRecord], start_year: int = 2000, end_year: int = 2027
) -> None:
    for r in records:
        assert start_year <= r.event_year <= end_year
        assert start_year <= r.event_date.year <= end_year


def assert_no_nxt_takeover(records: list[RawEventRecord]) -> None:
    for r in records:
        assert "takeover" not in r.event_name.lower()
