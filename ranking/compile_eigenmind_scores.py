import os
import csv
import numpy as np
from scipy.linalg import eigh
import heapq

# =================================================================
# 1. Official Core Mathematical Algorithms from the PDF & GitHub
# =================================================================

def normalized_laplacian(W: np.ndarray) -> np.ndarray:
    degrees = np.sum(W, axis=1)
    d_inv_sqrt = np.zeros_like(degrees)
    nz = degrees > 0
    d_inv_sqrt[nz] = 1.0 / np.sqrt(degrees[nz])
    D_inv_sqrt = np.diag(d_inv_sqrt)
    return np.identity(W.shape[0]) - D_inv_sqrt @ W @ D_inv_sqrt

def _build_weighted_lengths(W: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Convert similarity weights W_ij in [0,1] into positive edge lengths via -log.
    This is the official formula: \ell_{ij} = -\log W_{ij}
    """
    L = np.full_like(W, np.inf, dtype=float)
    mask = W > 0
    L[mask] = -np.log(np.clip(W[mask], eps, 1.0))
    np.fill_diagonal(L, 0.0)
    return L

def _dijkstra_all_sources(lengths: np.ndarray) -> np.ndarray:
    n = lengths.shape[0]
    dist = np.full((n, n), np.inf, dtype=float)
    for src in range(n):
        d = dist[src]
        d[src] = 0.0
        pq = [(0.0, src)]
        visited = np.zeros(n, dtype=bool)
        while pq:
            du, u = heapq.heappop(pq)
            if visited[u]:
                continue
            visited[u] = True
            for v in range(n):
                w = lengths[u, v]
                if w == np.inf or v == u:
                    continue
                nd = du + w
                if nd < d[v]:
                    d[v] = nd
                    heapq.heappush(pq, (nd, v))
    return dist

def compute_linf_connectivity_optimizer(W: np.ndarray) -> np.ndarray:
    """Official ℓ∞-connectivity optimizer x* in chunk space from the GitHub repository."""
    n = W.shape[0]
    degrees = np.sum(W, axis=1)
    if np.all(degrees == 0):
        return np.zeros(n, dtype=float)

    lengths = _build_weighted_lengths(W)
    dist = _dijkstra_all_sources(lengths)

    finite = np.isfinite(dist)
    if not np.all(finite):
        max_finite = np.max(dist[finite]) if np.any(finite) else 1.0
        dist = np.where(finite, dist, 10.0 * max_finite)

    transmission = np.sum(dist, axis=1)
    v_star = int(np.argmax(transmission))

    x_raw = dist[v_star, :].copy()

    deg_sum = float(np.sum(degrees))
    if deg_sum > 0:
        weighted_mean = float(np.sum(degrees * x_raw)) / deg_sum
        x_centered = x_raw - weighted_mean
    else:
        x_centered = x_raw - np.mean(x_raw)

    denom = float(np.max(np.abs(x_centered)))
    if denom < 1e-12:
        return np.zeros(n, dtype=float)

    return x_centered / denom

def calculate_hinge_scores(W: np.ndarray, x_star: np.ndarray, pole_quantile: float = 0.90) -> np.ndarray:
    """Official Hinge (Bridge) score formula from the GitHub repository."""
    x = x_star
    q_hi = float(np.quantile(x, pole_quantile))
    q_lo = float(np.quantile(x, 1.0 - pole_quantile))
    Pp = np.where(x >= q_hi)[0]
    Pm = np.where(x <= q_lo)[0]
    if len(Pp) == 0 or len(Pm) == 0:
        q_hi = float(np.quantile(x, 0.80))
        q_lo = float(np.quantile(x, 0.20))
        Pp = np.where(x >= q_hi)[0]
        Pm = np.where(x <= q_lo)[0]
    S_plus = np.sum(W[:, Pp], axis=1) if len(Pp) > 0 else np.zeros(W.shape[0])
    S_minus = np.sum(W[:, Pm], axis=1) if len(Pm) > 0 else np.zeros(W.shape[0])
    bridge = np.minimum(S_plus, S_minus)
    hinge = bridge * (1.0 - np.abs(x))
    return hinge

# =================================================================
# 2. Main Execution and Summary Compiler
# =================================================================

def main():
    csv_path = "adjacency_matrix_blocks.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Please run optimize_adjacency_matrix.py first.")
        return

    # Read the block-organized adjacency matrix
    node_names = []
    matrix_rows = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        node_names = header[1:]
        
        for row in reader:
            matrix_rows.append([float(x) for x in row[1:]])

    A = np.array(matrix_rows)
    num_nodes = len(node_names)
    print(f"Loaded optimized adjacency matrix with {num_nodes} active nodes.")

    # Symmetrize to represent undirected similarity/connection strength
    W = np.maximum(A, A.T)

    # --- Method 1: Spectral Singularity Scores ---
    L_sym = normalized_laplacian(W)
    eigenvalues, eigenvectors = eigh(L_sym)
    k_components = 3
    spectral_scores = np.max(np.abs(eigenvectors[:, :k_components]), axis=1)

    # --- Method 2: l-infinity Connectivity Centrality (x*) ---
    x_star = compute_linf_connectivity_optimizer(W)

    # --- Method 3: Hinge (Bridge) Scores ---
    hinge_scores = calculate_hinge_scores(W, x_star)

    # --- Compile Scores ---
    compiled_data = []
    for i in range(num_nodes):
        compiled_data.append({
            "name": node_names[i],
            "spectral": float(spectral_scores[i]),
            "connectivity": float(x_star[i]),
            "hinge": float(hinge_scores[i])
        })

    # Sort alphabetically by node name for the main lookup table
    compiled_data.sort(key=lambda x: x["name"])

    # Write to Markdown File
    report_path = "eigenmind_singularity_scores.md"
    print(f"Writing compiled scores to {report_path}...")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Eigenmind Singularity & Centrality Scores Summary\n\n")
        f.write(f"This report compiles the structural singularity and centrality scores for all **{num_nodes} active entities** in the Geopolitical Ontology, computed using the three mathematical methods from the **Eigenmind Graph Library**:\n\n")
        
        f.write("1.  **Spectral Singularity Score (Method 1):** The peak absolute coordinate of the node across the first 3 eigenvectors of the Symmetric Normalized Laplacian ($L_{sym}$). It represents the node's structural weight as a representative anchor of its connected component.\n")
        f.write("2.  **$\\ell_\\infty$-Connectivity Centrality ($x^*$) (Method 2):** The normalized transmission distance from the most remote node. Values close to $+1.0$ or $-1.0$ represent network extremes (poles), while values close to $0.0$ represent the physical center.\n")
        f.write("3.  **Hinge (Bridge) Score ($H_i$) (Method 3):** The capacity of the node to act as a bridge connecting the positive and negative poles of the network axis while remaining centrally located.\n\n")

        f.write("## Entity Singularity Scores Table\n\n")
        f.write("| Node Index | Entity Name | Spectral Score (Method 1) | $\\ell_\\infty$-Connectivity ($x^*$) (Method 2) | Hinge (Bridge) Score (Method 3) |\n")
        f.write("| :---: | :--- | :---: | :---: | :---: |\n")
        
        for idx, row in enumerate(compiled_data):
            f.write(f"| {idx} | `{row['name']}` | `{row['spectral']:.4f}` | `{row['connectivity']:.4f}` | `{row['hinge']:.4f}` |\n")

        f.write("\n## Structural Interpretations\n\n")
        f.write("*   **High Spectral + High Connectivity (Poles):** Nodes like `De_Dollarization` or `Geopolitical_Conflict` have high spectral weights and lie at the extremes ($x^* \\approx \\pm 1.0$), making them the defining poles of their respective subnets.\n")
        f.write("*   **Low Centrality ($x^* \\approx 0.0$) + High Hinge:** Nodes like `Strait_of_Hormuz` or `C6_Coalition` lie in the physical center of their networks and have high Hinge scores, making them critical gatekeepers and transit paths.\n")

    print("Scores compiled successfully.")

    # Format the table for stdout display (first 15 rows for preview/verification)
    print("\nPreview of Compiled Scores (First 15 rows):")
    print(f"{'Entity Name':<35} | {'Spectral':<10} | {'Connectivity':<12} | {'Hinge':<10}")
    print("-" * 77)
    for row in compiled_data[:15]:
        print(f"{row['name']:<35} | {row['spectral']:<10.4f} | {row['connectivity']:<12.4f} | {row['hinge']:<10.4f}")

if __name__ == "__main__":
    main()
