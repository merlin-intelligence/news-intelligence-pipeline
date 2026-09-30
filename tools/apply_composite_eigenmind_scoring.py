import sys
import pandas as pd
import numpy as np
import html
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

sys.stdout.reconfigure(encoding='utf-8')

# Load the 614 clean dataset
df = pd.read_csv('news_dedollarization_614_ranked_resolved_urls.csv', dtype={'assigned_bucket_id': str})
df['assigned_bucket_id'] = df['assigned_bucket_id'].astype(str).str.strip()

print(f"Loaded {len(df)} clean news articles.")

# Prepare combined text for vectorization
df['full_text_combined'] = (df['Title'].fillna('') + ' ' + df['Description'].fillna('') + ' ' + df['Theme'].fillna('') + ' ' + df['Extracted_Article_Text'].fillna('')).astype(str)

# -------------------------------------------------------------------
# Component 1: Surface Relevance Score S_surface (0 to 100)
# -------------------------------------------------------------------
S_surface = df['proximity_score'].values

# -------------------------------------------------------------------
# Component 2: Dense Conceptual Paradigm Immersion S_concept (0 to 100)
# -------------------------------------------------------------------
abstract_paradigm_query = (
    "monetary sovereignty permissioned financial infrastructure payment messaging rails "
    "SWIFT switches central bank clearing alternative payment network weaponization of dollar"
)

vectorizer_concept = TfidfVectorizer(stop_words='english', ngram_range=(1, 3), max_features=5000)
all_concept_texts = df['full_text_combined'].tolist() + [abstract_paradigm_query]
concept_matrix = vectorizer_concept.fit_transform(all_concept_texts)

doc_vecs = concept_matrix[:-1]
query_vec = concept_matrix[-1:]

raw_concept_sims = cosine_similarity(doc_vecs, query_vec).flatten()
S_concept = (raw_concept_sims * 100 / raw_concept_sims.max())

# -------------------------------------------------------------------
# Component 3: Hinge Gatekeeper Centrality H_hinge (0 to 100)
# -------------------------------------------------------------------
gen_matrix = tfidf_matrix = TfidfVectorizer(stop_words='english', max_features=3000).fit_transform(df['full_text_combined'])
sim_matrix = cosine_similarity(gen_matrix)

G = nx.Graph()
for i in range(len(df)):
    G.add_node(i)

for i in range(len(df)):
    for j in range(i+1, len(df)):
        if sim_matrix[i, j] > 0.22:
            G.add_edge(i, j, weight=sim_matrix[i, j])

betweenness_dict = nx.betweenness_centrality(G)
raw_hinge = np.array([betweenness_dict[i] for i in range(len(df))])
H_hinge = (raw_hinge * 100 / max(raw_hinge.max(), 1e-6))

# -------------------------------------------------------------------
# Component 4: Lovász Theta Orthogonal Novelty N_Lovasz (0 to 100)
# -------------------------------------------------------------------
# For each document, novelty is higher if it has low maximum similarity to documents ranked higher in surface score
sorted_by_surface = np.argsort(-S_surface)
N_lovasz = np.zeros(len(df))

for rank_pos, idx in enumerate(sorted_by_surface):
    if rank_pos == 0:
        N_lovasz[idx] = 100.0
    else:
        higher_indices = sorted_by_surface[:rank_pos]
        max_redundancy = np.max(sim_matrix[idx, higher_indices])
        N_lovasz[idx] = max(0.0, (1.0 - max_redundancy) * 100.0)

# Normalize components cleanly
df['S_surface'] = np.round(S_surface, 2)
df['S_concept'] = np.round(S_concept, 2)
df['H_hinge'] = np.round(H_hinge, 2)
df['N_lovasz'] = np.round(N_lovasz, 2)

# -------------------------------------------------------------------
# COMPOSITE EIGENMIND SINGULARITY INDEX FORMULA
# S_composite = 0.20*S_surface + 0.35*S_concept + 0.25*N_lovasz + 0.20*H_hinge
# -------------------------------------------------------------------
raw_composite = (0.20 * S_surface) + (0.35 * S_concept) + (0.25 * N_lovasz) + (0.20 * H_hinge)
df['composite_eigenmind_score'] = np.round(raw_composite * 100 / raw_composite.max(), 2)

# Sort full dataset strictly by Composite Eigenmind Score DESCENDING
df.sort_values(by='composite_eigenmind_score', ascending=False, inplace=True)
df.reset_index(drop=True, inplace=True)
df['composite_eigenmind_rank'] = df.index + 1

print("--- FULL CORPUS RANKED BY COMPOSITE EIGENMIND SINGULARITY INDEX ---")
print(f"Total articles: {len(df)}")
print("\nTop 15 Articles:")
for idx, row in df.head(15).iterrows():
    print(f"Composite Rank #{row['composite_eigenmind_rank']:2d} | Score: {row['composite_eigenmind_score']:6.2f} (Surf:{row['S_surface']:5.1f}, Conc:{row['S_concept']:5.1f}, Nov:{row['N_lovasz']:5.1f}) | Bucket {row['assigned_bucket_id']:4s} | Title: {row['Title'][:50]}")

# Locate "The Permission Wars"
permission_row = df[df['Title'].str.contains("Permission Wars", case=False, na=False)].iloc[0]
print(f"\n>>> 'The Permission Wars' NEW Composite Eigenmind Rank: #{permission_row['composite_eigenmind_rank']} (Composite Score: {permission_row['composite_eigenmind_score']:.2f}) <<<")

# Save full composite ranked dataset
df.to_csv('news_dedollarization_614_eigenmind_composite_ranked.csv', index=False)
