"""Data quality report over exports / warehouse staging."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console

from wwe_data.config import get_settings
from wwe_data.validation.dataset_checks import run_dataset_checks
from wwe_data.warehouse.cleaning import clean_to_warehouse, coalesce_participants

console = Console()


def write_data_quality_report() -> Path:
    settings = get_settings()
    exports = settings.exports_dir
    reports = settings.reports_dir
    reports.mkdir(parents=True, exist_ok=True)

    counts = clean_to_warehouse()
    validation = run_dataset_checks(exports)

    events = pd.read_csv(exports / "events_inventory.csv")
    matches = pd.read_csv(exports / "matches.csv")
    parts = pd.read_csv(exports / "match_participants.csv")
    parts_clean = coalesce_participants(parts)

    lines = [
        "# Data Quality Report",
        "",
        f"_Generated: {datetime.utcnow().isoformat()}Z_",
        "",
        "## Cleaning summary",
        "",
    ]
    for k, v in counts.items():
        lines.append(f"- **{k}:** {v}")

    lines += [
        "",
        "## Integrity checks",
        "",
        f"- Overall: {'PASS' if validation.ok else 'FAIL'}",
        "",
        "| Check | Status | Detail | Count |",
        "| --- | --- | --- | ---: |",
    ]
    for c in validation.checks:
        lines.append(
            f"| `{c.name}` | {'PASS' if c.passed else 'FAIL'} | {c.detail} | {c.count} |"
        )

    lines += [
        "",
        "## Null-vs-zero policy",
        "",
        "- `attendance` null means unknown — never treated as 0 in averages without explicit filter.",
        "- `match_duration_seconds` null means unavailable on source page.",
        "- Boolean false is genuine false; null is unavailable.",
        "",
        "## Participant soft duplicates",
        "",
        f"- Raw rows: {len(parts)}",
        f"- After coalesce: {len(parts_clean)}",
        f"- Removed: {len(parts) - len(parts_clean)}",
        "",
        "## Field null rates (events)",
        "",
    ]
    for col in ("attendance", "brand", "venue", "broadcast_platform"):
        if col in events.columns:
            pct = round(float(events[col].isna().mean() * 100), 2)
            lines.append(f"- `{col}`: {pct}%")

    lines += ["", "## Field null rates (matches)", ""]
    for col in ("match_duration_seconds", "winner", "loser", "match_type"):
        if col in matches.columns:
            pct = round(float(matches[col].isna().mean() * 100), 2)
            lines.append(f"- `{col}`: {pct}%")

    lines += [
        "",
        "## Known analytical gaps",
        "",
        "- Championship category/introduction/retirement dates unavailable",
        "- Chamber entry/elimination order unavailable",
        "- Brand sparsely populated",
        "- Championship analytics limited to PLE title changes",
        "",
    ]

    path = reports / "data_quality_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "cleaning_counts": counts,
        "validation_ok": validation.ok,
        "checks": [
            {"name": c.name, "passed": c.passed, "detail": c.detail, "count": c.count}
            for c in validation.checks
        ],
    }
    (reports / "data_quality_report.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    console.print(f"[green]DQ report[/green] → {path}")
    return path


def main() -> None:
    write_data_quality_report()


if __name__ == "__main__":
    main()
