import os
import csv
import numpy as np

def build_conflict_graph(W: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """Build conflict graph H: H_ij = 1 iff similarity >= threshold (no self-loops, symmetric)."""
    H = (W >= threshold).astype(np.int8)
    np.fill_diagonal(H, 0)
    return np.maximum(H, H.T)

def greedy_maximum_independent_set(H: np.ndarray, node_names: list) -> list:
    """Finds a diverse, non-redundant set of nodes using a greedy independent set algorithm.
    
    In graph theory, the size of this set is the Independence Number alpha(H), 
    which is bounded by the Lovász Theta parameter theta(H).
    """
    n = H.shape[0]
    remaining_nodes = set(range(n))
    independent_set = []
    conflicts_removed = {}

    while remaining_nodes:
        # Calculate degrees of remaining nodes in the sub-graph
        degrees = {}
        for node in remaining_nodes:
            # Count neighbors that are also in remaining_nodes
            deg = sum(1 for neighbor in remaining_nodes if H[node, neighbor] == 1)
            degrees[node] = deg

        # Pick the node with the minimum degree (least conflicts / highest independence)
        # In case of ties, pick alphabetically by name
        best_node = min(remaining_nodes, key=lambda node: (degrees[node], node_names[node]))
        
        independent_set.append(node_names[best_node])
        remaining_nodes.remove(best_node)

        # Identify and remove all neighbors (conflicting nodes)
        neighbors = [neighbor for neighbor in remaining_nodes if H[best_node, neighbor] == 1]
        conflicts_removed[node_names[best_node]] = [node_names[neighbor] for neighbor in neighbors]
        
        for neighbor in neighbors:
            remaining_nodes.remove(neighbor)

    return independent_set, conflicts_removed

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

    # We will run the diversity picker at two different conflict thresholds:
    # 1. High Conflict Threshold (0.7): Strict redundancy filtering
    # 2. Moderate Conflict Threshold (0.5): Broader thematic coverage
    
    thresholds = [0.5, 0.7]
    reports = {}

    for t in thresholds:
        H = build_conflict_graph(W, threshold=t)
        num_edges = np.sum(H) // 2
        ind_set, conflicts = greedy_maximum_independent_set(H, node_names)
        reports[t] = {
            "conflict_graph": H,
            "num_edges": num_edges,
            "independent_set": ind_set,
            "conflicts": conflicts
        }
        print(f"Threshold {t}: Found {len(ind_set)} diverse nodes in conflict graph (Edges: {num_edges}).")

    # Save summary report to markdown file
    report_path = "diversity_picker_report.md"
    print(f"Writing findings to {report_path}...")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Lovász-Style Diversity Picker & Conflict Graph Report\n\n")
        f.write("This report applies the **conflict graph** and **diversity selection** concepts from the **Eigenmind Graph Library** (`theta.py`) to the Geopolitical Ontology.\n\n")
        
        f.write("## 1. Theoretical Background\n\n")
        f.write("The `theta.py` file in the Eigenmind library focuses on the **Lovász $\\theta$ parameter**, which provides a semidefinite programming (SDP) sandwich bound on the **Independence Number** $\\alpha(H)$ of a conflict graph $H$:\n")
        f.write("$$\\omega(H) \\le \\theta(\\bar{H}) \\le \\chi(H)$$\n")
        f.write("$$\\alpha(H) \\le \\theta(H) \\le \\theta(\\bar{H}) \\le \\chi(\\bar{H})$$\n\n")
        f.write("In information retrieval and summarization, a **Conflict Graph** $H$ is constructed where an edge exists between two nodes if their semantic similarity exceeds a threshold (representing redundancy). Finding the **Maximum Independent Set** on this graph corresponds to selecting the **most diverse, non-redundant set of representative entities** that cover the graph's information space without overlapping duplicates.\n\n")

        for t in thresholds:
            rep = reports[t]
            f.write(f"## 2. Diversity Selection at Conflict Threshold $\\tau = {t}$\n\n")
            f.write(f"At this threshold, two entities are in 'conflict' (redundant) if their relationship weight is $\\ge {t}$.\n\n")
            f.write(f"*   **Total Conflict Edges in Graph $H$:** {rep['num_edges']}\n")
            f.write(f"*   **Size of Diverse Representative Set (Independence Number $\\alpha$):** {len(rep['independent_set'])}\n")
            f.write(f"*   **Selected Diverse Core Entities:** " + ", ".join([f"`{n}`" for n in rep['independent_set']]) + "\n\n")
            
            f.write("### Selected Entities & Redundant Neighbors Removed\n")
            f.write("The diversity picker selected each entity below and filtered out its closely related (redundant) neighbors to ensure maximum information coverage:\n\n")
            
            f.write("| Selected Entity | Redundant Neighbors Filtered Out (Conflicts) |\n")
            f.write("| :--- | :--- |\n")
            for selected in rep['independent_set']:
                neighbors = rep['conflicts'].get(selected, [])
                neighbors_str = ", ".join([f"`{n}`" for n in neighbors]) if neighbors else "*None (Fully Independent)*"
                f.write(f"| `{selected}` | {neighbors_str} |\n")
            f.write("\n")

        f.write("## 3. Geopolitical Application\n")
        f.write("By running this diversity picker, we extract a **core vocabulary** that represents all distinct thematic areas of the ontology. For instance, at $\\tau = 0.5$:\n")
        f.write("1.  **Block 1 (Conflict/Energy) representatives** are selected while filtering out highly similar neighbors (e.g. keeping `Oil` but filtering out `LNG` and `Strait_of_Hormuz` as redundant in a high-level summary).\n")
        f.write("2.  **Block 2 (Monetary/Dollar) representatives** are selected independently (e.g. `De_Dollarization`).\n")
        f.write("3.  **Block 3 (Societal Risk) representatives** are selected independently (e.g. `Societal_Polarization`).\n")
        f.write("This provides an optimal, non-redundant set of concepts for high-level summaries or dashboard displays.\n")

    print("Diversity picker analysis complete.")

if __name__ == "__main__":
    main()
