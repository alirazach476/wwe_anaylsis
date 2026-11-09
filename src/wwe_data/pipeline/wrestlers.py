"""Build wrestler master + aliases from match participants (no invented bios)."""

from __future__ import annotations

from wwe_data.models.match_schemas import (
    RawParticipantRecord,
    RawWrestlerAliasRecord,
    RawWrestlerRecord,
)
from wwe_data.pipeline.ids import make_wrestler_id


def build_wrestler_tables(
    participants: list[RawParticipantRecord],
) -> tuple[list[RawWrestlerRecord], list[RawWrestlerAliasRecord]]:
    # Canonical = first-seen normalized ring name spelling (case-preserved)
    by_id: dict[str, str] = {}
    aliases: dict[tuple[str, str], RawWrestlerAliasRecord] = {}

    for p in participants:
        name = p.ring_name.strip()
        if not name:
            continue
        wid = p.wrestler_id or make_wrestler_id(name)
        if wid not in by_id:
            by_id[wid] = name
        # Alias if spelling differs from canonical
        canon = by_id[wid]
        if name.lower() != canon.lower() or name != canon:
            key = (wid, name.lower())
            aliases[key] = RawWrestlerAliasRecord(
                wrestler_id=wid,
                ring_name=name,
            )
        # Always record ring name as alias of itself for history preservation
        self_key = (wid, canon.lower())
        aliases.setdefault(
            self_key,
            RawWrestlerAliasRecord(wrestler_id=wid, ring_name=canon),
        )

    wrestlers = [
        RawWrestlerRecord(
            wrestler_id=wid,
            canonical_name=name,
            # debut/retirement/nationality left null unless documented elsewhere
        )
        for wid, name in sorted(by_id.items(), key=lambda x: x[1].lower())
    ]
    alias_list = list(aliases.values())
    return wrestlers, alias_list
