{{ config(materialized='table') }}

-- PLE-sourced title changes only (no off-PLE reign fabrication)
select
  c.championship_key,
  c.championship_id,
  c.championship_name,
  count(*) filter (where f.title_change) as title_changes,
  min(e.event_date) as first_change,
  max(e.event_date) as last_change
from {{ source('analytics', 'dim_championship') }} c
left join {{ source('analytics', 'fact_championship_changes') }} f
  on c.championship_key = f.championship_key
left join {{ source('analytics', 'dim_event') }} e
  on f.event_key = e.event_key
group by 1, 2, 3
