"""Parse Wikipedia match-result text into structured fields (no fabrication)."""

from __future__ import annotations

import re
from typing import Optional


DURATION_RE = re.compile(
    r"^(?:(?P<hours>\d+):)?(?P<minutes>\d{1,2}):(?P<seconds>\d{2})$"
)

# Common result verbs used on Wikipedia WWE results tables
DEFEATED_SPLIT = re.compile(
    r"\s+defeated\s+|\s+beat\s+|\s+def\.?\s+",
    re.IGNORECASE,
)
DRAW_RE = re.compile(r"\b(drew|draw|no contest|double (?:dq|countout|count-out))\b", re.I)
WINNER_ONLY_RE = re.compile(
    r"^(?P<winner>.+?)\s+(?:won|wins)\b",
    re.IGNORECASE,
)
TITLE_RE = re.compile(
    r"\b(championship|title|champion)\b",
    re.IGNORECASE,
)
VACATED_RE = re.compile(r"\bvacat(?:ed|es|ing)\b", re.IGNORECASE)
RETAINED_HINT = re.compile(r"\(c\)", re.IGNORECASE)


def parse_duration_to_seconds(value: str | None) -> Optional[int]:
    if not value:
        return None
    text = value.strip()
    # Sometimes "—" or empty
    if text in {"", "—", "-", "N/A", "n/a"}:
        return None
    m = DURATION_RE.match(text)
    if not m:
        return None
    hours = int(m.group("hours") or 0)
    minutes = int(m.group("minutes"))
    seconds = int(m.group("seconds"))
    return hours * 3600 + minutes * 60 + seconds


def clean_wrestler_fragment(name: str) -> str:
    text = name.strip()
    text = re.sub(r"\s*\(c\)\s*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\([^)]*\)\s*", " ", text)  # drop other parentheticals carefully?
    # Actually keep team names; only strip (c) above was done — restore non-c parens for stables
    # Re-parse more gently:
    return re.sub(r"\s+", " ", text).strip(" ,;")


