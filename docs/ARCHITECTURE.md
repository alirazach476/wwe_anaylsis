# Architecture — WWE PLE Analytics Platform

## Layers

1. **Raw (immutable):** `data/exports/*.csv` from collection Phases 1–5  
2. **Cleaning:** `src/wwe_data/warehouse/cleaning.py` → `data/warehouse/stg_*.csv`  
3. **Dimensional warehouse:** `load_dimensional.py` → SQLite `wwe_analytics.sqlite` or Postgres (`docker-compose`)  
4. **Marts:** `materialize_marts.py` + dbt SQL under `dbt/models/marts/`  
5. **API:** FastAPI `src/wwe_data/api/app.py` (`/api/*`)  
6. **UI:** React + Vite + Plotly `frontend/`  
7. **Orchestration:** Airflow DAG `airflow/dags/wwe_warehouse_dag.py` (Compose profile `airflow`)

## Run locally

```powershell
python -m wwe_data.pipeline.clean
python -m wwe_data.warehouse.load_dimensional
python -m wwe_data.warehouse.materialize_marts
python -m wwe_data.api.app
cd frontend; npm install; npm run dev
```

Docker:

```powershell
docker compose up --build postgres api frontend
```

## Design constraints

- No fabricated historical rows  
- Null attendance ≠ 0  
- Championship analytics = PLE title changes only  
- Dashboard metrics from API/marts only  
