"""Materialize analytical marts from dimensional SQLite/CSV into data/warehouse/marts."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console
from sqlalchemy import create_engine

from wwe_data.config import get_settings
from wwe_data.warehouse.load_dimensional import _default_url, load_dimensional

console = Console()


def _is_true(series: pd.Series) -> pd.Series:
    return series.map(
        lambda x: str(x).strip().lower() in {"true", "1", "1.0", "yes"}
        if pd.notna(x)
        else False
    )


def _write(df: pd.DataFrame, out: Path, name: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / f"{name}.csv", index=False)
    try:
        df.to_parquet(out / f"{name}.parquet", index=False)
    except Exception:
        pass


def materialize_marts(database_url: str | None = None) -> dict[str, int]:
    url = database_url or _default_url()
    if not Path(url.replace("sqlite:///", "")).exists() and url.startswith("sqlite"):
        load_dimensional(url)
    engine = create_engine(url, future=True)
    settings = get_settings()
    out = settings.data_dir / "warehouse" / "marts"

    dim_event = pd.read_sql("SELECT * FROM dim_event", engine)
    fact_matches = pd.read_sql("SELECT * FROM fact_matches", engine)
    fact_parts = pd.read_sql("SELECT * FROM fact_match_participants", engine)
    dim_wrestler = pd.read_sql("SELECT * FROM dim_wrestler", engine)
    fact_champs = pd.read_sql("SELECT * FROM fact_championship_changes", engine)
    dim_champ = pd.read_sql("SELECT * FROM dim_championship", engine)
    fact_rumble = pd.read_sql("SELECT * FROM fact_royal_rumble", engine)
    fact_mitb = pd.read_sql("SELECT * FROM fact_money_in_the_bank", engine)
    fact_att = pd.read_sql("SELECT * FROM fact_event_attendance", engine)
    dim_country = pd.read_sql("SELECT * FROM dim_country", engine)
    dim_venue = pd.read_sql("SELECT * FROM dim_venue", engine)
    dim_mt = pd.read_sql("SELECT * FROM dim_match_type", engine)

    # mart_event_analytics
    m_counts = (
        fact_matches.groupby("event_key")
        .agg(
            matches=("match_id", "count"),
            title_matches=("is_title_match", lambda s: int(_is_true(s).sum())),
            main_events=("is_main_event", lambda s: int(_is_true(s).sum())),
            avg_duration=("match_duration_seconds", "mean"),
        )
        .reset_index()
    )
    mart_event = dim_event.merge(m_counts, on="event_key", how="left")
    mart_event = mart_event.merge(
        dim_country.rename(columns={"country_name": "country"}),
        on="country_key",
        how="left",
    )
    mart_event = mart_event.merge(
        dim_venue[["venue_key", "venue_name", "city"]],
        on="venue_key",
        how="left",
    )
    _write(mart_event, out, "mart_event_analytics")

    # mart_match_analytics
    mart_match = fact_matches.merge(
        dim_event[["event_key", "event_id", "event_name", "event_series", "event_year", "event_date"]],
        on="event_key",
        how="left",
    ).merge(dim_mt, on="match_type_key", how="left")
    _write(mart_match, out, "mart_match_analytics")

    # mart_wrestler_performance
    wp = fact_parts.merge(fact_matches[["match_key", "event_key", "is_title_match", "is_main_event"]], on="match_key", how="left")
    wp = wp.merge(dim_event[["event_key", "event_year"]], on="event_key", how="left")
    wp["is_title_match"] = _is_true(wp["is_title_match"])
    wp["is_main_event"] = _is_true(wp["is_main_event"])
    mart_w = (
        wp.groupby("wrestler_key", dropna=False)
        .agg(
            matches=("match_key", "nunique"),
            wins=("result", lambda s: int((s == "win").sum())),
            losses=("result", lambda s: int((s == "loss").sum())),
            title_matches=("is_title_match", "sum"),
            main_events=("is_main_event", "sum"),
            first_year=("event_year", "min"),
            last_year=("event_year", "max"),
        )
        .reset_index()
    )
    mart_w = mart_w.merge(dim_wrestler[["wrestler_key", "wrestler_id", "canonical_name"]], on="wrestler_key", how="left")
    mart_w["win_pct"] = mart_w.apply(
        lambda r: round(r["wins"] / (r["wins"] + r["losses"]), 4)
        if (r["wins"] + r["losses"]) > 0
        else None,
        axis=1,
    )
    mart_w["career_span_years"] = mart_w["last_year"] - mart_w["first_year"]
    _write(mart_w.sort_values("matches", ascending=False), out, "mart_wrestler_performance")

    # mart_championship_analytics (PLE-only)
    fc = fact_champs.merge(dim_champ, on="championship_key", how="left")
    fc = fc.merge(
        dim_event[["event_key", "event_name", "event_date", "event_year"]],
        on="event_key",
        how="left",
    )
    changes = fc[_is_true(fc["title_change"])].copy()
    champ_summary = (
        changes.groupby(["championship_key", "championship_name"], dropna=False)
        .agg(
            title_changes=("fact_id", "count"),
            first_change=("event_date", "min"),
            last_change=("event_date", "max"),
        )
        .reset_index()
    )
    _write(changes, out, "mart_championship_changes")
    _write(champ_summary, out, "mart_championship_analytics")

    # mart_royal_rumble_analytics
    rr = fact_rumble.merge(dim_wrestler[["wrestler_key", "canonical_name"]], on="wrestler_key", how="left")
    rr = rr.merge(dim_event[["event_key", "event_name", "event_year", "event_date"]], on="event_key", how="left")
    # Source uses eliminated_by == "Winner" for victors when is_winner flag is unset
    if "eliminated_by" in rr.columns:
        win_mask = rr["eliminated_by"].astype(str).str.fullmatch(r"(?i)winner").fillna(False)
        rr["is_winner"] = _is_true(rr.get("is_winner", pd.Series(False, index=rr.index))) | win_mask
    _write(rr, out, "mart_royal_rumble_analytics")

    # mart_mitb_analytics
    _write(fact_mitb, out, "mart_mitb_analytics")

    # mart_attendance_analytics
    att = fact_att.merge(dim_event[["event_key", "event_id", "event_name", "event_series", "event_date"]], on="event_key", how="left")
    att = att.merge(dim_country, on="country_key", how="left")
    att = att.merge(dim_venue[["venue_key", "venue_name", "city"]], on="venue_key", how="left")
    _write(att, out, "mart_attendance_analytics")

    # mart_historical_trends
    trends = (
        dim_event.groupby("event_year")
        .agg(events=("event_id", "count"), attendance=("attendance", "sum"))
        .reset_index()
    )
    my = mart_match.groupby("event_year").agg(matches=("match_id", "count")).reset_index()
    trends = trends.merge(my, on="event_year", how="left")
    _write(trends, out, "mart_historical_trends")

    # overview KPIs
    overview = pd.DataFrame(
        [
            {
                "total_events": len(dim_event),
                "total_matches": len(fact_matches),
                "unique_wrestlers": len(dim_wrestler),
                "championship_links": len(fact_champs),
                "title_changes": int(_is_true(fact_champs["title_change"]).sum()),
                "total_attendance": int(
                    pd.to_numeric(dim_event["attendance"], errors="coerce").fillna(0).sum()
                ),
                "attendance_known_events": int(
                    pd.to_numeric(dim_event["attendance"], errors="coerce").notna().sum()
                ),
            }
        ]
    )
    _write(overview, out, "mart_overview")

    counts = {p.stem: len(pd.read_csv(p)) for p in out.glob("mart_*.csv")}
    stamp = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source": url,
        "marts": counts,
    }
    (out / "marts_stamp.json").write_text(json.dumps(stamp, indent=2), encoding="utf-8")
    # also mirror key marts into data/analytics for dashboard/API fallback
    analytics = settings.data_dir / "analytics"
    analytics.mkdir(parents=True, exist_ok=True)
    for name in (
        "mart_overview",
        "mart_event_analytics",
        "mart_wrestler_performance",
        "mart_match_analytics",
        "mart_championship_analytics",
        "mart_championship_changes",
        "mart_royal_rumble_analytics",
        "mart_mitb_analytics",
        "mart_attendance_analytics",
        "mart_historical_trends",
    ):
        src = out / f"{name}.csv"
        if src.exists():
            pd.read_csv(src).to_csv(analytics / f"{name}.csv", index=False)
    console.print(f"[green]Marts materialized[/green] → {out}")
    return counts


def main() -> None:
    materialize_marts()


if __name__ == "__main__":
    main()
