# Phase 1 Inventory Review Gate

**Status:** Ready for human review. Match scraping is blocked until you approve.

## Snapshot (latest run)

| Metric | Value |
| --- | ---: |
| Eligible events collected | ~421 |
| Match cards | 0 (deferred) |
| Missing must-consider series | 0 |
| Unclassified events | ~0–6 (after registry refresh) |
| Announced future events | present (`event_status=announced`) |
| Fabricated unannounced future | none |

Artifacts:

- `data/exports/events_inventory.csv`
- `data/exports/events_inventory.parquet`
- `data/processed/events_inventory.json`
- `data/reports/coverage_audit.md`
- `data/processed/dataset_stamp.json`

## What was fixed for series coverage

- Expandable registry in `config/event_series_registry.yaml`
- NXT TakeOver / Stand & Deliver / Deadline / Heatwave / Vengeance Day filtered
- Year-aware exclusions for modern NXT reuse of historical names (Battleground, GAB, Roadblock)
- Rowspan-safe Wikipedia HTML parser (drops attendance-as-name bugs)
- SNME same-day dedupe
- Must-consider alias awareness (Day 1 ↔ New Year's Revolution, The Bash ↔ GAB)

## How to review

1. Open `data/reports/coverage_audit.md`
2. Spot-check yearly counts vs known PPV calendars
3. Scan unclassified / conflict rows in the CSV (`verification_status`)
4. Add any newly discovered series to the registry
5. Re-run: `python -m wwe_data.pipeline.inventory`

## Approve next phase

When satisfied, say to proceed with **Phase 2 match collection**. See `docs/PHASE2_MATCH_COLLECTION.md`.
