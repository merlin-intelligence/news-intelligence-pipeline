"""Google News search via its public RSS endpoint."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import requests

from newsintel.text import strip_html

log = logging.getLogger(__name__)

RSS_URL = "https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={gl}:{lang}"


def _parse_date(value: str) -> str:
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError):
        return ""


def search(
    query: str,
    days: int,
    language: str = "en",
    country: str = "US",
    max_results: int = 20,
    session: requests.Session | None = None,
    timeout: int = 15,
) -> list[dict]:
    """Return raw records for one query. Links point to news.google.com and are
    resolved to publisher URLs by newsintel.resolve, still within the harvest stage."""
    url = RSS_URL.format(
        q=quote(f"{query} when:{days}d"),
        hl=f"{language}-{country}",
        gl=country,
        lang=language,
    )
    http = session or requests
    resp = http.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 newsintel"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    records = []
    for item in root.iter("item"):
        source_el = item.find("source")
        source = (source_el.text or "").strip() if source_el is not None else ""
        source_url = source_el.get("url", "") if source_el is not None else ""
        title = (item.findtext("title") or "").strip()
        if source and title.endswith(f" - {source}"):
            title = title[: -len(source) - 3]
        records.append(
            {
                "title": title,
                "description": strip_html(item.findtext("description") or ""),
                "url": (item.findtext("link") or "").strip(),
                "source": source,
                "source_url": source_url,
                "published_at": _parse_date(item.findtext("pubDate") or ""),
            }
        )
        if len(records) >= max_results:
            break
    return records
