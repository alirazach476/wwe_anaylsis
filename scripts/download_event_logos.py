"""Download logo images for each event in all_events.xlsx.
Google Images is JS-rendered and blocks scripts, so this scrapes Bing Images
(same idea). Only results whose TITLE contains the word 'logo' are kept.
Usage: python download_event_logos.py [limit_events] [per_event]
"""
import re, sys, json, html, time
from pathlib import Path
import pandas as pd, requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "event_logos"
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else None
PER = int(sys.argv[2]) if len(sys.argv) > 2 else 3
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}

def safe(s): return re.sub(r"[^\w\- ]", "", s).strip().replace(" ", "_")

def search(q):
    r = requests.get("https://www.bing.com/images/search", params={"q": q}, headers={**H, "Accept-Language": "en-US,en;q=0.9"}, timeout=20)
    for a in BeautifulSoup(r.text, "html.parser").select("a.iusc"):
        try:
            m = json.loads(html.unescape(a.get("m", "{}")))
        except ValueError:
            continue
        yield m.get("murl"), m.get("t", "")

def download(name):
    folder = OUT / safe(name); folder.mkdir(parents=True, exist_ok=True)
    if any(folder.iterdir()): return len(list(folder.iterdir()))
    words = [w.lower() for w in re.findall(r"\w+", name) if not w.isdigit()]
    n = 0
    for url, title in search(f"WWE {name} logo"):
        if n >= PER: break
        t = title.lower()
        if not url or "logo" not in t or not all(w in t for w in words[:1]):
            continue
        try:
            r = requests.get(url, headers=H, timeout=15)
            ct = r.headers.get("content-type", "")
            if r.status_code != 200 or not ct.startswith("image") or len(r.content) < 2000: continue
            ext = {"jpeg": "jpg", "svg+xml": "svg"}.get(ct.split("/")[1].split(";")[0], ct.split("/")[1].split(";")[0])
            (folder / f"{safe(name)}_{n+1}.{ext}").write_bytes(r.content); n += 1
        except requests.RequestException:
            continue
    return n

names = pd.read_excel(ROOT / "data/exports/all_events.xlsx")["canonical_event_name"].dropna().unique()
if LIMIT: names = names[:LIMIT]
for i, name in enumerate(names, 1):
    print(f"[{i}/{len(names)}] {name}: {download(name)} images", flush=True)
    time.sleep(1)
