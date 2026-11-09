select
  match_id,
  wrestler_id,
  team_id,
  participant_role,
  result,
  entry_number,
  elimination_order,
  eliminated_by,
  time_in_match_seconds
from {{ source('raw', 'match_participants') }}
