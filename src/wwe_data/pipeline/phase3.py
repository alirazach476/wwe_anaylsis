"""Phase 3 orchestrator: validate → warehouse load → analytics → ready for dashboard."""

from __future__ import annotations

import argparse

from rich.console import Console

from wwe_data.analytics.materialize import materialize_analytics
from wwe_data.config import get_settings
from wwe_data.db.load_all import _default_sqlite_url, load_all
from wwe_data.pipeline.validate import write_validation_report
from wwe_data.validation.dataset_checks import run_dataset_checks

console = Console()


def run_phase3(*, postgres: bool = False, skip_load: bool = False) -> int:
    console.rule("[bold]Phase 3 — Validation / Warehouse / Analytics[/bold]")

    console.print("\n[cyan]1/3 Validation[/cyan]")
    report = run_dataset_checks()
    md_path, _ = write_validation_report(report)
    console.print(f"  checks: {sum(1 for c in report.checks if c.passed)}/{len(report.checks)} passed")
    console.print(f"  report: {md_path}")
    if not report.ok:
        console.print("[red]Validation failed — aborting warehouse load[/red]")
        for c in report.failed:
            console.print(f"  - {c.name}: {c.detail}")
        return 1

    if not skip_load:
        console.print("\n[cyan]2/3 Warehouse load[/cyan]")
        settings = get_settings()
        url = settings.database_url if postgres else _default_sqlite_url()
        counts = load_all(database_url=url)
        console.print(f"  tables: {', '.join(f'{k}={v}' for k, v in counts.items())}")
    else:
        console.print("\n[cyan]2/3 Warehouse load[/cyan] skipped")

    console.print("\n[cyan]3/3 Analytics materialize[/cyan]")
    paths = materialize_analytics()
    console.print(f"  outputs: {paths.get('stamp')}")

    console.print("\n[green]Phase 3 complete.[/green]")
    console.print("  Dashboard: streamlit run dashboard/app.py")
    console.print("  Optional dbt (Postgres): copy dbt/profiles.yml.example → ~/.dbt/profiles.yml")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3 validation + warehouse + analytics")
    parser.add_argument(
        "--postgres",
        action="store_true",
        help="Load into PostgreSQL (WWE_DATABASE_URL) instead of SQLite",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Skip warehouse load (analytics still runs from CSV)",
    )
    args = parser.parse_args()
    raise SystemExit(run_phase3(postgres=args.postgres, skip_load=args.skip_load))


if __name__ == "__main__":
    main()
