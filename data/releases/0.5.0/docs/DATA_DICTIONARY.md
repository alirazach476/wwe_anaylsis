# Data dictionary

Canonical fields for the WWE PLE historical platform (2000–2027).

## Events (`events_inventory`)

| Field | Type | Notes |
| --- | --- | --- |
| `event_id` | string | Deterministic hash of date + normalized name |
| `event_name` | string | Display / branding name as sourced |
| `canonical_event_name` | string | Normalized series + year form |
| `event_series` | string | Registry series key |
| `event_year` | int | 2000–2027 |
| `event_date` / `event_end_date` | date | Multi-night uses end date when known |
| `event_type` | enum | `ppv` \| `ple` \| `special` \| `other` |
| `event_status` | enum | `completed` \| `announced` |
| `venue`, `city`, `state_province`, `country` | string | Null when unknown — never fabricated |
| `attendance` | int | Null when unknown |
| `verification_status` | enum | `verified` \| `single_source` \| `conflict` \| … |

## Matches (`matches`)

| Field | Type | Notes |
| --- | --- | --- |
| `match_id` | string | Hash of event + number + result text |
| `event_id` | string | FK → events |
| `match_number` | int | Card order when present |
| `match_type` / `match_stipulation` | string | From results table |
| `match_duration_seconds` | int | Parsed from `m:ss` / `h:mm:ss` |
| `match_result` | string | Raw Wikipedia/WWE result text |
| `winner` / `loser` | string | Parsed sides; null if unparseable |
| `is_title_match` / `is_main_event` / `is_preshow` | bool | Heuristics from stipulation/order |
| `special_match_kind` | string | `royal_rumble` \| `money_in_the_bank` \| `survivor_series` \| `elimination_chamber` |

## Participants & wrestlers

- `match_participants`: one row per wrestler appearance (`result` = win/loss/…; rumble fields when present)
- `wrestlers` / `wrestler_aliases`: canonical IDs from ring names (no birth-name invention)

## Championships

- `championships`: distinct title names seen on cards
- `match_championships`: link table; `title_change` inferred only when `(c)` placement is clear

## Special datasets

| Dataset | Contents |
| --- | --- |
| `special_royal_rumble` | Entrant order / eliminations when table-sourced |
| `special_money_in_the_bank` | Ladder winners + **cash-in fields** (Phase 4) |
| `special_mitb_cash_ins` | Full cash-in history from Wikipedia list page |
| `special_survivor_series` | Traditional / WarGames team outcomes |
| `special_elimination_chamber` | Winner + roster; entry order null unless structured |

## Analytics marts (`data/analytics`)

| Table | Grain |
| --- | --- |
| `dim_events` | One row per event + collection status |
| `fct_matches` | Matches joined to event dimensions |
| `event_year_summary` | Counts by year |
| `series_summary` | Counts by series |
| `wrestler_match_counts` | Career-ish PLE appearance stats |
| `title_changes` | Inferred title changes only |
| `event_geography` | City/country event counts |
| `mitb_cash_ins` | Phase 4 cash-in fact table |

## Hard rules

- Missing values stay null — no invented results, attendance, or future cards
- Announced events may have zero matches (`skipped_announced`)
- Wikipedia footnotes / color keys are not matches
