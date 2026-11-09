"""Pydantic schemas for inventory-phase validation."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class EventStatus(str, Enum):
    completed = "completed"
    announced = "announced"
    cancelled = "cancelled"
    unknown = "unknown"


class VerificationStatus(str, Enum):
    verified = "verified"
    single_source = "single_source"
    conflict = "conflict"
    unverified = "unverified"
    needs_review = "needs_review"


class EventType(str, Enum):
    ppv = "ppv"
    ple = "ple"
    special = "special"
    other = "other"


class RawEventRecord(BaseModel):
    """Normalized event inventory record (pre-DB)."""

    event_id: str
    event_name: str
    canonical_event_name: str
    event_series: Optional[str] = None
    event_year: int
    event_date: date
    event_end_date: Optional[date] = None
    event_type: EventType = EventType.ple
    event_status: EventStatus = EventStatus.unknown
    venue: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: Optional[str] = None
    attendance: Optional[int] = None
    broadcast_platform: Optional[str] = None
    brand: Optional[str] = None
    official_url: Optional[str] = None
    source_url: str
    source_name: str
    verification_status: VerificationStatus = VerificationStatus.single_source
    notes: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    collection_timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("attendance")
    @classmethod
    def attendance_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("attendance cannot be negative")
        return v


class EventSourceRecord(BaseModel):
    event_id: str
    source_name: str
    source_url: str
    source_type: str
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    verification_status: VerificationStatus = VerificationStatus.unverified


class CollectionLogRecord(BaseModel):
    collection_id: str
    source_url: str
    collection_timestamp: datetime = Field(default_factory=datetime.utcnow)
    records_collected: int = 0
    errors: Optional[str] = None
    collection_status: str = "success"


class CoverageMetrics(BaseModel):
    total_eligible_events: int
    total_events_collected: int
    total_matches_collected: int = 0
    total_unique_wrestlers: int = 0
    total_championship_matches: int = 0
    total_title_changes: int = 0
    events_missing_match_cards: int = 0
    events_missing_results: int = 0
    records_requiring_manual_verification: int = 0
    coverage_by_year: dict[str, float]
    coverage_by_series: dict[str, dict[str, int | float]]
    missing_series_from_registry: list[str]
    unclassified_events: list[str]
    collection_timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: list[str] = Field(default_factory=list)
