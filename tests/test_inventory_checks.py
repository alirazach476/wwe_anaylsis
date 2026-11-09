from datetime import date, datetime

from wwe_data.models.schemas import EventStatus, EventType, RawEventRecord, VerificationStatus
from wwe_data.pipeline.ids import make_event_id
from wwe_data.validation.inventory_checks import (
    assert_dates_in_window,
    assert_no_nxt_takeover,
    assert_unique_event_ids,
)


def test_inventory_checks_pass_on_clean_set():
    d = date(2015, 3, 29)
    records = [
        RawEventRecord(
            event_id=make_event_id(d, "WrestleMania 31"),
            event_name="WrestleMania 31",
            canonical_event_name="WrestleMania (2015)",
            event_series="WrestleMania",
            event_year=2015,
            event_date=d,
            event_type=EventType.ple,
            event_status=EventStatus.completed,
            source_url="https://example.com",
            source_name="test",
            verification_status=VerificationStatus.single_source,
            last_updated=datetime.utcnow(),
            collection_timestamp=datetime.utcnow(),
        )
    ]
    assert_unique_event_ids(records)
    assert_dates_in_window(records)
    assert_no_nxt_takeover(records)
