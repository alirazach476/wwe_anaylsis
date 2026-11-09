"""Build manifest.json + eventLogoManifest.generated.ts from downloaded logo files."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "events"
TS = ROOT / "frontend" / "src" / "assets" / "eventLogoManifest.generated.ts"
MART = ROOT / "data" / "warehouse" / "marts" / "mart_event_analytics.csv"


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main() -> None:
    series = sorted({str(s) for s in pd.read_csv(MART)["event_series"].dropna().unique()})
    files: dict[str, str] = {}
    for p in OUT.iterdir():
        if p.suffix.lower() in {".png", ".svg", ".jpg", ".jpeg", ".webp"} and p.stat().st_size > 300:
            files[p.stem] = f"/events/{p.name}"

    items = []
    ok = 0
    for s in series:
        slug = slugify(s)
        path = files.get(slug)
        entry = {"series": s, "slug": slug}
        if path:
            entry["local_path"] = path
            entry["method"] = "wikipedia"
            ok += 1
        items.append(entry)

    manifest = {
        "generated_by": "scripts/build_event_logo_manifest.py",
        "source": "English Wikipedia / upload.wikimedia.org",
        "count_ok": ok,
        "count_total": len(series),
        "items": items,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = [
        "/* Auto-generated from Wikipedia-sourced event artwork — do not edit by hand. */",
        "export type EventLogoEntry = { series: string; slug: string; path: string; method?: string };",
        "export const EVENT_LOGOS: Record<string, EventLogoEntry> = {",
    ]
    for e in sorted((x for x in items if x.get("local_path")), key=lambda x: x["slug"]):
        payload = {
            "series": e["series"],
            "slug": e["slug"],
            "path": e["local_path"],
            "method": e.get("method"),
        }
        lines.append(f"  {json.dumps(e['slug'])}: {json.dumps(payload, ensure_ascii=False)},")
    lines.append("};")
    lines.append("export const EVENT_LOGO_BY_SERIES: Record<string, string> = {")
    for e in sorted((x for x in items if x.get("local_path")), key=lambda x: x["series"]):
        lines.append(f"  {json.dumps(e['series'])}: {json.dumps(e['local_path'])},")
    lines.append("};")
    TS.write_text("\n".join(lines) + "\n", encoding="utf-8")

    missing = [e["series"] for e in items if not e.get("local_path")]
    print(f"{ok}/{len(series)}")
    if missing:
        print("missing:", ", ".join(missing))


if __name__ == "__main__":
    main()
