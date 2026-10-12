"""Turn Google News redirect links into publisher URLs (run by the harvest stage).

Google News RSS links point to news.google.com and only redirect through
JavaScript, so they cannot be scraped directly. Two strategies, in order:

  1. direct decoding   — through Google's own endpoint (no key, see gnews_decode)
  2. Brave Search      — looks the title up and keeps the hit whose domain
                          matches the publisher (needs BRAVE_API_KEY)
"""

from __future__ import annotations

import logging

import pandas as pd

from newsintel.data import domain_of
from newsintel.harvest import brave, gnews_decode

log = logging.getLogger(__name__)


def needs_resolution(url: str) -> bool:
    return "news.google.com" in str(url)


def pick_result(results: list[dict], expected_domain: str) -> str:
    if not results:
        return ""
    for r in results:
        d = domain_of(r["url"])
        if expected_domain and (d == expected_domain or d.endswith("." + expected_domain)):
            return r["url"]
    return results[0]["url"]


def _resolve_with_brave(rows: pd.DataFrame) -> dict[str, str]:
    try:
        client = brave.BraveClient()
    except brave.BraveError as e:
        log.info("%s — Brave fallback unavailable", e)
        return {}
    found: dict[str, str] = {}
    for row in rows.itertuples():
        try:
            url = pick_result(client.web(row.title, count=3), row.domain)
        except brave.BraveError:
            raise
        except Exception as e:
            log.warning("Brave lookup failed for '%s': %s", row.title[:60], e)
            continue
        if url:
            found[row.url] = url
    return found


def resolve(df: pd.DataFrame, enabled: bool = True) -> pd.DataFrame:
    df = df.copy()
    df["resolved_url"] = df["url"]
    mask = df["url"].map(needs_resolution)
    if not mask.any():
        return df
    if not enabled:
        log.warning("URL resolution disabled: %d Google News links will likely fail extraction", mask.sum())
        return df

    mapping = gnews_decode.decode(df.loc[mask, "url"].tolist())
    remaining = df[mask & ~df["url"].isin(mapping)]
    if len(remaining):
        mapping.update(_resolve_with_brave(remaining))

    df.loc[mask, "resolved_url"] = df.loc[mask, "url"].map(lambda u: mapping.get(u, u))
    done = mask & ~df["resolved_url"].map(needs_resolution)
    df.loc[done, "domain"] = df.loc[done, "resolved_url"].map(domain_of)
    unresolved = int(df["resolved_url"].map(needs_resolution).sum())
    log.info("Resolve: %d/%d Google News links resolved", int(mask.sum()) - unresolved, int(mask.sum()))
    if unresolved:
        log.warning("%d links could not be resolved and will be skipped by extraction", unresolved)
    return df
