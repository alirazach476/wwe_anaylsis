"""Phase 4 orchestrator: enrichment → analytics refresh → validation."""

from __future__ import annotations

import argparse

from rich.console import Console

from wwe_data.analytics.materialize import materialize_analytics
from wwe_data.pipeline.enrich import enrich_specials
from wwe_data.pipeline.validate import write_validation_report
from wwe_data.validation.dataset_checks import run_dataset_checks

console = Console()


def run_phase4(*, skip_validate: bool = False) -> int:
    console.rule("[bold]Phase 4 — Enrichment / Dictionary / Refresh[/bold]")

    console.print("\n[cyan]1/3 Special-match enrichment[/cyan]")
    paths = enrich_specials()
    console.print(f"  stamp: {paths.get('stamp')}")

    console.print("\n[cyan]2/3 Rematerialize analytics[/cyan]")
    analytics = materialize_analytics()
    # Also materialize MITB cash-in analytics slice if present
    _materialize_mitb_analytics()
    console.print(f"  analytics stamp: {analytics.get('stamp')}")

    if not skip_validate:
        console.print("\n[cyan]3/3 Validation[/cyan]")
        report = run_dataset_checks()
        md_path, _ = write_validation_report(report)
        console.print(
            f"  checks: {sum(1 for c in report.checks if c.passed)}/{len(report.checks)} "
            f"→ {md_path}"
        )
        if not report.ok:
            console.print("[red]Validation FAIL[/red]")
            return 1
    else:
        console.print("\n[cyan]3/3 Validation[/cyan] skipped")

    console.print("\n[green]Phase 4 complete.[/green]")
    console.print("  Data dictionary: docs/DATA_DICTIONARY.md")
    console.print("  Dashboard: streamlit run dashboard/app.py")
    return 0


def _materialize_mitb_analytics() -> None:
    from pathlib import Path

    import pandas as pd

    from wwe_data.config import get_settings

    settings = get_settings()
    src = settings.exports_dir / "special_mitb_cash_ins.csv"
    winners = settings.exports_dir / "special_money_in_the_bank.csv"
    out = settings.data_dir / "analytics"
    out.mkdir(parents=True, exist_ok=True)
    if src.exists():
        df = pd.read_csv(src)
        df.to_csv(out / "mitb_cash_ins.csv", index=False)
        try:
            df.to_parquet(out / "mitb_cash_ins.parquet", index=False)
        except Exception:
            pass
        if "cash_in_outcome" in df.columns:
            summary = (
                df.groupby("cash_in_outcome", dropna=False)
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
            )
            summary.to_csv(out / "mitb_cash_in_outcomes.csv", index=False)
    if winners.exists():
        w = pd.read_csv(winners)
        w.to_csv(out / "mitb_ladder_winners.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4 enrichment")
    parser.add_argument("--skip-validate", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run_phase4(skip_validate=args.skip_validate))


if __name__ == "__main__":
    main()
