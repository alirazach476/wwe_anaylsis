-- WWE Historical PLE Platform — PostgreSQL schema
-- Apply with: psql $DATABASE_URL -f src/wwe_data/db/schema.sql
-- Or: python -c "from wwe_data.db import create_all; create_all()"

CREATE TABLE IF NOT EXISTS events (
    event_id            VARCHAR(64) PRIMARY KEY,
    event_name          VARCHAR(255) NOT NULL,
    canonical_event_name VARCHAR(255) NOT NULL,
    event_series        VARCHAR(128),
    event_year          INTEGER NOT NULL,
    event_date          DATE NOT NULL,
    event_end_date      DATE,
    event_type          VARCHAR(64),
    event_status        VARCHAR(32),
    venue               VARCHAR(255),
    city                VARCHAR(128),
    state_province      VARCHAR(128),
    country             VARCHAR(128),
    attendance          INTEGER,
    broadcast_platform  VARCHAR(128),
    brand               VARCHAR(64),
    official_url        TEXT,
    source_url          TEXT,
    verification_status VARCHAR(32),
    last_updated        TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_events_year ON events (event_year);
CREATE INDEX IF NOT EXISTS ix_events_date ON events (event_date);
CREATE INDEX IF NOT EXISTS ix_events_status ON events (event_status);
CREATE INDEX IF NOT EXISTS ix_events_series ON events (event_series);

CREATE TABLE IF NOT EXISTS wrestlers (
    wrestler_id      VARCHAR(64) PRIMARY KEY,
    canonical_name   VARCHAR(255) NOT NULL,
    debut_date       DATE,
    retirement_date  DATE,
    nationality      VARCHAR(128),
    source_url       TEXT
);

CREATE INDEX IF NOT EXISTS ix_wrestlers_name ON wrestlers (canonical_name);

CREATE TABLE IF NOT EXISTS wrestler_aliases (
    id               SERIAL PRIMARY KEY,
    wrestler_id      VARCHAR(64) NOT NULL REFERENCES wrestlers (wrestler_id),
    ring_name        VARCHAR(255) NOT NULL,
    alias_start_date DATE,
    alias_end_date   DATE,
    UNIQUE (wrestler_id, ring_name)
);

CREATE TABLE IF NOT EXISTS teams (
    team_id         VARCHAR(64) PRIMARY KEY,
    team_name       VARCHAR(255) NOT NULL,
    team_start_date DATE,
    team_end_date   DATE
);

CREATE TABLE IF NOT EXISTS matches (
    match_id                VARCHAR(64) PRIMARY KEY,
    event_id                VARCHAR(64) NOT NULL REFERENCES events (event_id),
    match_number            INTEGER,
    match_name              VARCHAR(255),
    match_type              VARCHAR(128),
    match_stipulation       TEXT,
    match_duration_seconds  INTEGER,
    match_result            TEXT,
    winner                  VARCHAR(255),
    loser                   VARCHAR(255),
    is_title_match          BOOLEAN,
    is_main_event           BOOLEAN,
    is_preshow              BOOLEAN,
    match_status            VARCHAR(32),
    source_url              TEXT,
    verification_status     VARCHAR(32)
);

CREATE INDEX IF NOT EXISTS ix_matches_event ON matches (event_id);

CREATE TABLE IF NOT EXISTS match_participants (
    id                      SERIAL PRIMARY KEY,
    match_id                VARCHAR(64) NOT NULL REFERENCES matches (match_id),
    wrestler_id             VARCHAR(64) NOT NULL REFERENCES wrestlers (wrestler_id),
    team_id                 VARCHAR(64) REFERENCES teams (team_id),
    participant_role        VARCHAR(64),
    result                  VARCHAR(64),
    entry_number            INTEGER,
    elimination_order       INTEGER,
    eliminated_by           VARCHAR(255),
    time_in_match_seconds   INTEGER,
    UNIQUE (match_id, wrestler_id, participant_role)
);

CREATE TABLE IF NOT EXISTS championships (
    championship_id       VARCHAR(64) PRIMARY KEY,
    championship_name     VARCHAR(255) NOT NULL,
    championship_category VARCHAR(128),
    introduction_date     DATE,
    retirement_date       DATE,
    source_url            TEXT
);

CREATE TABLE IF NOT EXISTS match_championships (
    id                SERIAL PRIMARY KEY,
    match_id          VARCHAR(64) NOT NULL REFERENCES matches (match_id),
    championship_id   VARCHAR(64) NOT NULL REFERENCES championships (championship_id),
    champion_before   VARCHAR(255),
    champion_after    VARCHAR(255),
    title_change      BOOLEAN,
    title_retained    BOOLEAN,
    title_vacated     BOOLEAN,
    UNIQUE (match_id, championship_id)
);

CREATE TABLE IF NOT EXISTS event_sources (
    id                  SERIAL PRIMARY KEY,
    event_id            VARCHAR(64) NOT NULL REFERENCES events (event_id),
    source_name         VARCHAR(128) NOT NULL,
    source_url          TEXT NOT NULL,
    source_type         VARCHAR(64),
    retrieved_at        TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    verification_status VARCHAR(32)
);

CREATE INDEX IF NOT EXISTS ix_event_sources_event ON event_sources (event_id);

CREATE TABLE IF NOT EXISTS collection_logs (
    collection_id         VARCHAR(64) PRIMARY KEY,
    source_url            TEXT NOT NULL,
    collection_timestamp  TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    records_collected     INTEGER DEFAULT 0,
    errors                TEXT,
    collection_status     VARCHAR(32) DEFAULT 'success'
);
