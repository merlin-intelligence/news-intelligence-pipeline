# -*- coding: utf-8 -*-
"""
harvest_brave_linkedin.py

Multi-Channel Signal Harvester for Merlin Intelligence & Orson News Architecture.
Queries the Brave Search API directly across:
  1. Brave News Search (independent journalistic news wire)
  2. Brave Web Search (think tanks, whitepapers, institutional reports)
  3. LinkedIn Pulse (long-form thought leadership articles)
  4. LinkedIn Posts (executive commentary, market desk notes, practitioner reactions)

Usage:
  python harvest_brave_linkedin.py --sample 5
  python harvest_brave_linkedin.py --seeds seeds_dedollarization.csv --sample 10 --output test_harvest.csv
  python harvest_brave_linkedin.py --extract-text
"""

import os
import sys
import io
import time
import argparse
from urllib.parse import urlparse
from typing import List, Dict, Any
import requests
import pandas as pd
from datetime import datetime

from datetime import datetime, timezone

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "BSAOo75P5OBCHpp0IibA2-_XYDVBNNh")
BRAVE_WEB_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_NEWS_URL = "https://api.search.brave.com/res/v1/news/search"


def get_headers() -> Dict[str, str]:
    return {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY
    }


def query_brave_news(seed: str, count: int = 3) -> List[Dict[str, Any]]:
    """Fetches real-time news articles from Brave News API."""
    params = {"q": seed, "count": count, "freshness": "pm"}
    results = []
    try:
        resp = requests.get(BRAVE_NEWS_URL, headers=get_headers(), params=params, timeout=12)
        if resp.status_code == 200:
            items = resp.json().get("results", [])
            for item in items:
                url = item.get("url", "")
                if url:
                    results.append({
                        "channel": "brave_news",
                        "seed": seed,
                        "title": item.get("title", "").strip(),
                        "url": url,
                        "domain": urlparse(url).netloc,
                        "description": item.get("description", "").strip(),
                        "published_age": item.get("age", ""),
                        "harvested_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    })
        elif resp.status_code == 429:
            print("  ⚠️ Brave API 429 Rate Limit (News). Backing off 2s...")
            time.sleep(2)
    except Exception as e:
        print(f"  ❌ Error fetching Brave News for '{seed}': {e}")
    return results


def query_brave_web(seed: str, count: int = 3) -> List[Dict[str, Any]]:
    """Fetches web research, think tank reports, and deep analyses via Brave Web Search."""
    params = {"q": seed, "count": count, "freshness": "pm"}
    results = []
    try:
        resp = requests.get(BRAVE_WEB_URL, headers=get_headers(), params=params, timeout=12)
        if resp.status_code == 200:
            items = resp.json().get("web", {}).get("results", [])
            for item in items:
                url = item.get("url", "")
                # Exclude social media or aggregator spam in pure web channel
                if url and "linkedin.com" not in url:
                    results.append({
                        "channel": "brave_web",
                        "seed": seed,
                        "title": item.get("title", "").strip(),
                        "url": url,
                        "domain": urlparse(url).netloc,
                        "description": item.get("description", "").strip(),
                        "published_age": item.get("page_age", ""),
                        "harvested_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    })
        elif resp.status_code == 429:
            print("  ⚠️ Brave API 429 Rate Limit (Web). Backing off 2s...")
            time.sleep(2)
    except Exception as e:
        print(f"  ❌ Error fetching Brave Web for '{seed}': {e}")
    return results


def query_brave_linkedin(seed: str, search_type: str = "pulse", count: int = 3) -> List[Dict[str, Any]]:
    """
    Fetches LinkedIn content using Brave Search site queries.
    search_type: 'pulse' for articles, 'posts' for executive commentary.
    """
    clean_seed = seed.replace('"', '').strip()
    if search_type == "pulse":
        query = f'site:linkedin.com/pulse/ {clean_seed}'
        channel_name = "linkedin_pulse"
    else:
        query = f'site:linkedin.com/posts/ {clean_seed}'
        channel_name = "linkedin_posts"

    params = {"q": query, "count": count}
    results = []
    try:
        resp = requests.get(BRAVE_WEB_URL, headers=get_headers(), params=params, timeout=12)
        if resp.status_code == 200:
            items = resp.json().get("web", {}).get("results", [])
            for item in items:
                url = item.get("url", "")
                if url and "linkedin.com" in url:
                    results.append({
                        "channel": channel_name,
                        "seed": seed,
                        "title": item.get("title", "").strip(),
                        "url": url,
                        "domain": "linkedin.com",
                        "description": item.get("description", "").strip(),
                        "published_age": item.get("page_age", ""),
                        "harvested_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    })
        elif resp.status_code == 429:
            print(f"  ⚠️ Brave API 429 Rate Limit ({channel_name}). Backing off 2s...")
            time.sleep(2)
    except Exception as e:
        print(f"  ❌ Error fetching LinkedIn ({search_type}) for '{seed}': {e}")
    return results


def run_harvest(seeds_file: str, sample_size: int = None, channels: List[str] = None, output_file: str = "harvest_brave_linkedin.csv"):
    if not os.path.exists(seeds_file):
        raise FileNotFoundError(f"Seeds file not found: {seeds_file}")

    df_seeds = pd.read_csv(seeds_file)
    col = "Keyword" if "Keyword" in df_seeds.columns else df_seeds.columns[0]
    seeds = [str(s).strip() for s in df_seeds[col].dropna() if str(s).strip()]

    if sample_size and sample_size > 0:
        seeds = seeds[:sample_size]

    if not channels:
        channels = ["brave_news", "brave_web", "linkedin_pulse", "linkedin_posts"]

    print("=================================================================")
    print("📡 Merlin Intelligence — Multi-Channel Brave + LinkedIn Harvester")
    print(f"📌 Input Seeds: {len(seeds)} queries (source: {seeds_file})")
    print(f"🌐 Active Channels: {', '.join(channels)}")
    print(f"💾 Output Destination: {output_file}")
    print("=================================================================\n")

    all_harvested = []
    start_time = time.time()

    for idx, seed in enumerate(seeds, 1):
        print(f"[{idx:02d}/{len(seeds):02d}] Harvesting seed: \"{seed}\"")
        seed_records = []

        if "brave_news" in channels:
            news_res = query_brave_news(seed, count=3)
            seed_records.extend(news_res)
            time.sleep(0.15)

        if "brave_web" in channels:
            web_res = query_brave_web(seed, count=3)
            seed_records.extend(web_res)
            time.sleep(0.15)

        if "linkedin_pulse" in channels:
            pulse_res = query_brave_linkedin(seed, search_type="pulse", count=3)
            seed_records.extend(pulse_res)
            time.sleep(0.15)

        if "linkedin_posts" in channels:
            posts_res = query_brave_linkedin(seed, search_type="posts", count=3)
            seed_records.extend(posts_res)
            time.sleep(0.15)

        print(f"   ↳ Found: {len(seed_records)} results across channels")
        all_harvested.extend(seed_records)

    df_results = pd.DataFrame(all_harvested)
    if df_results.empty:
        print("\n⚠️ No results harvested.")
        return df_results

    # Deduplicate by URL
    initial_count = len(df_results)
    df_results.drop_duplicates(subset=["url"], inplace=True)
    df_results.reset_index(drop=True, inplace=True)

    df_results.to_csv(output_file, index=False, encoding="utf-8")
    elapsed = time.time() - start_time

    print("\n=================================================================")
    print(f"🎉 Harvest Complete in {elapsed:.1f}s!")
    print(f"📊 Total Raw Results: {initial_count}")
    print(f"✨ Unique Canonical Links: {len(df_results)}")
    print("📈 Breakdown by Channel:")
    for ch, count in df_results["channel"].value_counts().items():
        print(f"   • {ch:16s}: {count:3d} articles/posts")
    print(f"💾 Saved to: {output_file}")
    print("=================================================================")

    return df_results


def parse_args():
    parser = argparse.ArgumentParser(description="Multi-Channel Brave & LinkedIn Harvester for Merlin Intelligence.")
    parser.add_argument("--seeds", type=str, default="seeds_dedollarization.csv", help="Path to seeds CSV.")
    parser.add_argument("--sample", type=int, default=5, help="Number of seeds to sample (default: 5, use 0 for all).")
    parser.add_argument("--channels", type=str, default="brave_news,brave_web,linkedin_pulse,linkedin_posts",
                        help="Comma-separated channels to scrape.")
    parser.add_argument("--output", type=str, default="harvest_brave_linkedin_sample.csv", help="Output CSV path.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    active_channels = [c.strip() for c in args.channels.split(",") if c.strip()]
    sample = None if args.sample == 0 else args.sample
    run_harvest(seeds_file=args.seeds, sample_size=sample, channels=active_channels, output_file=args.output)
