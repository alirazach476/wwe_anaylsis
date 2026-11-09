"""Vercel serverless entrypoint for the FastAPI analytics API."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from wwe_data.api.app import app  # noqa: E402

# Vercel Python runtime expects an ASGI `app` in this module.
__all__ = ["app"]
