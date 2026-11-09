"""Add Dominik vs Cena IC match (Raw 2025-11-10) and print helper info."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "data" / "exports"
MARTS = ROOT / "data" / "warehouse" / "marts"

EVENT_ID = "evt_20251110_raw_dominik-vs-cena-ic_a1b2c3d4"
MATCH_ID = "mtc_raw_20251110_dominik_cena_ic_01"
EVENT_DATE = "2025-11-10"
EVENT_NAME = "Raw"
EVENT_SERIES = "Raw"


def _wid(w: pd.DataFrame, name: str) -> str | None:
    exact = w[w["canonical_name"].astype(str) == name]
    if not exact.empty:
        return str(exact.iloc[0]["wrestler_id"])
    # Prefer clean single-name rows
    hit = w[w["canonical_name"].astype(str).str.fullmatch(name, case=False, na=False)]
    if not hit.empty:
        return str(hit.iloc[0]["wrestler_id"])
    return None


def main() -> None:
    w = pd.read_csv(EXPORTS / "wrestlers.csv")
    cena = _wid(w, "John Cena") or "wrs_john-cena_43142eec"
    # Prefer Dirty Dominik if present
    dirty = w[w["canonical_name"].astype(str).str.contains(r'Dominik Mysterio', case=False, na=False)]
    dirty = dirty[~dirty["canonical_name"].astype(str).str.contains(r"\(|with|and |\)", case=False, na=False)]
    dominik = (
        _wid(w, '"Dirty" Dominik Mysterio')
        or _wid(w, "Dominik Mysterio")
        or (str(dirty.iloc[0]["wrestler_id"]) if len(dirty) else "wrs_dirty-dominik-mysterio_6db57b9d")
    )
    print("cena", cena, "dominik", dominik)

    mc = pd.read_csv(EXPORTS / "match_championships.csv")
    ic_ids = (
        mc[mc["championship_id"].astype(str).str.contains("intercontinental", case=False, na=False)][
            "championship_id"
        ]
        .value_counts()
    )
    ic_id = str(ic_ids.index[0]) if len(ic_ids) else "chp_wwe-intercontinental-championship"
    # Prefer modern WWE IC if present
    for cand in ic_ids.index.astype(str):
        if "wwe-intercontinental" in cand.lower() or cand.lower().startswith("chp_wwe"):
            if "intercontinental" in cand.lower() and "undisputed" not in cand.lower() and "and-" not in cand.lower():
                ic_id = cand
                break
    print("ic", ic_id)

    # --- mart_event_analytics ---
    ev = pd.read_csv(MARTS / "mart_event_analytics.csv")
    if (ev["event_id"] == EVENT_ID).any():
        print("event already exists")
    else:
        max_key = int(pd.to_numeric(ev["event_key"], errors="coerce").max() or 0)
        row = {
            "event_key": max_key + 1,
            "event_id": EVENT_ID,
            "event_name": EVENT_NAME,
            "canonical_event_name": "Raw (November 10, 2025)",
            "event_series": EVENT_SERIES,
            "event_year": 2025,
            "event_date": EVENT_DATE,
            "event_end_date": None,
            "event_type": "weekly",
            "event_status": "completed",
            "venue_key": None,
            "country_key": None,
            "brand_key": None,
            "date_key": None,
            "attendance": None,
            "verification_status": "manual",
            "matches": 1,
            "title_matches": 1,
            "main_events": 1,
            "avg_duration": None,
            "country": "United States",
            "venue_name": None,
            "city": None,
        }
        # Align columns
        for c in ev.columns:
            if c not in row:
                row[c] = None
        ev = pd.concat([ev, pd.DataFrame([{c: row.get(c) for c in ev.columns}])], ignore_index=True)
        ev.to_csv(MARTS / "mart_event_analytics.csv", index=False)
        print("added event", EVENT_ID)

    # --- mart_match_analytics ---
    mm = pd.read_csv(MARTS / "mart_match_analytics.csv")
    if (mm["match_id"] == MATCH_ID).any():
        print("match already exists in mart")
    else:
        max_key = int(pd.to_numeric(mm["match_key"], errors="coerce").max() or 0)
        event_key = int(ev.loc[ev["event_id"] == EVENT_ID, "event_key"].iloc[0])
        mrow = {
            "match_key": max_key + 1,
            "match_id": MATCH_ID,
            "event_key": event_key,
            "match_type_key": None,
            "match_number": 1,
            "match_duration_seconds": None,
            "winner_name": None,  # unknown / not specified
            "loser_name": None,
            "is_title_match": 1,
            "is_main_event": 1,
            "is_preshow": 0,
            "match_status": "completed",
            "special_match_kind": "intercontinental_championship",
            "match_result": "Intercontinental Champion Dominik Mysterio vs. John Cena",
            "event_id": EVENT_ID,
            "event_name": EVENT_NAME,
            "event_series": EVENT_SERIES,
            "event_year": 2025,
            "event_date": EVENT_DATE,
            "match_type_group": "singles",
            "match_type_raw": "singles",
        }
        for c in mm.columns:
            if c not in mrow:
                mrow[c] = None
        mm = pd.concat([mm, pd.DataFrame([{c: mrow.get(c) for c in mm.columns}])], ignore_index=True)
        mm.to_csv(MARTS / "mart_match_analytics.csv", index=False)
        print("added mart match", MATCH_ID)

    # --- exports: matches ---
    matches_path = EXPORTS / "matches.csv"
    matches = pd.read_csv(matches_path)
    if (matches["match_id"] == MATCH_ID).any():
        print("matches.csv already has match")
    else:
        mexp = {
            "match_id": MATCH_ID,
            "event_id": EVENT_ID,
            "match_number": 1,
            "match_name": "Intercontinental Championship",
            "match_type": "singles",
            "match_stipulation": "Intercontinental Championship",
            "match_duration_seconds": None,
            "match_result": "Intercontinental Champion Dominik Mysterio vs. John Cena",
            "winner": None,
            "loser": None,
            "is_title_match": True,
            "is_main_event": True,
            "is_preshow": False,
            "match_status": "completed",
            "source_url": None,
            "verification_status": "manual",
            "special_match_kind": "intercontinental_championship",
        }
        for c in matches.columns:
            if c not in mexp:
                mexp[c] = None
        matches = pd.concat([matches, pd.DataFrame([{c: mexp.get(c) for c in matches.columns}])], ignore_index=True)
        matches.to_csv(matches_path, index=False)
        print("added matches.csv")

    # participants
    parts_path = EXPORTS / "match_participants.csv"
    parts = pd.read_csv(parts_path)
    parts = parts[parts["match_id"] != MATCH_ID]
    new_parts = pd.DataFrame(
        [
            {
                "match_id": MATCH_ID,
                "wrestler_id": dominik,
                "ring_name": "Dominik Mysterio",
                "team_id": None,
                "participant_role": "competitor",
                "result": None,
                "entry_number": None,
                "elimination_order": None,
                "eliminated_by": None,
                "time_in_match_seconds": None,
            },
            {
                "match_id": MATCH_ID,
                "wrestler_id": cena,
                "ring_name": "John Cena",
                "team_id": None,
                "participant_role": "competitor",
                "result": None,
                "entry_number": None,
                "elimination_order": None,
                "eliminated_by": None,
                "time_in_match_seconds": None,
            },
        ]
    )
    parts = pd.concat([parts, new_parts], ignore_index=True)
    parts.to_csv(parts_path, index=False)
    print("participants", len(new_parts))

    # championships
    ch_path = EXPORTS / "match_championships.csv"
    ch = pd.read_csv(ch_path)
    ch = ch[ch["match_id"] != MATCH_ID]
    new_ch = pd.DataFrame(
        [
            {
                "match_id": MATCH_ID,
                "championship_id": ic_id,
                "champion_before": "Dominik Mysterio",
                "champion_after": None,
                "title_change": False,
                "title_retained": False,
                "title_vacated": False,
            }
        ]
    )
    ch = pd.concat([ch, new_ch], ignore_index=True)
    ch.to_csv(ch_path, index=False)
    print("championship linked", ic_id)

    # events export if present
    events_path = EXPORTS / "events.csv"
    if events_path.exists():
        events = pd.read_csv(events_path)
        if "event_id" in events.columns and not (events["event_id"] == EVENT_ID).any():
            erow = {c: None for c in events.columns}
            erow.update(
                {
                    "event_id": EVENT_ID,
                    "event_name": EVENT_NAME,
                    "event_series": EVENT_SERIES,
                    "event_year": 2025,
                    "event_date": EVENT_DATE,
                    "event_type": "weekly",
                    "event_status": "completed",
                }
            )
            # fill known cols only
            for k in list(erow.keys()):
                if k not in events.columns:
                    del erow[k]
            events = pd.concat([events, pd.DataFrame([erow])], ignore_index=True)
            events.to_csv(events_path, index=False)
            print("events.csv updated")

    print("DONE", EVENT_ID, MATCH_ID)


if __name__ == "__main__":
    main()
