import pytest

from newsintel.scoring import score
from newsintel.selection import select


def test_selection_covers_categories_and_skips_duplicates(articles, cfg):
    scored = score(articles, cfg).articles
    out = select(scored, cfg)
    top = out[out["tier"] == "top"]
    assert len(top) == cfg.selection.top_n
    assert set(top["category_id"]) == {"rail", "solar", "water"}
    # the mirror copy of rail story 0 must never sit next to its original
    titles = set(out["title"])
    assert not {"Rail story 0", "Rail story copy"} <= titles
    assert len(out) <= cfg.selection.top_n + cfg.selection.next_n
    assert out["selection_rank"].tolist() == list(range(1, len(out) + 1))


def test_selection_top_is_sorted_by_score(articles, cfg):
    out = select(score(articles, cfg).articles, cfg)
    top = out[out["tier"] == "top"]["score"].tolist()
    assert top == sorted(top, reverse=True)


def test_theta_selection_covers_categories(articles, cfg):
    cfg.selection.method = "theta"
    cfg.selection.theta_conflict_threshold = 0.2
    out = select(score(articles, cfg).articles, cfg)
    top = out[out["tier"] == "top"]
    assert len(top) == cfg.selection.top_n
    assert set(top["category_id"]) == {"rail", "solar", "water"}
    assert not {"Rail story 0", "Rail story copy"} <= set(out["title"])
    assert top["score"].tolist() == sorted(top["score"], reverse=True)


def test_theta_selection_starts_from_best_article(articles, cfg):
    cfg.selection.method = "theta"
    cfg.selection.ensure_category_coverage = False
    scored = score(articles, cfg).articles
    out = select(scored, cfg)
    assert scored.iloc[0]["article_id"] in set(out[out["tier"] == "top"]["article_id"])


def test_selection_reuses_the_saved_similarity(articles, cfg, tmp_path):
    from newsintel.scoring import load_similarity, save_similarity

    result = score(articles, cfg)
    path = tmp_path / "similarity.npz"
    save_similarity(path, result.articles["article_id"], result.similarity)
    # reload in another order: rows must follow the requested ids
    shuffled = result.articles.sample(frac=1, random_state=0).reset_index(drop=True)
    sim = load_similarity(path, shuffled["article_id"])
    assert sim.shape == result.similarity.shape
    i, j = 0, 1
    a, b = shuffled["article_id"][i], shuffled["article_id"][j]
    pos = {x: k for k, x in enumerate(result.articles["article_id"])}
    assert sim[i, j] == pytest.approx(result.similarity[pos[a], pos[b]], abs=1e-6)

    # same input order (ties between equal scores keep that order): same picks,
    # whether the matrix is reloaded (no text needed) or recomputed from the texts
    reused = select(shuffled.drop(columns=["text"]), cfg, sim)
    recomputed = select(shuffled, cfg)
    assert reused["article_id"].tolist() == recomputed["article_id"].tolist()
    assert load_similarity(path, ["unknown-id"]) is None
