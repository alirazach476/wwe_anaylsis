"""Wire uploaded SNME John Cena final-match logo to the Dec 13 2025 event."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
IDX = ROOT / "frontend" / "public" / "logos" / "logo_index.json"
FILES = ROOT / "frontend" / "public" / "logos" / "files"
EVENT_ID = "evt_20251213_saturday-night-s-main-event_7d7cfe0c97"
EVENT_NAME = "Saturday Night's Main Event: John Cena's Final Match"
FILE_PNG = "Saturday Night's Main Event (2025) John Cenas final match.png"
SRC = Path(
    r"C:\Users\DELL\.cursor\projects\c-Users-DELL-Downloads-wwe-anaylsis\assets"
    r"\c__Users_DELL_AppData_Roaming_Cursor_User_workspaceStorage_af1959a06866942a4a857d587259225d_images"
    r"_image-c2f50197-4798-4861-b1dc-7b77ff2e9e69.png"
)


def norm(s: str) -> str:
    s = str(s or "").lower().replace("'", "").replace("’", "").replace("&", "and")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def slug(s: str) -> str:
    return norm(s).replace(" ", "-")


def main() -> None:
    if SRC.exists():
        FILES.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SRC, FILES / FILE_PNG)
        root_logos = ROOT / "logos"
        if root_logos.exists():
            shutil.copy2(SRC, root_logos / FILE_PNG)
        print("copied", FILE_PNG, (FILES / FILE_PNG).stat().st_size)

    path = "/logos/files/" + quote(FILE_PNG)
    data = json.loads(IDX.read_text(encoding="utf-8"))
    items = []
    for it in data.get("items", []):
        f = str(it.get("file") or "")
        n = str(it.get("event_name") or "")
        if "John Cenas final match" in f or (
            "Main Event" in n and "final match" in n.lower() and "2025" in (f + n)
        ):
            continue
        items.append(it)

    items.append(
        {
            "event_name": EVENT_NAME,
            "event_year": 2025,
            "event_id": EVENT_ID,
            "path": path,
            "file": FILE_PNG,
        }
    )
    data["items"] = items
    data["count"] = len(items)

    by_key = data.setdefault("by_key", {})
    by_event_id = data.setdefault("by_event_id", {})
    by_event_id[EVENT_ID] = path

    names = [
        EVENT_NAME,
        "Saturday Night's Main Event John Cena's Final Match",
        "Saturday Night's Main Event (2025) John Cenas final match",
        "John Cena's Final Match",
    ]
    for n in names:
        by_key[norm(n)] = path
        by_key[slug(n)] = path
        by_key[f"{norm(n)}|2025"] = path
        by_key[f"{slug(n)}|2025"] = path

    IDX.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wired by_event_id", EVENT_ID, "->", path)


if __name__ == "__main__":
    main()
