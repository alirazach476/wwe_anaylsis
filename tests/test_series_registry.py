from wwe_data.pipeline.series import SeriesRegistry


def test_registry_matches_core_series():
    reg = SeriesRegistry()
    assert reg.match("WrestleMania 40").canonical_name == "WrestleMania"
    assert reg.match("Royal Rumble 2008").series_id == "royal_rumble"
    assert reg.match("Money in the Bank").special_data == "money_in_the_bank"
    assert reg.match("Saturday Night's Main Event XLII").canonical_name == (
        "Saturday Night's Main Event"
    )
    assert reg.match("TLC: Tables, Ladders & Chairs").canonical_name == "TLC"
    assert reg.match("Clash in Paris").canonical_name == "Clash in Paris"


def test_registry_is_expandable():
    reg = SeriesRegistry()
    names = reg.all_canonical_names()
    assert "WrestleMania" in names
    assert "Tribute to the Troops" in names
    assert len(reg.required_series_ids()) > 20
