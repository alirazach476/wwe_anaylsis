"""Replace Dec 13 2025 SNME card with real results incl. Cena vs Gunther retirement match."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "data" / "exports"
MARTS = ROOT / "data" / "warehouse" / "marts"
RUNTIME = ROOT / "data" / "warehouse" / "runtime_exports"
EVENT_ID = "evt_20251213_saturday-night-s-main-event_7d7cfe0c97"
EVENT_DATE = "2025-12-13"


def _wid(w: pd.DataFrame, name: str) -> str:
    exact = w[w["canonical_name"].astype(str) == name]
    if not exact.empty:
        return str(exact.iloc[0]["wrestler_id"])
    hit = w[w["canonical_name"].astype(str).str.fullmatch(name, case=False, na=False)]
    if not hit.empty:
        return str(hit.iloc[0]["wrestler_id"])
    slug = name.lower().replace(" ", "-").replace("'", "")
    digest = hashlib.md5(name.encode()).hexdigest()[:8]
    return f"wrs_{slug}_{digest}"


def _mid(n: int, label: str) -> str:
    digest = hashlib.md5(f"{EVENT_ID}:{n}:{label}".encode()).hexdigest()[:12]
    return f"mtc_{digest}_{n}"


def main() -> None:
    w = pd.read_csv(EXPORTS / "wrestlers.csv")
    ids = {
        "Cody Rhodes": _wid(w, "Cody Rhodes"),
        "Oba Femi": _wid(w, "Oba Femi"),
        "Sol Ruca": _wid(w, "Sol Ruca"),
        "Bayley": _wid(w, "Bayley"),
        "AJ Styles": _wid(w, "AJ Styles"),
        "Dragon Lee": _wid(w, "Dragon Lee"),
        "Je'Von Evans": _wid(w, "Je'Von Evans"),
        "Leon Slater": _wid(w, "Leon Slater"),
        "Gunther": _wid(w, "Gunther"),
        "John Cena": _wid(w, "John Cena"),
    }
    for cand in ["Je'Von Evans", "JeVon Evans", "Jevon Evans"]:
        if (w["canonical_name"].astype(str) == cand).any():
            ids["Je'Von Evans"] = _wid(w, cand)
            break
    print({k: v for k, v in ids.items()})

    card = [
        {
            "n": 1,
            "label": "rhodes-vs-obi-femi",
            "duration": 9 * 60 + 10,
            "winner": None,
            "loser": None,
            "result": "Cody Rhodes vs. Oba Femi ended in a no contest",
            "group": "singles",
            "title": 0,
            "main": 0,
            "parts": [
                ("Cody Rhodes", None),
                ("Oba Femi", None),
            ],
        },
        {
            "n": 2,
            "label": "sol-ruca-vs-bayley",
            "duration": 9 * 60 + 25,
            "winner": "Sol Ruca",
            "loser": "Bayley",
            "result": "Sol Ruca (with Zaria) defeated Bayley (with Lyra Valkyria) by pinfall",
            "group": "singles",
            "title": 0,
            "main": 0,
            "parts": [
                ("Sol Ruca", "win"),
                ("Bayley", "loss"),
            ],
        },
        {
            "n": 3,
            "label": "styles-lee-vs-evans-slater",
            "duration": 6 * 60 + 30,
            "winner": "AJ Styles and Dragon Lee",
            "loser": "Je'Von Evans and Leon Slater",
            "result": "AJ Styles and Dragon Lee defeated Je'Von Evans and Leon Slater by pinfall",
            "group": "tag",
            "title": 0,
            "main": 0,
            "parts": [
                ("AJ Styles", "win"),
                ("Dragon Lee", "win"),
                ("Je'Von Evans", "loss"),
                ("Leon Slater", "loss"),
            ],
        },
        {
            "n": 4,
            "label": "gunther-vs-cena-retirement",
            "duration": 23 * 60 + 45,
            "winner": "Gunther",
            "loser": "John Cena",
            "result": "Gunther defeated John Cena by submission (Cena's retirement match)",
            "group": "singles",
            "title": 0,
            "main": 1,
            "parts": [
                ("Gunther", "win"),
                ("John Cena", "loss"),
            ],
        },
    ]

    # --- mart matches ---
    mm = pd.read_csv(MARTS / "mart_match_analytics.csv")
    old_ids = set(mm.loc[mm["event_id"] == EVENT_ID, "match_id"].astype(str))
    mm = mm[mm["event_id"] != EVENT_ID].copy()
    event_key = int(pd.read_csv(MARTS / "mart_event_analytics.csv").loc[
        lambda d: d["event_id"] == EVENT_ID, "event_key"
    ].iloc[0])
    max_mkey = int(pd.to_numeric(mm["match_key"], errors="coerce").max() or 0)
    type_key = {
        "singles": int(mm.loc[mm["match_type_group"] == "singles", "match_type_key"].mode().iloc[0]),
        "tag": int(mm.loc[mm["match_type_group"] == "tag", "match_type_key"].mode().iloc[0]),
    }

    new_rows = []
    new_parts = []
    for i, m in enumerate(card):
        mid = _mid(m["n"], m["label"])
        new_rows.append(
            {
                "match_key": max_mkey + 1 + i,
                "match_id": mid,
                "event_key": event_key,
                "match_type_key": type_key[m["group"]],
                "match_number": float(m["n"]),
                "match_duration_seconds": float(m["duration"]),
                "winner_name": m["winner"],
                "loser_name": m["loser"],
                "is_title_match": m["title"],
                "is_main_event": m["main"],
                "is_preshow": 0,
                "match_status": "completed",
                "special_match_kind": "retirement" if m["n"] == 4 else None,
                "match_result": m["result"],
                "event_id": EVENT_ID,
                "event_name": "Saturday Night's Main Event",
                "event_series": "Saturday Night's Main Event",
                "event_year": 2025,
                "event_date": EVENT_DATE,
                "match_type_group": m["group"],
                "match_type_raw": m["group"],
            }
        )
        for ring, result in m["parts"]:
            new_parts.append(
                {
                    "match_id": mid,
                    "wrestler_id": ids[ring],
                    "ring_name": ring,
                    "team_id": None,
                    "participant_role": "competitor",
                    "result": result,
                    "entry_number": None,
                    "elimination_order": None,
                    "eliminated_by": None,
                    "time_in_match_seconds": None,
                }
            )

    mm = pd.concat([mm, pd.DataFrame(new_rows)], ignore_index=True)
    mm.to_csv(MARTS / "mart_match_analytics.csv", index=False)
    print("wrote mart matches", len(new_rows), "removed", len(old_ids))

    # --- event mart ---
    ev = pd.read_csv(MARTS / "mart_event_analytics.csv")
    idx = ev.index[ev["event_id"] == EVENT_ID][0]
    ev.at[idx, "event_name"] = "Saturday Night's Main Event: John Cena's Final Match"
    ev.at[idx, "canonical_event_name"] = "Saturday Night's Main Event XLII (2025)"
    ev.at[idx, "matches"] = 4
    ev.at[idx, "title_matches"] = 0
    ev.at[idx, "main_events"] = 1
    ev.at[idx, "avg_duration"] = sum(m["duration"] for m in card) / 4
    ev.at[idx, "attendance"] = 19274
    ev.at[idx, "verification_status"] = "manual"
    ev.at[idx, "city"] = "Washington, D.C."
    ev.at[idx, "venue_name"] = "Capital One Arena"
    ev.to_csv(MARTS / "mart_event_analytics.csv", index=False)
    print("updated event row")

    # --- participants export + runtime ---
    for parts_path in [EXPORTS / "match_participants.csv", RUNTIME / "match_participants.csv"]:
        if not parts_path.exists():
            continue
        parts = pd.read_csv(parts_path)
        parts = parts[~parts["match_id"].astype(str).isin(old_ids)].copy()
        parts = pd.concat([parts, pd.DataFrame(new_parts)], ignore_index=True)
        parts.to_csv(parts_path, index=False)
        print("updated", parts_path, "rows", len(parts))

    # drop stale championships for old match ids
    for ch_path in [EXPORTS / "match_championships.csv", RUNTIME / "match_championships.csv"]:
        if not ch_path.exists():
            continue
        ch = pd.read_csv(ch_path)
        before = len(ch)
        ch = ch[~ch["match_id"].astype(str).isin(old_ids)]
        ch.to_csv(ch_path, index=False)
        print("cleaned championships", ch_path, before - len(ch))

    # logo
    src_logo = Path(
        r"C:\Users\DELL\.cursor\projects\c-Users-DELL-Downloads-wwe-anaylsis\assets"
        r"\c__Users_DELL_AppData_Roaming_Cursor_User_workspaceStorage_af1959a06866942a4a857d587259225d_images"
        r"_Saturday_Night_s_Main_Event__2025__John_Cenas_final_match-a2165474-f0a2-48f1-b599-1bce36b91f03.jpg"
    )
    logo_dir = ROOT / "frontend" / "public" / "logos" / "files"
    logo_dir.mkdir(parents=True, exist_ok=True)
    dest = logo_dir / "Saturday Night's Main Event (2025) John Cenas final match.jpg"
    if src_logo.exists():
        shutil.copy2(src_logo, dest)
        print("copied logo", dest.name)
        # also root logos folder if present
        root_logos = ROOT / "logos"
        if root_logos.exists():
            shutil.copy2(src_logo, root_logos / dest.name)
    else:
        print("logo source missing", src_logo)

    # patch logo_index if present
    idx_path = ROOT / "frontend" / "public" / "logos" / "logo_index.json"
    if idx_path.exists() and dest.exists():
        import json

        data = json.loads(idx_path.read_text(encoding="utf-8"))
        entries = data if isinstance(data, list) else data.get("logos") or data.get("files") or []
        name = dest.name
        path = f"/logos/files/{name}"
        if isinstance(entries, list):
            if not any(str(x).endswith(name) or (isinstance(x, dict) and name in str(x)) for x in entries):
                if entries and isinstance(entries[0], str):
                    entries.append(path)
                elif entries and isinstance(entries[0], dict):
                    entries.append({"file": name, "path": path, "series": "Saturday Night's Main Event", "year": 2025})
                else:
                    entries.append(path)
                if isinstance(data, list):
                    idx_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
                else:
                    key = "logos" if "logos" in data else ("files" if "files" in data else None)
                    if key:
                        data[key] = entries
                        idx_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print("updated logo_index")


if __name__ == "__main__":
    main()
