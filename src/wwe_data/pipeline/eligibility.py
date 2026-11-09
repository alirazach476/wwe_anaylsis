"""Eligibility filters — exclude weekly TV / NXT TakeOver / non-WWE without fabricating."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from wwe_data.config import load_eligibility


class EligibilityFilter:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_eligibility()
        window = self.config.get("window", {})
        self.start = date.fromisoformat(window.get("start_date", "2000-01-01"))
        self.end = date.fromisoformat(window.get("end_date", "2027-12-31"))
        excl = self.config.get("exclude", {})
        self.exclude_patterns = [
            re.compile(p, re.IGNORECASE) for p in excl.get("name_patterns", [])
        ]
        self.weekly_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in excl.get("weekly_or_tv_episode_patterns", [])
        ]
        self.allowlist = [
            re.compile(p, re.IGNORECASE)
            for p in self.config.get("allowlist_name_patterns", [])
        ]
        self.nxt_era_rules = []
        for rule in excl.get("nxt_era_name_patterns", []):
            self.nxt_era_rules.append(
                (
                    re.compile(rule["pattern"], re.IGNORECASE),
                    int(rule["exclude_from_year"]),
                )
            )

    def in_window(self, event_date: date) -> bool:
        return self.start <= event_date <= self.end

    def is_allowlisted(self, name: str, notes: str | None = None) -> bool:
        text = f"{name} {notes or ''}"
        return any(p.search(text) for p in self.allowlist)

    def is_excluded(self, name: str, notes: str | None = None, event_date: date | None = None) -> bool:
        if self.is_allowlisted(name, notes):
            return False
        text = name.strip()
        # NXT TakeOver hard exclude
        if re.search(r"nxt\s+takeover", text, re.IGNORECASE):
            return True
        # NXT-branded major events that are not main-roster PLEs
        if re.search(r"^nxt\b", text, re.IGNORECASE) and not self.is_allowlisted(
            name, notes
        ):
            return True
        # Notes explicitly mark NXT-only
        if notes and re.search(r"\bNXT\b", notes) and not re.search(
            r"\b(Raw|SmackDown)\b", notes, re.IGNORECASE
        ):
            # Allowlist can still override
            if not self.is_allowlisted(name, notes):
                return True

        for pattern in self.exclude_patterns:
            if pattern.search(text):
                if "main event" in pattern.pattern.lower() and self.is_allowlisted(
                    name, notes
                ):
                    continue
                return True

        if event_date is not None:
            for pattern, from_year in self.nxt_era_rules:
                if event_date.year >= from_year and pattern.search(text):
                    return True

        combined = f"{notes or ''}"
        for pattern in self.weekly_patterns:
            if pattern.search(combined) and not self.is_allowlisted(name, notes):
                return True
        return False

    def is_eligible(
        self,
        name: str,
        event_date: date,
        notes: str | None = None,
        *,
        force_include: bool = False,
    ) -> bool:
        if not self.in_window(event_date):
            return False
        if force_include or self.is_allowlisted(name, notes):
            return True
        if self.is_excluded(name, notes, event_date):
            return False
        return True
