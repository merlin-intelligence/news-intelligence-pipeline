"""Harvest stage: query every seed on every enabled channel."""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

from newsintel.config import Config
from newsintel.data import HARVEST_COLUMNS, article_id, domain_of
from newsintel.harvest import brave, google_news

log = logging.getLogger(__name__)


def harvest(cfg: Config, seeds: list[str], channels: list[str] | None = None) -> pd.DataFrame:
    channels = channels or cfg.harvest.channels
    h = cfg.harvest
    sites = {s.name: s.site for s in h.brave.site_channels}

    client = None
    if any(c != "google_news" for c in channels):
        try:
            client = brave.BraveClient()
        except brave.BraveError as e:
            skipped = [c for c in channels if c != "google_news"]
            log.warning("%s — skipping channel(s): %s", e, ", ".join(skipped))
            channels = [c for c in channels if c == "google_news"]

    session = requests.Session()
    freshness = brave.freshness_for(h.days)
    harvested_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    rows: list[dict] = []

    for i, seed in enumerate(seeds, 1):
        found = 0
        for channel in channels:
            try:
                if channel == "google_news":
                    records = google_news.search(
                        seed, h.days, h.google_news.language, h.google_news.country, h.max_results_per_seed, session
                    )
                    time.sleep(h.request_delay)
                elif channel == "brave_news":
                    records = client.news(seed, h.brave.count, freshness)
                elif channel == "brave_web":
                    records = client.web(seed, h.brave.count, freshness)
                else:  # site-restricted Brave web search
                    records = client.web(f"site:{sites[channel]} {seed.replace(chr(34), '')}", h.brave.count)
            except brave.BraveError:
                raise  # bad key / quota: stop instead of failing every query
            except Exception as e:  # one failing query must not stop the run
                log.warning("[%s] '%s' failed: %s", channel, seed, e)
                continue
            for r in records:
                rows.append({**r, "channel": channel, "seed": seed, "harvested_at": harvested_at})
            found += len(records)
        log.info("[%d/%d] %s → %d results", i, len(seeds), seed, found)

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=HARVEST_COLUMNS)

    df = df[df["url"].astype(str).str.startswith("http")].copy()
    df["article_id"] = df["url"].map(article_id)
    # Google News redirect links have no meaningful domain: use the publisher's.
    df["domain"] = [
        domain_of(su) if "news.google.com" in u and su else domain_of(u)
        for u, su in zip(df["url"], df.get("source_url", ""))
    ]

    cutoff = (date.today() - timedelta(days=h.days)).isoformat()
    too_old = (df["published_at"] != "") & (df["published_at"] < cutoff)
    df = df[~too_old]

    # Same article from several seeds/channels: keep the first occurrence.
    before = len(df)
    df["_title_key"] = df["title"].str.lower().str.replace(r"\W+", " ", regex=True).str.strip()
    df = df.drop_duplicates("article_id").drop_duplicates(["_title_key", "domain"])
    log.info("Harvest: %d results, %d unique articles", before, len(df))
    return df[HARVEST_COLUMNS].reset_index(drop=True)

