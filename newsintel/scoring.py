"""Score stage: rank articles with 0–100 components.

  relevance       similarity to the topic (project.description + keywords),
                  blended with keyword frequency
  category_match  best similarity to one category description; each category
                  is normalised separately so every category weighs the same
  novelty         1 − max similarity to any more relevant article
                  (penalises articles that repeat a better one)
  centrality      betweenness in the article similarity graph
                  (articles bridging otherwise separate stories)
  hinge           eigenmind hinge score: articles near the centre of the
                  graph's main axis that link both of its poles
                  ("relevant but not obvious"); weight 0 by default

  score = weighted sum of the active components, rescaled so the best is 100.

Everything is TF-IDF + cosine similarity: fast, deterministic, no model download.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import NamedTuple

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from newsintel.config import Category, Config
from newsintel.graph import hinge_scores as eigenmind_hinge
from newsintel.text import compile_entities, summarize, tag_entities

log = logging.getLogger(__name__)

MAX_TEXT_CHARS = 20_000
CENTRALITY_SAMPLE_ABOVE = 800  # approximate betweenness on large corpora


class Scored(NamedTuple):
    articles: pd.DataFrame  # sorted by score, best first
    similarity: np.ndarray  # article × article text similarity, rows in the order of `articles`


def build_corpus(df: pd.DataFrame) -> list[str]:
    return (
        df["title"].fillna("") + ". " + df["description"].fillna("") + ". " + df["text"].fillna("").str[:MAX_TEXT_CHARS]
    ).tolist()


def _rescale(values: np.ndarray) -> np.ndarray:
    top = values.max() if len(values) else 0
    return values * 100.0 / top if top > 0 else np.zeros_like(values, dtype=float)


def relevance_scores(
    docs: list[str], reference: str, keywords: list[str], keyword_weight: float, vectorizer_kwargs: dict
) -> np.ndarray:
    vec = TfidfVectorizer(**vectorizer_kwargs).fit(docs + [reference])
    cos = cosine_similarity(vec.transform(docs), vec.transform([reference])).ravel()
    if not keywords:
        return _rescale(cos)
    patterns = [re.compile(r"\b" + re.escape(k.lower()) + r"\b") for k in keywords]
    counts = np.array([sum(len(p.findall(d.lower())) for p in patterns) for d in docs], dtype=float)
    blended = (1 - keyword_weight) * _rescale(cos) + keyword_weight * _rescale(np.log1p(counts))
    return _rescale(blended)


def category_scores(docs: list[str], categories: list[Category], vectorizer_kwargs: dict) -> tuple[np.ndarray, list[str]]:
    """Return (category_match 0–100, assigned category id per doc)."""
    if not categories:
        return np.zeros(len(docs)), [""] * len(docs)
    descriptors = [f"{c.name}. {c.description}" for c in categories]
    vec = TfidfVectorizer(**vectorizer_kwargs).fit(docs + descriptors)
    sims = cosine_similarity(vec.transform(docs), vec.transform(descriptors))  # (n_docs, n_categories)
    col_max = sims.max(axis=0)
    normalized = np.divide(sims, col_max, out=np.zeros_like(sims), where=col_max > 0) * 100.0
    assigned = [categories[j].id if sims[i, j] > 0 else "" for i, j in enumerate(sims.argmax(axis=1))]
    return normalized.max(axis=1), assigned


def similarity_matrix(docs: list[str], vectorizer_kwargs: dict) -> np.ndarray:
    m = TfidfVectorizer(**vectorizer_kwargs).fit_transform(docs)
    sim = cosine_similarity(m)
    np.fill_diagonal(sim, 0.0)
    return sim


def text_similarity(docs: list[str], cfg: Config) -> np.ndarray:
    """The article × article similarity used by novelty, centrality, hinge and selection."""
    sc = cfg.scoring
    return similarity_matrix(docs, {"stop_words": sc.stop_words, "sublinear_tf": True, "max_features": sc.max_features})


def save_similarity(path: Path, article_ids, sim: np.ndarray) -> None:
    np.savez_compressed(path, ids=np.asarray(article_ids, dtype=str), sim=sim.astype(np.float32))


def load_similarity(path: Path, article_ids) -> np.ndarray | None:
    """Similarity matrix re-ordered to `article_ids`, or None if missing or out of date."""
    if not path.exists():
        return None
    with np.load(path) as data:
        pos = {a: i for i, a in enumerate(data["ids"].tolist())}
        try:
            idx = [pos[a] for a in article_ids]
        except KeyError:
            return None
        return data["sim"][np.ix_(idx, idx)].astype(float)


def novelty_scores(sim: np.ndarray, priority: np.ndarray) -> np.ndarray:
    """Greedy redundancy penalty: walk articles from most to least relevant and
    score each by how different it is from everything walked before it."""
    n = len(priority)
    novelty = np.zeros(n)
    seen_max = np.zeros(n)  # max similarity of each doc to the docs already walked
    for k, i in enumerate(np.argsort(-priority, kind="stable")):
        novelty[i] = 100.0 if k == 0 else max(0.0, 1.0 - seen_max[i]) * 100.0
        seen_max = np.maximum(seen_max, sim[i])
    return novelty


def centrality_scores(sim: np.ndarray, threshold: float) -> np.ndarray:
    n = sim.shape[0]
    g = nx.Graph()
    g.add_nodes_from(range(n))
    rows, cols = np.where(np.triu(sim, k=1) > threshold)
    g.add_edges_from(zip(rows.tolist(), cols.tolist()))
    k = min(n, 400) if n > CENTRALITY_SAMPLE_ABOVE else None
    bc = nx.betweenness_centrality(g, k=k, seed=0)
    return _rescale(np.array([bc[i] for i in range(n)]))


def hinge_component(sim: np.ndarray, threshold: float) -> np.ndarray:
    """eigenmind hinge on the article graph (edges below `threshold` dropped)."""
    w = np.where(sim >= threshold, sim, 0.0)
    if len(w) < 3 or not w.any():
        return np.zeros(len(w))
    if len(w) > 1000:
        log.info("Computing hinge scores on %d articles (eigenmind, may take a while)", len(w))
    _, hinge = eigenmind_hinge(w)
    return _rescale(hinge)


def composite(components: dict[str, np.ndarray], weights: dict[str, float]) -> np.ndarray:
    active = {k: w for k, w in weights.items() if w > 0 and k in components}
    total = sum(active.values())
    raw = sum(components[k] * (w / total) for k, w in active.items())
    return _rescale(np.asarray(raw, dtype=float))


def score(df: pd.DataFrame, cfg: Config) -> Scored:
    sc = cfg.scoring
    df = df.copy()
    if sc.require_text:
        df = df[df["extraction_status"] == "ok"]
    df = df.reset_index(drop=True)
    if df.empty:
        log.warning("No article to score")
        return Scored(df, np.zeros((0, 0)))

    docs = build_corpus(df)
    vk = {"stop_words": sc.stop_words, "sublinear_tf": True, "max_features": sc.max_features}
    reference = " ".join([cfg.project.title, cfg.project.description, *cfg.keywords]).strip()

    components = {
        "relevance": relevance_scores(docs, reference, cfg.keywords, sc.keyword_weight, {**vk, "ngram_range": (1, 2)}),
    }
    if cfg.categories:
        components["category_match"], df["category_id"] = category_scores(docs, cfg.categories, {**vk, "ngram_range": (1, 2)})
    else:
        df["category_id"] = ""
    sim = text_similarity(docs, cfg)
    components["novelty"] = novelty_scores(sim, components["relevance"])
    components["centrality"] = centrality_scores(sim, sc.graph_threshold)
    if sc.weights.get("hinge", 0) > 0:
        components["hinge"] = hinge_component(sim, sc.graph_threshold)

    for name in ("relevance", "category_match", "novelty", "centrality", "hinge"):
        df[name] = np.round(components.get(name, np.zeros(len(df))), 2)
    df["score"] = np.round(composite(components, sc.weights), 2)

    names = {c.id: c.name for c in cfg.categories}
    df["category_name"] = df["category_id"].map(names).fillna("")
    compiled = compile_entities(cfg.entities)
    df["entities"] = [tag_entities(d, compiled) for d in docs] if compiled else ""
    df["summary"] = [summarize(t, d) for t, d in zip(df["text"], df["description"])]

    order = np.argsort(-df["score"].to_numpy(), kind="stable")
    df = df.iloc[order].reset_index(drop=True)
    df["rank"] = np.arange(1, len(df) + 1)
    log.info("Scored %d articles", len(df))
    return Scored(df, sim[np.ix_(order, order)])
