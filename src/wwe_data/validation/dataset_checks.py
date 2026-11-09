"""Phase 3 dataset integrity checks over exported CSV tables."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from wwe_data.config import get_settings


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    count: int = 0


@dataclass
class ValidationReport:
    checks: list[CheckResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def failed(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]

    @property
    def ok(self) -> bool:
        return not self.failed


def _read(exports: Path, name: str) -> pd.DataFrame:
    path = exports / f"{name}.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False).replace({"": pd.NA})


def _as_set(series: pd.Series) -> set[str]:
    return {str(x) for x in series.dropna().astype(str) if str(x)}


def run_dataset_checks(exports_dir: Path | None = None) -> ValidationReport:
    settings = get_settings()
    exports = exports_dir or settings.exports_dir
    report = ValidationReport()

    events = _read(exports, "events_inventory")
    matches = _read(exports, "matches")
    participants = _read(exports, "match_participants")
    wrestlers = _read(exports, "wrestlers")
    aliases = _read(exports, "wrestler_aliases")
    championships = _read(exports, "championships")
    match_champs = _read(exports, "match_championships")
    status = _read(exports, "event_match_status")

    report.summary = {
        "events": len(events),
        "matches": len(matches),
        "participants": len(participants),
        "wrestlers": len(wrestlers),
        "championships": len(championships),
        "match_championships": len(match_champs),
    }

    def add(name: str, passed: bool, detail: str, count: int = 0) -> None:
        report.checks.append(CheckResult(name=name, passed=passed, detail=detail, count=count))

    # Required files present
    required = [
        "events_inventory",
        "matches",
        "match_participants",
        "wrestlers",
        "championships",
        "match_championships",
        "event_match_status",
    ]
    missing = [n for n in required if _read(exports, n).empty and not (exports / f"{n}.csv").exists()]
    add(
        "required_exports_present",
        not missing,
        "ok" if not missing else f"missing: {', '.join(missing)}",
        len(missing),
    )

    if events.empty or matches.empty:
        return report

    # Unique keys
    for label, df, col in (
        ("events", events, "event_id"),
        ("matches", matches, "match_id"),
        ("wrestlers", wrestlers, "wrestler_id"),
        ("championships", championships, "championship_id"),
    ):
        if df.empty or col not in df.columns:
            add(f"unique_{label}", False, f"missing {col}", 0)
            continue
        dup = int(df[col].duplicated().sum())
        add(f"unique_{label}", dup == 0, f"{dup} duplicate {col}" if dup else "ok", dup)

    event_ids = _as_set(events["event_id"])
    match_ids = _as_set(matches["match_id"])
    wrestler_ids = _as_set(wrestlers["wrestler_id"]) if not wrestlers.empty else set()
    champ_ids = _as_set(championships["championship_id"]) if not championships.empty else set()

    # FK: matches → events
    orphan_event_refs = (
        sorted(_as_set(matches["event_id"]) - event_ids) if "event_id" in matches.columns else []
    )
    add(
        "matches_event_fk",
        len(orphan_event_refs) == 0,
        "ok"
        if not orphan_event_refs
        else f"{len(orphan_event_refs)} matches point to unknown events",
        len(orphan_event_refs),
    )

    # FK: participants → matches / wrestlers
    if not participants.empty:
        bad_m = sorted(_as_set(participants["match_id"]) - match_ids)
        bad_w = sorted(_as_set(participants["wrestler_id"]) - wrestler_ids)
        add(
            "participants_match_fk",
            len(bad_m) == 0,
            "ok" if not bad_m else f"{len(bad_m)} participants with unknown match_id",
            len(bad_m),
        )
        add(
            "participants_wrestler_fk",
            len(bad_w) == 0,
            "ok" if not bad_w else f"{len(bad_w)} participants with unknown wrestler_id",
            len(bad_w),
        )

    if not aliases.empty and "wrestler_id" in aliases.columns:
        bad_a = sorted(_as_set(aliases["wrestler_id"]) - wrestler_ids)
        add(
            "aliases_wrestler_fk",
            len(bad_a) == 0,
            "ok" if not bad_a else f"{len(bad_a)} aliases with unknown wrestler_id",
            len(bad_a),
        )

    if not match_champs.empty:
        bad_mc_m = sorted(_as_set(match_champs["match_id"]) - match_ids)
        bad_mc_c = sorted(_as_set(match_champs["championship_id"]) - champ_ids)
        add(
            "match_championships_match_fk",
            len(bad_mc_m) == 0,
            "ok" if not bad_mc_m else f"{len(bad_mc_m)} links with unknown match_id",
            len(bad_mc_m),
        )
        add(
            "match_championships_championship_fk",
            len(bad_mc_c) == 0,
            "ok" if not bad_mc_c else f"{len(bad_mc_c)} links with unknown championship_id",
            len(bad_mc_c),
        )

    # Completed events should have cards (announced may be skipped)
    if (
        not status.empty
        and "collection_status" in status.columns
        and "event_id" in status.columns
        and "event_status" in events.columns
    ):
        completed_events = events[events["event_status"].astype(str) == "completed"]
        status_by_id = status.drop_duplicates("event_id").set_index("event_id")
        missing_cards = 0
        for eid in completed_events["event_id"].astype(str):
            if eid not in status_by_id.index:
                missing_cards += 1
                continue
            row = status_by_id.loc[eid]
            st = str(row["collection_status"])
            raw_cnt = row["match_count"] if "match_count" in status.columns else 0
            try:
                cnt = int(float(raw_cnt)) if pd.notna(raw_cnt) else 0
            except (TypeError, ValueError):
                cnt = 0
            if st == "skipped_announced":
                continue
            if st != "success" or cnt == 0:
                missing_cards += 1
        add(
            "completed_events_have_cards",
            missing_cards == 0,
            "ok" if missing_cards == 0 else f"{missing_cards} completed events without cards",
            missing_cards,
        )

    # Year window
    if "event_year" in events.columns:
        years = pd.to_numeric(events["event_year"], errors="coerce")
        out = int(((years < 2000) | (years > 2027)).sum())
        add("event_year_window", out == 0, "ok" if out == 0 else f"{out} events outside 2000–2027", out)

    # No fabricated NXT TakeOver in inventory
    if "event_name" in events.columns:
        takeover = int(events["event_name"].str.contains("takeover", case=False, na=False).sum())
        add("no_nxt_takeover", takeover == 0, "ok" if takeover == 0 else f"{takeover} TakeOver rows", takeover)

    # Title-match flag consistency
    if "is_title_match" in matches.columns and not match_champs.empty:
        titled = matches[matches["is_title_match"].astype(str).str.lower().isin(["true", "1"])]
        titled_ids = _as_set(titled["match_id"])
        linked = _as_set(match_champs["match_id"])
        missing_link = len(titled_ids - linked)
        # Soft warning — Wikipedia sometimes marks title match without parseable title name
        add(
            "title_matches_have_championship_link",
            True,
            f"{missing_link} is_title_match rows without championship link (informational)",
            missing_link,
        )

    return report
