"""Phase 4 enrichment: special-match depth from sourced Wikipedia pages."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console

from wwe_data.collectors.wikipedia_mitb_cashins import (
    enrich_mitb_winner_rows,
    fetch_mitb_cash_ins,
)
from wwe_data.config import get_settings

console = Console()


def _write_dataset(name: str, rows: list[dict], exports: Path, processed: Path) -> Path:
    df = pd.DataFrame(rows)
    csv_path = exports / f"{name}.csv"
    parquet_path = exports / f"{name}.parquet"
    json_path = processed / f"{name}.json"
    df.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    try:
        df.to_parquet(parquet_path, index=False)
    except Exception:
        pass
    return csv_path


def enrich_specials() -> dict[str, Path]:
    settings = get_settings()
    exports = settings.exports_dir
    processed = settings.processed_dir

    mitb_path = exports / "special_money_in_the_bank.csv"
    if not mitb_path.exists():
        raise FileNotFoundError(mitb_path)

    mitb_rows = pd.read_csv(mitb_path).where(pd.notna, None).to_dict(orient="records")
    console.print("Fetching MITB cash-in history from Wikipedia…")
    cash_ins = fetch_mitb_cash_ins()
    # Drop helper key before export
    cash_export = [{k: v for k, v in row.items() if k != "case_holder_norm"} for row in cash_ins]
    enriched = enrich_mitb_winner_rows(mitb_rows, cash_ins)

    def _has_date(value) -> bool:
        if value is None:
            return False
        try:
            if value != value:  # NaN
                return False
        except Exception:
            pass
        text = str(value).strip().lower()
        return text not in {"", "nan", "none"}

    filled = sum(1 for r in enriched if _has_date(r.get("cash_in_date")))
    console.print(
        f"  cash-ins sourced: {len(cash_ins)}; "
        f"ladder winners enriched: {filled}/{len(enriched)}"
    )

    # Chamber: keep entry/elimination order null unless a structured source exists
    chamber_path = exports / "special_elimination_chamber.csv"
    chamber_rows: list[dict] = []
    if chamber_path.exists():
        chamber = pd.read_csv(chamber_path).where(pd.notna, None).to_dict(orient="records")
        for row in chamber:
            out = dict(row)
            if out.get("winner") and out.get("participants"):
                out["verification_status"] = "single_source"
            chamber_rows.append(out)

    paths = {
        "special_mitb_cash_ins": _write_dataset(
            "special_mitb_cash_ins", cash_export, exports, processed
        ),
        "special_money_in_the_bank": _write_dataset(
            "special_money_in_the_bank", enriched, exports, processed
        ),
    }
    if chamber_rows:
        paths["special_elimination_chamber"] = _write_dataset(
            "special_elimination_chamber", chamber_rows, exports, processed
        )

    stamp = {
        "phase": "enrichment",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "mitb_cash_ins": len(cash_ins),
        "mitb_winners_enriched": filled,
        "mitb_winners_total": len(enriched),
        "chamber_rows": len(chamber_rows),
        "notes": [
            "MITB cash-ins from Wikipedia List of Money in the Bank ladder matches",
            "Chamber entry/elimination order left null when not structured on source pages",
        ],
    }
    stamp_path = processed / "dataset_stamp_enrichment.json"
    stamp_path.write_text(json.dumps(stamp, indent=2), encoding="utf-8")
    paths["stamp"] = stamp_path
    return paths


def main() -> None:
    paths = enrich_specials()
    console.print("[green]Phase 4 enrichment complete[/green]")
    for k, v in paths.items():
        console.print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
