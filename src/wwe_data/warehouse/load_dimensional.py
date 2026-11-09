"""Load cleaned warehouse CSVs into dimensional tables (SQLite or Postgres)."""

from __future__ import annotations

import argparse
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console
from sqlalchemy import create_engine, text

from wwe_data.config import get_settings
from wwe_data.warehouse.cleaning import clean_to_warehouse

console = Console()


def _default_url() -> str:
    settings = get_settings()
    path = settings.processed_dir / "wwe_analytics.sqlite"
    return f"sqlite:///{path.as_posix()}"


def _read_wh(name: str) -> pd.DataFrame:
    settings = get_settings()
    path = settings.data_dir / "warehouse" / f"{name}.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _exec_sql_file(engine, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    # SQLite does not support schemas the same way — rewrite for sqlite
    if engine.dialect.name == "sqlite":
        sql = sql.replace("CREATE SCHEMA IF NOT EXISTS staging;", "")
        sql = sql.replace("CREATE SCHEMA IF NOT EXISTS analytics;", "")
        sql = sql.replace("analytics.", "")
        sql = sql.replace("SERIAL", "INTEGER")
        # Remove REFERENCES for simpler sqlite bootstrap when order varies
    with engine.begin() as conn:
        for stmt in sql.split(";"):
            s = stmt.strip()
            if s:
                try:
                    conn.execute(text(s))
                except Exception as exc:
                    # ignore duplicate / unsupported bits on sqlite
                    if engine.dialect.name != "sqlite":
                        raise
                    console.print(f"[yellow]sqlite skip[/yellow]: {exc}")


def _date_key(d) -> int | None:
    ts = pd.to_datetime(d, errors="coerce")
    if pd.isna(ts):
        return None
    return int(ts.strftime("%Y%m%d"))


