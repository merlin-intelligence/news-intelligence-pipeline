import sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('news_dedollarization_614_ranked.csv')

# Step 1: Pick the best article for each of the 12 buckets
bucket_list = [
    "1.1", "1.2", "1.3", "1.4", "1.5",
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"
]

selected_indices = set()
top20_rows = []

for b_id in bucket_list:
    b_df = df[df['assigned_bucket_id'] == b_id]
    if len(b_df) > 0:
        top_idx = b_df.index[0] # Highest score in this bucket
        selected_indices.add(top_idx)

# Step 2: Fill remaining slots up to 20 with top overall articles not yet selected
for idx in df.index:
    if len(selected_indices) >= 20:
        break
    if idx not in selected_indices:
        selected_indices.add(idx)

# Top 20 dataframe
df_top20 = df.loc[list(selected_indices)].copy()
df_top20.sort_values(by='proximity_score', ascending=False, inplace=True)
df_top20.reset_index(drop=True, inplace=True)
df_top20['top20_rank'] = df_top20.index + 1

print("==================================================================")
print("TOP 20 NEWS ARTICLES (GUARANTEED BUCKET COVERAGE FOR ALL 12 BUCKETS)")
print("==================================================================")
for idx, row in df_top20.iterrows():
    print(f"Top20 #{row['top20_rank']:2d} | Overall Rank: {row['overall_rank']:3d} | Score: {row['proximity_score']:6.2f} | Bucket: {row['assigned_bucket_id']} | Title: {row['Title'][:65]}")

print("\nVerify Bucket Coverage in Top 20:")
print(df_top20['assigned_bucket_id'].value_counts())

# Step 3: Next 50 articles (Ranks 21 to 70 overall)
df_next50 = df.iloc[20:70].copy()
df_next50.reset_index(drop=True, inplace=True)

print("\n==================================================================")
print("NEXT 50 NEWS ARTICLES (RANKS 21 TO 70)")
print("==================================================================")
for idx, row in df_next50.iterrows():
    print(f"Rank {row['overall_rank']:2d} | Score: {row['proximity_score']:6.2f} | Bucket: {row['assigned_bucket_id']} | Title: {row['Title'][:65]}")

df_top20.to_csv('top20_dedollarization_news.csv', index=False)
df_next50.to_csv('next50_dedollarization_news.csv', index=False)
