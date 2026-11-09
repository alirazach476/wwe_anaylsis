from wwe_data.collectors.wikipedia_mitb_cashins import (
    enrich_mitb_winner_rows,
    parse_cash_in_tables,
)

SAMPLE_HTML = """
<table class="wikitable">
<tr><th>No.</th><th>Case Holder</th><th>Championship</th><th>Date</th>
<th>Location</th><th>Event</th><th>Results</th></tr>
<tr>
<td>1</td><td>Edge</td><td>WWE Championship</td><td>January 8, 2006</td>
<td>Albany, NY</td><td>New Year's Revolution</td>
<td>Defeated John Cena after two Spears to win the championship.</td>
</tr>
<tr>
<td>2</td><td>Rob Van Dam</td><td>WWE Championship</td><td>June 11, 2006</td>
<td>New York, NY</td><td>ECW One Night Stand</td>
<td>Defeated John Cena to win the championship.</td>
</tr>
</table>
"""


def test_parse_cash_in_tables():
    rows = parse_cash_in_tables(SAMPLE_HTML)
    assert len(rows) == 2
    assert rows[0]["case_holder"] == "Edge"
    assert rows[0]["cash_in_date"] == "2006-01-08"
    assert rows[0]["cash_in_outcome"] == "successful"
    assert rows[0]["cash_in_opponent"] == "John Cena"


def test_enrich_matches_winner_chronologically():
    mitb = [
        {
            "match_id": "m1",
            "winner": "Edge",
            "event_date": "2005-04-03",
            "cash_in_date": None,
        }
    ]
    cash = parse_cash_in_tables(SAMPLE_HTML)
    out = enrich_mitb_winner_rows(mitb, cash)
    assert out[0]["cash_in_date"] == "2006-01-08"
    assert out[0]["cash_in_event"] == "New Year's Revolution"
    assert out[0]["verification_status"] == "verified"


def test_unsuccessful_cash_in_detection():
    html = """
    <table class="wikitable">
    <tr><th>No.</th><th>Case Holder</th><th>Championship</th><th>Date</th>
    <th>Location</th><th>Event</th><th>Results</th></tr>
    <tr><td>1</td><td>Damien Sandow</td><td>World Heavyweight Championship</td>
    <td>October 28, 2013</td><td>Orlando, FL</td><td>Raw</td>
    <td>Sandow was defeated by defending champion John Cena after an Attitude Adjustment.</td>
    </tr>
    </table>
    """
    rows = parse_cash_in_tables(html)
    assert rows[0]["cash_in_outcome"] == "unsuccessful"
    assert rows[0]["championship_won"] is None
    assert "John Cena" in (rows[0]["cash_in_opponent"] or "")
