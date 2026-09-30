# -*- coding: utf-8 -*-
"""
tools/rank_top30_last20days.py

Ranks the newly scraped September 2026 (last 20 days) news articles using the
Equi-Weighted Composite Eigenmind Singularity Index:
- S_concept_equi (Equi-Weighted Multi-Anchor Concept Immersion across 12 buckets)
- N_lovasz (Lovász submodular greedy novelty)
- H_hinge (Graph betweenness topological centrality)
- S_surface (Surface TF-IDF relevance)

Extracts and saves the Top 30 successfully scraped news articles with full metadata,
country geotags, and clean executive summaries.
"""

import os
import sys
import io
import re
import glob
import html
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(SCRIPT_DIR)

BUCKET_TAXONOMY = [
    {"id": "1.1", "name": "Foreign Exchange Reserve Composition (IMF COFER)", "desc": "Tracking USD share trajectory, RMB/Euro reserve expansion, and non-traditional currency asset allocations."},
    {"id": "1.2", "name": "International Debt & Sovereign Bond Denomination", "desc": "Compression of USD debt share, Panda bond debuts (RMB), and Euro sovereign issuances."},
    {"id": "1.3", "name": "Global Trade Finance & Payments Network (SWIFT & BIS)", "desc": "SWIFT messaging share shifts, OTC FX turnover contraction, and cross-border bank loan currency shares."},
    {"id": "1.4", "name": "Treasury Convenience Yield & Swap Spread Compression", "desc": "Negative convenience yield, deeply negative swap spreads, and sovereign safe-haven premium erosion."},
    {"id": "1.5", "name": "Trade Policy Shocks & Tariff Threshold Dynamics", "desc": "Tariff threshold switching dynamics and risk-off asset appreciation outside the U.S. dollar."},
    {"id": "2.1", "name": "Central Bank Physical Gold Accumulation", "desc": "Record official gold purchases, un-freezable conflict hedging, and gold surpassing Treasuries in reserves."},
    {"id": "2.2", "name": "Alternative Clearing Rails (CIPS & Project mBridge)", "desc": "Cross-Border Interbank Payment System volume surges, non-SWIFT clearing, and multi-CBDC platforms."},
    {"id": "2.3", "name": "Commodity Invoicing & 'Petroyuan' Realignment", "desc": "1974 Saudi petrodollar expiry, non-dollar crude/LNG pricing, and Hormuz transit fee settlement."},
    {"id": "2.4", "name": "Non-USD Stablecoins & Digital Sovereign Assets", "desc": "Non-USD stablecoins growth, digital yuan/euro P2P corridors, and tokenized commercial deposit disintermediation."},
    {"id": "2.5", "name": "Deviations from Covered Interest Parity (CIP) & Auction Thinning", "desc": "CIP breakdown, rising USD borrowing friction, and diminishing indirect bidder allocations in Treasury auctions."},
    {"id": "2.6", "name": "Bilateral Swap Networks & Green RMB Bonds", "desc": "Bilateral central bank currency swap facilities and green RMB bond benchmarks providing non-USD safe assets."},
    {"id": "2.7", "name": "Institutional Credibility & Central Bank Governance Cues", "desc": "Federal Reserve independence cues, policy interference risks, and central bank governance trust."}
]

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

COUNTRY_PATTERNS = {
    "China": [r"\bchina\b", r"\bchinese\b", r"\bbeijing\b", r"\byuan\b", r"\brenminbi\b", r"\bcips\b", r"\bpboc\b"],
    "United States": [r"\bunited states\b", r"\bu\.s\.\b", r"\busa\b", r"\bamerica\b", r"\bwashington\b", r"\bfed\b", r"\bfederal reserve\b", r"\btreasury\b"],
    "Russia": [r"\brussia\b", r"\brussian\b", r"\bmoscow\b", r"\bruble\b", r"\bkremlin\b"],
    "Saudi Arabia": [r"\bsaudi\b", r"\briyadh\b", r"\baramco\b"],
    "Iran": [r"\biran\b", r"\biranian\b", r"\btehran\b"],
    "India": [r"\bindia\b", r"\bindian\b", r"\bdelhi\b", r"\brupee\b", r"\brbi\b"],
    "Brazil": [r"\bbrazil\b", r"\bbrazilian\b", r"\bbrasilia\b", r"\breal\b"],
    "Eurozone/EU": [r"\beuropean union\b", r"\beu\b", r"\beurozone\b", r"\beuro\b", r"\becb\b", r"\bbrussels\b"],
    "Japan": [r"\bjapan\b", r"\bjapanese\b", r"\btokyo\b", r"\byen\b", r"\bboj\b"],
    "UAE": [r"\buae\b", r"\bemirates\b", r"\bdubai\b", r"\babu dhabi\b", r"\bdirham\b"],
    "Indonesia": [r"\bindonesia\b", r"\bindonesian\b", r"\bjakarta\b", r"\brupiah\b"],
    "South Africa": [r"\bsouth africa\b", r"\bsouth african\b", r"\bjohannesburg\b", r"\brand\b"],
    "Libya": [r"\blibya\b", r"\blibyan\b", r"\btripoli\b"],
    "Pakistan": [r"\bpakistan\b", r"\bpakistani\b", r"\bislamabad\b"],
    "Angola": [r"\bangola\b", r"\bangolan\b", r"\bluanda\b"],
    "Hong Kong": [r"\bhong kong\b", r"\bhkma\b", r"\bhkd\b"],
    "UK": [r"\bunited kingdom\b", r"\bbritain\b", r"\bbritish\b", r"\blondon\b", r"\bpound\b", r"\bboe\b"],
    "Mongolia": [r"\bmongolia\b", r"\bmongolian\b", r"\bulaanbaatar\b"]
}

