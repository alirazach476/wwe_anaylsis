from pathlib import Path

import pandas as pd

from wwe_data.warehouse.cleaning import classify_match_type, coalesce_participants
from wwe_data.warehouse.materialize_marts import materialize_marts


def test_classify_match_type():
    assert classify_match_type("Singles match") == "singles"
    assert classify_match_type("Tag team match") == "tag"
    assert classify_match_type("Royal Rumble match") == "rumble"


def test_coalesce_participants():
    df = pd.DataFrame(
        [
            {"match_id": "m1", "wrestler_id": "w1", "participant_role": "competitor", "result": "win", "entry_number": None},
            {"match_id": "m1", "wrestler_id": "w1", "participant_role": "competitor", "result": None, "entry_number": 24},
        ]
    )
    out = coalesce_participants(df)
    assert len(out) == 1
    assert out.iloc[0]["entry_number"] == 24


def test_marts_exist_after_materialize():
    materialize_marts()
    root = Path("data/warehouse/marts")
    assert (root / "mart_overview.csv").exists()
    assert (root / "mart_wrestler_performance.csv").exists()
    ov = pd.read_csv(root / "mart_overview.csv")
    assert int(ov.iloc[0]["total_matches"]) > 0
