"""Clean Crown Jewel 2026 match participants and rematerialize wrestler stats."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRIMARY_EXPORTS = ROOT / "data" / "exports"
RUNTIME_EXPORTS = ROOT / "data" / "warehouse" / "runtime_exports"
MARTS = ROOT / "data" / "warehouse" / "marts"
WRESTLERS = PRIMARY_EXPORTS / "wrestlers.csv"

EVENT_ID = "evt_20261107_crown-jewel_15a43207f1"

# Official results (Wikipedia / WWE, Nov 7 2026)
MATCH_UPDATES = {
    "mtc_85b638dde1f3_1": {
        "match_number": 1,
        "match_type_raw": "Last Man Standing",
        "match_type_group": "other",
        "match_duration_seconds": 1640,
        "is_title_match": 0,
        "is_main_event": 0,
        "winner_name": "Cody Rhodes",
        "loser_name": "Randy Orton",
        "match_result": "Cody Rhodes defeated Randy Orton",
        "special_match_kind": "last_man_standing",
    },
    "mtc_6930c21272ab_2": {
        "match_number": 2,
        "match_type_raw": "Tag team",
        "match_type_group": "tag",
        "match_duration_seconds": 875,
        "is_title_match": 1,
        "is_main_event": 0,
        "winner_name": "Penta & Je'Von Evans",
        "loser_name": "The Vision (Bron Breakker & Austin Theory)",
        "match_result": "Penta and Je'Von Evans defeated The Vision (c) by pinfall",
        "special_match_kind": None,
    },
    "mtc_7df21168e34d_3": {
        "match_number": 3,
        "match_type_raw": "Singles",
        "match_type_group": "singles",
        "match_duration_seconds": 975,
        "is_title_match": 1,
        "is_main_event": 0,
        "winner_name": "Chelsea Green",
        "loser_name": "Liv Morgan",
        "match_result": "Chelsea Green defeated Liv Morgan by pinfall (Women's Crown Jewel Championship)",
        "special_match_kind": "crown_jewel_championship",
    },
    "mtc_d0caa0ecc921_4": {
        "match_number": 4,
        "match_type_raw": "Singles",
        "match_type_group": "singles",
        "match_duration_seconds": 3,
        "is_title_match": 1,
        "is_main_event": 0,
        "winner_name": "Tiffany Stratton",
        "loser_name": "Chelsea Green",
        "match_result": "Tiffany Stratton defeated Chelsea Green (c) by pinfall (MITB cash-in)",
        "special_match_kind": "money_in_the_bank_cash_in",
    },
    "mtc_cba5e608a4ee_5": {
        "match_number": 5,
        "match_type_raw": "Singles",
        "match_type_group": "singles",
        "match_duration_seconds": 1450,
        "is_title_match": 1,
        "is_main_event": 1,
        "winner_name": "Roman Reigns",
        "loser_name": "Sami Zayn",
        "match_result": "Roman Reigns defeated Sami Zayn by pinfall (Crown Jewel Championship)",
        "special_match_kind": "crown_jewel_championship",
    },
}

# Clean competitors per match (managers optional with result=None / role=manager)
PARTICIPANTS: dict[str, list[dict]] = {
    "mtc_85b638dde1f3_1": [
        {"ring_name": "Cody Rhodes", "result": "win", "participant_role": "competitor"},
        {"ring_name": "Randy Orton", "result": "loss", "participant_role": "competitor"},
    ],
    "mtc_6930c21272ab_2": [
        {"ring_name": "Penta", "result": "win", "participant_role": "competitor", "team_id": "team_penta_evans"},
        {"ring_name": "Je'Von Evans", "result": "win", "participant_role": "competitor", "team_id": "team_penta_evans"},
        {"ring_name": "Bron Breakker", "result": "loss", "participant_role": "competitor", "team_id": "team_vision"},
        {"ring_name": "Austin Theory", "result": "loss", "participant_role": "competitor", "team_id": "team_vision"},
        {"ring_name": "Maxxine Dupri", "result": None, "participant_role": "manager", "team_id": "team_vision"},
    ],
    "mtc_7df21168e34d_3": [
        {"ring_name": "Chelsea Green", "result": "win", "participant_role": "competitor"},
        {"ring_name": "Liv Morgan", "result": "loss", "participant_role": "competitor"},
    ],
    "mtc_d0caa0ecc921_4": [
        {"ring_name": "Tiffany Stratton", "result": "win", "participant_role": "competitor"},
        {"ring_name": "Chelsea Green", "result": "loss", "participant_role": "competitor"},
    ],
    "mtc_cba5e608a4ee_5": [
        {"ring_name": "Roman Reigns", "result": "win", "participant_role": "competitor"},
        {"ring_name": "Sami Zayn", "result": "loss", "participant_role": "competitor"},
    ],
}

NAME_ALIASES = {
    "Penta": ["Penta", "Penta El Zero Miedo", "Pentagón Jr.", "Pentagon Jr."],
    "Je'Von Evans": ["Je'Von Evans", "JeVon Evans", "Jevon Evans"],
}


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "unknown"


def _resolve_wrestler_id(name: str, wrestlers: pd.DataFrame, id_by_name: dict[str, str]) -> str:
    aliases = NAME_ALIASES.get(name, [name])
    for alias in aliases:
        if alias in id_by_name:
            return id_by_name[alias]
        hit = wrestlers[wrestlers["canonical_name"].str.casefold() == alias.casefold()]
        if not hit.empty:
            return str(hit.iloc[0]["wrestler_id"])
        hit = wrestlers[wrestlers["canonical_name"].str.contains(re.escape(alias), case=False, na=False)]
        if not hit.empty:
            return str(hit.iloc[0]["wrestler_id"])
    # last resort: stable synthetic id (should not happen for known roster)
    return f"wrs_{_slug(name)}_cj2026"


def rematerialize_wrestler_performance() -> int:
    parts = pd.read_csv(PRIMARY_EXPORTS / "match_participants.csv")
    matches = pd.read_csv(PRIMARY_EXPORTS / "matches.csv")
    # Prefer event year from mart_match_analytics (already joined) when events inventory lacks CJ
    mart_match = pd.read_csv(MARTS / "mart_match_analytics.csv")
    wrestlers = pd.read_csv(WRESTLERS)

    year_map = mart_match.set_index("match_id")["event_year"].to_dict()
    title_map = mart_match.set_index("match_id")["is_title_match"].to_dict()
    main_map = mart_match.set_index("match_id")["is_main_event"].to_dict()
    # overlay matches.csv fields
    for _, r in matches.iterrows():
        mid = r["match_id"]
        if pd.notna(r.get("is_title_match")):
            title_map[mid] = r["is_title_match"]
        if pd.notna(r.get("is_main_event")):
            main_map[mid] = r["is_main_event"]

    wp = parts.copy()
    wp["event_year"] = wp["match_id"].map(year_map)
    wp["is_title_match"] = wp["match_id"].map(title_map)
    wp["is_main_event"] = wp["match_id"].map(main_map)
    def _as_int_flag(series: pd.Series) -> pd.Series:
        mapped = (
            series.astype(str)
            .str.strip()
            .str.lower()
            .map({"true": 1, "1": 1, "yes": 1, "false": 0, "0": 0, "no": 0, "nan": 0, "none": 0})
        )
        return mapped.fillna(0).astype(int)

    # only count competitors in win/loss aggregates
    competitors = wp[wp["participant_role"].fillna("competitor").isin(["competitor", "entrant"])].copy()
    competitors["is_title_match"] = _as_int_flag(competitors["is_title_match"])
    competitors["is_main_event"] = _as_int_flag(competitors["is_main_event"])

    mart = (
        competitors.groupby("wrestler_id", dropna=False)
        .agg(
            matches=("match_id", "nunique"),
            wins=("result", lambda s: int((s == "win").sum())),
            losses=("result", lambda s: int((s == "loss").sum())),
            title_matches=("is_title_match", "sum"),
            main_events=("is_main_event", "sum"),
            first_year=("event_year", "min"),
            last_year=("event_year", "max"),
        )
        .reset_index()
    )
    name_map = wrestlers.set_index("wrestler_id")["canonical_name"].to_dict()
    # fallback to most common ring_name
    ring = (
        competitors.groupby("wrestler_id")["ring_name"]
        .agg(lambda s: s.value_counts().index[0] if len(s) else None)
        .to_dict()
    )
    mart["canonical_name"] = mart["wrestler_id"].map(lambda i: name_map.get(i) or ring.get(i) or i)
    mart["win_pct"] = mart.apply(
        lambda r: round(r["wins"] / (r["wins"] + r["losses"]), 4) if (r["wins"] + r["losses"]) > 0 else None,
        axis=1,
    )
    mart["career_span_years"] = mart["last_year"] - mart["first_year"]
    # preserve wrestler_key if present in existing mart
    existing = pd.read_csv(MARTS / "mart_wrestler_performance.csv")
    if "wrestler_key" in existing.columns:
        key_map = existing.set_index("wrestler_id")["wrestler_key"].to_dict()
        next_key = int(pd.to_numeric(existing["wrestler_key"], errors="coerce").max() or 0) + 1
        keys = []
        for wid in mart["wrestler_id"]:
            if wid in key_map and pd.notna(key_map[wid]):
                keys.append(int(key_map[wid]))
            else:
                keys.append(next_key)
                next_key += 1
        mart["wrestler_key"] = keys
        cols = [
            "wrestler_key",
            "wrestler_id",
            "canonical_name",
            "matches",
            "wins",
            "losses",
            "title_matches",
            "main_events",
            "first_year",
            "last_year",
            "win_pct",
            "career_span_years",
        ]
        mart = mart[cols]
    mart = mart.sort_values("matches", ascending=False)
    mart.to_csv(MARTS / "mart_wrestler_performance.csv", index=False)
    return len(mart)


def update_match_analytics() -> None:
    mart_path = MARTS / "mart_match_analytics.csv"
    if not mart_path.exists():
        return
    mart = pd.read_csv(mart_path)
    for mid, upd in MATCH_UPDATES.items():
        mask = mart["match_id"] == mid
        if not mask.any():
            continue
        for k, v in upd.items():
            if k in mart.columns:
                mart.loc[mask, k] = v
        mart.loc[mask, "event_id"] = EVENT_ID
        mart.loc[mask, "event_name"] = "Crown Jewel"
        mart.loc[mask, "event_series"] = "Crown Jewel"
        mart.loc[mask, "event_year"] = 2026
        mart.loc[mask, "event_date"] = "2026-11-07"
        mart.loc[mask, "match_status"] = "completed"
    mart.to_csv(mart_path, index=False)


def main() -> None:
    wrestlers = pd.read_csv(WRESTLERS)
    id_by_name = {
        str(r["canonical_name"]): str(r["wrestler_id"])
        for _, r in wrestlers.iterrows()
        if pd.notna(r.get("canonical_name"))
    }

    matches = pd.read_csv(PRIMARY_EXPORTS / "matches.csv")
    parts = pd.read_csv(PRIMARY_EXPORTS / "match_participants.csv")

    # Update match metadata
    for mid, upd in MATCH_UPDATES.items():
        mask = matches["match_id"] == mid
        if not mask.any():
            print(f"WARN missing match {mid}")
            continue
        for k, v in upd.items():
            if k in matches.columns:
                matches.loc[mask, k] = v
        matches.loc[mask, "event_id"] = EVENT_ID
        matches.loc[mask, "match_status"] = "completed"

    # Replace participants for these matches
    parts = parts[~parts["match_id"].isin(PARTICIPANTS.keys())].copy()
    template_cols = list(parts.columns)
    new_rows: list[dict] = []
    for mid, plist in PARTICIPANTS.items():
        for p in plist:
            wid = _resolve_wrestler_id(p["ring_name"], wrestlers, id_by_name)
            row = {c: None for c in template_cols}
            row["match_id"] = mid
            row["wrestler_id"] = wid
            row["ring_name"] = p["ring_name"]
            row["participant_role"] = p.get("participant_role", "competitor")
            row["result"] = p.get("result")
            row["team_id"] = p.get("team_id")
            new_rows.append(row)
            print(f"  {mid}: {p['ring_name']} -> {wid} ({p.get('result')})")

    parts = pd.concat([parts, pd.DataFrame(new_rows)], ignore_index=True)
    matches.to_csv(PRIMARY_EXPORTS / "matches.csv", index=False)
    parts.to_csv(PRIMARY_EXPORTS / "match_participants.csv", index=False)
    # Keep serverless bundle in sync (API falls back here when needed)
    RUNTIME_EXPORTS.mkdir(parents=True, exist_ok=True)
    parts.to_csv(RUNTIME_EXPORTS / "match_participants.csv", index=False)

    update_match_analytics()
    n = rematerialize_wrestler_performance()
    print(f"Updated CJ 2026 participants; rematerialized mart_wrestler_performance ({n} wrestlers)")


if __name__ == "__main__":
    main()