FAILURE_PATTERNS = [
    r"^Failed:",
    r"Enable JavaScript and cookies to continue",
    r"unusual activity from your computer network",
    r"We’re checking your connection to prevent automated abuse",
    r"Security Controls Triggered",
    r"Checking your browser",
    r"Access Denied",
    r"403 Forbidden",
    r"Attention Required! \| Cloudflare",
    r"502 Bad Gateway",
    r"503 Service Temporarily Unavailable",
    r"404 Not Found",
    r"451: Unavailable due to legal reasons",
    r"errors\.edgesuite\.net",
    r"^Just a quick check",
    r"Verify you are human",
    r"Please turn JavaScript on and reload the page",
    r"Robot Check",
    r"Please enable cookies",
    r"ShieldSquare Captcha",
    r"cf-browser-verification",
    r"Pardon Our Interruption",
    r"Access to this page is denied"
]

def is_valid_scrape(text):
    if not text or str(text).lower() == 'nan':
        return False
    t = str(text).strip()
    if len(t) < 250:
        return False
    for pat in FAILURE_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            return False
    return True

def extract_countries(text):
    text_lower = str(text).lower()
    found = []
    for country, patterns in COUNTRY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                found.append(country)
                break
    return ", ".join(found) if found else "Global / Multilateral"

def get_bucket_name(b_id):
    for b in BUCKET_TAXONOMY:
        if b["id"] == str(b_id).strip(): return b["name"]
    return str(b_id)

