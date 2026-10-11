"""Select stage: pick the "top" and "next" tiers shown in the report.

In every mode, near-duplicates (similarity above max_pairwise_similarity with
an article already picked) are skipped, so one story is not reported twice.

method: score (default)
  1. with ensure_category_coverage, the best article of every category is
     guaranteed a place in the top tier;
  2. remaining top slots are filled by score.

method: theta
  1. the pool is the top_n × theta_pool best-scored articles;
  2. the top tier is a θ-diverse subset of that pool (eigenmind: Lovász θ
     approximation of the overlap graph, then farthest-point selection
     starting from the best article), so it spans as many distinct stories
     as possible instead of piling up variations of the dominant one;
  3. with ensure_category_coverage, a category left out gets its best
     article, in place of the lowest-scored pick of an over-represented one.

The "next" tier is then filled by score in both modes.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from newsintel.config import Config
from newsintel.graph import theta_pick
from newsintel.scoring import build_corpus, text_similarity

log = logging.getLogger(__name__)


def _cover_categories(top: list[int], candidates: list[int], df: pd.DataFrame, cfg: Config) -> list[int]:
    """Swap in the best candidate of each missing category, replacing the
    lowest-scored pick of a category that has more than one."""
    top = list(top)
    for cat in cfg.categories:
        cats = df.loc[top, "category_id"]
        if (cats == cat.id).any():
            continue
        best = next((i for i in candidates if df.at[i, "category_id"] == cat.id and i not in top), None)
        counts = cats.value_counts()
        crowded = [i for i in top if counts.get(df.at[i, "category_id"], 0) > 1]
        if best is None or not crowded:
            continue
        top[top.index(min(crowded, key=lambda i: df.at[i, "score"]))] = best
    return top


def select(df: pd.DataFrame, cfg: Config, similarity: np.ndarray | None = None) -> pd.DataFrame:
    """`similarity` (rows in the order of `df`) is the matrix saved by the score
    stage; without it, it is recomputed from the articles' `text` column."""
    sel = cfg.selection
    if df.empty:
        return df.assign(tier=[], selection_rank=[])
    order = np.argsort(-df["score"].to_numpy(dtype=float), kind="stable")
    df = df.iloc[order].reset_index(drop=True)
    sim = text_similarity(build_corpus(df), cfg) if similarity is None else similarity[np.ix_(order, order)]
    picked: list[int] = []

    def is_duplicate(i: int) -> bool:
        return bool(picked) and sim[i, picked].max() > sel.max_pairwise_similarity

    def take(candidates, limit: int) -> None:
        for i in candidates:
            if len(picked) >= limit:
                return
            if i not in picked and not is_duplicate(i):
                picked.append(i)

    coverage = sel.ensure_category_coverage and cfg.categories
    if sel.method == "theta":
        take(df.index, sel.top_n * max(sel.theta_pool, 1))  # de-duplicated pool, by score
        pool = list(picked)
        chosen = theta_pick(sim[np.ix_(pool, pool)], sel.theta_conflict_threshold, sel.top_n, first=0)
        top = [pool[i] for i in chosen]
        if coverage:
            # candidates: every non-duplicate article, by score
            picked[:] = top
            take(df.index, len(df))
            top = _cover_categories(top, picked[len(top):], df, cfg)
        picked[:] = top
    else:
        if coverage:
            for cat in cfg.categories:
                take(df.index[df["category_id"] == cat.id], len(picked) + 1)
                if len(picked) >= sel.top_n:
                    break
        take(df.index, sel.top_n)

    top = sorted(picked, key=lambda i: -df.at[i, "score"])
    picked[:] = top
    take(df.index, sel.top_n + sel.next_n)
    following = picked[len(top):]

    out = pd.concat([df.loc[top].assign(tier="top"), df.loc[following].assign(tier="next")])
    out["selection_rank"] = np.arange(1, len(out) + 1)
    skipped = len(df) - len(out)
    log.info("Selected %d top + %d next articles (%s, %d not selected)", len(top), len(following), sel.method, skipped)
    return out.reset_index(drop=True)
