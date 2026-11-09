"""Pydantic schemas for Phase 2 match / wrestler / championship data."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from wwe_data.models.schemas import VerificationStatus


class RawMatchRecord(BaseModel):
    match_id: str
    event_id: str
    match_number: Optional[int] = None
    match_name: Optional[str] = None
    match_type: Optional[str] = None
    match_stipulation: Optional[str] = None
    match_duration_seconds: Optional[int] = None
    match_result: Optional[str] = None
    winner: Optional[str] = None
    loser: Optional[str] = None
    is_title_match: Optional[bool] = None
    is_main_event: Optional[bool] = None
    is_preshow: Optional[bool] = None
    match_status: str = "completed"  # completed | announced | unknown | no_contest
    source_url: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.single_source
    special_match_kind: Optional[str] = None  # royal_rumble | mitb | survivor_series | chamber


class RawParticipantRecord(BaseModel):
    match_id: str
    wrestler_id: str
    ring_name: str
    team_id: Optional[str] = None
    participant_role: Optional[str] = None  # competitor | manager | special_referee
    result: Optional[str] = None  # win | loss | draw | eliminated | survivor | winner
    entry_number: Optional[int] = None
    elimination_order: Optional[int] = None
    eliminated_by: Optional[str] = None
    time_in_match_seconds: Optional[int] = None


class RawWrestlerRecord(BaseModel):
    wrestler_id: str
    canonical_name: str
    debut_date: Optional[date] = None
    retirement_date: Optional[date] = None
    nationality: Optional[str] = None
    source_url: Optional[str] = None


class RawWrestlerAliasRecord(BaseModel):
    wrestler_id: str
    ring_name: str
    alias_start_date: Optional[date] = None
    alias_end_date: Optional[date] = None


class RawChampionshipRecord(BaseModel):
    championship_id: str
    championship_name: str
    championship_category: Optional[str] = None
    introduction_date: Optional[date] = None
    retirement_date: Optional[date] = None
    source_url: Optional[str] = None


class RawMatchChampionshipRecord(BaseModel):
    match_id: str
    championship_id: str
    champion_before: Optional[str] = None
    champion_after: Optional[str] = None
    title_change: Optional[bool] = None
    title_retained: Optional[bool] = None
    title_vacated: Optional[bool] = None


class RawTeamRecord(BaseModel):
    team_id: str
    team_name: str
    team_start_date: Optional[date] = None
    team_end_date: Optional[date] = None


class SpecialRumbleEntrant(BaseModel):
    match_id: str
    event_id: str
    entrant: str
    wrestler_id: str
    entry_number: Optional[int] = None
    elimination_order: Optional[int] = None
    eliminated_by: Optional[str] = None
    time_in_match_seconds: Optional[int] = None
    eliminations_made: Optional[int] = None
    is_winner: bool = False
    is_final_four: bool = False


class SpecialMitbCashIn(BaseModel):
    mitb_match_id: Optional[str] = None
    winner: Optional[str] = None
    contract_type: Optional[str] = None  # mens | womens | unknown
    cash_in_date: Optional[date] = None
    cash_in_event: Optional[str] = None
    opponent: Optional[str] = None
    cash_in_result: Optional[str] = None
    championship_won: Optional[str] = None
    source_url: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.needs_review


class EventMatchBundle(BaseModel):
    event_id: str
    event_name: str
    wiki_page: Optional[str] = None
    source_url: Optional[str] = None
    matches: list[RawMatchRecord] = Field(default_factory=list)
    participants: list[RawParticipantRecord] = Field(default_factory=list)
    rumble_entrants: list[SpecialRumbleEntrant] = Field(default_factory=list)
    collection_status: str = "success"
    error: Optional[str] = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)
