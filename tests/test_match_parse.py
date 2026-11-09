from wwe_data.pipeline.match_parse import (
    detect_title_match,
    is_results_footnote,
    parse_duration_to_seconds,
    parse_match_result_text,
)


def test_parse_duration():
    assert parse_duration_to_seconds("3:16") == 196
    assert parse_duration_to_seconds("1:10:17") == 4217
    assert parse_duration_to_seconds("—") is None


def test_parse_result_defeated():
    parsed = parse_match_result_text(
        "Tazz defeated Kurt Angle by technical submission"
    )
    assert parsed["winner"] == "Tazz"
    assert "Kurt Angle" in (parsed["loser"] or "")
    assert parsed["outcome"] == "win"


def test_title_detection():
    assert detect_title_match(
        "Triple threat match for the Undisputed WWF Intercontinental Championship"
    )
    assert not detect_title_match("Singles match")


def test_results_footnotes_filtered():
    assert is_results_footnote("(c)")
    assert is_results_footnote("– the champion(s) heading into the match")
    assert is_results_footnote("– this was a dark match")
    assert is_results_footnote("– the match was broadcast on the pre-show")
    assert not is_results_footnote(
        "Tazz defeated Kurt Angle by technical submission"
    )
