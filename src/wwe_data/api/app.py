"""FastAPI backend — queries warehouse marts / exports (Postgres when configured)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

from wwe_data.config import get_settings

app = FastAPI(
    title="WWE PLE Analytics API",
    description="Analytics API for WWE Premium Live Events 2000–2027",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _marts_dir() -> Path:
    return get_settings().data_dir / "warehouse" / "marts"


def _exports_dir() -> Path:
    settings = get_settings()
    primary = settings.exports_dir
    if (primary / "match_participants.csv").exists() or (primary / "championships.csv").exists():
        return primary
    # Bundled copy for serverless deploys (exports/ is often gitignored)
    bundled = settings.data_dir / "warehouse" / "runtime_exports"
    return bundled if bundled.exists() else primary


def _analytics_sqlite() -> Path:
    return get_settings().processed_dir / "wwe_analytics.sqlite"


@lru_cache
def _engine():
    settings = get_settings()
    url = settings.database_url
    # Prefer analytics sqlite if postgres unreachable for local
    sqlite = _analytics_sqlite()
    if sqlite.exists():
        return create_engine(f"sqlite:///{sqlite.as_posix()}", future=True)
    return create_engine(url, future=True)


def _read_mart(name: str) -> pd.DataFrame:
    path = _marts_dir() / f"{name}.csv"
    if not path.exists():
        alt = get_settings().data_dir / "analytics" / f"{name}.csv"
        path = alt if alt.exists() else path
    if not path.exists():
        raise HTTPException(404, f"Mart not found: {name}. Run materialize_marts.")
    return pd.read_csv(path)


def _paginate(df: pd.DataFrame, limit: int, offset: int) -> list[dict[str, Any]]:
    return df.iloc[offset : offset + limit].where(pd.notna(df), None).to_dict(orient="records")


def _special_rumble_path() -> Path | None:
    settings = get_settings()
    for base in (_exports_dir(), settings.exports_dir, settings.data_dir / "exports"):
        path = base / "special_royal_rumble.csv"
        if path.exists():
            return path
    return None


def _is_rumble_match(match: dict[str, Any]) -> bool:
    return (
        str(match.get("special_match_kind") or "").lower() == "royal_rumble"
        or "rumble" in str(match.get("match_type_group") or "").lower()
        or "rumble" in str(match.get("match_type_raw") or "").lower()
    )


def _unique_entry_count(participants: list[dict[str, Any]]) -> int:
    return len({p.get("entry_number") for p in participants if p.get("entry_number") is not None})


def _rumble_special_to_participants(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        elim_by = None if pd.isna(r.get("eliminated_by")) else str(r.get("eliminated_by"))
        flagged_win = bool(r.get("is_winner")) if pd.notna(r.get("is_winner")) else False
        is_win = flagged_win or (elim_by or "").strip().lower() == "winner"
        elim = r.get("elimination_order")
        entry = r.get("entry_number")
        rows.append(
            {
                "match_id": None if pd.isna(r.get("match_id")) else r.get("match_id"),
                "wrestler_id": None if pd.isna(r.get("wrestler_id")) else r.get("wrestler_id"),
                "ring_name": None if pd.isna(r.get("entrant")) else r.get("entrant"),
                "participant_role": "competitor",
                "result": "win" if is_win else ("loss" if pd.notna(elim) else None),
                "entry_number": int(entry) if pd.notna(entry) else None,
                "elimination_order": int(elim) if pd.notna(elim) else None,
                "eliminated_by": None if is_win else elim_by,
                "time_in_match_seconds": (
                    None if pd.isna(r.get("time_in_match_seconds")) else r.get("time_in_match_seconds")
                ),
            }
        )
    return rows


def _enrich_rumble_participants(event_id: str, match_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fill stub rumble cards and split men's/women's tables that were merged onto one match."""
    rumble_matches = [m for m in match_rows if _is_rumble_match(m)]
    if not rumble_matches:
        return match_rows

    path = _special_rumble_path()
    if path is None:
        return match_rows

    special = pd.read_csv(path)
    event_special = special[special["event_id"].astype(str) == str(event_id)].copy()
    if event_special.empty:
        return match_rows

    event_special = event_special.reset_index(drop=True)
    rumble_sorted = sorted(
        rumble_matches,
        key=lambda m: (
            m.get("match_number") is None,
            float(m.get("match_number") or 0),
        ),
    )
    n_special = len(event_special)
    uniq_entries = int(event_special["entry_number"].nunique(dropna=True))
    dup_entries = n_special > uniq_entries
    by_mid = {
        str(mid): grp.reset_index(drop=True)
        for mid, grp in event_special.groupby(event_special["match_id"].astype(str))
    }

    if len(rumble_sorted) >= 2 and n_special >= 50 and (dup_entries or n_special % 30 == 0):
        step = 30 if n_special % 30 == 0 else max(1, n_special // len(rumble_sorted))
        chunks = [event_special.iloc[i : i + step] for i in range(0, n_special, step)]
        for match, chunk in zip(rumble_sorted, chunks):
            if len(chunk) >= 20:
                match["participants"] = _rumble_special_to_participants(chunk)
    else:
        # Prefer special rows keyed to this match_id; never clone one rumble onto every stub.
        for match in rumble_sorted:
            mid = str(match.get("match_id") or "")
            parts = match.get("participants") or []
            if mid in by_mid and len(by_mid[mid]) >= 20:
                match["participants"] = _rumble_special_to_participants(by_mid[mid])
            elif _unique_entry_count(parts) < 25 and len(rumble_sorted) == 1 and n_special >= 20:
                match["participants"] = _rumble_special_to_participants(event_special)

    rich_ids = {
        str(m.get("match_id"))
        for m in rumble_sorted
        if _unique_entry_count(m.get("participants") or []) >= 25
    }
    if rich_ids:
        match_rows = [
            m
            for m in match_rows
            if not (
                _is_rumble_match(m)
                and str(m.get("match_id")) not in rich_ids
                and _unique_entry_count(m.get("participants") or []) < 10
            )
        ]
    return match_rows


def _clean_wrestler_display_name(name: str) -> str:
    """Collapse scraped variants into one readable ring name."""
    import re

    s = str(name or "").strip()
    if not s:
        return ""
    # Drop parenthetical / bracket manager / brand / title clutter
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\[[^\]]*\]", " ", s)
    s = s.replace(")", " ").replace("(", " ").replace("]", " ").replace("[", " ")
    s = re.sub(r"[\"“”'*]+", "", s)
    s = re.sub(r"\s+", " ", s).strip(" -–,.")
    # Narrative / result scrapes: keep the wrestler before "by …"
    if re.search(r"(?i)\s+by\s+", s):
        s = re.split(r"(?i)\s+by\s+", s, maxsplit=1)[0].strip()
    # Title-prefix scrapes: "WWE United States Champion John Cena"
    m = re.search(
        r"(?i)\b(?:undisputed\s+)?(?:wwe|wwf|world|universal|intercontinental|united states|us|raw|smackdown|women'?s|men'?s|tag team|heavyweight)?\s*champion\s+(.+)$",
        s,
    )
    if m and len(m.group(1).split()) <= 4:
        s = m.group(1).strip()
    # Leading junk from bad scrapes
    s = re.sub(r"(?i)^(and|although|team|team raw|team authority|the shield)\s+", "", s).strip()
    s = re.sub(r"(?i)^the shield\s*\(?\s*", "", s).strip()
    # Prefer "Miz" over "The Miz"; keep "The Undertaker"
    m = re.match(r"(?i)^the\s+(.+)$", s)
    if m:
        rest = m.group(1).strip()
        rl = rest.lower()
        if rl == "undertaker":
            s = "The Undertaker"
        elif rl in {"big show", "miz"} or " " not in rest:
            s = rest
    # Drop filler nicknames that split the same person
    s = re.sub(r"(?i)\bfreakin\b", "", s)
    # Trailing match markers: "John Cena 2"
    s = re.sub(r"\s+\d+$", "", s)
    s = re.sub(r"\s+", " ", s).strip(" -–,.")
    return s


