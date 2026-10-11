"""Decode Google News article links (news.google.com/rss/articles/<id>) to the
publisher URL, without an API key.

Google only exposes the target URL through its internal "batchexecute" RPC:
  1. GET  /rss/articles/<id>  → page carrying a signature and a timestamp
  2. POST /_/DotsSplashUi/data/batchexecute with (id, timestamp, signature)
     → the publisher URL ("garturlres")

Adapted from the googlenewsdecoder package (MIT). This is an undocumented
endpoint: if Google changes it, resolution falls back to Brave Search.
"""

from __future__ import annotations

import json
import logging
import re
import time
from urllib.parse import parse_qs, quote, urlparse

import requests

log = logging.getLogger(__name__)

BATCHEXECUTE_URL = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
_SG = re.compile(r'data-n-a-sg="([^"]+)"')
_TS = re.compile(r'data-n-a-ts="([^"]+)"')
CONSENT_COOKIES = {"CONSENT": "YES+", "SOCS": "CAESEwgDEgk0ODE3Nzk3MjQaAmVuIAEaBgiA_LyaBg"}
_CTX = [
    ["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1],
    "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0,
]  # fmt: skip


def google_article_id(url: str) -> str | None:
    p = urlparse(url)
    parts = p.path.split("/")
    if p.hostname == "news.google.com" and len(parts) > 1 and parts[-2] in ("articles", "read"):
        return parts[-1] or None
    return None


def _signature(session: requests.Session, art_id: str, source_url: str, timeout: int) -> tuple[str, str] | None:
    qs = parse_qs(urlparse(source_url).query)
    hl, gl, ceid = (qs.get(k, [d])[0] for k, d in (("hl", "en-US"), ("gl", "US"), ("ceid", "US:en")))
    url = f"https://news.google.com/rss/articles/{art_id}?hl={quote(hl)}&gl={quote(gl)}&ceid={quote(ceid)}"
    resp = session.get(url, timeout=timeout)
    if not resp.ok:
        return None
    sg, ts = _SG.search(resp.text), _TS.search(resp.text)
    return (sg.group(1), ts.group(1)) if sg and ts else None


def _batchexecute(session: requests.Session, items: list[tuple[str, str, str, str]], timeout: int) -> dict[str, str]:
    """items: (request_id, article_id, timestamp, signature) → {request_id: url}"""
    envelopes = [
        ["Fbv4je", json.dumps(["garturlreq", _CTX, aid, int(ts) if ts.isdigit() else ts, sig], separators=(",", ":")), None, rid]
        for rid, aid, ts, sig in items
    ]
    resp = session.post(
        BATCHEXECUTE_URL,
        data=f"f.req={quote(json.dumps([envelopes], separators=(',', ':')))}",
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        timeout=timeout,
    )
    resp.raise_for_status()
    body = resp.text.split("\n\n", 1)[-1].lstrip()
    if body.startswith(")]}'"):
        body = body.split("\n", 1)[1]
    found: dict[str, str] = {}
    for row in json.loads(body):
        if isinstance(row, list) and len(row) >= 3 and row[0] == "wrb.fr" and isinstance(row[2], str):
            payload = json.loads(row[2])
            if payload and payload[0] == "garturlres":
                rid = next((str(c) for c in reversed(row[3:]) if c is not None), None)
                if rid is not None:
                    found[rid] = payload[1]
    return found


def decode(urls: list[str], batch_size: int = 20, interval: float = 0.5, timeout: int = 15) -> dict[str, str]:
    """Return {google_url: publisher_url} for the links that could be decoded."""
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    # From the EU, Google redirects to a cookie-consent page unless consent is set.
    for name, value in CONSENT_COOKIES.items():
        session.cookies.set(name, value, domain=".google.com")
    decoded: dict[str, str] = {}
    for start in range(0, len(urls), batch_size):
        batch = urls[start : start + batch_size]
        items = []
        for i, url in enumerate(batch):
            art_id = google_article_id(url)
            if not art_id:
                continue
            try:
                sig = _signature(session, art_id, url, timeout)
            except requests.RequestException as e:
                log.debug("Signature fetch failed for %s: %s", url, e)
                continue
            if sig:
                items.append((str(i), art_id, sig[1], sig[0]))
            time.sleep(interval)
        if not items:
            continue
        try:
            for rid, target in _batchexecute(session, items, timeout).items():
                decoded[batch[int(rid)]] = target
        except (requests.RequestException, ValueError, IndexError) as e:
            log.warning("Google News decoding failed for a batch: %s", e)
        log.info("Decoded %d/%d Google News links", len(decoded), len(urls))
    return decoded
