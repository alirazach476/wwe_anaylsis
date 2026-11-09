# WWE Dataset Validation Report (Phase 3)

_Generated: 2026-11-08T15:11:41.507528Z_

## Summary

- **events:** 424
- **matches:** 3383
- **participants:** 10897
- **wrestlers:** 2033
- **championships:** 840
- **match_championships:** 1766

- **Checks passed:** 15 / 15
- **Overall:** PASS

## Checks

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
