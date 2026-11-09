# Phase 2 — Match collection

**Status:** Implemented (Wikipedia MediaWiki API).

## What runs

```powershell
python -m wwe_data.pipeline.matches
python -m wwe_data.pipeline.matches --retry-failed
```

## Outputs

- `data/exports/matches.csv` (+ parquet)
- `data/exports/match_participants.csv`
- `data/exports/wrestlers.csv`, `wrestler_aliases.csv`
- `data/exports/championships.csv`, `match_championships.csv`
- `data/exports/special_royal_rumble.csv`
- `data/exports/special_money_in_the_bank.csv`
- `data/exports/special_survivor_series.csv`
- `data/exports/special_elimination_chamber.csv`
- `data/reports/completeness_report.md`

## Known gaps (not fabricated)

- Most **Tribute to the Troops** cards — Wikipedia page lacks standard results tables
- A few early **SNME** editions without dedicated article pages
- **Announced future** events — skipped on purpose
- MITB cash-in / Chamber entry-order fields left **null** when not on the event page

## Hard rules

- No fabricated match results
- Respect robots.txt / ToS
- Prefer APIs and permitted pages
- Flag conflicts / empty cards for manual review
