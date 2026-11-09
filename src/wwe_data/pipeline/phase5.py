"""Phase 5 orchestrator: completeness refresh → release package (+ optional API note)."""

from __future__ import annotations

import argparse

from rich.console import Console

from wwe_data.pipeline.release import build_release
from wwe_data.reports.completeness_exports import write_completeness_from_exports

console = Console()


def run_phase5(version: str | None = None) -> int:
    console.rule("[bold]Phase 5 — Release packaging / API[/bold]")

    console.print("\n[cyan]1/2 Completeness refresh[/cyan]")
    report = write_completeness_from_exports()
    console.print(f"  report: {report}")

    console.print("\n[cyan]2/2 Release package[/cyan]")
    out = build_release(version=version)

    console.print("\n[green]Phase 5 complete.[/green]")
    console.print(f"  release: {out}")
    console.print("  API: pip install -e \".[api]\" && python -m wwe_data.api.app")
    console.print("  Docs: http://127.0.0.1:8000/docs")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 5 release packaging")
    parser.add_argument("--version", type=str, default=None)
    args = parser.parse_args()
    raise SystemExit(run_phase5(version=args.version))


if __name__ == "__main__":
    main()