def strip_champ_markers(name: str) -> str:
    text = re.sub(r"\s*\(c\)\s*", " ", name, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip(" ,;")


# Back-compat alias
_strip_champ_markers = strip_champ_markers


def split_team_members(side: str) -> list[str]:
    """Split a side like 'Jeff Hardy and Matt Hardy' or comma lists into members."""
    text = _strip_champ_markers(side)
    # Remove leading team brand in parentheses already stripped
    # "The Hardy Boyz ( Jeff Hardy and Matt Hardy )" → members inside parens if present
    inner = re.search(r"\(([^)]+)\)\s*$", text)
    if inner and re.search(r"\band\b|,", inner.group(1), re.I):
        text = inner.group(1)
    # Split on " and " / "," / "&" but not inside smaller units — heuristic
    parts = re.split(r"\s+and\s+|\s*&\s*|,\s*", text)
    return [p.strip() for p in parts if p.strip() and p.strip().lower() not in {"c"}]


def parse_match_result_text(result: str) -> dict:
    """
    Extract winner/loser sides and outcome from a Wikipedia results cell.
    Returns keys: winner, loser, outcome, raw_sides (list), is_draw
    Missing pieces stay None — never invented.
    """
    text = re.sub(r"\s+", " ", (result or "").strip())
    if not text:
        return {
            "winner": None,
            "loser": None,
            "outcome": None,
            "winners": [],
            "losers": [],
            "is_draw": False,
        }

    if DRAW_RE.search(text) and not DEFEATED_SPLIT.search(text):
        # e.g. "X and Y fought to a draw"
        return {
            "winner": None,
            "loser": None,
            "outcome": "draw",
            "winners": [],
            "losers": [],
            "is_draw": True,
        }

    parts = DEFEATED_SPLIT.split(text, maxsplit=1)
    if len(parts) == 2:
        winners_side = _strip_champ_markers(parts[0])
        losers_side = _strip_champ_markers(parts[1])
        # Drop trailing method clauses on loser side: "by pinfall", "by submission"
        losers_side = re.split(
            r"\s+by\s+(?:pinfall|submission|technical submission|dq|disqualification|"
            r"countout|count-out|forfeit|referee.?s decision|KO|knockout)\b",
            losers_side,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()
        # Also strip "in a ..." remnants if any leaked
        return {
            "winner": winners_side or None,
            "loser": losers_side or None,
            "outcome": "win",
            "winners": split_team_members(winners_side) if winners_side else [],
            "losers": split_team_members(losers_side) if losers_side else [],
            "is_draw": False,
        }

    m = WINNER_ONLY_RE.match(text)
    if m:
        winners_side = _strip_champ_markers(m.group("winner"))
        return {
            "winner": winners_side or None,
            "loser": None,
            "outcome": "win",
            "winners": split_team_members(winners_side) if winners_side else [],
            "losers": [],
            "is_draw": False,
        }

    return {
        "winner": None,
        "loser": None,
        "outcome": None,
        "winners": [],
        "losers": [],
        "is_draw": False,
    }


def detect_title_match(stipulation: str | None, result: str | None = None) -> bool:
    text = f"{stipulation or ''} {result or ''}"
    return bool(TITLE_RE.search(text))


def extract_championship_names(stipulation: str | None) -> list[str]:
    if not stipulation:
        return []
    text = stipulation.strip()
    # Patterns: "for the WWE Championship", "for the Raw Women's Championship and ..."
    names: list[str] = []
    for m in re.finditer(
        r"for the\s+(.+?)(?:\s+and the\s+|\s*$)",
        text,
        flags=re.IGNORECASE,
    ):
        chunk = m.group(1).strip().rstrip(".")
        # Split dual titles "X and the Y"
        parts = re.split(r"\s+and the\s+", chunk, flags=re.IGNORECASE)
        for p in parts:
            p = p.strip()
            if TITLE_RE.search(p):
                names.append(p)
    # Fallback: whole stipulation mentions championship
    if not names and TITLE_RE.search(text):
        m = re.search(r"((?:WWE|WWF|World|Raw|SmackDown|NXT|Women'?s|Tag|Intercontinental|"
                      r"United States|Hardcore|European|Cruiserweight|Universal|"
                      r"Undisputed)[^,]*?(?:Championship|Title))", text, re.I)
        if m:
            names.append(m.group(1).strip())
    return names


def infer_title_change(
    result_text: str | None,
    winner: str | None,
) -> tuple[Optional[bool], Optional[bool], Optional[bool]]:
    """Return (title_change, title_retained, title_vacated) when inferable; else Nones."""
    text = result_text or ""
    if VACATED_RE.search(text):
        return False, False, True
    # If champion marker (c) appears on loser side after split — change; on winner — retain
    if not result_text or not winner:
        return None, None, None
    parts = DEFEATED_SPLIT.split(result_text, maxsplit=1)
    if len(parts) != 2:
        return None, None, None
    win_side, lose_side = parts
    win_has_c = bool(RETAINED_HINT.search(win_side))
    lose_has_c = bool(RETAINED_HINT.search(lose_side))
    if lose_has_c and not win_has_c:
        return True, False, False
    if win_has_c:
        return False, True, False
    return None, None, None


def classify_special_match(stipulation: str | None, result: str | None = None) -> Optional[str]:
    text = f"{stipulation or ''} {result or ''}".lower()
    if "royal rumble" in text:
        return "royal_rumble"
    if "money in the bank" in text and "ladder" in text:
        return "money_in_the_bank"
    if "elimination chamber" in text:
        return "elimination_chamber"
    if "survivor series" in text or "wargames" in text or "war games" in text:
        return "survivor_series"
    return None


_FOOTNOTE_RESULT_RE = re.compile(
    r"^(?:"
    r"\(c\)|"
    r"note\b|"
    r"color\s+key"
    r")",
    re.IGNORECASE,
)


def is_results_footnote(result_text: str | None) -> bool:
    """True for Wikipedia results-table legend / footnote rows, not real matches."""
    text = re.sub(r"\s+", " ", (result_text or "").strip())
    if not text or len(text) < 3:
        return True
    if text.lower() in {"(c)", "c"}:
        return True
    if _FOOTNOTE_RESULT_RE.match(text):
        return True
    # Legend lines never contain a result verb
    if text.startswith(("–", "—", "-")) and not DEFEATED_SPLIT.search(text):
        return True
    return False
