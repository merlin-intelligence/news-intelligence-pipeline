"""Brave Search API client (web + news). Requires BRAVE_API_KEY."""

from __future__ import annotations

import logging
import os
import time
from datetime import date, timedelta

import pandas as pd
import requests

from newsintel.text import strip_html

log = logging.getLogger(__name__)

WEB_URL = "https://api.search.brave.com/res/v1/web/search"
NEWS_URL = "https://api.search.brave.com/res/v1/news/search"


class BraveError(RuntimeError):
    pass


def api_key() -> str | None:
    return os.environ.get("BRAVE_API_KEY") or None


def freshness_for(days: int) -> str:
    """Brave accepts a custom 'YYYY-MM-DDtoYYYY-MM-DD' range."""
    today = date.today()
    return f"{(today - timedelta(days=days)).isoformat()}to{today.isoformat()}"


def _iso_date(value: str | None) -> str:
    if not value:
        return ""
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    return "" if pd.isna(ts) else ts.date().isoformat()


class BraveClient:
    def __init__(self, key: str | None = None, min_interval: float = 1.05, max_retries: int = 3, timeout: int = 15):
        self.key = key or api_key()
        if not self.key:
            raise BraveError("BRAVE_API_KEY is not set (see .env.example)")
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "Accept-Encoding": "gzip", "X-Subscription-Token": self.key}
        )
        # The free plan allows 1 request/second; paid plans can lower this.
        self.min_interval = float(os.environ.get("BRAVE_MIN_INTERVAL", min_interval))
        self.max_retries = max_retries
        self.timeout = timeout
        self._last_call = 0.0

    def _get(self, url: str, params: dict) -> dict:
        for attempt in range(self.max_retries + 1):
            wait = self.min_interval - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            resp = self.session.get(url, params=params, timeout=self.timeout)
            if resp.status_code == 429 and attempt < self.max_retries:
                backoff = 2 ** (attempt + 1)
                log.warning("Brave rate limit hit, retrying in %ss", backoff)
                time.sleep(backoff)
                continue
            if resp.status_code in (401, 403):
                raise BraveError(f"Brave API rejected the key (HTTP {resp.status_code})")
            resp.raise_for_status()
            return resp.json()
        return {}

    @staticmethod
    def _record(item: dict) -> dict:
        meta = item.get("meta_url") or {}
        profile = item.get("profile") or {}
        return {
            "title": strip_html(item.get("title", "")),
            "description": strip_html(item.get("description", "")),
            "url": item.get("url", ""),
            "source": profile.get("name") or meta.get("hostname", ""),
            "source_url": "",
            "published_at": _iso_date(item.get("page_age")),
        }

    def web(self, query: str, count: int = 5, freshness: str | None = None) -> list[dict]:
        params = {"q": query, "count": count}
        if freshness:
            params["freshness"] = freshness
        items = self._get(WEB_URL, params).get("web", {}).get("results", [])
        return [self._record(i) for i in items if i.get("url")]

    def news(self, query: str, count: int = 5, freshness: str | None = None) -> list[dict]:
        params = {"q": query, "count": count}
        if freshness:
            params["freshness"] = freshness
        items = self._get(NEWS_URL, params).get("results", [])
        return [self._record(i) for i in items if i.get("url")]