def clean_scraped_summary(raw_text, desc):
    """Produces clean executive summary without boilerplate."""
    text = str(raw_text) if raw_text and str(raw_text).lower() != 'nan' else str(desc)
    # Remove noise
    noise = [
        r"we value your privacy.*?(?=(\.|\n|$))",
        r"we and our partners store and/or access information.*?(?=(\.|\n|$))",
        r"cookies and process personal data.*?(?=(\.|\n|$))",
        r"subscribe to read the full article.*?(?=(\.|\n|$))",
        r"all rights reserved.*?(?=(\.|\n|$))",
        r"terms of service.*?(?=(\.|\n|$))",
        r"privacy policy.*?(?=(\.|\n|$))",
        r"more \+ coverage web3 games nfts crypto.*?(?=(\.|\n|$))",
        r"by\s+[a-z\s]+on\s+[a-z0-9,\s]+(?=(\.|\n|$))"
    ]
    for n in noise:
        text = re.sub(n, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    
    # Extract first 2-3 clean sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    clean_sents = [s.strip() for s in sentences if len(s.strip()) > 30 and not any(w in s.lower() for w in ['cookie', 'javascript', 'subscribe', 'sign in', 'log in', 'advertisement', 'copyright'])]
    
    if clean_sents:
        summary = " ".join(clean_sents[:3])
        if len(summary) > 360:
            summary = summary[:357] + "..."
        return summary
    return text[:280] + "..." if len(text) > 280 else text

def rank_and_save_top30():
    # Discover input fulltext file
    candidates = glob.glob("news_dedollarization_26-09-17-17_fulltext.csv") + glob.glob("news_dedollarization_26-09-17-17_fulltext_checkpoint.csv")
    if not candidates:
        print("❌ Error: No September 2026 fulltext CSV found.")
        return False

    input_csv = candidates[0]
    print(f"📖 Loading scraped corpus from: {input_csv}")
    df_raw = pd.read_csv(input_csv)
    print(f"Raw rows in dataset: {len(df_raw)}")

    # Filter for valid scrapes only
    valid_mask = df_raw['Extracted_Article_Text'].apply(is_valid_scrape)
    df = df_raw[valid_mask].copy().reset_index(drop=True)
    print(f"✅ Successfully scraped articles: {len(df)} (excluded {len(df_raw) - len(df)} failed/blocked)")

    if len(df) == 0:
        print("❌ No valid scraped articles found.")
        return False

    # Standardize resolved URL
    def get_url(r):
        b = str(r.get('Resolved_URL_via_BraveSearch', '')).strip()
        u = str(r.get('URL', '')).strip()
        return b if b and b.startswith('http') and 'news.google.com' not in b else u

    df['resolved_url'] = df.apply(get_url, axis=1)
    df.drop_duplicates(subset=['Title'], keep='first', inplace=True)
    df.drop_duplicates(subset=['resolved_url'], keep='first', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Combined text for TF-IDF
    df['full_text_combined'] = (df['Title'].fillna('') + ' ' + df.get('Description', '').fillna('') + ' ' + df.get('Theme', '').fillna('') + ' ' + df['Extracted_Article_Text'].fillna('')).astype(str)
    df['country_tags'] = df['full_text_combined'].apply(extract_countries)

    # 1. Equi-Weighted Multi-Anchor Concept Immersion S_concept_equi
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=5000)
    all_texts = df['full_text_combined'].tolist() + list(BUCKET_DESCRIPTORS.values())
    matrix = vectorizer.fit_transform(all_texts)
    doc_matrix = matrix[:len(df)]
    bucket_matrix = matrix[len(df):]

    sims_12 = cosine_similarity(doc_matrix, bucket_matrix)
    sims_12_norm = np.zeros_like(sims_12)
    for k in range(12):
        col = sims_12[:, k]
        max_c = col.max() if col.max() > 0 else 1.0
        sims_12_norm[:, k] = (col / max_c) * 100.0

    df['S_concept_equi'] = np.round(np.max(sims_12_norm, axis=1), 2)
    bucket_ids = list(BUCKET_DESCRIPTORS.keys())
    best_bucket_idx = np.argmax(sims_12, axis=1)
    df['assigned_bucket_id'] = [bucket_ids[i] for i in best_bucket_idx]
    df['assigned_bucket_name'] = df['assigned_bucket_id'].apply(get_bucket_name)

    # 2. Graph Centrality H_hinge
    gen_matrix = TfidfVectorizer(stop_words='english', max_features=2500).fit_transform(df['full_text_combined'])
    sim_matrix = cosine_similarity(gen_matrix)
    G = nx.Graph()
    for i in range(len(df)): G.add_node(i)
    for i in range(len(df)):
        for j in range(i+1, len(df)):
            if sim_matrix[i, j] > 0.20: G.add_edge(i, j, weight=sim_matrix[i, j])

    betweenness_dict = nx.betweenness_centrality(G)
    raw_hinge = np.array([betweenness_dict[i] for i in range(len(df))])
    H_hinge = (raw_hinge * 100 / max(raw_hinge.max(), 1e-6))

    # 3. Surface Relevance & Lovász Novelty
    surface_vec = TfidfVectorizer(stop_words='english').fit_transform(["de-dollarization monetary sovereignty central bank reserves alternative clearing gold multipolar currency"] + df['full_text_combined'].tolist())
    S_surface = (cosine_similarity(surface_vec[1:], surface_vec[:1]).flatten()) * 100.0
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

    # 4. Composite Singularity Index
    raw_composite = (0.20 * S_surface) + (0.35 * df['S_concept_equi'].values) + (0.25 * N_lovasz) + (0.20 * H_hinge)
    df['composite_eigenmind_score'] = np.round(raw_composite * 100 / raw_composite.max(), 2)
    df.sort_values(by='composite_eigenmind_score', ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['composite_eigenmind_rank'] = df.index + 1

    # Guarantee multi-bucket diversity for Top 30
    selected_indices = set()
    for b_id in bucket_ids:
        b_matches = df[df['assigned_bucket_id'] == b_id]
        if len(b_matches) > 0:
            selected_indices.add(b_matches.index[0])

    for idx in df.index:
        if len(selected_indices) >= 30: break
        if idx not in selected_indices: selected_indices.add(idx)

    df_top30 = df.loc[list(selected_indices)].copy()
    df_top30.sort_values(by='composite_eigenmind_score', ascending=False, inplace=True)
    df_top30.reset_index(drop=True, inplace=True)
    df_top30['top30_rank'] = df_top30.index + 1

    # Generate clean executive summaries
    summaries = []
    for _, r in df_top30.iterrows():
        s = clean_scraped_summary(r['Extracted_Article_Text'], r.get('Description', ''))
        summaries.append(s)
    df_top30['executive_summary'] = summaries

    # Save Top 30 CSV
    output_top30_csv = "news_dedollarization_top30_last20days.csv"
    cols_to_save = [
        'top30_rank', 'composite_eigenmind_rank', 'composite_eigenmind_score',
        'assigned_bucket_id', 'assigned_bucket_name', 'Date', 'Title',
        'country_tags', 'resolved_url', 'executive_summary',
        'S_concept_equi', 'N_lovasz', 'H_hinge', 'S_surface'
    ]
    df_top30[cols_to_save].to_csv(output_top30_csv, index=False, encoding='utf-8')

    # Also save full-text top 30
    df_top30.to_csv("news_dedollarization_top30_last20days_fulltext.csv", index=False, encoding='utf-8')

    print(f"\n=================================================================")
    print(f"🎯 Successfully extracted and ranked Top 30 News (Last 20 Days)")
    print(f"💾 Output saved to: {output_top30_csv}")
    print(f"=================================================================")
    for i, r in df_top30.head(10).iterrows():
        print(f"#{r['top30_rank']:02d} [Score {r['composite_eigenmind_score']:.1f}] [{r['assigned_bucket_id']}] {r['Date']} | {r['Title'][:70]}")

    return True

if __name__ == "__main__":
    rank_and_save_top30()
