"""Phase 5: build a versioned release snapshot with checksums."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from rich.console import Console

from wwe_data.config import get_settings

console = Console()

RELEASE_GLOBS = [
    ("exports", "data/exports/*.csv"),
    ("exports", "data/exports/*.parquet"),
    ("analytics", "data/analytics/*.csv"),
    ("analytics", "data/analytics/*.parquet"),
    ("analytics", "data/analytics/*.json"),
    ("reports", "data/reports/*.md"),
    ("reports", "data/reports/*.json"),
    ("docs", "docs/*.md"),
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_release(version: str | None = None) -> Path:
    settings = get_settings()
    root = Path(__file__).resolve().parents[3]
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    version = version or f"0.5.0-{stamp[:8]}"
    out = settings.data_dir / "releases" / version
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    files_meta: list[dict] = []
    checksum_lines: list[str] = []

    for folder, pattern in RELEASE_GLOBS:
        for src in sorted(root.glob(pattern)):
            if not src.is_file():
                continue
            dest_dir = out / folder
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
            shutil.copy2(src, dest)
            digest = _sha256(dest)
            rel = f"{folder}/{src.name}"
            files_meta.append(
                {
                    "path": rel,
                    "bytes": dest.stat().st_size,
                    "sha256": digest,
                }
            )
            checksum_lines.append(f"{digest}  {rel}")

    # Include sqlite warehouse if present
    sqlite = settings.processed_dir / "wwe_history.sqlite"
    if sqlite.exists():
        dest_dir = out / "warehouse"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / sqlite.name
        shutil.copy2(sqlite, dest)
        digest = _sha256(dest)
        rel = f"warehouse/{sqlite.name}"
        files_meta.append({"path": rel, "bytes": dest.stat().st_size, "sha256": digest})
        checksum_lines.append(f"{digest}  {rel}")

    # Quick stats from exports
    stats: dict = {}
    try:
        import pandas as pd

        events = pd.read_csv(settings.exports_dir / "events_inventory.csv")
        matches = pd.read_csv(settings.exports_dir / "matches.csv")
        stats = {
            "events": int(len(events)),
            "matches": int(len(matches)),
            "announced_events": int((events["event_status"] == "announced").sum())
            if "event_status" in events.columns
            else None,
        }
    except Exception as exc:
        stats = {"error": str(exc)}

    manifest = {
        "name": "wwe-ple-history",
        "version": version,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "scope": {"start_year": 2000, "end_year": 2027},
        "stats": stats,
        "file_count": len(files_meta),
        "files": files_meta,
        "notes": [
            "No fabricated match results or future cards",
            "MITB cash-ins enriched from Wikipedia list page (Phase 4)",
            "Chamber entry order left null when not structured on source",
        ],
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    # Zip archive
    archive = shutil.make_archive(str(out), "zip", root_dir=out)
    console.print(f"[green]Release built[/green] → {out}")
    console.print(f"  archive: {archive}")
    console.print(f"  files: {len(files_meta)} | stats: {stats}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Phase 5 release package")
    parser.add_argument("--version", type=str, default=None)
    args = parser.parse_args()
    build_release(version=args.version)


if __name__ == "__main__":
    main()
