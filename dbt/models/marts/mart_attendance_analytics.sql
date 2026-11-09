{{ config(materialized='table') }}

select
  a.event_key,
  e.event_id,
  e.event_name,
  e.event_series,
  e.event_date,
  a.event_year,
  a.attendance,
  c.country_name,
  v.venue_name,
  v.city
from {{ source('analytics', 'fact_event_attendance') }} a
left join {{ source('analytics', 'dim_event') }} e
  on a.event_key = e.event_key
left join {{ source('analytics', 'dim_country') }} c
  on a.country_key = c.country_key
left join {{ source('analytics', 'dim_venue') }} v
  on a.venue_key = v.venue_key
