"""Database engine / session helpers."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from wwe_data.config import get_settings
from wwe_data.db.models import Base


def get_engine(url: str | None = None):
    settings = get_settings()
    return create_engine(url or settings.database_url, future=True)


def create_all(url: str | None = None) -> None:
    engine = get_engine(url)
    Base.metadata.create_all(engine)


def get_session(url: str | None = None) -> Session:
    engine = get_engine(url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()
