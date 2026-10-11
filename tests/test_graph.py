import numpy as np
import pandas as pd
import pytest

from newsintel.graph import analyze, diverse_subset, hinge_scores, theta_pick


def chain(n=5):
    w = np.zeros((n, n))
    for i in range(n - 1):
        w[i, i + 1] = w[i + 1, i] = 0.8
    return w


def hub():
    """Two pairs (0-1, 3-4) and a hub (2) linked to both sides."""
    w = np.zeros((5, 5))
    for a, b, v in [(0, 1, 0.9), (3, 4, 0.9), (1, 2, 0.5), (2, 3, 0.5), (0, 2, 0.3), (2, 4, 0.3)]:
        w[a, b] = w[b, a] = v
    return w


def test_hinge_scores_poles_and_centre():
    x, hinge = hinge_scores(hub())
    assert np.isclose(np.abs(x).max(), 1.0)
    assert abs(x[2]) < abs(x[0]) and abs(x[2]) < abs(x[4])
    assert hinge.argmax() == 2 and hinge[2] > 0  # the hub links both poles


def test_diverse_subset_drops_conflicting_neighbours():
    picked = diverse_subset(chain(), list("abcde"), threshold=0.5)
    kept = [k for k, _ in picked]
    assert kept == ["a", "c", "e"]


def test_theta_pick_returns_k_distinct_nodes_from_first():
    rng = np.random.default_rng(0)
    sim = rng.random((15, 15))
    sim = (sim + sim.T) / 2
    np.fill_diagonal(sim, 0)
    picked = theta_pick(sim, threshold=0.7, k=5, first=3)
    assert picked[0] == 3 and len(set(picked)) == 5


@pytest.mark.xfail(
    strict=True,
    reason="eigenmind 0.1.1: theta_diversity_picker runs farthest-point selection on a factor "
    "where conflicting nodes are anti-correlated, so it picks nodes from the same conflict clique",
)
def test_theta_pick_spreads_over_clusters():
    # three tight clusters of 4 nodes: a diverse pick of 3 takes one from each
    n = 12
    sim = np.full((n, n), 0.05)
    for c in range(3):
        sim[c * 4:(c + 1) * 4, c * 4:(c + 1) * 4] = 0.9
    np.fill_diagonal(sim, 0)
    picked = theta_pick(sim, threshold=0.5, k=3, first=0)
    assert picked[0] == 0
    assert sorted(i // 4 for i in picked) == [0, 1, 2]


def test_theta_pick_small_input_returns_everything():
    assert theta_pick(np.zeros((2, 2)), 0.5, k=5) == [0, 1]


def test_analyze_writes_outputs(tmp_path):
    names = list("abcde")
    pd.DataFrame(hub(), index=names, columns=names).to_csv(tmp_path / "adj.csv")
    csv_path, md_path = analyze(tmp_path / "adj.csv", tmp_path / "out", [0.5], theta_k=2)
    scores = pd.read_csv(csv_path)
    assert len(scores) == 5 and scores.iloc[0]["node"] == "c"
    report = md_path.read_text(encoding="utf-8")
    assert "Diverse subset" in report and "θ-diverse subset of 2 nodes" in report
