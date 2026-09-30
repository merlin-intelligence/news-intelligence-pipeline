import sys
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.stdout.reconfigure(encoding='utf-8')

# Load the 614 successfully scraped articles
df = pd.read_csv('news_dedollarization_26-07-23-17_successful_scrapes.csv')
print(f"Loaded {len(df)} articles.")

# Define the 12 Indicator Buckets from Systemic_Realignment_and_DeDollarization_Indicators.md
BUCKETS = {
    "1.1": {
        "name": "1.1 Foreign Exchange Reserve Composition (IMF COFER)",
        "short_name": "FX Reserve Composition",
        "keywords": ["cofer", "foreign exchange reserve", "reserve currency", "dollar share", "reserve diversification", "central bank reserve", "imf cofer", "currency composition", "rmb share", "euro reserve", "non-traditional currency"]
    },
    "1.2": {
        "name": "1.2 International Debt & Sovereign Bond Denomination",
        "short_name": "International Debt Denomination",
        "keywords": ["panda bond", "sovereign bond", "international debt", "bond issuance", "dim sum bond", "euro-denominated", "debt denomination", "cross-border loan", "non-usd debt", "bond market"]
    },
    "1.3": {
        "name": "1.3 Global Trade Finance & Payments Network (SWIFT & BIS)",
        "short_name": "Trade Finance & SWIFT/BIS Networks",
        "keywords": ["swift", "bis", "triennial survey", "trade finance", "payment share", "cross-border payment", "fx turnover", "messaging system", "correspondent bank", "interbank payment"]
    },
    "1.4": {
        "name": "1.4 Treasury Convenience Yield & Swap Spread Compression",
        "short_name": "Treasury Yield & Swap Spreads",
        "keywords": ["convenience yield", "swap spread", "treasury yield", "treasury premium", "g10 sovereign", "us sovereign debt", "nber", "interest rate swap", "convenience premium"]
    },
    "1.5": {
        "name": "1.5 Trade Policy Shocks & Tariff Threshold Dynamics",
        "short_name": "Trade Policy & Tariff Dynamics",
        "keywords": ["tariff", "trade war", "protectionism", "trade policy", "tariff threshold", "invoicing switch", "liberation day", "trade tariff", "customs duty", "sanctions shock"]
    },
    "2.1": {
        "name": "2.1 Central Bank Physical Gold Accumulation",
        "short_name": "Central Bank Physical Gold",
        "keywords": ["gold", "bullion", "gold reserve", "repatriation", "gold buying", "unfreezable asset", "physical gold", "world gold council", "vault", "central bank gold"]
    },
    "2.2": {
        "name": "2.2 Alternative Clearing Rails (CIPS & Project mBridge)",
        "short_name": "Alternative Rails (CIPS & mBridge)",
        "keywords": ["cips", "mbridge", "project mbridge", "clearing rail", "cross-border interbank", "wcbdc", "multi-cbdc", "pboc", "hkma", "alternative payment"]
    },
    "2.3": {
        "name": "2.3 Commodity Invoicing & 'Petroyuan' Realignment",
        "short_name": "Petroyuan & Commodity Invoicing",
        "keywords": ["petroyuan", "petrodollar", "oil settlement", "saudi Arabia", "opec", "crude oil", "lng settlement", "strait of hormuz", "commodity invoicing", "energy trade", "oil in yuan"]
    },
    "2.4": {
        "name": "2.4 Non-USD Stablecoins & Digital Sovereign Assets",
        "short_name": "Non-USD Stablecoins & Digital Assets",
        "keywords": ["stablecoin", "cbdc", "digital yuan", "digital euro", "e-hkd", "tokenized deposit", "non-usd stablecoin", "digital asset", "crypto", "tokenization"]
    },
    "2.5": {
        "name": "2.5 Deviations from Covered Interest Parity (CIP) & Auction Thinning",
        "short_name": "CIP Deviations & Treasury Auctions",
        "keywords": ["covered interest parity", "cip", "bid-to-cover", "treasury auction", "indirect bidder", "dollar liquidity", "auction thinning", "borrowing premium", "treasury demand"]
    },
    "2.6": {
        "name": "2.6 Bilateral Swap Networks & Green RMB Bonds",
        "short_name": "Bilateral Swaps & Green RMB Bonds",
        "keywords": ["swap facility", "currency swap", "bilateral swap", "green bond", "rmb green bond", "esg asset", "central bank swap", "liquidity backstop", "swap line"]
    },
    "2.7": {
        "name": "2.7 Institutional Credibility & Central Bank Governance Cues",
        "short_name": "Institutional Credibility & Governance",
        "keywords": ["fed independence", "federal reserve", "central bank governance", "credibility", "ecb report", "monetary authority", "institutional trust", "policy interference", "governance"]
    }
}

