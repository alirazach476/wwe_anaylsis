from datetime import date

from wwe_data.pipeline.normalize import (
    parse_attendance,
    parse_location,
    parse_wiki_date,
    parse_wiki_end_date,
)


def test_parse_wiki_date():
    assert parse_wiki_date("January 23", 2000) == date(2000, 1, 23)
    assert parse_wiki_date("December 7 (aired December 25)", 2008) == date(2008, 12, 7)
    assert parse_wiki_date("April 18 – April 19", 2026) == date(2026, 4, 18)
    assert parse_wiki_end_date("April 18 – April 19", 2026) == date(2026, 4, 19)


def test_parse_location_and_attendance():
    assert parse_location("New York City, New York") == (
        "New York City",
        "New York",
        "United States",
    )
    assert parse_location("Toronto, Ontario, Canada")[2] == "Canada"
    assert parse_attendance("19,231") == 19231
    assert parse_attendance(None) is None
