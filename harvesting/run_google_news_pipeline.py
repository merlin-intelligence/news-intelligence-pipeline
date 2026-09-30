# -*- coding: utf-8 -*-
"""
run_google_news_pipeline.py

Master Orchestrator Tool for Google News Collection & Text Extraction.
Takes seeds_dedollarization.csv as input and runs Step 1 and Step 2 end-to-end.
"""

import os
import sys
import io
import argparse
import subprocess

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    parser = argparse.ArgumentParser(description="Master Google News & Playwright Extraction Pipeline")
    parser.add_argument("--seeds", "--input", type=str, default="seeds_dedollarization.csv",
                        help="Seed CSV file to run (default: seeds_dedollarization.csv)")
    args = parser.parse_args()

    print("=================================================================")
    print(f"🚀 Starting Merlin Intelligence Google News Pipeline...")
    print(f"📌 Input Seed File: {args.seeds}")
    print("=================================================================")

    # Step 1: Scrape Google News
    cmd_step1 = [sys.executable, os.path.join(SCRIPT_DIR, "to_execute_googlenews_merlin_intelligence_1_0.py"), "--seeds", args.seeds]
    print(f"\n[Step 1/2] Running Google News Scraper: {' '.join(cmd_step1)}")
    res1 = subprocess.run(cmd_step1, cwd=SCRIPT_DIR)
    if res1.returncode != 0:
        print("❌ Step 1 failed. Aborting pipeline.")
        sys.exit(res1.returncode)

    # Step 2: Resolve URLs & Extract Full Text
    cmd_step2 = [sys.executable, os.path.join(SCRIPT_DIR, "to_execute_resolveggmerlin_intelligence.py")]
    print(f"\n[Step 2/2] Running URL Resolution & Full-Text Extraction: {' '.join(cmd_step2)}")
    res2 = subprocess.run(cmd_step2, cwd=SCRIPT_DIR)
    if res2.returncode != 0:
        print("❌ Step 2 failed. Aborting pipeline.")
        sys.exit(res2.returncode)

    print("\n=================================================================")
    print("🎉 Google News Pipeline Executed Successfully!")
    print("=================================================================")

if __name__ == "__main__":
    main()
