"""Load full Phase 2 exports into SQLite (default) or PostgreSQL."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from rich.console import Console
from sqlalchemy import create_engine, text

from wwe_data.config import get_settings
from wwe_data.db.session import create_all

console = Console()

# Load order respects FK dependencies
LOAD_ORDER = [
    ("events_inventory", "events"),
    ("wrestlers", "wrestlers"),
    ("championships", "championships"),
    ("matches", "matches"),
    ("wrestler_aliases", "wrestler_aliases"),
    ("match_participants", "match_participants"),
    ("match_championships", "match_championships"),
]

EVENT_COLUMNS = [
    "event_id",
    "event_name",
    "canonical_event_name",
    "event_series",
    "event_year",
    "event_date",
    "event_end_date",
    "event_type",
    "event_status",
    "venue",
    "city",
    "state_province",
    "country",
    "attendance",
    "broadcast_platform",
    "brand",
    "official_url",
    "source_url",
    "verification_status",
    "last_updated",
]

MATCH_COLUMNS = [
    "match_id",
    "event_id",
    "match_number",
    "match_name",
    "match_type",
    "match_stipulation",
    "match_duration_seconds",
    "match_result",
    "winner",
    "loser",
    "is_title_match",
    "is_main_event",
    "is_preshow",
    "match_status",
    "source_url",
    "verification_status",
]

PARTICIPANT_COLUMNS = [
    "match_id",
    "wrestler_id",
    "team_id",
    "participant_role",
    "result",
    "entry_number",
    "elimination_order",
    "eliminated_by",
    "time_in_match_seconds",
]

MATCH_CHAMP_COLUMNS = [
    "match_id",
    "championship_id",
    "champion_before",
    "champion_after",
    "title_change",
    "title_retained",
    "title_vacated",
]


def _default_sqlite_url() -> str:
    settings = get_settings()
    path = settings.processed_dir / "wwe_history.sqlite"
    return f"sqlite:///{path.as_posix()}"


def _read_csv(exports: Path, name: str) -> pd.DataFrame:
    path = exports / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _prep_events(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in EVENT_COLUMNS:
        if col not in out.columns:
            out[col] = None
    out = out[EVENT_COLUMNS]
    out["event_year"] = pd.to_numeric(out["event_year"], errors="coerce").astype("Int64")
    out["attendance"] = pd.to_numeric(out["attendance"], errors="coerce").astype("Int64")
    # SQLite ORM column is NOT NULL without a DB-side default on INSERT
    missing_ts = out["last_updated"].isna() | (out["last_updated"].astype(str).str.strip() == "")
    if missing_ts.any():
        out.loc[missing_ts, "last_updated"] = pd.Timestamp.utcnow().isoformat()
    return out


def _prep_matches(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in MATCH_COLUMNS:
        if col not in out.columns:
            out[col] = None
    out = out[MATCH_COLUMNS]
    for col in ("match_number", "match_duration_seconds"):
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
    for col in ("is_title_match", "is_main_event", "is_preshow"):
        out[col] = out[col].map(
            lambda x: None if pd.isna(x) else str(x).lower() in {"true", "1", "yes"}
        )
    return out


def _prep_participants(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in PARTICIPANT_COLUMNS:
        if col not in out.columns:
            out[col] = None
    out = out[PARTICIPANT_COLUMNS]
    for col in ("entry_number", "elimination_order", "time_in_match_seconds"):
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
    # Rumble winners often appear once from results + once from entrant table
    out["_score"] = (
        out["entry_number"].notna().astype(int)
        + out["elimination_order"].notna().astype(int)
        + out["result"].notna().astype(int)
        + out["time_in_match_seconds"].notna().astype(int)
    )
    out = (
        out.sort_values("_score", ascending=False)
        .drop_duplicates(subset=["match_id", "wrestler_id", "participant_role"], keep="first")
        .drop(columns=["_score"])
    )
    return out


def _prep_match_champs(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in MATCH_CHAMP_COLUMNS:
        if col not in out.columns:
            out[col] = None
    out = out[MATCH_CHAMP_COLUMNS]
    for col in ("title_change", "title_retained", "title_vacated"):
        out[col] = out[col].map(
            lambda x: None if pd.isna(x) else str(x).lower() in {"true", "1", "yes"}
        )
    out = out.drop_duplicates(subset=["match_id", "championship_id"], keep="first")
    return out


def _clear_tables(engine) -> None:
    tables = [
        "match_championships",
        "match_participants",
        "wrestler_aliases",
        "matches",
        "championships",
        "wrestlers",
        "event_sources",
        "events",
        "collection_logs",
        "teams",
    ]
    with engine.begin() as conn:
        # SQLite needs FK off for truncate-style deletes
        if engine.dialect.name == "sqlite":
            conn.execute(text("PRAGMA foreign_keys=OFF"))
        for table in tables:
            conn.execute(text(f"DELETE FROM {table}"))
        if engine.dialect.name == "sqlite":
            conn.execute(text("PRAGMA foreign_keys=ON"))


def load_all(
    database_url: str | None = None,
    exports_dir: Path | None = None,
    replace: bool = True,
) -> dict[str, int]:
    settings = get_settings()
    exports = exports_dir or settings.exports_dir
    url = database_url or _default_sqlite_url()

    create_all(url)
    engine = create_engine(url, future=True)
    if replace:
        _clear_tables(engine)

    counts: dict[str, int] = {}
    preparers = {
        "events": _prep_events,
        "matches": _prep_matches,
        "match_participants": _prep_participants,
        "match_championships": _prep_match_champs,
    }

    for csv_name, table in LOAD_ORDER:
        df = _read_csv(exports, csv_name)
        prep = preparers.get(table)
        if prep:
            df = prep(df)
        elif table == "wrestlers":
            keep = [
                "wrestler_id",
                "canonical_name",
                "debut_date",
                "retirement_date",
                "nationality",
                "source_url",
            ]
            for c in keep:
                if c not in df.columns:
                    df[c] = None
            df = df[keep]
        elif table == "championships":
            keep = [
                "championship_id",
                "championship_name",
                "championship_category",
                "introduction_date",
                "retirement_date",
                "source_url",
            ]
            for c in keep:
                if c not in df.columns:
                    df[c] = None
            df = df[keep]
        elif table == "wrestler_aliases":
            keep = ["wrestler_id", "ring_name", "alias_start_date", "alias_end_date"]
            for c in keep:
                if c not in df.columns:
                    df[c] = None
            df = df[keep]

        df.to_sql(table, engine, if_exists="append", index=False)
        counts[table] = len(df)
        console.print(f"  loaded {table}: {len(df)}")

    console.print(f"[green]Warehouse ready[/green] → {url}")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3 warehouse load")
    parser.add_argument(
        "--postgres",
        action="store_true",
        help="Use WWE_DATABASE_URL (PostgreSQL) instead of local SQLite",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Override database URL",
    )
    args = parser.parse_args()
    settings = get_settings()
    if args.url:
        url = args.url
    elif args.postgres:
        url = settings.database_url
    else:
        url = _default_sqlite_url()
    console.print(f"Loading exports into {url}")
    load_all(database_url=url)


if __name__ == "__main__":
    main()
