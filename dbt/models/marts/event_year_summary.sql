select
  e.event_year,
  count(distinct e.event_id) as events,
  count(*) filter (where e.event_status = 'completed') as completed,
  count(*) filter (where e.event_status = 'announced') as announced,
  count(m.match_id) as matches,
  count(*) filter (where m.is_title_match) as title_matches,
  count(*) filter (where m.is_main_event) as main_events
from {{ ref('stg_events') }} e
left join {{ ref('stg_matches') }} m
  on e.event_id = m.event_id
group by 1
order by 1
