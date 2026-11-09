-- Dimensional warehouse schemas
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.pipeline_runs (
    run_id              TEXT PRIMARY KEY,
    started_at          TIMESTAMP NOT NULL,
    finished_at         TIMESTAMP,
    status              TEXT NOT NULL,
    records_loaded      INTEGER DEFAULT 0,
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key            INTEGER PRIMARY KEY,
    full_date           DATE NOT NULL,
    year                INTEGER NOT NULL,
    month               INTEGER NOT NULL,
    day                 INTEGER NOT NULL,
    quarter             INTEGER NOT NULL,
    decade              INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_country (
    country_key         SERIAL PRIMARY KEY,
    country_name        TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS analytics.dim_venue (
    venue_key           SERIAL PRIMARY KEY,
    venue_name          TEXT,
    city                TEXT,
    state_province      TEXT,
    country_name        TEXT,
    UNIQUE (venue_name, city, country_name)
);

CREATE TABLE IF NOT EXISTS analytics.dim_brand (
    brand_key           SERIAL PRIMARY KEY,
    brand_name          TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS analytics.dim_team (
    team_key            SERIAL PRIMARY KEY,
    team_id             TEXT UNIQUE,
    team_name           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_match_type (
    match_type_key      SERIAL PRIMARY KEY,
    match_type_group    TEXT NOT NULL UNIQUE,
    match_type_raw      TEXT
);

CREATE TABLE IF NOT EXISTS analytics.dim_championship (
    championship_key    SERIAL PRIMARY KEY,
    championship_id     TEXT NOT NULL UNIQUE,
    championship_name   TEXT NOT NULL,
    championship_name_norm TEXT,
    championship_category TEXT,
    introduction_date   DATE,
    retirement_date     DATE
);

CREATE TABLE IF NOT EXISTS analytics.dim_wrestler (
    wrestler_key        SERIAL PRIMARY KEY,
    wrestler_id         TEXT NOT NULL UNIQUE,
    canonical_name      TEXT NOT NULL,
    debut_date          DATE,
    retirement_date     DATE,
    nationality         TEXT
);

CREATE TABLE IF NOT EXISTS analytics.dim_event (
    event_key           SERIAL PRIMARY KEY,
    event_id            TEXT NOT NULL UNIQUE,
    event_name          TEXT NOT NULL,
    canonical_event_name TEXT,
    event_series        TEXT,
    event_year          INTEGER,
    event_date          DATE,
    event_end_date      DATE,
    event_type          TEXT,
    event_status        TEXT,
    venue_key           INTEGER REFERENCES analytics.dim_venue(venue_key),
    country_key         INTEGER REFERENCES analytics.dim_country(country_key),
    brand_key           INTEGER REFERENCES analytics.dim_brand(brand_key),
    date_key            INTEGER REFERENCES analytics.dim_date(date_key),
    attendance          INTEGER,
    verification_status TEXT
);

CREATE TABLE IF NOT EXISTS analytics.fact_matches (
    match_key           SERIAL PRIMARY KEY,
    match_id            TEXT NOT NULL UNIQUE,
    event_key           INTEGER REFERENCES analytics.dim_event(event_key),
    match_type_key      INTEGER REFERENCES analytics.dim_match_type(match_type_key),
    match_number        INTEGER,
    match_duration_seconds INTEGER,
    winner_name         TEXT,
    loser_name          TEXT,
    is_title_match      BOOLEAN,
    is_main_event       BOOLEAN,
    is_preshow          BOOLEAN,
    match_status        TEXT,
    special_match_kind  TEXT,
    match_result        TEXT
);

CREATE TABLE IF NOT EXISTS analytics.fact_match_participants (
    fact_id             SERIAL PRIMARY KEY,
    match_key           INTEGER REFERENCES analytics.fact_matches(match_key),
    wrestler_key        INTEGER REFERENCES analytics.dim_wrestler(wrestler_key),
    team_key            INTEGER REFERENCES analytics.dim_team(team_key),
    participant_role    TEXT,
    result              TEXT,
    entry_number        INTEGER,
    elimination_order   INTEGER,
    eliminated_by       TEXT,
    time_in_match_seconds INTEGER,
    UNIQUE (match_key, wrestler_key, participant_role)
);

CREATE TABLE IF NOT EXISTS analytics.fact_championship_changes (
    fact_id             SERIAL PRIMARY KEY,
    match_key           INTEGER REFERENCES analytics.fact_matches(match_key),
    championship_key    INTEGER REFERENCES analytics.dim_championship(championship_key),
    event_key           INTEGER REFERENCES analytics.dim_event(event_key),
    champion_after      TEXT,
    title_change        BOOLEAN,
    title_retained      BOOLEAN,
    title_vacated       BOOLEAN,
    UNIQUE (match_key, championship_key)
);

CREATE TABLE IF NOT EXISTS analytics.fact_royal_rumble (
    fact_id             SERIAL PRIMARY KEY,
    match_key           INTEGER,
    event_key           INTEGER,
    wrestler_key        INTEGER,
    entry_number        INTEGER,
    elimination_order   INTEGER,
    eliminated_by       TEXT,
    time_in_match_seconds INTEGER,
    eliminations_made   INTEGER,
    is_winner           BOOLEAN,
    is_final_four       BOOLEAN
);

CREATE TABLE IF NOT EXISTS analytics.fact_money_in_the_bank (
    fact_id             SERIAL PRIMARY KEY,
    match_id            TEXT,
    event_key           INTEGER,
    winner_name         TEXT,
    cash_in_date        DATE,
    cash_in_event       TEXT,
    cash_in_opponent    TEXT,
    cash_in_outcome     TEXT,
    championship_won    TEXT
);

CREATE TABLE IF NOT EXISTS analytics.fact_survivor_series (
    fact_id             SERIAL PRIMARY KEY,
    match_id            TEXT,
    event_key           INTEGER,
    match_format        TEXT,
    winning_side        TEXT,
    losing_side         TEXT,
    survivors           TEXT
);

CREATE TABLE IF NOT EXISTS analytics.fact_event_attendance (
    event_key           INTEGER PRIMARY KEY REFERENCES analytics.dim_event(event_key),
    attendance          INTEGER,
    country_key         INTEGER,
    venue_key           INTEGER,
    event_year          INTEGER
);

CREATE INDEX IF NOT EXISTS ix_fact_matches_event ON analytics.fact_matches(event_key);
CREATE INDEX IF NOT EXISTS ix_fact_participants_wrestler ON analytics.fact_match_participants(wrestler_key);
CREATE INDEX IF NOT EXISTS ix_dim_event_year ON analytics.dim_event(event_year);
