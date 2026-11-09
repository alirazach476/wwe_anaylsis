{{ config(materialized='table') }}

select
  e.event_year,
  count(distinct e.event_id) as events,
  sum(e.attendance) as attendance,
  count(m.match_key) as matches
from {{ source('analytics', 'dim_event') }} e
left join {{ source('analytics', 'fact_matches') }} m
  on e.event_key = m.event_key
group by 1
order by 1
