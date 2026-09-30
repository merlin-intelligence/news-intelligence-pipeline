import sys
import pandas as pd
import re

sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('news_dedollarization_614_ranked.csv')
print(f"Loaded {len(df)} articles for country tag extraction.")

# Define mapping of Country Tags to keyword/alias patterns
COUNTRY_PATTERNS = {
    "China": r"\b(china|chinese|beijing|cips|renminbi|rmb|yuan|pboc|panda bond|dim sum bond)\b",
    "United States": r"\b(us|usa|u\.s\.|united states|america|american|fed|federal reserve|washington|treasury|treasuries)\b",
    "Iran": r"\b(iran|iranian|tehran|hormuz)\b",
    "Saudi Arabia": r"\b(saudi|saudi arabia|riyadh|petrodollar)\b",
    "Libya": r"\b(libya|libyan|tripoli)\b",
    "Japan": r"\b(japan|japanese|tokyo|yen|boj)\b",
    "Indonesia": r"\b(indonesia|indonesian|jakarta|rupiah)\b",
    "Pakistan": r"\b(pakistan|pakistani|islamabad)\b",
    "Russia": r"\b(russia|russian|moscow|ruble)\b",
    "United Arab Emirates": r"\b(uae|united arab emirates|dubai|abu dhabi|dirham)\b",
    "Eurozone / EU": r"\b(eu|europe|european|eurozone|ecb|germany|france|brussels|euro)\b",
    "India": r"\b(india|indian|delhi|mumbai|rupee|rbi)\b",
    "Brazil": r"\b(brazil|brazilian|brasilia|real)\b",
    "South Africa": r"\b(south africa|south african|pretoria|rand)\b",
    "Angola": r"\b(angola|angolan|luanda)\b",
    "United Kingdom": r"\b(uk|u\.k\.|britain|british|london|pound|sterling|boe)\b",
    "Hong Kong": r"\b(hong kong|hk|hkma|hkex)\b",
}

def extract_country_tags(row):
    text = f"{row.get('Title', '')} {row.get('Description', '')} {row.get('Theme', '')} {str(row.get('Extracted_Article_Text', ''))[:4000]}"
    tags = []
    for country, pattern in COUNTRY_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            tags.append(country)
    if not tags:
        tags = ["Global / Multilateral"]
    return ", ".join(tags)

df['country_tags'] = df.apply(extract_country_tags, axis=1)

print("\nSample country tags for Top 15 articles:")
for idx, row in df.head(15).iterrows():
    print(f"Rank #{idx+1:2d} | Title: {row['Title'][:50]} | Countries: {row['country_tags']}")

df.to_csv('news_dedollarization_614_ranked_with_countries.csv', index=False)
