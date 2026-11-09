select
  m.match_id,
  m.event_id,
  e.event_name,
  e.event_series,
  e.event_year,
  e.event_date,
  e.event_status,
  e.city,
  e.country,
  m.match_number,
  m.match_name,
  m.match_type,
  m.match_stipulation,
  m.match_duration_seconds,
  m.match_result,
  m.winner,
  m.loser,
  m.is_title_match,
  m.is_main_event,
  m.is_preshow,
  m.match_status,
  m.verification_status
from {{ ref('stg_matches') }} m
left join {{ ref('stg_events') }} e
  on m.event_id = e.event_id
