"""Collect Wikipedia REST summary image URLs for event series."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_series_titles import SERIES_TITLES

ROOT = Path(__file__).resolve().parents[1]
MART = ROOT / "data" / "warehouse" / "marts" / "mart_event_analytics.csv"
OUT_JSON = ROOT / "data" / "tmp" / "wiki_logo_urls.json"
EVENTS_DIR = ROOT / "frontend" / "public" / "events"
REST = "https://en.wikipedia.org/api/rest_v1/page/summary/"
UA = "WWE-PLE-Analytics/1.3"

S = requests.Session()
S.headers.update({"User-Agent": UA})


def slugify(series: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", series.lower()).strip("-") or "event"


def ext_from_url(url: str) -> str:
    path = unquote(urlparse(url).path).lower()
    if path.endswith(".jpeg"):
        return ".jpg"
    for e in (".svg", ".png", ".jpg", ".webp"):
        if path.endswith(e):
            return e
    if "svg.png" in path:
        return ".png"
    return ".png"


def existing_file(slug: str) -> Path | None:
    for e in (".png", ".svg", ".jpg", ".webp", ".jpeg"):
        p = EVENTS_DIR / f"{slug}{e}"
        if p.exists() and p.stat().st_size > 300:
            return p
    return None


def fetch_summary(title: str) -> dict | None:
    for attempt in range(6):
        r = S.get(REST + title, timeout=45)
        if r.status_code == 429:
            wait = 15 + attempt * 15
            print(f"  429 on {title}, wait {wait}s")
            time.sleep(wait)
            continue
        if r.status_code == 404:
            return None
        if r.status_code >= 400:
            return None
        return r.json()
    return None


def image_from_summary(data: dict) -> tuple[str | None, str | None]:
    orig = (data.get("originalimage") or {}).get("source")
    thumb = (data.get("thumbnail") or {}).get("source")
    src = orig or thumb
    if not src:
        return None, data.get("pageimage")
    pageimage = data.get("pageimage") or unquote(urlparse(src).path.split("/")[-1])
    return src, pageimage


def curl_download(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    clean = url.split("?")[0]
    for u in (clean, url):
        try:
            subprocess.run(
                [
                    "curl",
                    "-fsSL",
                    "-A",
                    UA,
                    "-o",
                    str(dest),
                    u,
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
            if dest.exists() and dest.stat().st_size > 300:
                return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            continue
    if dest.exists():
        dest.unlink(missing_ok=True)
    return False


def main() -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    series_list = sorted({str(s) for s in pd.read_csv(MART)["event_series"].dropna().unique()})
    results: list[dict] = []
    urls_found = 0
    downloaded = 0
    skipped_existing = 0

    for i, series in enumerate(series_list, 1):
        slug = slugify(series)
        titles = SERIES_TITLES.get(series, [series.replace(" ", "_")])
        image_url = None
        pageimage = None
        title_used = None

        for wiki_title in titles:
            print(f"[{i}/{len(series_list)}] {series} -> {wiki_title}")
            data = fetch_summary(wiki_title)
            time.sleep(2.5)
            if not data:
                continue
            image_url, pageimage = image_from_summary(data)
            title_used = data.get("title") or wiki_title.replace("_", " ")
            if image_url:
                break

        entry = {
            "series": series,
            "slug": slug,
            "title": title_used,
            "image_url": image_url,
            "pageimage": pageimage,
        }
        results.append(entry)

        if image_url:
            urls_found += 1
            cached = existing_file(slug)
            if cached:
                skipped_existing += 1
                print(f"  URL ok, skip download (have {cached.name})")
            else:
                ext = ext_from_url(image_url)
                dest = EVENTS_DIR / f"{slug}{ext}"
                if curl_download(image_url, dest):
                    downloaded += 1
                    print(f"  downloaded → {dest.name}")
                else:
                    print("  download failed")
        else:
            print("  no image in REST summary")

    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    missing = [e["series"] for e in results if not e.get("image_url")]
    print("\n--- summary ---")
    print(f"series_total: {len(series_list)}")
    print(f"urls_found: {urls_found}")
    print(f"files_downloaded: {downloaded}")
    print(f"files_skipped_existing: {skipped_existing}")
    print(f"missing_urls: {len(missing)}")
    if missing:
        print("missing:", ", ".join(missing))


if __name__ == "__main__":
    main()