def _is_garbage_wrestler_name(display: str) -> bool:
    import re

    s = (display or "").strip()
    if not s or len(s) < 2:
        return True
    if re.match(r"^\d", s):
        return True
    if len(s) > 42:
        return True
    low = s.lower()
    junk = (
        "looks to",
        "quiet ",
        "retrieving",
        "sudden death",
        "team hell",
        "team raw",
        "team authority",
        "although ",
    )
    return any(j in low for j in junk)


def _wrestler_name_key(name: str) -> str:
    import re

    display = _clean_wrestler_display_name(name)
    key = re.sub(r"[^a-z0-9\s]", "", display.lower())
    key = re.sub(r"\s+", " ", key).strip()
    if key.startswith("the "):
        rest = key[4:]
        if rest in {"miz", "big show"}:
            key = rest
    return key


def _dedupe_wrestlers_by_name(df: pd.DataFrame) -> pd.DataFrame:
    """One row per wrestler name: merge scraped aliases / manager variants."""
    if df.empty or "canonical_name" not in df.columns:
        return df

    work = df.copy()
    work["_display"] = work["canonical_name"].map(_clean_wrestler_display_name)
    work = work[~work["_display"].map(_is_garbage_wrestler_name)]
    work["_name_key"] = work["_display"].map(_wrestler_name_key)
    work = work[work["_name_key"].astype(str).str.len() > 0]
    if work.empty:
        return work.drop(columns=["_name_key", "_display"], errors="ignore")

    for col in ("matches", "wins", "losses", "title_matches", "main_events", "career_span_years"):
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)

    # Prefer the cleanest / highest-volume row as the identity for links
    work = work.sort_values(
        by=[c for c in ("matches", "wins") if c in work.columns],
        ascending=False,
    )

    rows: list[dict[str, Any]] = []
    for key, g in work.groupby("_name_key", sort=False):
        primary = g.iloc[0]
        # Prefer shortest clean display without leftover punctuation
        displays = [str(x) for x in g["_display"].tolist() if str(x).strip()]
        display = min(displays, key=lambda s: (len(s), s.lower())) if displays else str(primary["canonical_name"])

        matches = float(g["matches"].sum()) if "matches" in g else 0.0
        wins = float(g["wins"].sum()) if "wins" in g else 0.0
        losses = float(g["losses"].sum()) if "losses" in g else 0.0
        title_matches = float(g["title_matches"].sum()) if "title_matches" in g else 0.0
        main_events = float(g["main_events"].sum()) if "main_events" in g else 0.0
        first_year = pd.to_numeric(g.get("first_year"), errors="coerce").min()
        last_year = pd.to_numeric(g.get("last_year"), errors="coerce").max()
        win_pct = (wins / matches) if matches else None

        rows.append(
            {
                "wrestler_id": primary.get("wrestler_id"),
                "wrestler_key": primary.get("wrestler_key"),
                "canonical_name": display,
                "matches": int(matches),
                "wins": int(wins),
                "losses": int(losses),
                "title_matches": int(title_matches),
                "main_events": int(main_events),
                "first_year": int(first_year) if pd.notna(first_year) else None,
                "last_year": int(last_year) if pd.notna(last_year) else None,
                "win_pct": round(float(win_pct), 4) if win_pct is not None else None,
                "career_span_years": (
                    int(last_year - first_year)
                    if pd.notna(first_year) and pd.notna(last_year)
                    else primary.get("career_span_years")
                ),
                "merged_variants": int(len(g)),
            }
        )

    out = pd.DataFrame(rows)
    if "matches" in out.columns:
        out = out.sort_values("matches", ascending=False)
    return out.reset_index(drop=True)


