# Phase 5 — Release packaging & query API

**Status:** Implemented.

## What runs

```powershell
python -m wwe_data.pipeline.phase5
# optional pinned version:
python -m wwe_data.pipeline.phase5 --version 0.5.0

pip install -e ".[api]"
python -m wwe_data.api.app
# open http://127.0.0.1:8000/docs
```

## Outputs

| Path | Description |
| --- | --- |
| `data/releases/<version>/` | CSV/parquet exports, analytics, reports, docs |
| `data/releases/<version>/manifest.json` | Stats + file inventory |
| `data/releases/<version>/SHA256SUMS` | Checksums |
| `data/releases/<version>.zip` | Zip archive of the folder |
| `data/reports/completeness_report.md` | Regenerated from current exports |

## API endpoints

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/health` | Liveness + warehouse flag |
| GET | `/stats` | Event / match / wrestler counts |
| GET | `/events` | Filter by `year`, `series`, `status` |
| GET | `/events/{event_id}` | Event + match card |
| GET | `/matches` | Filter by event / year / title |
| GET | `/wrestlers/top` | Analytics top appearances |
| GET | `/mitb/cash-ins` | Phase 4 cash-in table |
| GET | `/analytics/year` | Year summary mart |

Uses SQLite warehouse when present; falls back to CSV exports.

## Notes

- Asuka (2020) has no structured cash-in row on the Wikipedia cash-in tables (note-only award path) — left unmatched on purpose
- Chamber entry order still null when Wikipedia only describes pods in prose
