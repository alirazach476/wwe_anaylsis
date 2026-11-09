"""Rebuild completeness report from current CSV exports (no re-scrape)."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console

from wwe_data.config import get_settings

console = Console()


def write_completeness_from_exports(output_dir: Path | None = None) -> Path:
    settings = get_settings()
    exports = settings.exports_dir
    out = output_dir or settings.reports_dir
    out.mkdir(parents=True, exist_ok=True)

    events = pd.read_csv(exports / "events_inventory.csv")
    matches = pd.read_csv(exports / "matches.csv")
    wrestlers = pd.read_csv(exports / "wrestlers.csv")
    match_champs = pd.read_csv(exports / "match_championships.csv")
    status = pd.read_csv(exports / "event_match_status.csv")
    rumble = (
        pd.read_csv(exports / "special_royal_rumble.csv")
        if (exports / "special_royal_rumble.csv").exists()
        else pd.DataFrame()
    )
    mitb = (
        pd.read_csv(exports / "special_money_in_the_bank.csv")
        if (exports / "special_money_in_the_bank.csv").exists()
        else pd.DataFrame()
    )

    title_changes = 0
    if "title_change" in match_champs.columns:
        title_changes = int(
            match_champs["title_change"].astype(str).str.lower().isin(["true", "1"]).sum()
        )

    status_counts = Counter(status["collection_status"].astype(str)) if not status.empty else {}

    # Missing cards among completed events
    completed = events[events["event_status"].astype(str) == "completed"]
    status_by = status.drop_duplicates("event_id").set_index("event_id") if not status.empty else None
    missing_cards: list[str] = []
    if status_by is not None:
        for _, ev in completed.iterrows():
            eid = ev["event_id"]
            if eid not in status_by.index:
                missing_cards.append(f"{ev['event_date']} | {ev['event_name']} | not_collected")
                continue
            row = status_by.loc[eid]
            st = str(row["collection_status"])
            try:
                cnt = int(float(row["match_count"])) if pd.notna(row["match_count"]) else 0
            except (TypeError, ValueError):
                cnt = 0
            if st == "skipped_announced":
                continue
            if st != "success" or cnt == 0:
                missing_cards.append(f"{ev['event_date']} | {ev['event_name']} | {st}")

    year_rows = []
    if "event_year" in events.columns:
        for year, grp in events.groupby(pd.to_numeric(events["event_year"], errors="coerce")):
            if pd.isna(year):
                continue
            year = int(year)
            eids = set(grp["event_id"])
            mcount = int(matches["event_id"].isin(eids).sum()) if not matches.empty else 0
            completed_n = int((grp["event_status"].astype(str) == "completed").sum())
            with_cards = 0
            if status_by is not None and completed_n:
                for eid in grp.loc[grp["event_status"].astype(str) == "completed", "event_id"]:
                    if eid in status_by.index:
                        st = str(status_by.loc[eid, "collection_status"])
                        cnt = status_by.loc[eid, "match_count"]
                        try:
                            cnt_i = int(float(cnt)) if pd.notna(cnt) else 0
                        except (TypeError, ValueError):
                            cnt_i = 0
                        if st == "success" and cnt_i > 0:
                            with_cards += 1
            pct = round(100.0 * with_cards / completed_n, 1) if completed_n else 0.0
            year_rows.append((year, pct, mcount))

    mitb_filled = 0
    if not mitb.empty and "cash_in_date" in mitb.columns:
        mitb_filled = int(mitb["cash_in_date"].notna().sum())

    stamp = datetime.utcnow().isoformat() + "Z"
    lines = [
        "# WWE Dataset Completeness Report",
        "",
        f"_Generated: {stamp}_",
        "",
        "## Summary",
        "",
        f"- **Total eligible events:** {len(events)}",
        f"- **Total matches collected:** {len(matches)}",
        f"- **Total unique wrestlers:** {len(wrestlers)}",
        f"- **Championship match links:** {len(match_champs)}",
        f"- **Title changes (inferred):** {title_changes}",
        f"- **Events missing match cards:** {len(missing_cards)}",
        f"- **Royal Rumble entrant rows:** {len(rumble)}",
        f"- **MITB winners with cash-in linked:** {mitb_filled}/{len(mitb) if len(mitb) else 0}",
        "",
        "## Collection status",
        "",
    ]
    for k, v in sorted(status_counts.items()):
        lines.append(f"- `{k}`: {v}")

    lines += [
        "",
        "## Coverage by year",
        "",
        "| Year | Completed-event card coverage % | Matches |",
        "| --- | ---: | ---: |",
    ]
    for year, pct, mcount in year_rows:
        lines.append(f"| {year} | {pct} | {mcount} |")

    lines += ["", "## Events missing match cards", ""]
    if missing_cards:
        for row in missing_cards:
            lines.append(f"- {row}")
    else:
        lines.append("- None")

    lines += [
        "",
        "## Notes",
        "",
        "- Regenerated from exports (Phase 5) — footnotes stripped in Phase 3 cleanup",
        "- MITB cash-ins enriched in Phase 4; unmatched winners are transfers / unused / note-only",
        "- No fabricated match results",
        "",
    ]

    md_path = out / "completeness_report.md"
    json_path = out / "completeness_report.json"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    payload = {
        "generated_at": stamp,
        "events": len(events),
        "matches": len(matches),
        "wrestlers": len(wrestlers),
        "missing_cards": len(missing_cards),
        "status_counts": dict(status_counts),
        "mitb_cash_in_linked": mitb_filled,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    console.print(f"[green]Completeness report[/green] → {md_path}")
    return md_path


def main() -> None:
    write_completeness_from_exports()


if __name__ == "__main__":
    main()