def _filter_by_series_family(df: pd.DataFrame, series: str) -> pd.DataFrame:
    """Match event families loosely so Backlash includes WrestleMania Backlash, etc."""
    key = str(series).strip().lower()
    if not key or "event_series" not in df.columns:
        return df
    ser = df["event_series"].astype(str).str.lower()
    name = df["event_name"].astype(str).str.lower() if "event_name" in df.columns else ser
    if key == "backlash":
        return df[ser.str.contains("backlash", na=False) | name.str.contains("backlash", na=False)]
    if key == "wrestlemania":
        return df[
            (ser.str.contains("wrestlemania", na=False) | name.str.startswith("wrestlemania", na=False))
            & ~name.str.contains("backlash", na=False)
        ]
    return df[ser.str.contains(key, na=False, regex=False) | name.str.contains(key, na=False, regex=False)]


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "marts": _marts_dir().exists(),
        "warehouse_sqlite": _analytics_sqlite().exists(),
    }


@app.get("/api/analytics/overview")
def analytics_overview(
    year_from: int | None = None,
    year_to: int | None = None,
    series: str | None = None,
    country: str | None = None,
) -> dict[str, Any]:
    events = _read_mart("mart_event_analytics")
    matches = _read_mart("mart_match_analytics")
    if year_from is not None:
        events = events[pd.to_numeric(events["event_year"], errors="coerce") >= year_from]
        matches = matches[pd.to_numeric(matches["event_year"], errors="coerce") >= year_from]
    if year_to is not None:
        events = events[pd.to_numeric(events["event_year"], errors="coerce") <= year_to]
        matches = matches[pd.to_numeric(matches["event_year"], errors="coerce") <= year_to]
    if series:
        events = _filter_by_series_family(events, series)
        matches = _filter_by_series_family(matches, series)
    if country and "country" in events.columns:
        events = events[events["country"] == country]
        eids = set(events["event_id"])
        matches = matches[matches["event_id"].isin(eids)]
    att = pd.to_numeric(events.get("attendance"), errors="coerce")
    att_known = att[att > 0]
    trends = _read_mart("mart_historical_trends")
    if year_from is not None:
        trends = trends[pd.to_numeric(trends["event_year"], errors="coerce") >= year_from]
    if year_to is not None:
        trends = trends[pd.to_numeric(trends["event_year"], errors="coerce") <= year_to]
    by_country = (
        events.groupby("country", dropna=False).size().reset_index(name="events")
        if "country" in events.columns
        else pd.DataFrame()
    )
    by_series = events.groupby("event_series", dropna=False).size().reset_index(name="events")
    champs = _read_mart("mart_championship_analytics")
    years = pd.to_numeric(events["event_year"], errors="coerce").dropna()
    return {
        "kpis": {
            "total_events": int(len(events)),
            "total_matches": int(len(matches)),
            "unique_wrestlers": int(_read_mart("mart_wrestler_performance")["wrestler_id"].nunique()),
            "total_championships": int(len(champs)),
            "championship_matches": int(
                matches["is_title_match"].astype(str).str.lower().isin(["true", "1"]).sum()
            ),
            "title_changes": int(len(_read_mart("mart_championship_changes"))),
            "total_venues": int(events["venue_name"].nunique()) if "venue_name" in events.columns else 0,
            "total_countries": int(events["country"].nunique()) if "country" in events.columns else 0,
            "year_from": int(years.min()) if not years.empty else None,
            "year_to": int(years.max()) if not years.empty else None,
            "total_attendance": int(att_known.sum()) if not att_known.empty else 0,
            "attendance_known_events": int(len(att_known)),
            "avg_attendance": int(round(float(att_known.mean()))) if not att_known.empty else None,
        },
        "by_year": trends.where(pd.notna(trends), None).to_dict(orient="records"),
        "by_country": by_country.where(pd.notna(by_country), None).to_dict(orient="records"),
        "by_series": by_series.sort_values("events", ascending=False)
        .head(30)
        .where(pd.notna(by_series), None)
        .to_dict(orient="records"),
    }


