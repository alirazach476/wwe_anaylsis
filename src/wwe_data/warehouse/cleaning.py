"""Clean exports into data/warehouse without modifying originals."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from wwe_data.config import get_settings

MATCH_TYPE_TAXONOMY = {
    "singles": re.compile(r"\bsingles\b", re.I),
    "tag": re.compile(r"\btag\b|\btrio\b|\bsix[- ]man\b|\beight[- ]man\b", re.I),
    "triple_threat": re.compile(r"triple[- ]threat|fatal[- ]four|fatal 4", re.I),
    "ladder": re.compile(r"\bladder\b", re.I),
    "cage": re.compile(r"steel cage|hell in a cell|elimination chamber|war ?games", re.I),
    "rumble": re.compile(r"royal rumble", re.I),
    "other": None,
}


def classify_match_type(stip: str | None, match_type: str | None = None) -> str:
    text = f"{stip or ''} {match_type or ''}"
    for name, pattern in MATCH_TYPE_TAXONOMY.items():
        if pattern is None:
            continue
        if pattern.search(text):
            return name
    return "other"


def normalize_championship_name(name: str | None) -> str | None:
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return None
    text = re.sub(r"\[[^\]]*\]", "", str(name))
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("WWF", "WWE")  # branding normalization only
    return text or None


def coalesce_participants(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ("entry_number", "elimination_order", "time_in_match_seconds"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    keys = ["match_id", "wrestler_id", "participant_role"]
    if not all(k in out.columns for k in keys):
        return out

    def _merge_group(g: pd.DataFrame) -> pd.Series:
        row = g.iloc[0].copy()
        for col in g.columns:
            if col in keys:
                continue
            vals = g[col].dropna()
            if len(vals) == 0:
                continue
            # Prefer non-null richer fields: first non-null after sorting by completeness
            row[col] = vals.iloc[0]
        # Explicit numeric preference: max entry/elim when present
        for col in ("entry_number", "elimination_order", "time_in_match_seconds"):
            if col in g.columns and g[col].notna().any():
                row[col] = g[col].max()
        if "result" in g.columns and g["result"].notna().any():
            # prefer win/loss labels over blank
            ranked = g["result"].dropna()
            row["result"] = ranked.iloc[0]
        return row

    return out.groupby(keys, as_index=False, dropna=False).apply(_merge_group).reset_index(drop=True)


def _write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    try:
        df.to_parquet(path.with_suffix(".parquet"), index=False)
    except Exception:
        pass


def clean_to_warehouse(exports_dir: Path | None = None, out_dir: Path | None = None) -> dict[str, int]:
    settings = get_settings()
    exports = exports_dir or settings.exports_dir
    out = out_dir or (settings.data_dir / "warehouse")
    out.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}

    events = pd.read_csv(exports / "events_inventory.csv")
    events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")
    events["event_end_date"] = pd.to_datetime(events["event_end_date"], errors="coerce")
    events["attendance"] = pd.to_numeric(events["attendance"], errors="coerce")
    # Preserve null attendance — never fill with 0
    _write(events, out / "stg_events.csv")
    counts["stg_events"] = len(events)

    matches = pd.read_csv(exports / "matches.csv")
    matches["match_number"] = pd.to_numeric(matches["match_number"], errors="coerce")
    matches["match_duration_seconds"] = pd.to_numeric(
        matches["match_duration_seconds"], errors="coerce"
    )
    matches["match_type_group"] = [
        classify_match_type(s, t)
        for s, t in zip(matches.get("match_stipulation"), matches.get("match_type"))
    ]
    _write(matches, out / "stg_matches.csv")
    counts["stg_matches"] = len(matches)

    parts = pd.read_csv(exports / "match_participants.csv")
    before = len(parts)
    parts = coalesce_participants(parts)
    counts["participants_deduped"] = before - len(parts)
    _write(parts, out / "stg_match_participants.csv")
    counts["stg_match_participants"] = len(parts)

    wrestlers = pd.read_csv(exports / "wrestlers.csv")
    _write(wrestlers, out / "stg_wrestlers.csv")
    counts["stg_wrestlers"] = len(wrestlers)

    aliases = pd.read_csv(exports / "wrestler_aliases.csv")
    _write(aliases, out / "stg_wrestler_aliases.csv")
    counts["stg_wrestler_aliases"] = len(aliases)

    champs = pd.read_csv(exports / "championships.csv")
    champs["championship_name_norm"] = champs["championship_name"].map(normalize_championship_name)
    _write(champs, out / "stg_championships.csv")
    counts["stg_championships"] = len(champs)

    mc = pd.read_csv(exports / "match_championships.csv")
    _write(mc, out / "stg_match_championships.csv")
    counts["stg_match_championships"] = len(mc)

    for name in (
        "special_royal_rumble",
        "special_money_in_the_bank",
        "special_mitb_cash_ins",
        "special_survivor_series",
        "special_elimination_chamber",
        "event_match_status",
    ):
        path = exports / f"{name}.csv"
        if path.exists():
            df = pd.read_csv(path)
            _write(df, out / f"stg_{name}.csv")
            counts[f"stg_{name}"] = len(df)

    stamp = {
        "cleaned_at": datetime.utcnow().isoformat() + "Z",
        "source": str(exports),
        "output": str(out),
        "counts": counts,
        "policy": {
            "raw_exports_immutable": True,
            "null_attendance_preserved": True,
            "zero_distinct_from_null": True,
        },
    }
    (out / "cleaning_stamp.json").write_text(json.dumps(stamp, indent=2), encoding="utf-8")
    return counts
