"""Extract championship references from title matches (null-safe, no fabrication)."""

from __future__ import annotations

from wwe_data.models.match_schemas import (
    RawChampionshipRecord,
    RawMatchChampionshipRecord,
    RawMatchRecord,
)
from wwe_data.pipeline.ids import make_championship_id
from wwe_data.pipeline.match_parse import (
    extract_championship_names,
    infer_title_change,
)


def build_championship_tables(
    matches: list[RawMatchRecord],
) -> tuple[list[RawChampionshipRecord], list[RawMatchChampionshipRecord]]:
    champs: dict[str, RawChampionshipRecord] = {}
    links: list[RawMatchChampionshipRecord] = []

    for match in matches:
        if not match.is_title_match:
            continue
        names = extract_championship_names(match.match_stipulation)
        if not names:
            # Title match flagged but name not parsed — still flag for review via empty skip
            continue
        change, retained, vacated = infer_title_change(match.match_result, match.winner)
        for name in names:
            cid = make_championship_id(name)
            champs.setdefault(
                cid,
                RawChampionshipRecord(
                    championship_id=cid,
                    championship_name=name,
                    championship_category=None,
                    source_url=match.source_url,
                ),
            )
            links.append(
                RawMatchChampionshipRecord(
                    match_id=match.match_id,
                    championship_id=cid,
                    champion_before=None,  # not inventing prior champion identity
                    champion_after=match.winner if change else (match.winner if retained else None),
                    title_change=change,
                    title_retained=retained,
                    title_vacated=vacated,
                )
            )
    return list(champs.values()), links
