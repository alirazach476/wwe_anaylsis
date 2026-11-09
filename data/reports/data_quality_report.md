# Data Quality Report

_Generated: 2026-11-08T15:22:20.147062Z_

## Cleaning summary

- **stg_events:** 424
- **stg_matches:** 3383
- **participants_deduped:** 41
- **stg_match_participants:** 10856
- **stg_wrestlers:** 2033
- **stg_wrestler_aliases:** 2033
- **stg_championships:** 840
- **stg_match_championships:** 1766
- **stg_special_royal_rumble:** 1155
- **stg_special_money_in_the_bank:** 37
- **stg_special_mitb_cash_ins:** 36
- **stg_special_survivor_series:** 52
- **stg_special_elimination_chamber:** 38
- **stg_event_match_status:** 424

## Integrity checks

- Overall: PASS

| Check | Status | Detail | Count |
| --- | --- | --- | ---: |
| `required_exports_present` | PASS | ok | 0 |
| `unique_events` | PASS | ok | 0 |
| `unique_matches` | PASS | ok | 0 |
| `unique_wrestlers` | PASS | ok | 0 |
| `unique_championships` | PASS | ok | 0 |
| `matches_event_fk` | PASS | ok | 0 |
| `participants_match_fk` | PASS | ok | 0 |
| `participants_wrestler_fk` | PASS | ok | 0 |
| `aliases_wrestler_fk` | PASS | ok | 0 |
| `match_championships_match_fk` | PASS | ok | 0 |
| `match_championships_championship_fk` | PASS | ok | 0 |
| `completed_events_have_cards` | PASS | ok | 0 |
| `event_year_window` | PASS | ok | 0 |
| `no_nxt_takeover` | PASS | ok | 0 |
| `title_matches_have_championship_link` | PASS | 45 is_title_match rows without championship link (informational) | 45 |

## Null-vs-zero policy

- `attendance` null means unknown — never treated as 0 in averages without explicit filter.
- `match_duration_seconds` null means unavailable on source page.
- Boolean false is genuine false; null is unavailable.

## Participant soft duplicates

- Raw rows: 10897
- After coalesce: 10856
- Removed: 41

## Field null rates (events)

- `attendance`: 10.38%
- `brand`: 99.76%
- `venue`: 0.24%
- `broadcast_platform`: 100.0%

## Field null rates (matches)

- `match_duration_seconds`: 6.38%
- `winner`: 1.36%
- `loser`: 3.9%
- `match_type`: 2.9%

## Known analytical gaps

- Championship category/introduction/retirement dates unavailable
- Chamber entry/elimination order unavailable
- Brand sparsely populated
- Championship analytics limited to PLE title changes
