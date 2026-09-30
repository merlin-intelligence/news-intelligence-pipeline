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

df['full_text_combined'] = (df['Title'].fillna('') + ' ' + df['Description'].fillna('') + ' ' + df['Theme'].fillna('') + ' ' + df['Extracted_Article_Text'].fillna('')).astype(str)

# 12 Indicator Bucket Concept Descriptors (Equi-Weighted Anchors)
BUCKET_DESCRIPTORS = {
    "1.1": "IMF COFER foreign exchange reserve composition dollar share decline renminbi euro diversification reserve assets non-traditional currencies",
    "1.2": "international debt sovereign bond denomination panda bonds euro-denominated debt issuance cross-border loans non-USD debt",
    "1.3": "global trade finance payments network SWIFT payment share BIS triennial survey OTC foreign exchange turnover correspondent banking",
    "1.4": "treasury convenience yield swap spread compression U.S. sovereign debt premium interest rate swap spreads G10 sovereign yields",
    "1.5": "trade policy shocks tariff threshold dynamics protectionism trade war invoicing switch safe-haven risk-off appreciation",
    "2.1": "central bank physical gold accumulation official gold reserves unfreezable hedge conflict risk gold surpassing treasuries",
    "2.2": "alternative clearing rails CIPS project mBridge cross-border interbank payment system multi-CBDC wCBDC non-SWIFT clearing",
    "2.3": "commodity invoicing petroyuan petrodollar agreement saudi arabia crude oil LNG trade settlement strait of hormuz transit fees",
    "2.4": "non-USD stablecoins digital sovereign assets digital yuan digital euro tokenized bank deposits cross-border P2P payments",
    "2.5": "covered interest parity CIP deviations treasury auction thinning indirect bidder allocations dollar liquidity borrowing premium",
    "2.6": "bilateral currency swap networks green RMB bonds central bank swap facility liquidity backstop ESG safe asset",
    "2.7": "institutional credibility central bank governance federal reserve independence policy interference monetary authority trust"
}

# Vectorize all articles and the 12 bucket descriptors
vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=5000)
all_texts = df['full_text_combined'].tolist() + list(BUCKET_DESCRIPTORS.values())
matrix = vectorizer.fit_transform(all_texts)

doc_matrix = matrix[:len(df)]
bucket_matrix = matrix[len(df):]

# Calculate similarity of each doc to each of the 12 buckets: shape (N_docs, 12)
sims_12 = cosine_similarity(doc_matrix, bucket_matrix)

# Normalize each bucket's score column to 0..100 to ensure 100% EQUI-WEIGHTING across all 12 buckets
sims_12_norm = np.zeros_like(sims_12)
for k in range(12):
    col = sims_12[:, k]
    max_c = col.max() if col.max() > 0 else 1.0
    sims_12_norm[:, k] = (col / max_c) * 100.0

# Equi-Weighted Concept Immersion Score S_concept_equi: maximum normalized match across all 12 buckets
df['S_concept_equi'] = np.round(np.max(sims_12_norm, axis=1), 2)

# Calculate Hinge score & Lovasz Novelty as before
gen_matrix = TfidfVectorizer(stop_words='english', max_features=3000).fit_transform(df['full_text_combined'])
sim_matrix = cosine_similarity(gen_matrix)

G = nx.Graph()
for i in range(len(df)): G.add_node(i)
for i in range(len(df)):
    for j in range(i+1, len(df)):
        if sim_matrix[i, j] > 0.22: G.add_edge(i, j, weight=sim_matrix[i, j])

betweenness_dict = nx.betweenness_centrality(G)
raw_hinge = np.array([betweenness_dict[i] for i in range(len(df))])
H_hinge = (raw_hinge * 100 / max(raw_hinge.max(), 1e-6))

S_surface = df['proximity_score'].values
sorted_by_surface = np.argsort(-S_surface)
N_lovasz = np.zeros(len(df))
for rank_pos, idx in enumerate(sorted_by_surface):
    if rank_pos == 0: N_lovasz[idx] = 100.0
    else:
        higher_indices = sorted_by_surface[:rank_pos]
        N_lovasz[idx] = max(0.0, (1.0 - np.max(sim_matrix[idx, higher_indices])) * 100.0)

df['S_surface'] = np.round(S_surface, 2)
df['H_hinge'] = np.round(H_hinge, 2)
df['N_lovasz'] = np.round(N_lovasz, 2)

# Equi-Weighted Composite Score
raw_composite_equi = (0.20 * S_surface) + (0.35 * df['S_concept_equi'].values) + (0.25 * N_lovasz) + (0.20 * H_hinge)
df['composite_eigenmind_score'] = np.round(raw_composite_equi * 100 / raw_composite_equi.max(), 2)

# Sort full dataset strictly by Composite Equi-Weighted Score DESCENDING
df.sort_values(by='composite_eigenmind_score', ascending=False, inplace=True)
df.reset_index(drop=True, inplace=True)
df['composite_eigenmind_rank'] = df.index + 1

print("==================================================================")
print("AVERAGE S_concept_equi SCORES ACROSS ALL 12 BUCKETS (EQUI-WEIGHTED)")
print("==================================================================")
grouped = df.groupby('assigned_bucket_id')[['S_surface', 'S_concept_equi', 'N_lovasz', 'H_hinge', 'composite_eigenmind_score']].mean()
print(grouped.round(2))

# Check "The Permission Wars"
permission_row = df[df['Title'].str.contains("Permission Wars", case=False, na=False)].iloc[0]
print(f"\n>>> 'The Permission Wars' Equi-Weighted Composite Rank: #{permission_row['composite_eigenmind_rank']} (Score: {permission_row['composite_eigenmind_score']:.2f}, S_concept_equi: {permission_row['S_concept_equi']:.2f}) <<<")

df.to_csv('news_dedollarization_614_eigenmind_equiweighted_ranked.csv', index=False)
