"""Respectful HTTP client with delay, UA, caching, and 429-aware retries."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from wwe_data.config import get_settings


class RateLimitError(Exception):
    def __init__(self, retry_after: float = 5.0) -> None:
        self.retry_after = retry_after
        super().__init__(f"rate limited; retry after {retry_after}s")


class HttpClient:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.settings = get_settings()
        self.cache_dir = cache_dir or (self.settings.raw_dir / "http_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.settings.user_agent,
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            }
        )
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        delay = self.settings.request_delay_seconds
        if elapsed < delay:
            time.sleep(delay - elapsed)

    def _cache_path(self, url: str, params: dict[str, Any] | None) -> Path:
        key = hashlib.sha256(
            json.dumps({"url": url, "params": params or {}}, sort_keys=True).encode()
        ).hexdigest()
        return self.cache_dir / f"{key}.json"

    def _get(self, url: str, params: dict[str, Any] | None = None) -> requests.Response:
        self._throttle()
        resp = self.session.get(url, params=params, timeout=60)
        self._last_request_at = time.monotonic()
        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", "8"))
            time.sleep(retry_after)
            raise RateLimitError(retry_after)
        if resp.status_code >= 500:
            raise requests.HTTPError(f"{resp.status_code} server error", response=resp)
        resp.raise_for_status()
        return resp

    @retry(
        retry=retry_if_exception_type((RateLimitError, requests.HTTPError, requests.ConnectionError)),
        stop=stop_after_attempt(8),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        reraise=True,
    )
    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        *,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        cache_path = self._cache_path(url, params)
        if use_cache and cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        resp = self._get(url, params)
        data = resp.json()
        cache_path.write_text(json.dumps(data), encoding="utf-8")
        return data

    @retry(
        retry=retry_if_exception_type((RateLimitError, requests.HTTPError, requests.ConnectionError)),
        stop=stop_after_attempt(8),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        reraise=True,
    )
    def get_text(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        *,
        use_cache: bool = True,
    ) -> str:
        cache_path = self._cache_path(url, params).with_suffix(".txt")
        if use_cache and cache_path.exists():
            return cache_path.read_text(encoding="utf-8")

        resp = self._get(url, params)
        text = resp.text
        cache_path.write_text(text, encoding="utf-8")
        return text
