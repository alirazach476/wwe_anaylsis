select
  w.wrestler_id,
  w.canonical_name,
  count(distinct p.match_id) as matches,
  count(*) filter (where p.result = 'win') as wins,
  count(*) filter (where p.result = 'loss') as losses,
  count(*) filter (where m.is_title_match) as title_matches,
  count(*) filter (where m.is_main_event) as main_events,
  min(e.event_year) as first_year,
  max(e.event_year) as last_year
from {{ source('raw', 'wrestlers') }} w
left join {{ ref('stg_participants') }} p
  on w.wrestler_id = p.wrestler_id
left join {{ ref('stg_matches') }} m
  on p.match_id = m.match_id
left join {{ ref('stg_events') }} e
  on m.event_id = e.event_id
group by 1, 2
order by matches desc
