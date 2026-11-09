"""SQLAlchemy ORM models matching the required database schema."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_series: Mapped[str | None] = mapped_column(String(128))
    event_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    event_end_date: Mapped[date | None] = mapped_column(Date)
    event_type: Mapped[str | None] = mapped_column(String(64))
    event_status: Mapped[str | None] = mapped_column(String(32), index=True)
    venue: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(128))
    state_province: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(128))
    attendance: Mapped[int | None] = mapped_column(Integer)
    broadcast_platform: Mapped[str | None] = mapped_column(String(128))
    brand: Mapped[str | None] = mapped_column(String(64))
    official_url: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str | None] = mapped_column(String(32))
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    sources = relationship("EventSource", back_populates="event")
    matches = relationship("Match", back_populates="event")


class Wrestler(Base):
    __tablename__ = "wrestlers"

    wrestler_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    debut_date: Mapped[date | None] = mapped_column(Date)
    retirement_date: Mapped[date | None] = mapped_column(Date)
    nationality: Mapped[str | None] = mapped_column(String(128))
    source_url: Mapped[str | None] = mapped_column(Text)

    aliases = relationship("WrestlerAlias", back_populates="wrestler")


class WrestlerAlias(Base):
    __tablename__ = "wrestler_aliases"
    __table_args__ = (UniqueConstraint("wrestler_id", "ring_name", name="uq_alias"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wrestler_id: Mapped[str] = mapped_column(ForeignKey("wrestlers.wrestler_id"))
    ring_name: Mapped[str] = mapped_column(String(255), nullable=False)
    alias_start_date: Mapped[date | None] = mapped_column(Date)
    alias_end_date: Mapped[date | None] = mapped_column(Date)

    wrestler = relationship("Wrestler", back_populates="aliases")


class Match(Base):
    __tablename__ = "matches"

    match_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.event_id"), index=True)
    match_number: Mapped[int | None] = mapped_column(Integer)
    match_name: Mapped[str | None] = mapped_column(String(255))
    match_type: Mapped[str | None] = mapped_column(String(128))
    match_stipulation: Mapped[str | None] = mapped_column(Text)
    match_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    match_result: Mapped[str | None] = mapped_column(Text)
    winner: Mapped[str | None] = mapped_column(String(255))
    loser: Mapped[str | None] = mapped_column(String(255))
    is_title_match: Mapped[bool | None] = mapped_column(Boolean)
    is_main_event: Mapped[bool | None] = mapped_column(Boolean)
    is_preshow: Mapped[bool | None] = mapped_column(Boolean)
    match_status: Mapped[str | None] = mapped_column(String(32))
    source_url: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str | None] = mapped_column(String(32))

    event = relationship("Event", back_populates="matches")
    participants = relationship("MatchParticipant", back_populates="match")
    championships = relationship("MatchChampionship", back_populates="match")


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    team_start_date: Mapped[date | None] = mapped_column(Date)
    team_end_date: Mapped[date | None] = mapped_column(Date)


class MatchParticipant(Base):
    __tablename__ = "match_participants"
    __table_args__ = (
        UniqueConstraint("match_id", "wrestler_id", "participant_role", name="uq_mp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.match_id"), index=True)
    wrestler_id: Mapped[str] = mapped_column(ForeignKey("wrestlers.wrestler_id"))
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.team_id"))
    participant_role: Mapped[str | None] = mapped_column(String(64))
    result: Mapped[str | None] = mapped_column(String(64))
    entry_number: Mapped[int | None] = mapped_column(Integer)
    elimination_order: Mapped[int | None] = mapped_column(Integer)
    eliminated_by: Mapped[str | None] = mapped_column(String(255))
    time_in_match_seconds: Mapped[int | None] = mapped_column(Integer)

    match = relationship("Match", back_populates="participants")


class Championship(Base):
    __tablename__ = "championships"

    championship_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    championship_name: Mapped[str] = mapped_column(String(255), nullable=False)
    championship_category: Mapped[str | None] = mapped_column(String(128))
    introduction_date: Mapped[date | None] = mapped_column(Date)
    retirement_date: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(Text)


class MatchChampionship(Base):
    __tablename__ = "match_championships"
    __table_args__ = (
        UniqueConstraint("match_id", "championship_id", name="uq_match_champ"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.match_id"), index=True)
    championship_id: Mapped[str] = mapped_column(
        ForeignKey("championships.championship_id")
    )
    champion_before: Mapped[str | None] = mapped_column(String(255))
    champion_after: Mapped[str | None] = mapped_column(String(255))
    title_change: Mapped[bool | None] = mapped_column(Boolean)
    title_retained: Mapped[bool | None] = mapped_column(Boolean)
    title_vacated: Mapped[bool | None] = mapped_column(Boolean)

    match = relationship("Match", back_populates="championships")


class EventSource(Base):
    __tablename__ = "event_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.event_id"), index=True)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(64))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    verification_status: Mapped[str | None] = mapped_column(String(32))

    event = relationship("Event", back_populates="sources")


class CollectionLog(Base):
    __tablename__ = "collection_logs"

    collection_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    collection_timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    records_collected: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[str | None] = mapped_column(Text)
    collection_status: Mapped[str] = mapped_column(String(32), default="success")
