from datetime import date

from wwe_data.pipeline.eligibility import EligibilityFilter


def test_excludes_weekly_and_nxt_takeover():
    f = EligibilityFilter()
    assert f.is_excluded("NXT TakeOver: Brooklyn")
    assert f.is_excluded("TakeOver: Brooklyn")
    assert f.is_excluded("Stand & Deliver", event_date=date(2025, 4, 19))
    assert f.is_excluded("Raw")
    assert f.is_excluded("SmackDown")
    assert f.is_excluded("NXT Stand & Deliver")
    # Historical Battleground kept; modern NXT Battleground dropped
    assert not f.is_excluded("Battleground", event_date=date(2015, 7, 19))
    assert f.is_excluded("Battleground", event_date=date(2025, 5, 25))


def test_allows_snme_and_tribute():
    f = EligibilityFilter()
    assert f.is_allowlisted("Saturday Night's Main Event XXXVII")
    assert f.is_allowlisted("Tribute to the Troops")
    assert f.is_eligible(
        "Saturday Night's Main Event XXXVII", date(2024, 12, 14), force_include=True
    )


def test_window():
    f = EligibilityFilter()
    assert f.in_window(date(2000, 1, 23))
    assert f.in_window(date(2027, 12, 31))
    assert not f.in_window(date(1999, 12, 31))
    assert not f.in_window(date(2028, 1, 1))