def load_dimensional(database_url: str | None = None) -> dict[str, int]:
    clean_to_warehouse()
    url = database_url or _default_url()
    engine = create_engine(url, future=True)
    schema_path = Path(__file__).resolve().parents[1] / "db" / "warehouse_schema.sql"
    _exec_sql_file(engine, schema_path)

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    started = datetime.utcnow()
    counts: dict[str, int] = {}

    events = _read_wh("stg_events")
    matches = _read_wh("stg_matches")
    parts = _read_wh("stg_match_participants")
    wrestlers = _read_wh("stg_wrestlers")
    champs = _read_wh("stg_championships")
    mc = _read_wh("stg_match_championships")
    rumble = _read_wh("stg_special_royal_rumble")
    mitb = _read_wh("stg_special_money_in_the_bank")
    survivor = _read_wh("stg_special_survivor_series")

    # dim_date
    dates = pd.to_datetime(events["event_date"], errors="coerce").dropna().unique()
    dim_date = pd.DataFrame({"full_date": pd.to_datetime(dates)})
    dim_date["date_key"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["day"] = dim_date["full_date"].dt.day
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["decade"] = (dim_date["year"] // 10) * 10
    dim_date.to_sql("dim_date", engine, if_exists="replace", index=False)
    counts["dim_date"] = len(dim_date)

    # dim_country
    countries = (
        events[["country"]]
        .dropna()
        .drop_duplicates()
        .rename(columns={"country": "country_name"})
    )
    countries.insert(0, "country_key", range(1, len(countries) + 1))
    countries.to_sql("dim_country", engine, if_exists="replace", index=False)
    country_map = dict(zip(countries["country_name"], countries["country_key"]))
    counts["dim_country"] = len(countries)

    # dim_venue
    venues = events[["venue", "city", "state_province", "country"]].copy()
    venues = venues.rename(
        columns={"venue": "venue_name", "country": "country_name"}
    ).drop_duplicates()
    venues.insert(0, "venue_key", range(1, len(venues) + 1))
    venues.to_sql("dim_venue", engine, if_exists="replace", index=False)
    venue_map = {
        (r.venue_name if pd.notna(r.venue_name) else None, r.city, r.country_name): r.venue_key
        for r in venues.itertuples()
    }
    counts["dim_venue"] = len(venues)

    # dim_brand
    brands = events[["brand"]].copy()
    brands["brand_name"] = brands["brand"].fillna("Unknown")
    brands = brands[["brand_name"]].drop_duplicates()
    brands.insert(0, "brand_key", range(1, len(brands) + 1))
    brands.to_sql("dim_brand", engine, if_exists="replace", index=False)
    brand_map = dict(zip(brands["brand_name"], brands["brand_key"]))
    counts["dim_brand"] = len(brands)

    # dim_team placeholder
    dim_team = pd.DataFrame(
        [{"team_key": 1, "team_id": None, "team_name": "Unknown"}]
    )
    dim_team.to_sql("dim_team", engine, if_exists="replace", index=False)
    counts["dim_team"] = 1

    # dim_match_type
    mt = matches[["match_type_group"]].drop_duplicates() if "match_type_group" in matches.columns else pd.DataFrame({"match_type_group": ["other"]})
    mt = mt.dropna()
    mt.insert(0, "match_type_key", range(1, len(mt) + 1))
    mt["match_type_raw"] = mt["match_type_group"]
    mt.to_sql("dim_match_type", engine, if_exists="replace", index=False)
    mt_map = dict(zip(mt["match_type_group"], mt["match_type_key"]))
    counts["dim_match_type"] = len(mt)

    # dim_championship
    dim_c = champs.copy()
    dim_c.insert(0, "championship_key", range(1, len(dim_c) + 1))
    keep = [
        "championship_key",
        "championship_id",
        "championship_name",
        "championship_name_norm",
        "championship_category",
        "introduction_date",
        "retirement_date",
    ]
    for c in keep:
        if c not in dim_c.columns:
            dim_c[c] = None
    dim_c[keep].to_sql("dim_championship", engine, if_exists="replace", index=False)
    champ_map = dict(zip(dim_c["championship_id"], dim_c["championship_key"]))
    counts["dim_championship"] = len(dim_c)

    # dim_wrestler
    dim_w = wrestlers.copy()
    dim_w.insert(0, "wrestler_key", range(1, len(dim_w) + 1))
    wkeep = [
        "wrestler_key",
        "wrestler_id",
        "canonical_name",
        "debut_date",
        "retirement_date",
        "nationality",
    ]
    for c in wkeep:
        if c not in dim_w.columns:
            dim_w[c] = None
    dim_w[wkeep].to_sql("dim_wrestler", engine, if_exists="replace", index=False)
    wrestler_map = dict(zip(dim_w["wrestler_id"], dim_w["wrestler_key"]))
    counts["dim_wrestler"] = len(dim_w)

    # dim_event
    dim_e = events.copy()
    dim_e.insert(0, "event_key", range(1, len(dim_e) + 1))
    dim_e["date_key"] = dim_e["event_date"].map(_date_key)
    dim_e["country_key"] = dim_e["country"].map(country_map)
    dim_e["brand_key"] = dim_e["brand"].fillna("Unknown").map(brand_map)
    dim_e["venue_key"] = [
        venue_map.get(
            (v if pd.notna(v) else None, c, co),
            None,
        )
        for v, c, co in zip(dim_e["venue"], dim_e["city"], dim_e["country"])
    ]
    ekeep = [
        "event_key",
        "event_id",
        "event_name",
        "canonical_event_name",
        "event_series",
        "event_year",
        "event_date",
        "event_end_date",
        "event_type",
        "event_status",
        "venue_key",
        "country_key",
        "brand_key",
        "date_key",
        "attendance",
        "verification_status",
    ]
    dim_e[ekeep].to_sql("dim_event", engine, if_exists="replace", index=False)
    event_map = dict(zip(dim_e["event_id"], dim_e["event_key"]))
    counts["dim_event"] = len(dim_e)

    # fact_matches
    fm = matches.copy()
    fm.insert(0, "match_key", range(1, len(fm) + 1))
    fm["event_key"] = fm["event_id"].map(event_map)
    fm["match_type_key"] = fm.get("match_type_group", pd.Series(dtype=object)).map(mt_map)
    fm["winner_name"] = fm["winner"]
    fm["loser_name"] = fm["loser"]
    fkeep = [
        "match_key",
        "match_id",
        "event_key",
        "match_type_key",
        "match_number",
        "match_duration_seconds",
        "winner_name",
        "loser_name",
        "is_title_match",
        "is_main_event",
        "is_preshow",
        "match_status",
        "special_match_kind",
        "match_result",
    ]
    for c in fkeep:
        if c not in fm.columns:
            fm[c] = None
    fm[fkeep].to_sql("fact_matches", engine, if_exists="replace", index=False)
    match_map = dict(zip(fm["match_id"], fm["match_key"]))
    counts["fact_matches"] = len(fm)

    # fact_match_participants
    fp = parts.copy()
    fp["match_key"] = fp["match_id"].map(match_map)
    fp["wrestler_key"] = fp["wrestler_id"].map(wrestler_map)
    fp["team_key"] = 1
    fp.insert(0, "fact_id", range(1, len(fp) + 1))
    pkeep = [
        "fact_id",
        "match_key",
        "wrestler_key",
        "team_key",
        "participant_role",
        "result",
        "entry_number",
        "elimination_order",
        "eliminated_by",
        "time_in_match_seconds",
    ]
    for c in pkeep:
        if c not in fp.columns:
            fp[c] = None
    fp = fp.dropna(subset=["match_key", "wrestler_key"])
    fp[pkeep].to_sql("fact_match_participants", engine, if_exists="replace", index=False)
    counts["fact_match_participants"] = len(fp)

    # fact_championship_changes
    if not mc.empty:
        fc = mc.copy()
        fc["match_key"] = fc["match_id"].map(match_map)
        fc["championship_key"] = fc["championship_id"].map(champ_map)
        mid_to_eid = dict(zip(matches["match_id"], matches["event_id"]))
        fc["event_key"] = fc["match_id"].map(mid_to_eid).map(event_map)
        fc.insert(0, "fact_id", range(1, len(fc) + 1))
        ckeep = [
            "fact_id",
            "match_key",
            "championship_key",
            "event_key",
            "champion_after",
            "title_change",
            "title_retained",
            "title_vacated",
        ]
        for c in ckeep:
            if c not in fc.columns:
                fc[c] = None
        fc = fc.dropna(subset=["match_key", "championship_key"])
        fc[ckeep].to_sql("fact_championship_changes", engine, if_exists="replace", index=False)
        counts["fact_championship_changes"] = len(fc)

    # fact_royal_rumble
    if not rumble.empty:
        fr = rumble.copy()
        fr["match_key"] = fr["match_id"].map(match_map)
        fr["event_key"] = fr["event_id"].map(event_map)
        fr["wrestler_key"] = fr["wrestler_id"].map(wrestler_map)
        fr.insert(0, "fact_id", range(1, len(fr) + 1))
        rkeep = [
            "fact_id",
            "match_key",
            "event_key",
            "wrestler_key",
            "entry_number",
            "elimination_order",
            "eliminated_by",
            "time_in_match_seconds",
            "eliminations_made",
            "is_winner",
            "is_final_four",
        ]
        for c in rkeep:
            if c not in fr.columns:
                fr[c] = None
        fr[rkeep].to_sql("fact_royal_rumble", engine, if_exists="replace", index=False)
        counts["fact_royal_rumble"] = len(fr)

    # fact_money_in_the_bank
    if not mitb.empty:
        fmi = mitb.copy()
        fmi["event_key"] = fmi["event_id"].map(event_map) if "event_id" in fmi.columns else None
        fmi["winner_name"] = fmi.get("winner")
        fmi.insert(0, "fact_id", range(1, len(fmi) + 1))
        mkeep = [
            "fact_id",
            "match_id",
            "event_key",
            "winner_name",
            "cash_in_date",
            "cash_in_event",
            "cash_in_opponent",
            "cash_in_outcome",
            "championship_won",
        ]
        for c in mkeep:
            if c not in fmi.columns:
                fmi[c] = None
        fmi[mkeep].to_sql("fact_money_in_the_bank", engine, if_exists="replace", index=False)
        counts["fact_money_in_the_bank"] = len(fmi)

    # fact_survivor_series
    if not survivor.empty:
        fs = survivor.copy()
        fs["event_key"] = fs["event_id"].map(event_map) if "event_id" in fs.columns else None
        fs.insert(0, "fact_id", range(1, len(fs) + 1))
        skeep = [
            "fact_id",
            "match_id",
            "event_key",
            "match_format",
            "winning_side",
            "losing_side",
            "survivors",
        ]
        for c in skeep:
            if c not in fs.columns:
                fs[c] = None
        fs[skeep].to_sql("fact_survivor_series", engine, if_exists="replace", index=False)
        counts["fact_survivor_series"] = len(fs)

    # fact_event_attendance
    fa = dim_e[["event_key", "attendance", "country_key", "venue_key", "event_year"]].copy()
    fa.to_sql("fact_event_attendance", engine, if_exists="replace", index=False)
    counts["fact_event_attendance"] = len(fa)

    # pipeline run log
    finished = datetime.utcnow()
    run_df = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "started_at": started.isoformat(),
                "finished_at": finished.isoformat(),
                "status": "success",
                "records_loaded": int(sum(counts.values())),
                "notes": json_dumps_safe(counts),
            }
        ]
    )
    run_df.to_sql("pipeline_runs", engine, if_exists="append", index=False)

    console.print(f"[green]Dimensional load complete[/green] → {url}")
    for k, v in counts.items():
        console.print(f"  {k}: {v}")
    return counts


def json_dumps_safe(obj) -> str:
    import json

    return json.dumps(obj)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load dimensional warehouse")
    parser.add_argument("--postgres", action="store_true")
    parser.add_argument("--url", type=str, default=None)
    args = parser.parse_args()
    settings = get_settings()
    if args.url:
        url = args.url
    elif args.postgres:
        url = settings.database_url
    else:
        url = _default_url()
    load_dimensional(database_url=url)


if __name__ == "__main__":
    main()
