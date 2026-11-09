"""Phase 3: run dataset validation and write integrity report."""

from __future__ import annotations

import json
from datetime import datetime

from rich.console import Console
from rich.table import Table

from wwe_data.config import get_settings
from wwe_data.validation.dataset_checks import ValidationReport, run_dataset_checks

console = Console()


def write_validation_report(report: ValidationReport) -> tuple:
    settings = get_settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().isoformat() + "Z"

    lines = [
        "# WWE Dataset Validation Report (Phase 3)",
        "",
        f"_Generated: {stamp}_",
        "",
        "## Summary",
        "",
    ]
    for k, v in report.summary.items():
        lines.append(f"- **{k}:** {v}")
    lines += [
        "",
        f"- **Checks passed:** {sum(1 for c in report.checks if c.passed)} / {len(report.checks)}",
        f"- **Overall:** {'PASS' if report.ok else 'FAIL'}",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail | Count |",
        "| --- | --- | --- | ---: |",
    ]
    for c in report.checks:
        status = "PASS" if c.passed else "FAIL"
        detail = c.detail.replace("|", "\\|")
        lines.append(f"| `{c.name}` | {status} | {detail} | {c.count} |")

    if report.failed:
        lines += ["", "## Failures", ""]
        for c in report.failed:
            lines.append(f"- `{c.name}`: {c.detail}")

    md_path = settings.reports_dir / "validation_report.md"
    json_path = settings.reports_dir / "validation_report.json"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = {
        "generated_at": stamp,
        "ok": report.ok,
        "summary": report.summary,
        "checks": [
            {
                "name": c.name,
                "passed": c.passed,
                "detail": c.detail,
                "count": c.count,
            }
            for c in report.checks
        ],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return md_path, json_path


def main() -> int:
    report = run_dataset_checks()
    md_path, json_path = write_validation_report(report)

    table = Table(title="Phase 3 validation")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for c in report.checks:
        table.add_row(c.name, "[green]PASS[/green]" if c.passed else "[red]FAIL[/red]", c.detail)
    console.print(table)
    console.print(f"\nReport: {md_path}")
    console.print(f"JSON:   {json_path}")
    if report.ok:
        console.print("[green]Validation PASS[/green]")
        return 0
    console.print("[red]Validation FAIL[/red]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
