select
  match_id,
  event_id,
  match_number,
  match_name,
  match_type,
  match_stipulation,
  match_duration_seconds,
  match_result,
  winner,
  loser,
  is_title_match,
  is_main_event,
  is_preshow,
  match_status,
  source_url,
  verification_status
from {{ source('raw', 'matches') }}
