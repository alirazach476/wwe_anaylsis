# Phase 3 — Validation, warehouse, analytics, dashboard

**Status:** Implemented.

## What runs

```powershell
python -m wwe_data.pipeline.phase3
# or step by step:
python -m wwe_data.pipeline.validate
python -m wwe_data.db.load_all
python -m wwe_data.analytics.materialize
streamlit run dashboard/app.py
```

PostgreSQL instead of local SQLite:

```powershell
python -m wwe_data.pipeline.phase3 --postgres
# requires WWE_DATABASE_URL in .env
```

## Outputs

| Path | Description |
| --- | --- |
| `data/reports/validation_report.md` | Referential integrity + window checks |
| `data/processed/wwe_history.sqlite` | Local warehouse (default) |
| `data/analytics/*.csv` (+ parquet) | Marts: year/series/wrestler/title/geo |
| `dbt/` | Optional Postgres dbt project mirroring marts |
| `dashboard/app.py` | Streamlit explorer |

## Checks included

- Required export files present
- Unique `event_id` / `match_id` / `wrestler_id` / `championship_id`
- FK integrity: matches→events, participants→matches/wrestlers, title links
- Event year window 2000–2027
- No NXT TakeOver in inventory
- Completed-event card coverage

## Design notes

- SQLite is the default warehouse so Phase 3 works without a local Postgres install
- Analytics materialize is the offline equivalent of `dbt run`
- Dashboard reads `data/analytics` first, then falls back to `data/exports`
