{{ config(materialized='table') }}

select
  m.match_key,
  m.match_id,
  e.event_id,
  e.event_name,
  e.event_series,
  e.event_year,
  e.event_date,
  m.match_number,
  mt.match_type_group,
  m.match_duration_seconds,
  m.winner_name,
  m.loser_name,
  m.is_title_match,
  m.is_main_event,
  m.is_preshow,
  m.special_match_kind,
  m.match_result
from {{ source('analytics', 'fact_matches') }} m
left join {{ source('analytics', 'dim_event') }} e
  on m.event_key = e.event_key
left join {{ source('analytics', 'dim_match_type') }} mt
  on m.match_type_key = mt.match_type_key
