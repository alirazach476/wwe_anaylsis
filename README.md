# WWE Anaylsis

**Premium Live Event analytics for WWE — 2000 to 2027.**

A broadcast-style dashboard and FastAPI backend over a curated PLE warehouse: events, matches, wrestlers, championships, landmark records, and interactive Plotly charts — themed to each event’s logo palette.

<p align="center">
  <a href="https://wwe-anaylsis.vercel.app">
    <img src="https://img.shields.io/badge/Live_Demo-Vercel-black?style=for-the-badge&logo=vercel" alt="Live on Vercel" />
  </a>
  &nbsp;
  <img src="https://img.shields.io/badge/Stack-React_+_FastAPI-E31C25?style=for-the-badge" alt="Stack" />
  &nbsp;
  <img src="https://img.shields.io/badge/Coverage-2000–2027-111111?style=for-the-badge" alt="Coverage" />
</p>

<p align="center">
  <strong>🚀 Production:</strong>
  <a href="https://wwe-anaylsis.vercel.app">https://wwe-anaylsis.vercel.app</a>
</p>

---

## Screenshots of the product surface

| Surface | Highlights |
| --- | --- |
| **Home** | Catalog KPIs, attendance trends, match/event chart gallery |
| **Events** | Poster-style cards, series filters, deep event detail |
| **Matches** | Duration, finish methods, filtered mix analysis |
| **Wrestlers** | Full deduped roster, Man/Woman avatars, career detail |
| **Championships** | Title landscapes including Crown Jewel featured belts |
| **Timeline** | Curated historical landmarks (Cena 17, Reigns 1,316 days, weight records, …) |
| **API** | FastAPI marts endpoints for every page |

Event chrome picks colors from each PLE logo so WrestleMania, Summerslam, Royal Rumble, and the rest feel distinct — not a generic purple dashboard.

---

## Architecture

```text
Wikipedia / registry  →  clean  →  dimensional warehouse
                                      ↓
                                   marts CSV
                                      ↓
                         FastAPI  (/api/*)  +  React (Vite)
                                      ↓
                              Vercel (static + Python ASGI)
```

- **Frontend:** React 18, TypeScript, Vite, Plotly, React Router  
- **Backend:** FastAPI serving analytics marts (pandas)  
- **Deploy:** `vercel.json` builds `frontend/dist` and routes `/api` → `api/index.py`  
- **Project name on Vercel:** `wwe_anaylsis`

---

## Quick start (local)

```powershell
# API
pip install -e ".[api,dev]"
python -m wwe_data.api.app

# Dashboard (new terminal)
cd frontend
npm install
npm run dev
```

API defaults to `http://127.0.0.1:8000`. Vite proxies `/api` and `/health`.

Optional full pipeline:

```powershell
python -m wwe_data.pipeline.clean
python -m wwe_data.warehouse.load_dimensional
python -m wwe_data.warehouse.materialize_marts
```

Docker: `docker compose up --build postgres api frontend`

---

## Deploy

Live on Vercel as **`wwe_anaylsis`**:

**https://wwe-anaylsis.vercel.app**

```powershell
vercel deploy --prod --yes
```

Key pieces:

- `api/index.py` — ASGI entry exporting FastAPI `app`
- `api/requirements.txt` — lean serverless deps
- `data/warehouse/marts/**` + `runtime_exports/**` — bundled via `includeFiles`
- `frontend/public/logos/files` — event logos for themes & posters

---

## Repo layout

```text
api/                 Vercel Python entry
frontend/            React dashboard
src/wwe_data/        Collectors, warehouse, API, analytics
data/warehouse/      Marts + runtime export CSVs
config/              Event series registry & eligibility
docs/                Architecture & data dictionary
scripts/             One-off data fixes (e.g. Crown Jewel)
```

---

## Docs

- [DATA_INVENTORY](docs/DATA_INVENTORY.md)
- [ARCHITECTURE](docs/ARCHITECTURE.md)
- [DATA_DICTIONARY](docs/DATA_DICTIONARY.md)

---

## Notes

- Scope is **Premium Live Events** (and allowlisted specials) — not weekly TV or house shows.
- Landmark records on Timeline are curated where mart aggregates diverge from official all-time marks.
- Collection uses MediaWiki’s documented API with an expandable series registry.

---

<p align="center">
  Built for the ring — analyzed for the board.
  <br />
  <a href="https://wwe-anaylsis.vercel.app">Open the live dashboard →</a>
</p>
