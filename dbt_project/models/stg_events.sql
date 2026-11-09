-- Staging model for events (activate after PostgreSQL load)
select
    event_id,
    event_name,
    canonical_event_name,
    event_series,
    event_year,
    event_date,
    event_end_date,
    event_type,
    event_status,
    venue,
    city,
    state_province,
    country,
    attendance,
    brand,
    verification_status,
    last_updated
from {{ source('wwe', 'events') }}
