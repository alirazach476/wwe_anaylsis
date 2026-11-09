from datetime import date, datetime

from wwe_data.models.schemas import EventStatus, EventType, RawEventRecord, VerificationStatus
from wwe_data.pipeline.dedupe import merge_event_records
from wwe_data.pipeline.ids import make_event_id


def _rec(name: str, d: date, source: str, venue: str | None = None) -> RawEventRecord:
    return RawEventRecord(
        event_id=make_event_id(d, name),
        event_name=name,
        canonical_event_name=name,
        event_series="Royal Rumble",
        event_year=d.year,
        event_date=d,
        event_type=EventType.ple,
        event_status=EventStatus.completed,
        venue=venue,
        source_url="https://example.com",
        source_name=source,
        verification_status=VerificationStatus.single_source,
        last_updated=datetime.utcnow(),
        collection_timestamp=datetime.utcnow(),
    )


def test_event_id_stable():
    d = date(2000, 1, 23)
    assert make_event_id(d, "Royal Rumble") == make_event_id(d, "Royal Rumble")


def test_dedupe_merges_sources():
    d = date(2000, 1, 23)
    merged = merge_event_records(
        [
            _rec("Royal Rumble", d, "wikipedia_ppv_list", "Madison Square Garden"),
            _rec("Royal Rumble", d, "wikipedia_snme", "Madison Square Garden"),
        ]
    )
    assert len(merged) == 1
    assert merged[0].verification_status == VerificationStatus.verified


def test_dedupe_flags_conflict():
    d = date(2000, 1, 23)
    merged = merge_event_records(
        [
            _rec("Royal Rumble", d, "a", "Venue A"),
            _rec("Royal Rumble", d, "b", "Venue B"),
        ]
    )
    assert merged[0].verification_status == VerificationStatus.conflict
