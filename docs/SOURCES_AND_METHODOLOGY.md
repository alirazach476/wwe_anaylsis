# Sources, Limitations, and Collection Methodology

## Scope

Eligible WWE-promoted major events from **2000-01-01** to **2027-12-31**:

- Traditional PPVs and modern Premium Live Events (PLEs)
- International / Saudi specials when listed as WWE supercards
- Saturday Night's Main Event (and Sunday Night's Main Event if announced)
- Tribute to the Troops and other **allowlisted** specials

Explicitly out of scope: weekly Raw/SmackDown/NXT, NXT TakeOver, house shows, non-WWE promotions.

## Primary sources (Phase 1)

| Source | Access method | Role |
| --- | --- | --- |
| [List of WWE pay-per-view and livestreaming supercards](https://en.wikipedia.org/wiki/List_of_WWE_pay-per-view_and_livestreaming_supercards) | MediaWiki API (`action=parse`) | Master PPV/PLE inventory |
| [Saturday Night's Main Event](https://en.wikipedia.org/wiki/Saturday_Night%27s_Main_Event) | MediaWiki API | SNME specials 2000–2027 |
| [List of WWE television specials](https://en.wikipedia.org/wiki/List_of_WWE_television_specials) | MediaWiki API | Allowlisted specials only |

Wikipedia is used via the **documented MediaWiki API**, with caching, User-Agent identification, and request throttling.

## Secondary sources (planned after inventory review)

| Source | Notes |
| --- | --- |
| WWE.com | Official announced events / metadata |
| The SmackDown Hotel | Rich historical DB; often JS-rendered — respect robots/ToS; prefer static/schedule pages or permitted exports |
| Online World of Wrestling | Results archive — robots check before scrape |
| WrestlingOracle | Event listings — robots/ToS check |

`wwe_data.collectors.secondary_sources.audit_secondary_robots()` records robots.txt status. **No bypass** of auth, paywalls, CAPTCHAs, or access controls.

## Event series registry

`config/event_series_registry.yaml` is the expandable registry. New historical series discovered during research are added here so they are automatically classified on subsequent runs. Unmatched eligible events are labeled `Unclassified Eligible` (not dropped) for coverage audit.

## Date & status rules

- Historical events: verified dates from sources; `event_status = completed` when `event_date <= today`
- Announced future events: stored with `event_status = announced`
- Unannounced future events: **not fabricated**
- Dataset designed to refresh through 2027-12-31
- `dataset_stamp.json` records `last_collection_timestamp`

## Data quality

- Nulls for missing values — never invented attendance/results
- Deterministic `event_id` from date + normalized name
- Multi-source agreement → `verified`; disagreement → `conflict` + notes
- Ring names / historical branding preserved in `event_name`; series in `event_series`

## Limitations (Phase 1)

- Inventory is primarily Wikipedia-derived; secondary cross-validation pending
- Match cards, participants, championships, and special-match datasets are **not** collected yet
- Some Wikipedia tables vary by year (brand color keys, multi-night WrestleMania); parser uses HTML tables and skips continuation venue-only rows
- Attendance figures inherit source uncertainty
- JS-heavy archive sites may require Playwright **only where permitted**

## Gate

Do **not** start match scraping until:

1. Coverage audit is reviewed (`data/reports/coverage_audit.md`)
2. Missing must-consider series are explained or added to the registry
3. Unclassified events are classified or confirmed eligible
