{{ config(materialized='table') }}

select
  w.wrestler_key,
  w.wrestler_id,
  w.canonical_name,
  count(distinct p.match_key) as matches,
  count(*) filter (where p.result = 'win') as wins,
  count(*) filter (where p.result = 'loss') as losses,
  count(*) filter (where m.is_title_match) as title_matches,
  count(*) filter (where m.is_main_event) as main_events,
  min(e.event_year) as first_year,
  max(e.event_year) as last_year,
  case
    when count(*) filter (where p.result in ('win', 'loss')) = 0 then null
    else round(
      count(*) filter (where p.result = 'win')::numeric
      / nullif(count(*) filter (where p.result in ('win', 'loss')), 0),
      4
    )
  end as win_pct
from {{ source('analytics', 'dim_wrestler') }} w
left join {{ source('analytics', 'fact_match_participants') }} p
  on w.wrestler_key = p.wrestler_key
left join {{ source('analytics', 'fact_matches') }} m
  on p.match_key = m.match_key
left join {{ source('analytics', 'dim_event') }} e
  on m.event_key = e.event_key
group by 1, 2, 3
