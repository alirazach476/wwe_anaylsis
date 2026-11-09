{{ config(materialized='table') }}

select
  fact_id,
  match_id,
  event_key,
  winner_name,
  cash_in_date,
  cash_in_event,
  cash_in_opponent,
  cash_in_outcome,
  championship_won
from {{ source('analytics', 'fact_money_in_the_bank') }}
