"""Remove Wikipedia footnote rows that were mis-parsed as matches."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from rich.console import Console

from wwe_data.config import get_settings
from wwe_data.pipeline.match_parse import is_results_footnote

console = Console()


def _rewrite_csv(path: Path, df: pd.DataFrame) -> None:
    df.to_csv(path, index=False)
    parquet = path.with_suffix(".parquet")
    try:
        df.to_parquet(parquet, index=False)
    except Exception:
        pass
    json_path = get_settings().processed_dir / f"{path.stem}.json"
    json_path.write_text(
        json.dumps(df.where(pd.notna(df), None).to_dict(orient="records"), indent=2, default=str),
        encoding="utf-8",
    )


def cleanup_exports() -> int:
    settings = get_settings()
    exports = settings.exports_dir
    matches_path = exports / "matches.csv"
    matches = pd.read_csv(matches_path)
    before = len(matches)
    mask = matches["match_result"].map(lambda x: not is_results_footnote(x if pd.notna(x) else None))
    # Also drop NaN match_number rows with no real result verb (same footnotes)
    cleaned = matches[mask].copy()
    removed_ids = set(matches.loc[~mask, "match_id"].astype(str))
    _rewrite_csv(matches_path, cleaned)
    console.print(f"matches: {before} → {len(cleaned)} (removed {before - len(cleaned)})")

    for name in (
        "match_participants",
        "match_championships",
        "special_royal_rumble",
        "special_money_in_the_bank",
        "special_survivor_series",
        "special_elimination_chamber",
    ):
        path = exports / f"{name}.csv"
        if not path.exists() or "match_id" not in pd.read_csv(path, nrows=0).columns:
            continue
        df = pd.read_csv(path)
        keep = ~df["match_id"].astype(str).isin(removed_ids)
        _rewrite_csv(path, df[keep].copy())
        console.print(f"{name}: kept {int(keep.sum())}/{len(df)}")

    # Update event_match_status match_count
    status_path = exports / "event_match_status.csv"
    if status_path.exists():
        status = pd.read_csv(status_path)
        counts = cleaned.groupby("event_id").size().to_dict()
        status["match_count"] = status["event_id"].map(lambda e: int(counts.get(e, 0)))
        _rewrite_csv(status_path, status)

    # Clean partial bundles so resume cache stays consistent
    partial = settings.processed_dir / "match_bundles_partial.jsonl"
    if partial.exists():
        kept_lines = []
        for line in partial.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            matches_list = row.get("matches") or []
            filtered = [
                m
                for m in matches_list
                if not is_results_footnote(m.get("match_result"))
            ]
            bad_ids = {m.get("match_id") for m in matches_list} - {m.get("match_id") for m in filtered}
            row["matches"] = filtered
            if bad_ids:
                row["participants"] = [
                    p for p in (row.get("participants") or []) if p.get("match_id") not in bad_ids
                ]
                row["rumble_entrants"] = [
                    r for r in (row.get("rumble_entrants") or []) if r.get("match_id") not in bad_ids
                ]
            kept_lines.append(json.dumps(row, default=str))
        partial.write_text("\n".join(kept_lines) + ("\n" if kept_lines else ""), encoding="utf-8")
        console.print(f"cleaned partial bundles: {partial}")

    return before - len(cleaned)


if __name__ == "__main__":
    n = cleanup_exports()
    console.print(f"[green]Removed {n} footnote match rows[/green]")
