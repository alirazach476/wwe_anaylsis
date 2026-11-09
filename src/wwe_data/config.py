"""Application settings and config loaders."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_DIR = ROOT / "config"
DEFAULT_DATA_DIR = ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WWE_",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg2://wwe:wwe@localhost:5432/wwe_history"
    start_year: int = 2000
    end_year: int = 2027
    user_agent: str = (
        "WWE-Historical-Data-Platform/0.1 (+research; respectful; local)"
    )
    request_delay_seconds: float = 1.0
    data_dir: Path = Field(default=DEFAULT_DATA_DIR)
    config_dir: Path = Field(default=DEFAULT_CONFIG_DIR)

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    for path in (
        settings.data_dir,
        settings.raw_dir,
        settings.processed_dir,
        settings.exports_dir,
        settings.reports_dir,
    ):
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Read-only hosts (e.g. Vercel serverless) cannot create data dirs
            pass
    return settings


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_series_registry(config_dir: Path | None = None) -> dict[str, Any]:
    cfg = config_dir or get_settings().config_dir
    return load_yaml(cfg / "event_series_registry.yaml")


def load_eligibility(config_dir: Path | None = None) -> dict[str, Any]:
    cfg = config_dir or get_settings().config_dir
    return load_yaml(cfg / "eligibility.yaml")
