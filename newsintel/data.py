"""Shared data schema and file helpers.

Every stage reads and writes one CSV with these columns (later stages add more):

    article_id, channel, seed, title, description, url, source, domain,
    published_at, harvested_at
    + resolved_url                                  (harvest stage, after link resolution)
    + text, extraction_status, extraction_error     (extract stage)
    + relevance, category_match, novelty, centrality, hinge, score, rank,
      category_id, category_name, entities, summary (score stage; text dropped)
    + tier, selection_rank                          (select stage)
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pandas as pd

HARVEST_COLUMNS = [
    "article_id",
    "channel",
    "seed",
    "title",
    "description",
    "url",
    "source",
    "domain",
    "published_at",
    "harvested_at",
]

SEED_COLUMN_CANDIDATES = ("query", "seed", "seeds", "keyword", "keywords", "theme")


def normalize_url(url: str) -> str:
    """Drop fragment and tracking query params so duplicates collapse."""
    try:
        p = urlparse(str(url).strip())
    except ValueError:
        return str(url).strip()
    query = "&".join(q for q in p.query.split("&") if q and not q.lower().startswith(("utm_", "fbclid", "gclid")))
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", query, ""))


def article_id(url: str) -> str:
    return hashlib.sha1(normalize_url(url).encode("utf-8")).hexdigest()[:12]


def domain_of(url: str) -> str:
    netloc = urlparse(str(url)).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False, encoding="utf-8-sig")  # the BOM makes Excel read UTF-8 correctly
    tmp.replace(path)


def load_seeds(file: Path | None, column: str | None = None, inline: list[str] | None = None, limit: int | None = None) -> list[str]:
    """Seeds come from a CSV (auto-detected column), a .txt (one per line), and/or the config."""
    seeds: list[str] = list(inline or [])
    if file:
        if not file.exists():
            raise FileNotFoundError(f"Seeds file not found: {file}")
        if file.suffix.lower() == ".txt":
            seeds += [line for line in file.read_text(encoding="utf-8-sig").splitlines()]
        else:
            df = pd.read_csv(file, dtype=str, keep_default_na=False, encoding="utf-8-sig")
            if column:
                if column not in df.columns:
                    raise ValueError(f"Column '{column}' not found in {file}")
                col = column
            else:
                lower = {c.lower(): c for c in df.columns}
                col = next((lower[c] for c in SEED_COLUMN_CANDIDATES if c in lower), df.columns[0])
            seeds += df[col].tolist()

    out, seen = [], set()
    for s in (str(s).strip() for s in seeds):
        if s and not s.startswith("#") and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out[:limit] if limit else out
