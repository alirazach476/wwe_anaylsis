{{ config(materialized='table') }}

select
  r.fact_id,
  r.entry_number,
  r.elimination_order,
  r.eliminated_by,
  r.time_in_match_seconds,
  r.eliminations_made,
  r.is_winner,
  r.is_final_four,
  w.canonical_name,
  e.event_name,
  e.event_year,
  e.event_date
from {{ source('analytics', 'fact_royal_rumble') }} r
left join {{ source('analytics', 'dim_wrestler') }} w
  on r.wrestler_key = w.wrestler_key
left join {{ source('analytics', 'dim_event') }} e
  on r.event_key = e.event_key
