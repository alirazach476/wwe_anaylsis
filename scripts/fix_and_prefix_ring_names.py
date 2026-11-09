"""Strip leading 'and ' from ring names and remap to canonical wrestler ids."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "data" / "exports"
RUNTIME = ROOT / "data" / "warehouse" / "runtime_exports"
WRESTLERS = EXPORTS / "wrestlers.csv"


def clean_name(name: str) -> str:
    s = str(name or "").strip()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\[[^\]]*\]", " ", s)
    s = re.sub(r"[)\"'“”*]+", " ", s)
    s = re.sub(r"(?i)^\s*and\s+", "", s)
    s = re.sub(r"\s+", " ", s).strip(" -–,.")
    return s


def name_key(name: str) -> str:
    key = re.sub(r"[^a-z0-9\s]", "", clean_name(name).lower())
    return re.sub(r"\s+", " ", key).strip()


def main() -> None:
    wrestlers = pd.read_csv(WRESTLERS)
    # Prefer clean canonical rows (no leading and)
    best: dict[str, tuple[str, str, int]] = {}
    for _, r in wrestlers.iterrows():
        raw = str(r.get("canonical_name") or "")
        if re.match(r"(?i)^\s*and\s+", raw):
            continue
        key = name_key(raw)
        if not key:
            continue
        wid = str(r["wrestler_id"])
        # shorter / cleaner names win ties
        score = -len(raw)
        prev = best.get(key)
        if not prev or score > prev[2]:
            best[key] = (wid, clean_name(raw) or raw, score)

    parts_path = EXPORTS / "match_participants.csv"
    parts = pd.read_csv(parts_path)
    changed = 0
    for i, row in parts.iterrows():
        raw = str(row.get("ring_name") or "")
        cleaned = clean_name(raw)
        if not cleaned:
            continue
        key = name_key(cleaned)
        new_id = row.get("wrestler_id")
        if key in best:
            new_id = best[key][0]
            cleaned = best[key][1]
        if cleaned != raw or str(new_id) != str(row.get("wrestler_id")):
            parts.at[i, "ring_name"] = cleaned
            parts.at[i, "wrestler_id"] = new_id
            changed += 1

    parts.to_csv(parts_path, index=False)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    parts.to_csv(RUNTIME / "match_participants.csv", index=False)
    print(f"Updated {changed} participant rows")


if __name__ == "__main__":
    main()
