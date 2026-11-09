{{ config(materialized='table') }}

select
  e.event_key,
  e.event_id,
  e.event_name,
  e.event_series,
  e.event_year,
  e.event_date,
  e.event_status,
  e.attendance,
  c.country_name as country,
  v.venue_name,
  v.city,
  count(m.match_key) as matches,
  count(*) filter (where m.is_title_match) as title_matches,
  count(*) filter (where m.is_main_event) as main_events,
  avg(m.match_duration_seconds) as avg_duration
from {{ source('analytics', 'dim_event') }} e
left join {{ source('analytics', 'fact_matches') }} m
  on e.event_key = m.event_key
left join {{ source('analytics', 'dim_country') }} c
  on e.country_key = c.country_key
left join {{ source('analytics', 'dim_venue') }} v
  on e.venue_key = v.venue_key
group by 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