# General De-Dollarization core keywords for overall proximity scoring
DEDOLLARIZATION_CORE = [
    "dedollarization", "de-dollarization", "dollar dominance", "dollar status", "reserve currency",
    "us dollar", "multipolar currency", "currency diversification", "hegemony", "weaponization",
    "financial sanctions", "dollar reliance", "monetary realignment", "petrodollar", "cips",
    "swift alternative", "gold reserves", "bilateral trade settlement", "local currency settlement"
]

# Prepare combined text for each article (Title + Description + Theme + snippet of Extracted_Article_Text)
def get_full_text(row):
    title = str(row.get('Title', ''))
    desc = str(row.get('Description', ''))
    theme = str(row.get('Theme', ''))
    body = str(row.get('Extracted_Article_Text', ''))[:3000] # First 3000 chars
    return f"{title} {desc} {theme} {body}"

df['combined_text'] = df.apply(get_full_text, axis=1)

# TF-IDF Vectorization to measure semantic similarity to De-Dollarization Core and to each Bucket
corpus = df['combined_text'].tolist()

# Define reference texts for TF-IDF matching
dedol_ref_text = " ".join(DEDOLLARIZATION_CORE * 5)
bucket_ref_texts = {b_id: " ".join(b_info['keywords'] * 5) for b_id, b_info in BUCKETS.items()}

all_texts = corpus + [dedol_ref_text] + list(bucket_ref_texts.values())

vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
tfidf_matrix = vectorizer.fit_transform(all_texts)

article_vectors = tfidf_matrix[:len(df)]
dedol_vector = tfidf_matrix[len(df):len(df)+1]
bucket_vectors = tfidf_matrix[len(df)+1:]

# Calculate core proximity score (0 to 100 scale)
core_sims = cosine_similarity(article_vectors, dedol_vector).flatten()

# Add keyword count bonus for direct occurrences of key terms
def get_keyword_score(text):
    text_lower = text.lower()
    score = 0
    for kw in DEDOLLARIZATION_CORE:
        if kw in text_lower:
            score += text_lower.count(kw)
    return score

kw_scores = df['combined_text'].apply(get_keyword_score)
max_kw = kw_scores.max() if kw_scores.max() > 0 else 1
norm_kw = kw_scores / max_kw

# Composite proximity score: 70% TF-IDF Cosine Similarity + 30% Keyword Frequency
composite_score = (core_sims * 70) + (norm_kw * 30)
df['proximity_score'] = np.round(composite_score * 100 / composite_score.max(), 2)

# Calculate bucket similarity scores for each article
bucket_sims = cosine_similarity(article_vectors, bucket_vectors) # shape (N_articles, 12)
bucket_ids = list(BUCKETS.keys())

# For each article, determine the best matching bucket and score
best_bucket_idx = np.argmax(bucket_sims, axis=1)
df['assigned_bucket_id'] = [bucket_ids[i] for i in best_bucket_idx]
df['assigned_bucket_name'] = [BUCKETS[bucket_ids[i]]['name'] for i in best_bucket_idx]
df['assigned_bucket_short'] = [BUCKETS[bucket_ids[i]]['short_name'] for i in best_bucket_idx]

# Check distribution of articles across buckets
print("\n--- Initial Bucket Distribution ---")
print(df['assigned_bucket_id'].value_counts())

# Rank all articles by proximity_score descending
df.sort_values(by='proximity_score', ascending=False, inplace=True)
df.reset_index(drop=True, inplace=True)
df['overall_rank'] = df.index + 1

print("\n--- Top 10 Overall Articles ---")
for idx, row in df.head(10).iterrows():
    print(f"Rank {row['overall_rank']:2d} | Score: {row['proximity_score']:6.2f} | Bucket: {row['assigned_bucket_id']} | Title: {row['Title'][:70]}")

# Save full rankings CSV
df.to_csv('news_dedollarization_614_ranked.csv', index=False)
print("\nSaved full rankings to news_dedollarization_614_ranked.csv")
