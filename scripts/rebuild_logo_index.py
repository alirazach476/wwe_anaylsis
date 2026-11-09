"""Rebuild frontend/public/logos/logo_index.json from project logos/ folder."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGOS = ROOT / "logos"
OUT = ROOT / "frontend" / "public" / "logos" / "logo_index.json"


def norm(s: str) -> str:
    s = s.lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def slug(s: str) -> str:
    return re.sub(r"\s+", "-", norm(s))


def main() -> None:
    items = []
    by_key: dict[str, str] = {}
    for p in sorted(LOGOS.iterdir()):
        if not p.is_file() or p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}:
            continue
        m = re.match(r"^(.+?)\s*\((\d{4})\)\.(.+)$", p.name)
        if m:
            name, year = m.group(1).strip(), int(m.group(2))
        else:
            name, year = p.stem, None
        # Encode spaces / apostrophes / parentheses for reliable <img src>
        from urllib.parse import quote

        url = "/logos/files/" + quote(p.name)
        items.append({"event_name": name, "event_year": year, "path": url, "file": p.name})
        n, s = norm(name), slug(name)
        if year is not None:
            by_key[f"{n}|{year}"] = url
            by_key[f"{s}|{year}"] = url
            by_key[f"{name.lower()}|{year}"] = url
        else:
            by_key[n] = url
            by_key[s] = url
            by_key[name.lower()] = url
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"count": len(items), "items": items, "by_key": by_key}, indent=2), encoding="utf-8")
    print(f"wrote {len(items)} logos -> {OUT}")
    print("final smackdown", by_key.get("john cenas final smackdown"))


if __name__ == "__main__":
    main()
