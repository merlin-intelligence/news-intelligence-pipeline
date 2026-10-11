import numpy as np
import pytest

from newsintel.scoring import centrality_scores, composite, hinge_component, novelty_scores, score


def test_novelty_penalizes_duplicates():
    sim = np.array([[0, 0.95, 0.1], [0.95, 0, 0.1], [0.1, 0.1, 0]])
    nov = novelty_scores(sim, priority=np.array([3.0, 2.0, 1.0]))
    assert nov[0] == 100 and nov[1] < 10 and nov[2] > 85


def test_centrality_finds_the_bridge():
    # 0-1 cluster, 3-4 cluster, 2 links both
    sim = np.zeros((5, 5))
    for a, b in [(0, 1), (1, 2), (2, 3), (3, 4)]:
        sim[a, b] = sim[b, a] = 0.5
    c = centrality_scores(sim, threshold=0.2)
    assert c.argmax() == 2 and c.max() == pytest.approx(100)


def test_composite_ignores_zero_weights_and_rescales():
    out = composite({"a": np.array([100.0, 50.0]), "b": np.array([0.0, 100.0])}, {"a": 1.0, "b": 0.0})
    assert out.tolist() == [100.0, 50.0]


def test_score_assigns_categories_and_ranks(articles, cfg):
    df = score(articles, cfg).articles
    assert len(df) == len(articles)
    assert df["rank"].tolist() == list(range(1, len(df) + 1))
    assert df["score"].max() == 100 and (df["score"] >= 0).all()
    by_seed = df.groupby("seed")["category_id"].agg(lambda s: s.mode()[0])
    assert by_seed.to_dict() == {"rail": "rail", "solar": "solar", "water": "water"}
    assert (df.loc[df["seed"] == "solar", "entities"] == "Grid").all()
    assert df["summary"].str.len().gt(0).all()


def test_score_drops_failed_extractions(articles, cfg):
    articles.loc[0, "extraction_status"] = "blocked"
    assert len(score(articles, cfg).articles) == len(articles) - 1


def test_score_without_categories(articles, cfg):
    cfg.categories = []
    df = score(articles, cfg).articles
    assert (df["category_id"] == "").all() and df["score"].max() == 100


def test_hinge_component_is_off_by_default(articles, cfg):
    df = score(articles, cfg).articles
    assert (df["hinge"] == 0).all()


def test_hinge_component_finds_the_hub():
    sim = np.zeros((5, 5))
    for a, b, v in [(0, 1, 0.9), (3, 4, 0.9), (1, 2, 0.5), (2, 3, 0.5), (0, 2, 0.3), (2, 4, 0.3)]:
        sim[a, b] = sim[b, a] = v
    h = hinge_component(sim, threshold=0.2)
    assert h.argmax() == 2 and h.max() == pytest.approx(100)
    assert (hinge_component(sim, threshold=0.95) == 0).all()  # no edge left


def test_hinge_component_when_weighted(articles, cfg):
    cfg.scoring.weights["hinge"] = 0.2
    df = score(articles, cfg).articles
    assert df["hinge"].between(0, 100).all()
    assert df["score"].max() == pytest.approx(100)
