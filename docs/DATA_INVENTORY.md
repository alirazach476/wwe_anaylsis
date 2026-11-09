# Data Inventory — WWE PLE Platform (2000–2027)

_Generated from actual repository exports. Originals under `data/exports/` are immutable raw sources._

## Scope

Eligible WWE-promoted PPVs / Premium Live Events / allowlisted specials only.  
**Excluded:** Raw, SmackDown, NXT, NXT TakeOver, weekly TV, regular house shows.

## Dataset catalog

| File | Rows | Primary key / grain | Notes |
| --- | ---: | --- | --- |
| `events_inventory.csv` | 424 | `event_id` | 419 completed, 5 announced |
| `matches.csv` | 3383 | `match_id` | Footnotes stripped (Phase 3) |
| `match_participants.csv` | 10897 | `(match_id, wrestler_id, participant_role)` | 41 soft dups (Rumble) |
| `wrestlers.csv` | 2033 | `wrestler_id` | |
| `wrestler_aliases.csv` | 2033 | `(wrestler_id, ring_name)` | |
| `championships.csv` | 840 | `championship_id` | category/dates 100% null |
| `match_championships.csv` | 1766 | `(match_id, championship_id)` | `champion_before` 100% null |
| `special_royal_rumble.csv` | 1155 | entrant per rumble match | entry_number complete |
| `special_money_in_the_bank.csv` | 37 | ladder winner rows | cash-in join Phase 4 |
| `special_mitb_cash_ins.csv` | 36 | cash-in history | Wikipedia list page |
| `special_survivor_series.csv` | 52 | SS / WarGames | |
| `special_elimination_chamber.csv` | 38 | chamber matches | entry/elim order null |
| `event_match_status.csv` | 424 | `event_id` | collection metadata |

Analytics marts (derived): `data/analytics/*.csv`.  
SQLite warehouse (optional local): `data/processed/wwe_history.sqlite`.  
Release package: `data/releases/0.5.0/`.

## Relationships

```
events 1—N matches
matches 1—N match_participants N—1 wrestlers
matches 1—N match_championships N—1 championships
events 1—1 event_match_status
```

**FK check (exports):** 0 orphan match→event, participant→match/wrestler, match_championship→match/championship.

## Null / quality highlights

| Field | Approx null % | Policy |
| --- | ---: | --- |
| `events.attendance` | 10.4 | Keep null; never coerce to 0 |
| `events.brand` | 99.8 | Unknown member in dim_brand |
| `matches.match_duration_seconds` | 6.4 | Keep null |
| `matches.match_name` | 100 | Unused |
| `championships.introduction/retirement_date` | 100 | Unavailable |
| `match_championships.champion_before` | 100 | Unavailable from parse |
| Chamber `entry_order` | 100 | Not fabricated |
| Participant `team_id` | 100 | dim_team unknown only |

## Analytical limitations (do not fabricate)

1. Championship lineage = **PLE title changes only** (no full off-PLE reign calendar).
2. Brand / team sparsely populated.
3. Chamber entry/elimination order not structured on sources.
4. MITB Asuka (2020) unmatched (Wikipedia note-only path).
5. Imagery not in dataset — dashboard uses series CSS themes only.

## Lineage

Wikipedia MediaWiki API → collectors → `data/exports` → cleaning (`data/warehouse`) → Postgres staging → dbt dims/facts/marts → FastAPI → React dashboard.
