"""Graph computations, built on the eigenmind library.

Shared helpers (used by scoring and selection on the article similarity graph):

  hinge_scores    ℓ∞-connectivity position x* and hinge score of every node
                  (eigenmind.connectivity): central nodes linking both poles
  theta_pick      k diverse nodes from a Lovász θ approximation of the
                  conflict graph (eigenmind.theta)

And the optional `graph` command, which analyses a concept adjacency CSV
(first row and first column hold node names, cells are weights in [0, 1] —
e.g. the concept graph used to write the seeds). Per node:

  spectral      peak |coordinate| over the first 3 eigenvectors of the
                symmetric normalised Laplacian (anchor of its component)
  connectivity  x* in [-1, 1]: ±1 are the poles of the graph, 0 its centre
  hinge         how strongly a central node links both poles

plus diverse subsets of nodes — a greedy maximal independent set of the
conflict graph per similarity threshold, and a θ-diverse subset of k nodes.
Useful to pick non-redundant concepts when writing seeds or categories.
"""

from __future__ import annotations

from pathlib import Path

import eigenmind as em
import numpy as np
import pandas as pd


def hinge_scores(w: np.ndarray, pole_quantile: float = 0.90) -> tuple[np.ndarray, np.ndarray]:
    """Return (x*, hinge) for a symmetric weight matrix with zero diagonal."""
    x = em.compute_linf_connectivity_optimizer(w)
    ranking, *_ = em.rank_relevant_but_not_obvious_chunks(w, x, pole_quantile)
    hinge = np.zeros(len(w))
    for idx, score, *_ in ranking:
        hinge[idx] = score
    return x, hinge


def theta_pick(similarity: np.ndarray, threshold: float, k: int, first: int | None = None, max_iters: int = 200) -> list[int]:
    """Indices of k diverse nodes: θ low-rank factor of the conflict graph
    (similarity ≥ threshold), then greedy farthest-point selection.
    `first` forces the starting node (e.g. the best-scored one)."""
    if len(similarity) <= k:
        return list(range(len(similarity)))
    conflict = em.build_conflict_mask(similarity, threshold)
    _, _, y, *_ = em.theta_subgradient_approximation(conflict, max_iters=max_iters)
    if first is None:
        selected, _ = em.theta_diversity_picker(y, k=k, seed="leverage")
    else:
        selected, _ = em.theta_diversity_picker(y, k=k, seed="index", seed_index=first)
    return [int(i) for i in selected]


# --- concept graph command ---------------------------------------------------


def load_adjacency(path: Path) -> tuple[list[str], np.ndarray]:
    df = pd.read_csv(path, index_col=0)
    names = [str(c) for c in df.columns]
    a = df.to_numpy(dtype=float)
    if a.shape[0] != a.shape[1]:
        raise ValueError(f"Adjacency matrix must be square, got {a.shape}")
    w = np.maximum(a, a.T)  # undirected
    np.fill_diagonal(w, 0.0)
    return names, w


def spectral_scores(w: np.ndarray, k: int = 3) -> np.ndarray:
    _, vecs = np.linalg.eigh(em.normalized_laplacian(w))
    return np.abs(vecs[:, : min(k, len(w))]).max(axis=1)


def diverse_subset(w: np.ndarray, names: list[str], threshold: float) -> list[tuple[str, list[str]]]:
    """Greedy maximal independent set on the conflict graph (w >= threshold):
    repeatedly keep the node with the fewest conflicts and drop its neighbours."""
    conflict = em.build_conflict_mask(w, threshold).astype(bool)
    remaining = set(range(len(names)))
    picked = []
    while remaining:
        best = min(remaining, key=lambda i: (sum(conflict[i, j] for j in remaining), names[i]))
        dropped = sorted(j for j in remaining if conflict[best, j])
        picked.append((names[best], [names[j] for j in dropped]))
        remaining -= {best, *dropped}
    return picked


def analyze(adjacency: Path, out_dir: Path, thresholds: list[float], theta_k: int = 10) -> tuple[Path, Path]:
    names, w = load_adjacency(adjacency)
    x, hinge = hinge_scores(w)
    scores = pd.DataFrame(
        {"node": names, "spectral": spectral_scores(w), "connectivity": x, "hinge": hinge}
    ).round(4)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "graph_scores.csv"
    scores.sort_values("hinge", ascending=False).to_csv(csv_path, index=False)

    lines = [f"# Concept graph analysis — {adjacency.name}", "", f"{len(names)} nodes.", ""]
    lines += ["## Top hinge nodes", "", "| Node | Spectral | Connectivity | Hinge |", "|---|---:|---:|---:|"]
    for r in scores.sort_values("hinge", ascending=False).head(15).itertuples():
        lines.append(f"| {r.node} | {r.spectral:.3f} | {r.connectivity:.3f} | {r.hinge:.3f} |")
    for t in thresholds:
        subset = diverse_subset(w, names, t)
        lines += ["", f"## Diverse subset at similarity ≥ {t} ({len(subset)} nodes)", "", "| Kept | Redundant neighbours dropped |", "|---|---|"]
        lines += [f"| {k} | {', '.join(d) or '—'} |" for k, d in subset]
        if theta_k:
            picked = theta_pick(w, t, theta_k)
            lines += ["", f"θ-diverse subset of {len(picked)} nodes: " + ", ".join(names[i] for i in picked)]
    md_path = out_dir / "graph_report.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path
