"""Full dataset refresh: inventory stamp → enrich → validate → analytics (no re-scrape by default)."""

from __future__ import annotations

import argparse

from rich.console import Console

from wwe_data.pipeline.phase3 import run_phase3
from wwe_data.pipeline.phase4 import run_phase4

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh analytics/enrichment layers from current exports"
    )
    parser.add_argument(
        "--rescrape-matches",
        action="store_true",
        help="Also re-run Phase 2 match collection (network-heavy)",
    )
    parser.add_argument(
        "--postgres",
        action="store_true",
        help="Reload PostgreSQL warehouse during Phase 3 step",
    )
    args = parser.parse_args()

    if args.rescrape_matches:
        from wwe_data.pipeline.matches import main as matches_main

        console.print("[cyan]Re-scraping match cards…[/cyan]")
        matches_main()

    console.print("[cyan]Phase 4 enrichment…[/cyan]")
    code = run_phase4()
    if code != 0:
        raise SystemExit(code)

    console.print("[cyan]Phase 3 warehouse + analytics…[/cyan]")
    raise SystemExit(run_phase3(postgres=args.postgres, skip_load=False))


if __name__ == "__main__":
    main()
