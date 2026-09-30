# -*- coding: utf-8 -*-
"""
to_execute_googlenews_merlin_intelligence_1_0.py

Google News scraper tool for Merlin Intelligence.
Dynamically accepts seeds_dedollarization.csv or any seed CSV file as input.
"""

import os
import sys
import io
import argparse
import email.utils
from datetime import datetime, timedelta
import pandas as pd
import gnews
import gnews.gnews

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def get_args():
    parser = argparse.ArgumentParser(description='Google News scraper tool with dynamic seed selection.')
    parser.add_argument('--seeds', '--input', type=str, default='seeds_dedollarization.csv',
                        help='Path or filename of the seeds CSV file (default: seeds_dedollarization.csv)')
    parser.add_argument('--days', type=int, default=20,
                        help='Number of days back to scrape from Google News (default: 20)')
    return parser.parse_args()

def locate_seeds_file(seeds_arg):
    # Try exact path
    if os.path.exists(seeds_arg):
        return seeds_arg
    
    # Try inside clean_seeds/
    clean_path = os.path.join('clean_seeds', seeds_arg)
    if os.path.exists(clean_path):
        return clean_path
        
    # Try looking in parent directories
    parent_path = os.path.join('..', seeds_arg)
    if os.path.exists(parent_path):
        return parent_path

    # Fallback to searching any seeds_*.csv in current dir or clean_seeds/
    for search_dir in ['.', 'clean_seeds']:
        if os.path.exists(search_dir):
            for f in os.listdir(search_dir):
                if f.startswith('seeds_') and f.endswith('.csv'):
                    return os.path.join(search_dir, f)
                    
    raise FileNotFoundError(f"Could not locate seeds file '{seeds_arg}'. Please ensure seeds_dedollarization.csv exists.")

def main():
    args = get_args()
    seed_file_path = locate_seeds_file(args.seeds)
    print(f"=================================================================")
    print(f"📰 Merlin Intelligence Google News Scraper")
    print(f"📌 Using Seeds File: {seed_file_path}")
    print(f"=================================================================")

    df_seeds = pd.read_csv(seed_file_path)
    
    # Identify keyword column (Keyword, Seeds, Theme, or 1st column)
    col_name = None
    for candidate in ['Keyword', 'Seeds', 'Theme', 'seed', 'keyword', 'theme']:
        if candidate in df_seeds.columns:
            col_name = candidate
            break
    if col_name is None:
        col_name = df_seeds.columns[0]
        
    search_themes = [str(x).strip() for x in df_seeds[col_name].dropna() if str(x).strip()]
    print(f"Loaded {len(search_themes)} search queries from column '{col_name}'.")

    current_date = datetime.now()
    days_back = args.days
    cutoff_date = current_date - timedelta(days=days_back)
    period_str = f"{days_back}d"
    all_articles_data = []

    print(f"Scraping window: last {days_back} days (since {cutoff_date.strftime('%Y-%m-%d')}).")

    # Bypass gnews URL redirection checks (gives 25x speedup per seed)
    gnews.gnews.process_url = lambda item, exclude_websites, proxies=None: item.get('link')
    gnews_client_en = gnews.GNews(language="en", max_results=20, period=period_str)

    for idx, search_term in enumerate(search_themes, 1):
        print(f"[{idx}/{len(search_themes)}] Searching Google News for: \"{search_term}\"...")
        try:
            news_results = gnews_client_en.get_news(search_term)
            if news_results:
                for result in news_results:
                    published_date_tuple = email.utils.parsedate_tz(result.get('published date', ''))
                    if published_date_tuple:
                        published_date = datetime.fromtimestamp(email.utils.mktime_tz(published_date_tuple))
                    else:
                        published_date = current_date

                    if published_date >= cutoff_date:
                        all_articles_data.append({
                            "Theme": search_term,
                            "Title": result.get('title', ''),
                            "Date": published_date.strftime("%Y-%m-%d"),
                            "Description": result.get('description', ''),
                            "URL": result.get('url', ''),
                            "Language": "English"
                        })
        except Exception as e:
            print(f"⚠️ Error searching for '{search_term}': {e}")

    if not all_articles_data:
        print("❌ No articles collected.")
        sys.exit(0)

    df_out = pd.DataFrame(all_articles_data)
    # Deduplicate by Title
    df_out.drop_duplicates(subset=['Title'], keep='first', inplace=True)

    timestamp_str = datetime.now().strftime("%y-%m-%d-%H")
    seed_base = os.path.splitext(os.path.basename(seed_file_path))[0].replace("seeds_", "")
    output_filename = f"news_{seed_base}_{timestamp_str}.csv"
    
    df_out.to_csv(output_filename, index=False, encoding='utf-8')
    print(f"=================================================================")
    print(f"✅ Collected {len(df_out)} unique news items across {len(search_themes)} seeds.")
    print(f"💾 Output saved to: '{output_filename}'")
    print(f"=================================================================")

if __name__ == "__main__":
    main()
