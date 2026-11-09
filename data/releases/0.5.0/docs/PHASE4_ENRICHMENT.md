# Phase 4 — Enrichment, data dictionary, refresh

**Status:** Implemented.

## What runs

```powershell
python -m wwe_data.pipeline.phase4
# or
python -m wwe_data.pipeline.enrich
python -m wwe_data.pipeline.refresh
```

## What was added

- **MITB cash-ins** from [List of Money in the Bank ladder matches](https://en.wikipedia.org/wiki/List_of_Money_in_the_Bank_ladder_matches) (MediaWiki API)
  - New export: `data/exports/special_mitb_cash_ins.csv`
  - Ladder-winner rows get `cash_in_*` fields when holder + date align
- **Chamber** rows stay without fabricated entry order (prose-only on most pages)
- **Data dictionary:** `docs/DATA_DICTIONARY.md`
- **Refresh CLI:** rematerialize enrichment + warehouse analytics

## Hard rules preserved

- No invented cash-ins or chamber entry orders
- Unmatched ladder winners remain `needs_review` (briefcase transfers, unused contracts, futures)
