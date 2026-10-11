"""Report stage: a single self-contained HTML file (no external assets).

The page layout is the Jinja2 template templates/report.html.j2 (styles in
templates/report.css); this module only prepares the values it displays.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from newsintel.config import Config

SCORE_LABELS = {
    "relevance": "Relevance",
    "category_match": "Category match",
    "novelty": "Novelty",
    "centrality": "Centrality",
    "hinge": "Hinge",
}

_env = Environment(
    loader=PackageLoader("newsintel", "templates"),
    autoescape=select_autoescape(["html", "j2"]),
    undefined=StrictUndefined,  # a typo in the template fails loudly instead of rendering blank
)


def _text(value) -> str:
    return "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)


def _int(value) -> str:
    try:
        return f"{float(value):.0f}"
    except (TypeError, ValueError):
        return "0"


def _ordered(df: pd.DataFrame, sort_by: str) -> pd.DataFrame:
    if sort_by == "date":
        return df.assign(_d=pd.to_datetime(df["published_at"], errors="coerce")).sort_values(
            ["_d", "score"], ascending=[False, False], na_position="last"
        )
    return df


def _active_components(cfg: Config) -> list[str]:
    return [k for k, w in cfg.scoring.weights.items() if w > 0 and (k != "category_match" or cfg.categories)]


def _top_story(row: dict, components: list[str]) -> dict:
    meta = [f"#{_int(row['rank'])}", _text(row.get("source") or row.get("domain")), _text(row.get("published_at")), _text(row.get("channel"))]
    if row.get("entities"):
        meta.append(_text(row["entities"]))
    return {
        "url": _text(row["resolved_url"]),
        "title": _text(row["title"]),
        "meta": [m for m in meta if m],
        "category": _text(row.get("category_name")),
        "summary": _text(row.get("summary")),
        "bars": [("Score", _int(row["score"]))] + [(SCORE_LABELS[k], _int(row.get(k))) for k in components],
    }


def _further(row: dict) -> dict:
    return {
        "rank": _int(row["rank"]),
        "date": _text(row.get("published_at")),
        "url": _text(row["resolved_url"]),
        "title": _text(row["title"]),
        "source": _text(row.get("source") or row.get("domain")),
        "category": _text(row.get("category_name")),
        "score": _int(row["score"]),
    }


def render(selection: pd.DataFrame, scored: pd.DataFrame, cfg: Config, stats: dict) -> str:
    top = _ordered(selection[selection["tier"] == "top"], cfg.report.sort_by)
    further = _ordered(selection[selection["tier"] == "next"], cfg.report.sort_by)
    components = _active_components(cfg)

    categories = []
    if cfg.categories:
        counts = scored["category_id"].value_counts() if len(scored) else pd.Series(dtype=int)
        top_counts = top["category_id"].value_counts() if len(top) else pd.Series(dtype=int)
        categories = [
            {"name": c.name, "description": c.description, "count": int(counts.get(c.id, 0)), "in_top": int(top_counts.get(c.id, 0))}
            for c in cfg.categories
        ]

    channels = stats.get("channels", {})
    return _env.get_template("report.html.j2").render(
        title=cfg.project.title,
        subtitle=cfg.report.subtitle or cfg.project.description,
        days=cfg.harvest.days,
        generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        stats=[
            (stats.get("seeds", 0), "search queries"),
            (stats.get("harvested", 0), "articles found"),
            (stats.get("extracted", 0), "full texts read"),
            (len(scored), "articles ranked"),
            (len(top), "top stories"),
        ],
        categories=categories,
        top=[_top_story(r, components) for r in top.to_dict("records")],
        further=[_further(r) for r in further.to_dict("records")],
        channels=", ".join(f"{k} ({v})" for k, v in channels.items()) or "—",
        weights=", ".join(f"{SCORE_LABELS[k].lower()} {cfg.scoring.weights[k]:.0%}" for k in components),
        uses_hinge=cfg.scoring.weights.get("hinge", 0) > 0,
        theta=cfg.selection.method == "theta",
        coverage=cfg.selection.ensure_category_coverage and bool(cfg.categories),
        project=cfg.project.name,
    )
