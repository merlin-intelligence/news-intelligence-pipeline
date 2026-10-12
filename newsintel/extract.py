"""Extract stage: download each article and keep its readable text.

Two engines:
  * playwright — headless Chromium, renders JavaScript (default, most robust)
  * requests   — plain HTTP, much faster, fails on JS-only sites

Progress is checkpointed so an interrupted run resumes where it stopped.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import pandas as pd
import requests

from newsintel.config import ExtractionConfig
from newsintel.data import read_csv, write_csv
from newsintel.text import classify_text, extract_article

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
RESULT_COLUMNS = ["article_id", "text", "extraction_status", "extraction_error", "page_date"]
FINAL_STATUSES = {"ok", "blocked", "too_short"}  # "error" is retried on resume

OnResult = Callable[[str, dict], None]


def _result(html: str | None, min_chars: int, error: str = "", url: str | None = None) -> dict:
    if html is None:
        return {"text": "", "extraction_status": "error", "extraction_error": error[:300], "page_date": ""}
    text, date = extract_article(html, url)
    status = classify_text(text, min_chars)
    ok = status == "ok"
    return {"text": text if ok else "", "extraction_status": status, "extraction_error": "", "page_date": date if ok else ""}


def _run_requests(jobs: dict[str, str], cfg: ExtractionConfig, on_result: OnResult) -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})

    def fetch(url: str) -> dict:
        try:
            resp = session.get(url, timeout=cfg.timeout)
            if resp.status_code >= 400:
                return _result(None, cfg.min_chars, f"HTTP {resp.status_code}")
            return _result(resp.text, cfg.min_chars, url=resp.url)
        except Exception as e:
            return _result(None, cfg.min_chars, str(e))

    with ThreadPoolExecutor(max_workers=cfg.workers) as pool:
        futures = {pool.submit(fetch, url): aid for aid, url in jobs.items()}
        for fut in as_completed(futures):
            on_result(futures[fut], fut.result())


async def _run_playwright(jobs: dict[str, str], cfg: ExtractionConfig, on_result: OnResult) -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        raise RuntimeError(
            "Playwright is not installed. Run `pip install playwright && playwright install chromium`, "
            "or set extraction.engine: requests"
        ) from e

    sem = asyncio.Semaphore(cfg.workers)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT, locale="en-US")
        # Skip heavy resources: we only need the DOM.
        await context.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in ("image", "media", "font")
            else route.continue_(),
        )

        async def worker(aid: str, url: str) -> None:
            async with sem:
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=cfg.timeout * 1000)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=3000)
                    except Exception:
                        pass  # pages with endless polling never go idle
                    result = _result(await page.content(), cfg.min_chars, url=page.url)
                except Exception as e:
                    result = _result(None, cfg.min_chars, str(e).splitlines()[0] if str(e) else repr(e))
                finally:
                    await page.close()
                on_result(aid, result)

        await asyncio.gather(*(worker(aid, url) for aid, url in jobs.items()))
        await browser.close()


def filter_by_age(df: pd.DataFrame, days: int) -> pd.DataFrame:
    """Discard articles whose resolved published_at is older than `days`."""
    if df.empty or days <= 0 or "published_at" not in df.columns:
        return df
    ref = pd.to_datetime(df["harvested_at"], errors="coerce").max() if "harvested_at" in df.columns else pd.NaT
    if pd.isna(ref):
        ref = datetime.now(timezone.utc)
    cutoff = (ref - timedelta(days=days)).date().isoformat()
    pub_dates = df["published_at"].fillna("").astype(str).str.strip().str[:10]
    too_old = (pub_dates != "") & (pub_dates < cutoff)
    if too_old.any():
        n = int(too_old.sum())
        log.info("Discarded %d articles older than %d days (published before %s)", n, days, cutoff)
        return df[~too_old].reset_index(drop=True)
    return df


def extract(
    df: pd.DataFrame,
    cfg: ExtractionConfig,
    checkpoint: Path | None = None,
    days: int | None = None,
) -> pd.DataFrame:
    done: dict[str, dict] = {}
    if checkpoint and checkpoint.exists():
        prev = read_csv(checkpoint)
        done = {r["article_id"]: r for r in prev.to_dict("records") if r["extraction_status"] in FINAL_STATUSES}
        log.info("Resuming extraction: %d articles already processed", len(done))

    for aid, url in zip(df["article_id"], df["resolved_url"]):
        if "news.google.com" in url and aid not in done:
            done[aid] = {"text": "", "extraction_status": "unresolved", "extraction_error": "Google News link not resolved"}
    jobs = {aid: url for aid, url in zip(df["article_id"], df["resolved_url"]) if aid not in done}
    total, counter = len(jobs), {"n": 0}

    def save() -> None:
        if checkpoint:
            write_csv(pd.DataFrame([{"article_id": k, **v} for k, v in done.items()], columns=RESULT_COLUMNS), checkpoint)

    def on_result(aid: str, result: dict) -> None:
        done[aid] = result
        counter["n"] += 1
        log.debug("%s → %s", jobs[aid], result["extraction_status"])
        if counter["n"] % cfg.checkpoint_every == 0:
            save()
            log.info("Extracted %d/%d", counter["n"], total)

    if jobs:
        log.info("Extracting %d articles with %s (%d workers)", total, cfg.engine, cfg.workers)
        try:
            if cfg.engine == "playwright":
                asyncio.run(_run_playwright(jobs, cfg, on_result))
            else:
                _run_requests(jobs, cfg, on_result)
        finally:
            save()

    results = pd.DataFrame([{"article_id": k, **v} for k, v in done.items()], columns=RESULT_COLUMNS)
    out = df.drop(columns=[c for c in RESULT_COLUMNS[1:] if c in df.columns]).merge(results, on="article_id", how="left")
    out[RESULT_COLUMNS[1:]] = out[RESULT_COLUMNS[1:]].fillna("")
    # Search results often lack a date (Brave web, site channels): use the page's own.
    missing = (out["published_at"] == "") & (out["page_date"] != "")
    out.loc[missing, "published_at"] = out.loc[missing, "page_date"]
    if missing.any():
        log.info("Publication date taken from the page for %d articles", int(missing.sum()))
    out = out.drop(columns=["page_date"])
    counts = out["extraction_status"].value_counts().to_dict()
    log.info("Extraction: %s", ", ".join(f"{k}={v}" for k, v in counts.items()))
    if days is not None and days > 0:
        out = filter_by_age(out, days)
    return out
