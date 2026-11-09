"""Expandable event-series registry matching."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from wwe_data.config import load_series_registry


@dataclass
class SeriesMatch:
    series_id: str
    canonical_name: str
    event_type: str
    special_data: str | None = None


class SeriesRegistry:
    def __init__(self, registry: dict[str, Any] | None = None) -> None:
        self.raw = registry or load_series_registry()
        self.series = [s for s in self.raw.get("series", []) if not s.get("alias_of")]
        self._compiled: list[tuple[re.Pattern[str], dict[str, Any]]] = []
        for entry in self.raw.get("series", []):
            for pattern in entry.get("match_patterns") or []:
                self._compiled.append(
                    (re.compile(pattern, re.IGNORECASE), entry)
                )

    def match(self, event_name: str) -> SeriesMatch | None:
        name = event_name.strip()
        for regex, entry in self._compiled:
            if regex.search(name):
                target = entry
                alias = entry.get("alias_of")
                if alias:
                    target = next(
                        (s for s in self.raw.get("series", []) if s.get("id") == alias),
                        entry,
                    )
                return SeriesMatch(
                    series_id=target.get("id") or entry["id"],
                    canonical_name=target.get("canonical_name") or name,
                    event_type=target.get("event_type") or "other",
                    special_data=target.get("special_data"),
                )
        return None

    def all_canonical_names(self) -> list[str]:
        return sorted(
            {
                s["canonical_name"]
                for s in self.raw.get("series", [])
                if s.get("canonical_name") and not s.get("discovery_bucket")
            }
        )

    def required_series_ids(self) -> list[str]:
        """Series that should appear in a complete historical inventory when they ran."""
        skip = {"for_your_consideration", "next_big_thing", "smash", "world_tour"}
        return [
            s["id"]
            for s in self.series
            if s.get("id") not in skip and not s.get("is_fallback")
        ]
