"""Materialize analytics tables from exports (dbt-equivalent local run)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console

from wwe_data.config import get_settings

console = Console()


def _read(exports: Path, name: str) -> pd.DataFrame:
    csv_path = exports / f"{name}.csv"
    parquet = exports / f"{name}.parquet"
    if parquet.exists():
        try:
            return pd.read_parquet(parquet)
        except Exception:
            pass
    return pd.read_csv(csv_path)


def _write(df: pd.DataFrame, out_dir: Path, name: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{name}.csv"
    parquet_path = out_dir / f"{name}.parquet"
    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(parquet_path, index=False)
    except Exception:
        pass
    return csv_path


def materialize_analytics(exports_dir: Path | None = None) -> dict[str, Path]:
    settings = get_settings()
    exports = exports_dir or settings.exports_dir
    out = settings.data_dir / "analytics"

    events = _read(exports, "events_inventory")
    matches = _read(exports, "matches")
    participants = _read(exports, "match_participants")
    wrestlers = _read(exports, "wrestlers")
    match_champs = _read(exports, "match_championships")
    championships = _read(exports, "championships")
    status = _read(exports, "event_match_status")

    events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")
    matches["match_number"] = pd.to_numeric(matches["match_number"], errors="coerce")
    matches["match_duration_seconds"] = pd.to_numeric(
        matches["match_duration_seconds"], errors="coerce"
    )
    for col in ("is_title_match", "is_main_event", "is_preshow"):
        if col in matches.columns:
            matches[col] = matches[col].astype(str).str.lower().isin(["true", "1", "yes"])

    # dim_events
    dim_events = events.copy()
    if not status.empty:
        dim_events = dim_events.merge(
            status[["event_id", "match_count", "collection_status"]],
            on="event_id",
            how="left",
        )
    else:
        dim_events["match_count"] = 0
        dim_events["collection_status"] = None

    # fct_matches
    fct_matches = matches.merge(
        events[
            [
                "event_id",
                "event_name",
                "event_series",
                "event_year",
                "event_date",
                "event_status",
                "city",
                "country",
            ]
        ],
        on="event_id",
        how="left",
    )

    # event_year_summary
    year_summary = (
        dim_events.groupby("event_year", dropna=False)
        .agg(
            events=("event_id", "count"),
            completed=("event_status", lambda s: int((s == "completed").sum())),
            announced=("event_status", lambda s: int((s == "announced").sum())),
        )
        .reset_index()
    )
    match_by_year = (
        fct_matches.groupby("event_year", dropna=False)
        .agg(
            matches=("match_id", "count"),
            title_matches=("is_title_match", "sum"),
            main_events=("is_main_event", "sum"),
        )
        .reset_index()
    )
    year_summary = year_summary.merge(match_by_year, on="event_year", how="left")
    for col in ("matches", "title_matches", "main_events"):
        year_summary[col] = year_summary[col].fillna(0).astype(int)

    # series_summary
    series_summary = (
        dim_events.groupby("event_series", dropna=False)
        .agg(
            events=("event_id", "count"),
            first_year=("event_year", "min"),
            last_year=("event_year", "max"),
            total_attendance=("attendance", lambda s: pd.to_numeric(s, errors="coerce").sum()),
        )
        .reset_index()
        .sort_values("events", ascending=False)
    )
    series_matches = (
        fct_matches.groupby("event_series", dropna=False)["match_id"]
        .count()
        .reset_index(name="matches")
    )
    series_summary = series_summary.merge(series_matches, on="event_series", how="left")
    series_summary["matches"] = series_summary["matches"].fillna(0).astype(int)

    # wrestler_match_counts
    part = participants.merge(
        matches[["match_id", "event_id", "is_title_match", "is_main_event"]],
        on="match_id",
        how="left",
    )
    part = part.merge(events[["event_id", "event_year"]], on="event_id", how="left")
    part["is_title_match"] = part["is_title_match"].fillna(False).astype(bool)
    part["is_main_event"] = part["is_main_event"].fillna(False).astype(bool)
    wrestler_stats = (
        part.groupby(["wrestler_id"], dropna=False)
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
    wrestler_stats = wrestler_stats.merge(
        wrestlers[["wrestler_id", "canonical_name"]], on="wrestler_id", how="left"
    )
    wrestler_stats = wrestler_stats.sort_values("matches", ascending=False)

    # title_changes
    title_changes = match_champs.copy()
    if "title_change" in title_changes.columns:
        mask = title_changes["title_change"].astype(str).str.lower().isin(["true", "1", "yes"])
        title_changes = title_changes[mask]
    title_changes = title_changes.merge(
        championships[["championship_id", "championship_name"]],
        on="championship_id",
        how="left",
    )
    title_changes = title_changes.merge(
        matches[["match_id", "event_id", "winner", "match_result"]],
        on="match_id",
        how="left",
    )
    title_changes = title_changes.merge(
        events[["event_id", "event_name", "event_date", "event_year"]],
        on="event_id",
        how="left",
    )

    # country / brand geography
    geography = (
        dim_events.groupby(["country", "city"], dropna=False)
        .agg(events=("event_id", "count"), attendance=("attendance", lambda s: pd.to_numeric(s, errors="coerce").sum()))
        .reset_index()
        .sort_values("events", ascending=False)
    )

    paths = {
        "dim_events": _write(dim_events, out, "dim_events"),
        "fct_matches": _write(fct_matches, out, "fct_matches"),
        "event_year_summary": _write(year_summary, out, "event_year_summary"),
        "series_summary": _write(series_summary, out, "series_summary"),
        "wrestler_match_counts": _write(wrestler_stats, out, "wrestler_match_counts"),
        "title_changes": _write(title_changes, out, "title_changes"),
        "event_geography": _write(geography, out, "event_geography"),
    }

    stamp = {
        "phase": "analytics",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "tables": {k: str(v) for k, v in paths.items()},
        "row_counts": {
            "dim_events": len(dim_events),
            "fct_matches": len(fct_matches),
            "wrestler_match_counts": len(wrestler_stats),
            "title_changes": len(title_changes),
        },
    }
    stamp_path = out / "analytics_stamp.json"
    stamp_path.write_text(json.dumps(stamp, indent=2), encoding="utf-8")
    paths["stamp"] = stamp_path
    console.print(f"[green]Analytics materialized[/green] → {out}")
    return paths


def main() -> None:
    materialize_analytics()


if __name__ == "__main__":
    main()