@app.get("/api/events")
def list_events(
    year: int | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    series: str | None = None,
    country: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    df = _read_mart("mart_event_analytics")
    if year is not None:
        df = df[pd.to_numeric(df["event_year"], errors="coerce") == year]
    if year_from is not None:
        df = df[pd.to_numeric(df["event_year"], errors="coerce") >= year_from]
    if year_to is not None:
        df = df[pd.to_numeric(df["event_year"], errors="coerce") <= year_to]
    if series:
        df = _filter_by_series_family(df, series)
    if country and "country" in df.columns:
        df = df[df["country"] == country]
    if status and "event_status" in df.columns:
        df = df[df["event_status"] == status]
    if q:
        df = df[df["event_name"].astype(str).str.contains(q, case=False, na=False)]
    df = df.sort_values("event_date")
    return {"total": int(len(df)), "items": _paginate(df, limit, offset)}


@app.get("/api/events/{event_id}")
def get_event(event_id: str) -> dict[str, Any]:
    events = _read_mart("mart_event_analytics")
    row = events[events["event_id"] == event_id]
    if row.empty:
        raise HTTPException(404, "event not found")
    matches = _read_mart("mart_match_analytics")
    card = matches[matches["event_id"] == event_id].sort_values("match_number")
    payload = row.iloc[0].where(pd.notna(row.iloc[0]), None).to_dict()
    match_rows = card.where(pd.notna(card), None).to_dict(orient="records")

    # Attach real participants + championship rows when exports exist
    parts_path = _exports_dir() / "match_participants.csv"
    champs_path = _exports_dir() / "match_championships.csv"
    parts_by_match: dict[str, list[dict[str, Any]]] = {}
    champs_by_match: dict[str, list[dict[str, Any]]] = {}
    if parts_path.exists() and match_rows:
        parts = pd.read_csv(parts_path)
        mids = {m["match_id"] for m in match_rows if m.get("match_id")}
        sub = parts[parts["match_id"].isin(mids)]
        for mid, grp in sub.groupby("match_id"):
            parts_by_match[str(mid)] = grp.where(pd.notna(grp), None).to_dict(orient="records")
    if champs_path.exists() and match_rows:
        ch = pd.read_csv(champs_path)
        mids = {m["match_id"] for m in match_rows if m.get("match_id")}
        sub = ch[ch["match_id"].isin(mids)]
        for mid, grp in sub.groupby("match_id"):
            champs_by_match[str(mid)] = grp.where(pd.notna(grp), None).to_dict(orient="records")

    for m in match_rows:
        mid = str(m.get("match_id") or "")
        m["participants"] = parts_by_match.get(mid, [])
        m["championships"] = champs_by_match.get(mid, [])
    match_rows = _enrich_rumble_participants(str(event_id), match_rows)
    payload["matches"] = match_rows
    return payload


@app.get("/api/wrestlers")
def list_wrestlers(
    q: str | None = None,
    min_matches: int = 0,
    limit: int = Query(5000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    sort: str = "matches",
) -> dict[str, Any]:
    """All wrestlers with PLE match appearances — one row per unique ring name."""
    df = _dedupe_wrestlers_by_name(_read_mart("mart_wrestler_performance"))
    if min_matches and min_matches > 0:
        df = df[pd.to_numeric(df["matches"], errors="coerce") >= min_matches]
    if q:
        df = df[df["canonical_name"].astype(str).str.contains(q, case=False, na=False)]
    if sort in df.columns:
        df = df.sort_values(sort, ascending=False)
    return {"total": int(len(df)), "items": _paginate(df, limit, offset)}


@app.get("/api/wrestlers/{wrestler_id}")
def get_wrestler(wrestler_id: str) -> dict[str, Any]:
    df = _read_mart("mart_wrestler_performance")
    row = df[df["wrestler_id"] == wrestler_id]
    if row.empty:
        raise HTTPException(404, "wrestler not found")
    # recent matches via participants export
    parts = pd.read_csv(_exports_dir() / "match_participants.csv")
    matches = _read_mart("mart_match_analytics")
    his = parts[parts["wrestler_id"] == wrestler_id].merge(
        matches, on="match_id", how="left"
    )
    payload = row.iloc[0].where(pd.notna(row.iloc[0]), None).to_dict()
    payload["match_history"] = (
        his.sort_values("event_date", ascending=False)
        .head(50)
        .where(pd.notna(his), None)
        .to_dict(orient="records")
    )
    return payload


@app.get("/api/matches")
def list_matches(
    event_id: str | None = None,
    year: int | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    series: str | None = None,
    match_type: str | None = None,
    title_only: bool = False,
    main_only: bool = False,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    df = _read_mart("mart_match_analytics")
    if event_id:
        df = df[df["event_id"] == event_id]
    if year is not None:
        df = df[pd.to_numeric(df["event_year"], errors="coerce") == year]
    if year_from is not None:
        df = df[pd.to_numeric(df["event_year"], errors="coerce") >= year_from]
    if year_to is not None:
        df = df[pd.to_numeric(df["event_year"], errors="coerce") <= year_to]
    if series:
        df = _filter_by_series_family(df, series)
    if match_type and "match_type_group" in df.columns:
        df = df[df["match_type_group"] == match_type]
    if title_only:
        df = df[df["is_title_match"].astype(str).str.lower().isin(["true", "1"])]
    if main_only:
        df = df[df["is_main_event"].astype(str).str.lower().isin(["true", "1"])]
    return {"total": int(len(df)), "items": _paginate(df, limit, offset)}


@app.get("/api/championships")
def list_championships(limit: int = 100, offset: int = 0) -> dict[str, Any]:
    df = _read_mart("mart_championship_analytics").sort_values(
        "title_changes", ascending=False
    )
    return {"total": int(len(df)), "items": _paginate(df, limit, offset)}


@app.get("/api/analytics/wrestlers")
def analytics_wrestlers(limit: int = 25) -> dict[str, Any]:
    df = _dedupe_wrestlers_by_name(_read_mart("mart_wrestler_performance")).sort_values(
        "matches", ascending=False
    )
    return {"top_by_appearances": _paginate(df, limit, 0)}


@app.get("/api/analytics/matches")
def analytics_matches() -> dict[str, Any]:
    df = _read_mart("mart_match_analytics")
    type_dist = (
        df["match_type_group"].fillna("other").value_counts().reset_index()
    )
    type_dist.columns = ["match_type_group", "count"]
    dur = pd.to_numeric(df["match_duration_seconds"], errors="coerce")
    title_mask = df["is_title_match"].astype(str).str.lower().isin(["true", "1"])
    main_mask = df["is_main_event"].astype(str).str.lower().isin(["true", "1"])

    by_year = (
        df.assign(year=pd.to_numeric(df["event_year"], errors="coerce"))
        .dropna(subset=["year"])
        .groupby("year")
        .agg(
            matches=("match_id", "count"),
            title_matches=("is_title_match", lambda s: int(s.astype(str).str.lower().isin(["true", "1"]).sum())),
            avg_duration_sec=("match_duration_seconds", lambda s: float(pd.to_numeric(s, errors="coerce").mean())),
        )
        .reset_index()
        .sort_values("year")
    )
    by_year["year"] = by_year["year"].astype(int)

    dur_by_type = (
        df.assign(
            match_type_group=df["match_type_group"].fillna("other"),
            dur=dur,
        )
        .groupby("match_type_group")["dur"]
        .agg(avg_sec="mean", median_sec="median", count="count")
        .reset_index()
        .sort_values("count", ascending=False)
    )

    # Duration histogram (minutes)
    dur_min = (dur.dropna() / 60).clip(upper=60)
    bins = list(range(0, 61, 5))
    hist: list[dict[str, int]] = []
    cats = pd.cut(dur_min, bins=bins, right=False, include_lowest=True)
    vc = cats.value_counts(sort=False)
    for interval, count in vc.items():
        hist.append({"bin_start": int(interval.left), "bin_end": int(interval.right), "count": int(count)})

    # Finish method heuristic from match_result text
    result = df["match_result"].fillna("").astype(str).str.lower()
    finishes = {
        "pinfall": int(result.str.contains(r"\bpin\b|pinfall").sum()),
        "submission": int(result.str.contains("submission").sum()),
        "dq": int(result.str.contains(r"\bdq\b|disqualif").sum()),
        "countout": int(result.str.contains("count.?out").sum()),
        "no contest": int(result.str.contains("no contest").sum()),
        "draw": int(result.str.contains(r"\bdraw\b").sum()),
    }

    series_counts = (
        df["event_series"].fillna("Other").astype(str).value_counts().head(12).reset_index()
    )
    series_counts.columns = ["event_series", "count"]

    return {
        "type_distribution": type_dist.to_dict(orient="records"),
        "duration": {
            "count": int(dur.notna().sum()),
            "mean": float(dur.mean()) if dur.notna().any() else None,
            "median": float(dur.median()) if dur.notna().any() else None,
        },
        "title_share": float(title_mask.mean()) if len(df) else 0.0,
        "main_event_share": float(main_mask.mean()) if len(df) else 0.0,
        "by_year": by_year.where(pd.notna(by_year), None).to_dict(orient="records"),
        "duration_by_type": dur_by_type.where(pd.notna(dur_by_type), None).to_dict(orient="records"),
        "duration_histogram": hist,
        "finish_methods": [{"method": k, "count": v} for k, v in finishes.items() if v > 0],
        "by_series": series_counts.to_dict(orient="records"),
        "totals": {
            "matches": int(len(df)),
            "title_matches": int(title_mask.sum()),
            "main_events": int(main_mask.sum()),
        },
    }


def _crown_jewel_championship_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Ensure WWE Crown Jewel Championship lineages appear in championship analytics."""
    import re

    path = _exports_dir() / "championships.csv"
    if not path.exists():
        return [], []

    raw = pd.read_csv(path)
    mask = raw["championship_name"].astype(str).str.contains(
        r"Crown Jewel Championship", case=False, na=False
    )
    subset = raw.loc[mask].copy()
    if subset.empty:
        return [], []

    def clean_name(name: str) -> str:
        s = str(name)
        s = re.sub(r"\[[^\]]*\]", "", s)
        s = re.sub(r"(?i)^inaugural\s+\d{4}\s+", "", s)
        s = re.sub(r"(?i)^\d{4}\s+", "", s)
        return re.sub(r"\s+", " ", s).strip()

    subset["clean_name"] = subset["championship_name"].map(clean_name)
    # One row per cleaned lineage (men's + women's)
    grouped = (
        subset.groupby("clean_name", as_index=False)
        .agg(
            championship_id=("championship_id", "first"),
            title_changes=("championship_id", "count"),
            source_url=("source_url", "first"),
        )
        .sort_values("clean_name")
    )

    # Known inaugural / landmark holders for spotlight cards
    landmarks = {
        "WWE Crown Jewel Championship": {
            "inaugural_champion": "Cody Rhodes",
            "inaugural_event": "Crown Jewel 2024",
            "inaugural_date": "2024-11-02",
            "note": "Awarded to the winner of Undisputed WWE Champion vs World Heavyweight Champion.",
        },
        "WWE Women's Crown Jewel Championship": {
            "inaugural_champion": "Liv Morgan",
            "inaugural_event": "Crown Jewel 2024",
            "inaugural_date": "2024-11-02",
            "note": "Awarded to the winner of Raw Women’s World Champion vs SmackDown Women’s Champion.",
        },
    }

    summary_rows: list[dict[str, Any]] = []
    change_rows: list[dict[str, Any]] = []
    for _, row in grouped.iterrows():
        name = str(row["clean_name"])
        meta = landmarks.get(name, {})
        summary_rows.append(
            {
                "championship_key": None,
                "championship_name": name,
                "championship_id": row.get("championship_id"),
                "title_changes": int(row["title_changes"]),
                "title_matches": int(row["title_changes"]),
                "first_change": meta.get("inaugural_date"),
                "last_change": meta.get("inaugural_date"),
                "featured": True,
                "lineage": "Crown Jewel",
            }
        )
        if meta:
            change_rows.append(
                {
                    "event_date": meta.get("inaugural_date"),
                    "event_name": meta.get("inaugural_event"),
                    "championship_name": name,
                    "champion_after": meta.get("inaugural_champion"),
                    "title_change": True,
                    "note": meta.get("note"),
                    "featured": True,
                }
            )

    return summary_rows, change_rows


@app.get("/api/analytics/championships")
def analytics_championships(limit: int = 30) -> dict[str, Any]:
    summary = _read_mart("mart_championship_analytics").sort_values(
        "title_changes", ascending=False
    )
    changes = _read_mart("mart_championship_changes")
    crown_summary, crown_changes = _crown_jewel_championship_records()

    # Prepend Crown Jewel lineages if missing from mart summary
    if crown_summary:
        existing = set(summary["championship_name"].astype(str).str.lower())
        extra = [r for r in crown_summary if r["championship_name"].lower() not in existing]
        if extra:
            summary = pd.concat([pd.DataFrame(extra), summary], ignore_index=True)

    recent = changes.sort_values("event_date", ascending=False)
    recent_records = _paginate(recent, 50, 0)
    # Keep Crown Jewel spotlight rows at the front of recent changes
    for row in reversed(crown_changes):
        recent_records.insert(0, row)

    return {
        "summary": _paginate(summary, max(limit, 40), 0),
        "recent_changes": recent_records,
        "featured": crown_summary,
        "limitation": "PLE-sourced title changes only; not full reign calendar. Crown Jewel Championship lineages are included as featured titles.",
    }


@app.get("/api/analytics/historical-records")
def analytics_historical_records(limit: int = 15) -> dict[str, Any]:
    """Warehouse-derived PLE title-change leaders (complement curated landmark records)."""
    import re

    changes = _read_mart("mart_championship_changes")
    names = changes["champion_after"].fillna("").astype(str)

    def clean_name(s: str) -> str:
        s = re.sub(r"\([^)]*\)", " ", s)
        s = re.sub(r"\s+", " ", s).strip(" -–,")
        # Keep first solo name when it's a clear singles champion string
        if " and " in s.lower() or " & " in s:
            return s  # tag teams stay as-is for separate board
        return s

    cleaned = names.map(clean_name)
    singles = cleaned[~cleaned.str.contains(r"(?i)\band\b|&", na=False)]
    tags = cleaned[cleaned.str.contains(r"(?i)\band\b|&", na=False)]

    top_singles = (
        singles.value_counts()
        .head(limit)
        .reset_index()
    )
    top_singles.columns = ["name", "ple_title_wins"]
    top_tags = tags.value_counts().head(10).reset_index()
    top_tags.columns = ["name", "ple_title_wins"]

    by_title = (
        changes.groupby("championship_name", dropna=False)
        .size()
        .reset_index(name="changes")
        .sort_values("changes", ascending=False)
        .head(12)
    )

    return {
        "ple_most_title_wins": top_singles.where(pd.notna(top_singles), None).to_dict(orient="records"),
        "ple_most_tag_title_wins": top_tags.where(pd.notna(top_tags), None).to_dict(orient="records"),
        "ple_busiest_titles": by_title.where(pd.notna(by_title), None).to_dict(orient="records"),
        "note": "PLE card title changes only — not the same as all-time WWE official reign counts.",
    }


@app.get("/api/analytics/royal-rumble")
def analytics_rumble() -> dict[str, Any]:
    df = _read_mart("mart_royal_rumble_analytics")
    winners = df[df["is_winner"].astype(str).str.lower().isin(["true", "1"])]
    entry = (
        winners.groupby("entry_number").size().reset_index(name="wins")
        if not winners.empty
        else pd.DataFrame()
    )
    elim = (
        df.groupby("canonical_name")["eliminations_made"]
        .sum()
        .sort_values(ascending=False)
        .head(25)
        .reset_index()
    )
    return {
        "winners": winners.where(pd.notna(winners), None).to_dict(orient="records"),
        "wins_by_entry_number": entry.to_dict(orient="records"),
        "elimination_leaders": elim.to_dict(orient="records"),
    }


@app.get("/api/analytics/money-in-the-bank")
def analytics_mitb() -> dict[str, Any]:
    df = _read_mart("mart_mitb_analytics")
    outcomes = (
        df["cash_in_outcome"].fillna("unknown").value_counts().reset_index()
    )
    outcomes.columns = ["outcome", "count"]
    return {
        "rows": df.where(pd.notna(df), None).to_dict(orient="records"),
        "outcomes": outcomes.to_dict(orient="records"),
    }


@app.get("/api/analytics/attendance")
def analytics_attendance() -> dict[str, Any]:
    df = _read_mart("mart_attendance_analytics")
    att = pd.to_numeric(df["attendance"], errors="coerce")
    known = df.loc[att > 0].copy()
    known["attendance"] = att.loc[att > 0]
    by_country = (
        known.groupby("country_name")["attendance"]
        .agg(["count", "sum", "mean"])
        .reset_index()
        .sort_values("sum", ascending=False)
    )
    return {
        "known_events": int(len(known)),
        "avg_attendance": int(round(float(known["attendance"].mean()))) if len(known) else None,
        "by_country": by_country.where(pd.notna(by_country), None).to_dict(orient="records"),
        "top_events": _paginate(known.sort_values("attendance", ascending=False), 25, 0),
    }


@app.get("/api/analytics/global")
def analytics_global() -> dict[str, Any]:
    df = _read_mart("mart_event_analytics")
    geo = (
        df.groupby(["country", "city"], dropna=False)
        .agg(events=("event_id", "count"), attendance=("attendance", "sum"))
        .reset_index()
        .sort_values("events", ascending=False)
    )
    return {"geography": geo.where(pd.notna(geo), None).to_dict(orient="records")}


@app.get("/api/analytics/ml")
def analytics_ml() -> dict[str, Any]:
    path = get_settings().data_dir.parent / "models" / "registry.json"
    # models lives at project root /models
    path = Path(__file__).resolve().parents[3] / "models" / "registry.json"
    if not path.exists():
        return {"experiments": [], "note": "Run experiments/run_ml_experiments.py"}
    import json

    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/filters/meta")
def filters_meta() -> dict[str, Any]:
    events = _read_mart("mart_event_analytics")
    matches = _read_mart("mart_match_analytics")
    return {
        "years": sorted(
            {
                int(y)
                for y in pd.to_numeric(events["event_year"], errors="coerce").dropna()
            }
        ),
        "series": sorted({str(s) for s in events["event_series"].dropna().unique()}),
        "countries": sorted(
            {str(c) for c in events.get("country", pd.Series(dtype=str)).dropna().unique()}
        ),
        "match_types": sorted(
            {
                str(t)
                for t in matches.get("match_type_group", pd.Series(dtype=str)).dropna().unique()
            }
        ),
    }


def main() -> None:
    import uvicorn

    uvicorn.run("wwe_data.api.app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
