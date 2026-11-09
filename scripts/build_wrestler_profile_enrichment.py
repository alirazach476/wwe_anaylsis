"""Build wrestler finishers/moves/managers enrichment JSON for the API."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

from wwe_data.analytics.wrestler_moves_catalog import (  # noqa: E402
    KNOWN_MANAGERS,
    lookup_moves,
    normalize_ring_name,
)

MARTS = ROOT / "data" / "warehouse" / "marts"
EXPORTS = ROOT / "data" / "exports"
RUNTIME = ROOT / "data" / "warehouse" / "runtime_exports"
OUT = RUNTIME / "wrestler_profile_enrichment.json"

WITH_RE = re.compile(r"^(?P<body>.+?)\s*\(\s*with\s+(?P<mgrs>.+)\)\s*$", re.I)
SPLIT_MGR = re.compile(r"\s*,\s*|\s+and\s+", re.I)
NOISE = {
    "c",
    "by pinfall",
    "by submission",
    "by disqualification",
    "by technical knockout",
    "by knockout",
}


def _split_managers(raw: str) -> list[str]:
    parts = [p.strip(" .") for p in SPLIT_MGR.split(raw) if p.strip()]
    clean = []
    for p in parts:
        p = re.sub(r"^\s*and\s+", "", p, flags=re.I).strip()
        if len(p) < 3:
            continue
        if p.lower() in NOISE:
            continue
        clean.append(p)
    return clean


def extract_managers_from_matches(matches: pd.DataFrame, parts: pd.DataFrame) -> dict[str, Counter]:
    """Map wrestler_id -> Counter(manager_name)."""
    by_match = {
        mid: grp for mid, grp in parts.groupby(parts["match_id"].astype(str))
    }
    out: dict[str, Counter] = defaultdict(Counter)

    for _, row in matches.iterrows():
        mid = str(row.get("match_id") or "")
        grp = by_match.get(mid)
        if grp is None or grp.empty:
            continue
        for col in ("winner_name", "loser_name"):
            side = str(row.get(col) or "").strip()
            if not side or side.lower() in {"nan", "none"}:
                continue
            m = WITH_RE.match(side)
            if not m:
                continue
            body = m.group("body")
            managers = _split_managers(m.group("mgrs"))
            if not managers:
                continue
            # Skip giant multi-team sides where “(with X)” only applies to the last unit
            if len(body) > 70:
                # Keep only the last clause after comma/and (e.g. Real Americans (with Zeb))
                bits = re.split(r",| and ", body)
                body = bits[-1].strip() if bits else body
            body_n = normalize_ring_name(body)
            for _, prow in grp.iterrows():
                ring = str(prow.get("ring_name") or "")
                wid = str(prow.get("wrestler_id") or "")
                if not wid or not ring:
                    continue
                ring_n = normalize_ring_name(ring)
                if not ring_n:
                    continue
                # Require the wrestler to be the managed side (or a clear tag partner on that side)
                if ring_n == body_n or body_n.endswith(ring_n) or ring_n in body_n.split():
                    for mgr in managers:
                        out[wid][mgr] += 1
    return out


def main() -> None:
    perf = pd.read_csv(MARTS / "mart_wrestler_performance.csv")
    matches = pd.read_csv(MARTS / "mart_match_analytics.csv")
    parts_path = RUNTIME / "match_participants.csv"
    if not parts_path.exists():
        parts_path = EXPORTS / "match_participants.csv"
    parts = pd.read_csv(parts_path)

    extracted = extract_managers_from_matches(matches, parts)
    profiles: dict[str, dict] = {}

    for _, row in perf.iterrows():
        wid = str(row["wrestler_id"])
        name = str(row["canonical_name"])
        curated = lookup_moves(name)
        mgr_counts = extracted.get(wid, Counter())
        # Prefer curated managers, then high-confidence card managers from allowlist
        merged_mgrs: list[str] = []
        seen = set()
        for mgr in curated.get("managers") or []:
            key = normalize_ring_name(str(mgr))
            if key in seen:
                continue
            seen.add(key)
            merged_mgrs.append(str(mgr))
        for mgr, _count in mgr_counts.most_common(12):
            key = normalize_ring_name(mgr)
            if key in seen or key not in KNOWN_MANAGERS:
                continue
            if key == normalize_ring_name(name):
                continue
            seen.add(key)
            merged_mgrs.append(mgr)

        profiles[wid] = {
            "wrestler_id": wid,
            "canonical_name": name,
            "finishers": curated.get("finishers") or [],
            "signature_moves": curated.get("signatures") or [],
            "managers": merged_mgrs,
            "role": curated.get("role") or "wrestler",
            "clients": curated.get("clients") or [],
            "managers_from_card": [
                {"name": n, "appearances": int(c)} for n, c in mgr_counts.most_common(8)
            ],
        }

    # also index by normalized name for alias lookups
    by_name = {normalize_ring_name(v["canonical_name"]): k for k, v in profiles.items()}

    RUNTIME.mkdir(parents=True, exist_ok=True)
    payload = {
        "count": len(profiles),
        "by_wrestler_id": profiles,
        "name_index": by_name,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with_moves = sum(1 for v in profiles.values() if v["finishers"] or v["signature_moves"])
    with_mgr = sum(1 for v in profiles.values() if v["managers"])
    print(f"Wrote {OUT} profiles={len(profiles)} with_moves={with_moves} with_managers={with_mgr}")


if __name__ == "__main__":
    main()
