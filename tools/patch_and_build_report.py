# -*- coding: utf-8 -*-
"""
tools/patch_and_build_report.py

Updates build_simplified_report.py with all user-requested refinements:
1. Pipeline Architecture (Section 01):
   - Mention vectorization and similarity against semantic descriptors without mentioning "TF-IDF n-gram representation" or "cosine similarity".
2. Detailed Macro Observations & Selected News (Section 02):
   - Observations 01, 02, 03, 04 provide dedicated, styled "Corroborating Intelligence / Selected News" blocks with direct source links, publication dates, and key mechanisms.
3. Investment Universe ETF Profiles ("Colors"):
   - Detailed color cards for all 9 ETFs (SPY, GLD, UUP, TLT, IEF, LSHUX, DBC, EEM, MCHI) with roles, capital weights, and macro rationale.
4. Proprietary Naming:
   - Replaced "the automated SLSQP minimum-variance optimizer" with "the proprietary Merlin Asset Allocation model".
5. Capital Allocation Focus:
   - Features capital allocation (+37.24% UUP, 67.45% total safe-haven balance sheet), explicitly noting that granular percentage risk contributions (%RC) and factor sensitivities are available for finer institutional analysis.
6. Zero Mentions of Calmar:
   - Replaced all occurrences of Calmar with risk-adjusted compounding efficiency.
7. Complete removal of scores, ranks, badges, and all "LLM Curated" mentions across code and output.
8. Synchronizes dedollarization_intelligence_report.html and dedollarization_intelligence_report_v2.html in workspace and artifact directories.
"""

import os
import sys
import io
import shutil

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
TARGET_PY = os.path.join(BASE_DIR, "build_simplified_report.py")

print(f"Target python script: {TARGET_PY}")

with open(TARGET_PY, "r", encoding="utf-8") as f:
    orig_code = f.read()

# Clean up any leftover "LLM Curated" in pre_code
orig_code = orig_code.replace("LLM Curated", "Curated")
orig_code = orig_code.replace("LLM-curated", "curated")
orig_code = orig_code.replace("LLM_CURATED_CATALOG", "EXECUTIVE_CATALOG")
orig_code = orig_code.replace("llm curated", "curated")

cut_marker = "    # Build HTML"
if cut_marker not in orig_code:
    print("❌ Cut marker not found!")
    sys.exit(1)

pre_code = orig_code.split(cut_marker)[0]

# Replacement HTML building code
html_builder_code = """    # Build HTML
    html_content = f\"\"\"<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Merlin Intelligence — De-Dollarization Macro Intelligence Report: Onto-Semantic Signals, Empirical Indicators & Quantitative Portfolio Synthesis.">
<title>Merlin Intelligence — De-Dollarization Macro Intelligence Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Lora:ital,wght@0,400;0,500;1,400&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">

<style>
:root {{
  --bg:         #F0ECE6;
  --ink:        #14120F;
  --gold:       #A27844;
  --rule:       #C3B9AC;
  --light:      #8A7F74;
  --pale:       #F7F4F0;
  --dark:       #1E1A16;
  --accent:     #8C2A1C;
  --slate:      #3E4B4A;
  --slate-pale: #E7ECEA;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{
  background: var(--bg); color: var(--ink);
  font-family: 'Lora', Georgia, serif; font-size: 17px; line-height: 1.72;
  -webkit-font-smoothing: antialiased;
}}
.wrap       {{ max-width: 820px; margin: 0 auto; padding: 0 2rem; }}
.wrap--wide {{ max-width: 1100px; margin: 0 auto; padding: 0 2rem; }}

nav {{ padding: 1.2rem 0 1.0rem; border-bottom: 0.5px solid var(--rule); }}
nav .wrap--wide {{ display: flex; align-items: center; justify-content: space-between; }}
.nav-brand {{
  font-family: 'Space Mono', monospace; font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.08em; color: var(--ink); text-decoration: none; text-transform: uppercase;
  display: flex; align-items: center; gap: 0.7rem;
}}
.nav-logo {{
  height: 38px; width: 38px; object-fit: cover; display: block;
  border: 0.5px solid var(--rule); border-radius: 50%; padding: 2px; background: var(--pale);
}}
.nav-sub {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--light); letter-spacing: 0.04em; }}

.hero {{ padding: 4.5rem 0 3.5rem; position: relative; overflow: hidden; }}
.hero::before {{
  content: ''; position: absolute; inset: 0;
  background-image: repeating-linear-gradient(-62deg, transparent, transparent 80px, rgba(162,120,68,0.055) 80px, rgba(162,120,68,0.055) 80.5px);
  pointer-events: none;
}}
.hero-eyebrow {{ font-family: 'Space Mono', monospace; font-size: 0.68rem; color: var(--gold); letter-spacing: 0.10em; text-transform: uppercase; margin-bottom: 1.2rem; display: block; }}
.hero-headline {{ font-family: 'Playfair Display', serif; font-size: clamp(2.2rem, 5vw, 3.4rem); font-weight: 400; line-height: 1.14; color: var(--ink); margin-bottom: 1.2rem; max-width: 860px; }}
.hero-headline em {{ font-style: italic; color: var(--gold); }}
.hero-sub {{ font-size: 1.05rem; color: var(--light); max-width: 720px; line-height: 1.65; margin-bottom: 2.2rem; }}

.hero-stats {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;
  border-top: 0.5px solid var(--rule); padding-top: 2.0rem; margin-top: 1.5rem;
}}
.stat-item {{ border-left: 2px solid var(--gold); padding-left: 1.0rem; }}
.stat-val {{ font-family: 'Space Mono', monospace; font-size: 1.6rem; font-weight: 700; color: var(--ink); display: block; line-height: 1.2; }}
.stat-lbl {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--light); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.3rem; display: block; }}

@media (max-width: 768px) {{
  .hero-stats {{ grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
}}

main {{ padding: 3.5rem 0; }}
section {{ margin-bottom: 4.5rem; }}
.sec-label {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--gold); letter-spacing: 0.10em; text-transform: uppercase; display: block; margin-bottom: 0.6rem; }}
.section-title {{ font-family: 'Playfair Display', serif; font-size: 1.85rem; font-weight: 400; color: var(--ink); margin-bottom: 0.8rem; line-height: 1.25; }}
.section-title em {{ font-style: italic; color: var(--gold); }}
.section-intro {{ font-size: 0.96rem; color: var(--light); max-width: 780px; margin-bottom: 2.0rem; line-height: 1.65; }}

/* Pipeline Architecture Grid */
.pipeline-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.2rem; margin: 2.0rem 0; }}
.pipeline-card {{ border: 0.5px solid var(--rule); background: var(--pale); padding: 1.4rem; display: flex; flex-direction: column; justify-content: space-between; position: relative; }}
.pipeline-step {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; font-weight: 700; color: var(--gold); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; display: block; }}
.pipeline-title {{ font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 600; color: var(--ink); margin-bottom: 0.6rem; line-height: 1.3; }}
.pipeline-desc {{ font-size: 0.82rem; color: var(--light); line-height: 1.5; }}
@media (max-width: 900px) {{ .pipeline-grid {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 600px) {{ .pipeline-grid {{ grid-template-columns: 1fr; }} }}

/* Macro Regime Cards */
.macro-section {{ display: flex; flex-direction: column; gap: 2.2rem; margin: 2.0rem 0; }}
.macro-card {{ border: 0.5px solid var(--rule); background: var(--pale); padding: 2.2rem; }}
.macro-eyebrow {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--gold); text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.5rem; }}
.macro-title {{ font-family: 'Playfair Display', serif; font-size: 1.45rem; font-weight: 600; color: var(--ink); margin-bottom: 1.1rem; line-height: 1.3; }}
.macro-title em {{ font-style: italic; color: var(--gold); }}
.macro-body {{ font-size: 0.98rem; color: var(--ink); line-height: 1.74; }}
.macro-body p {{ margin-bottom: 1.1rem; }}
.macro-body p:last-child {{ margin-bottom: 0; }}

.callout-box {{ border-left: 3px solid var(--gold); background: var(--bg); padding: 1.1rem 1.4rem; margin: 1.3rem 0; font-size: 0.92rem; line-height: 1.65; }}
.callout-box strong {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; text-transform: uppercase; color: var(--gold); display: block; margin-bottom: 0.3rem; letter-spacing: 0.05em; }}

.quant-box {{ border-left: 3px solid var(--slate); background: var(--slate-pale); padding: 1.3rem 1.5rem; margin: 1.4rem 0; }}
.quant-box .quant-label {{ font-family: 'Space Mono', monospace; font-size: 0.68rem; font-weight: 700; color: var(--slate); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; }}
.quant-box p {{ margin-bottom: 0.8rem; font-size: 0.94rem; line-height: 1.65; }}
.quant-box p:last-child {{ margin-bottom: 0; }}

/* Corroborating Intelligence / Selected News Box */
.selected-news-box {{
  margin-top: 1.4rem;
  background: var(--bg);
  border: 0.5px solid var(--rule);
  border-left: 3px solid var(--gold);
  padding: 1.1rem 1.4rem;
}}
.selected-news-label {{
  font-family: 'Space Mono', monospace;
  font-size: 0.66rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--gold);
  margin-bottom: 0.75rem;
  display: block;
}}
.selected-news-list {{
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 0;
  margin: 0;
}}
.selected-news-item {{
  font-size: 0.88rem;
  line-height: 1.45;
}}
.selected-news-link {{
  font-family: 'Playfair Display', serif;
  font-size: 0.98rem;
  font-weight: 600;
  color: var(--ink);
  text-decoration: none;
  border-bottom: 1px dotted var(--gold);
  transition: color 0.15s ease;
}}
.selected-news-link:hover {{
  color: var(--gold);
}}
.selected-news-meta {{
  font-family: 'Space Mono', monospace;
  font-size: 0.64rem;
  color: var(--light);
  display: block;
  margin-top: 0.2rem;
}}

/* ETF Universe Color Grid */
.etf-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.1rem;
  margin: 1.5rem 0 1.6rem;
}}
@media (max-width: 900px) {{ .etf-grid {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 600px) {{ .etf-grid {{ grid-template-columns: 1fr; }} }}

.etf-card {{
  background: var(--bg);
  border: 0.5px solid var(--rule);
  padding: 1.15rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}
.etf-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}}
.etf-ticker {{
  font-family: 'Space Mono', monospace;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ink);
  background: rgba(20, 18, 15, 0.08);
  padding: 0.18rem 0.5rem;
  border-radius: 2px;
}}
.etf-alloc {{
  font-family: 'Space Mono', monospace;
  font-size: 0.70rem;
  font-weight: 700;
  color: var(--gold);
}}
.etf-name {{
  font-family: 'Playfair Display', serif;
  font-size: 1.02rem;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 0.45rem;
  line-height: 1.3;
}}
.etf-desc {{
  font-size: 0.82rem;
  line-height: 1.52;
  color: var(--ink);
  margin: 0;
}}

/* Taxonomy Grid */
.taxonomy-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; margin: 1.8rem 0; }}
.taxonomy-card {{ border: 0.5px solid var(--rule); background: var(--pale); padding: 1.2rem; display: flex; flex-direction: column; justify-content: space-between; }}
.tax-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; }}
.tax-badge {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; font-weight: 700; background: var(--ink); color: var(--bg); padding: 0.15rem 0.5rem; }}
.tax-count {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--gold); }}
.tax-title {{ font-family: 'Playfair Display', serif; font-size: 0.98rem; font-weight: 600; color: var(--ink); margin-bottom: 0.4rem; line-height: 1.3; }}
.tax-desc {{ font-size: 0.80rem; color: var(--light); line-height: 1.45; margin: 0; }}

@media (max-width: 900px) {{ .taxonomy-grid {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 600px) {{ .taxonomy-grid {{ grid-template-columns: 1fr; }} }}

/* News Cards */
.news-cards {{ display: flex; flex-direction: column; gap: 1.8rem; margin-top: 1.8rem; }}
.news-card {{ border: 0.5px solid var(--rule); background: var(--pale); padding: 1.8rem; position: relative; transition: transform 0.2s ease, box-shadow 0.2s ease; }}
.news-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(20,18,15,0.04); }}
.card-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 0.8rem; margin-bottom: 0.9rem; flex-wrap: wrap; }}
.card-badges {{ display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }}
.badge-date {{ font-family: 'Space Mono', monospace; font-size: 0.70rem; font-weight: 700; background: var(--ink); color: var(--bg); padding: 0.25rem 0.60rem; }}
.badge-bucket {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; background: rgba(162,120,68,0.12); color: var(--ink); padding: 0.2rem 0.55rem; border: 0.5px solid rgba(162,120,68,0.3); font-weight: 700; }}
.card-title {{ font-family: 'Playfair Display', serif; font-size: 1.30rem; font-weight: 600; line-height: 1.3; color: var(--ink); margin-bottom: 0.7rem; }}
.card-title a {{ color: var(--ink); text-decoration: none; border-bottom: 1px dashed var(--gold); }}
.card-title a:hover {{ color: var(--gold); }}
.card-meta {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--light); margin-bottom: 0.8rem; display: block; }}

.country-tags-wrap {{ display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 1.0rem; align-items: center; }}
.country-label {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--gold); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; margin-right: 0.2rem; }}
.country-tag {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--ink); background: var(--bg); border: 0.5px solid var(--rule); padding: 0.12rem 0.45rem; border-radius: 2px; }}

.card-summary {{ font-size: 0.94rem; color: var(--ink); line-height: 1.65; margin-bottom: 1.1rem; }}
.card-mechanism {{ border-left: 2.5px solid var(--gold); padding: 0.75rem 1rem; background: var(--bg); font-size: 0.88rem; color: var(--ink); line-height: 1.6; }}
.card-mechanism strong {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; text-transform: uppercase; color: var(--gold); display: block; margin-bottom: 0.25rem; letter-spacing: 0.05em; }}

/* Table */
.table-wrap {{ overflow-x: auto; margin-top: 1.8rem; border: 0.5px solid var(--rule); }}
table {{ width: 100%; border-collapse: collapse; background: var(--pale); font-size: 0.88rem; text-align: left; }}
th {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--gold); padding: 0.9rem 0.85rem; border-bottom: 1px solid var(--rule); background: var(--bg); }}
td {{ padding: 0.85rem; border-bottom: 0.5px solid var(--rule); vertical-align: middle; }}
tr:last-child td {{ border-bottom: none; }}
tr:hover {{ background: rgba(162,120,68,0.04); }}
.td-date {{ font-family: 'Space Mono', monospace; font-weight: 700; color: var(--ink); width: 110px; }}
.td-bucket {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--light); width: 160px; }}
.td-countries {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--ink); width: 180px; }}
.td-title {{ font-family: 'Playfair Display', serif; font-size: 0.96rem; color: var(--ink); }}
.td-title a {{ color: var(--ink); text-decoration: none; }}
.td-title a:hover {{ color: var(--gold); text-decoration: underline; }}

footer {{ padding: 2.5rem 0; border-top: 0.5px solid var(--rule); margin-top: 3.5rem; font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--light); }}
footer .wrap--wide {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; }}
</style>
</head>
<body>

<nav>
  <div class="wrap--wide">
    <a href="#" class="nav-brand">
      <img src="MI-icon.png" alt="Merlin Intelligence" class="nav-logo" onerror="this.style.display='none'">
      <span>Merlin Intelligence — De-Dollarization Intelligence</span>
    </a>
    <span class="nav-sub">Geoeconomic Signal Intelligence & Macro Synthesis • September 2026</span>
  </div>
</nav>

<header class="hero">
  <div class="wrap--wide">
    <span class="hero-eyebrow">Geoeconomic Signal Intelligence & Macro Synthesis</span>
    <h1 class="hero-headline">De-Dollarization Signals: <em>Macro Intelligence & Empirical Indicators</em></h1>
    <p class="hero-sub">
      Comprehensive intelligence evaluation of {len(df_all)} clean full-text news articles across 12 empirical indicator categories, synthesizing onto-semantic signals with quantitative macro portfolio dynamics.
    </p>

    <div class="hero-stats">
      <div class="stat-item"><span class="stat-val">{len(df_all)}</span><span class="stat-lbl">Clean Full-Text Articles</span></div>
      <div class="stat-item"><span class="stat-val">12</span><span class="stat-lbl">Indicator Buckets Covered</span></div>
      <div class="stat-item"><span class="stat-val">20</span><span class="stat-lbl">Priority Focus Intelligence</span></div>
      <div class="stat-item"><span class="stat-val">50</span><span class="stat-lbl">Extended Coverage Articles</span></div>
    </div>
  </div>
</header>

<main class="wrap--wide">

  <!-- SECTION 01: PIPELINE ARCHITECTURE -->
  <section id="pipeline">
    <span class="sec-label">01. Intelligence Pipeline Architecture</span>
    <h2 class="section-title">From Onto-Graph to Seeds, Signals, and News Bucketing</h2>
    <p class="section-intro">
      The Merlin Intelligence news analysis engine operates on an end-to-end onto-semantic architecture. Rather than relying on simple keyword scraping or ungrounded summaries, the pipeline enforces formal semantic constraints from knowledge representation down to individual news classification:
    </p>

    <div class="pipeline-grid">
      <div class="pipeline-card">
        <div>
          <span class="pipeline-step">Phase 01 // Ontology</span>
          <h3 class="pipeline-title">The Onto-Semantic Graph</h3>
          <p class="pipeline-desc">
            Constructing a formal directed knowledge graph mapping global monetary actors (central banks, sovereign wealth funds), institutional standards (IMF COFER, SWIFT messaging, BIS OTC turnover), market mechanisms (CIP deviations, Treasury convenience yields, swap spreads), and alternative transaction rails (CIPS, mBridge, multi-CBDC corridors, stablecoins).
          </p>
        </div>
      </div>

      <div class="pipeline-card">
        <div>
          <span class="pipeline-step">Phase 02 // Taxonomy</span>
          <h3 class="pipeline-title">Algorithmic Seed Generation</h3>
          <p class="pipeline-desc">
            Projecting topological graph centrality hubs and cross-boundary bridge nodes into a curated taxonomy of 100 domain-specific search query seeds across 12 empirical indicator buckets. Seeds target specific monetary mechanics (e.g., Panda bond debuts, non-SWIFT messaging, Treasury auction tailing) rather than generic media noise.
          </p>
        </div>
      </div>

      <div class="pipeline-card">
        <div>
          <span class="pipeline-step">Phase 03 // Harvesting</span>
          <h3 class="pipeline-title">Harvesting & Canonical Resolution</h3>
          <p class="pipeline-desc">
            Querying Google News RSS feeds across multi-week lookback windows, resolving raw URLs to canonical publisher links via Brave Search APIs to eliminate aggregator redirects, and deploying concurrent headless Chromium Playwright workers to extract clean, un-gated full-text journalistic content.
          </p>
        </div>
      </div>

      <div class="pipeline-card">
        <div>
          <span class="pipeline-step">Phase 04 // Immersion</span>
          <h3 class="pipeline-title">Multi-Anchor Concept Bucketing</h3>
          <p class="pipeline-desc">
            Vectorizing clean full texts and computing high-dimensional similarity against the multi-anchor semantic descriptors of the 12 empirical indicator buckets. Each article is assigned to its dominant category based on concept immersion, guaranteeing continuous calibration across all dimensions of monetary realignment.
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- SECTION 02: MACRO OBSERVATIONS -->
  <section id="macro-observations">
    <span class="sec-label">02. Macro Regime Observations</span>
    <h2 class="section-title">Empirical Signals & Model Observations</h2>
    <p class="section-intro">
      Synthesizing real-world news signals harvested across September 2026 with the empirical findings of our 9-Asset Walk-Forward Portfolio K-Max strategy reveals profound structural shifts across energy, sovereign debt, foreign exchange reserves, and global macro portfolio allocations:
    </p>

    <div class="macro-section">

      <!-- SUBSECTION 1: ENERGY & DOLLAR -->
      <article class="macro-card">
        <span class="macro-eyebrow">Macro Observation · 01</span>
        <h3 class="macro-title">Interactions Between Energy Prices and Dollar Dynamics</h3>
        <div class="macro-body">
          <p>
            The escalation of geopolitical friction in the Persian Gulf and maritime interdictions around the Strait of Hormuz have injected sharp risk premia into global crude oil and liquefied natural gas (LNG) markets. Historically, energy supply shocks triggered an automatic, mechanical surge in structural demand for U.S. dollars through the mandatory petrodollar invoicing framework established in 1974, followed by the predictable recycling of petrodollars into U.S. Treasuries.
          </p>
          <p>
            Today, that structural transmission mechanism is breaking down. Major oil exporters and importers—spanning Saudi Arabia, the UAE, Iran, Russia, China, and India—are aggressively deploying non-dollar settlement corridors. Hydrocarbon transactions are increasingly cleared directly in renminbi (the petroyuan), UAE dirhams, and local currencies, bypassing traditional New York correspondent clearing banks and SWIFT rails.
          </p>
          <p>
            Consequently, rising energy prices no longer drive structural foreign accumulation of U.S. Treasuries. Instead, energy inflation functions as an un-hedged terms-of-trade shock against Western economies, expanding trade deficits and driving domestic import inflation, while Eurasian energy trade loops become self-contained, insulated from U.S. dollar liquidity constraints.
          </p>

          <div class="selected-news-box">
            <span class="selected-news-label">Corroborating Intelligence · Selected News</span>
            <ul class="selected-news-list">
              <li class="selected-news-item">
                <a href="https://energy.economictimes.indiatimes.com/news/oil-and-gas/oil-trades-shift-towards-a-currency-agnostic-future/133903259" target="_blank" rel="noopener" class="selected-news-link">Oil trade’s shift towards a currency-agnostic future</a>
                <span class="selected-news-meta">ET EnergyWorld • September 08, 2026 • Petroyuan expansion, bilateral crude clearing & bypass of SWIFT rails</span>
              </li>
              <li class="selected-news-item">
                <a href="https://fortune.com/2026/09/11/oil-prices-hormuz-diplomacy-saudi-arabia-houthis-pakistan-us-bab-al-mandab/" target="_blank" rel="noopener" class="selected-news-link">Oil prices dive on signs of Hormuz diplomacy while Saudi Arabia is left hanging in fight vs. Houthis</a>
                <span class="selected-news-meta">Fortune • September 11, 2026 • Persian Gulf maritime bottlenecks, Bab al-Mandab security & geopolitical crude risk premia</span>
              </li>
              <li class="selected-news-item">
                <a href="https://www.europesays.com/3233377/" target="_blank" rel="noopener" class="selected-news-link">US-Iran Conflict Reignites as Hedge Funds Push Crude Oil Bullish Bets to Highest Since May</a>
                <span class="selected-news-meta">BigGo Finance / EuropeSays • September 04, 2026 • Geopolitical crude supply shocks & speculative energy positioning</span>
              </li>
            </ul>
          </div>
        </div>
      </article>

      <!-- SUBSECTION 2: GLOBAL BONDS SELL-OFF -->
      <article class="macro-card">
        <span class="macro-eyebrow">Macro Observation · 02</span>
        <h3 class="macro-title">Global Bonds Sell-Off and Spiking Interest Rates</h3>
        <div class="macro-body">
          <p>
            Sovereign debt markets across G7 economies are experiencing severe duration repricing and yield curve steepening. The U.S. 10-year Treasury yield surged toward 4.86% (3-year highs), while the 30-year bond breached 5.30%—its highest level in 19 years. Concurrently, European government bond yields have pushed higher, undermining traditional fixed-income capital preservation assumptions.
          </p>
          <p>
            In a pivotal warning published in early September 2026, European Central Bank (ECB) economists highlighted an unprecedented crowding-out dynamic: a massive bonanza of bond sales by U.S. mega-cap technology giants is absorbing global institutional fixed-income demand, pulling capital directly away from European sovereign debt and driving up public borrowing costs across the Eurozone. When high-yielding U.S. corporate balance sheets compete for long-term duration capital, sovereign issuers lose their historic yield insulation.
          </p>
          <p>
            This duration sell-off was compounded on September 9, 2026, when the U.S. Treasury under Secretary Scott Bessent conducted its first debt buyback operation. Offering a modest $6 billion against Wall Street expectations of $8–10 billion, the cosmetic intervention backfired, triggering an aggressive yield spike as primary dealers realized that official debt repurchase capacity cannot keep pace with multi-trillion-dollar federal deficits. The structural compression of the Treasury "convenience yield" and persistent deeply negative interest rate swap spreads confirm that sovereign debt is no longer treated as pristine, unassailable safe-haven ballast.
          </p>

          <div class="selected-news-box">
            <span class="selected-news-label">Corroborating Intelligence · Selected News</span>
            <ul class="selected-news-list">
              <li class="selected-news-item">
                <a href="https://www.euractiv.com/news/us-tech-bond-bonanza-could-raise-european-borrowing-costs-say-ecb-analysts/" target="_blank" rel="noopener" class="selected-news-link">US tech bond bonanza could raise European borrowing costs, say ECB analysts</a>
                <span class="selected-news-meta">Euractiv • September 01, 2026 • Mega-cap US corporate debt crowding out European sovereign debt demand</span>
              </li>
              <li class="selected-news-item">
                <a href="https://www.tradingview.com/news/stocktwits:951f65fe9094b:0-the-weekly-spread-what-shaped-yields-and-the-dollar-this-week/" target="_blank" rel="noopener" class="selected-news-link">The Weekly Spread: What Shaped Yields And The Dollar This Week</a>
                <span class="selected-news-meta">TradingView • September 19, 2026 • G7 duration steepening, swap spread compression & Treasury convenience yield erosion</span>
              </li>
            </ul>
          </div>
        </div>
      </article>

      <!-- SUBSECTION 3: 20-YEAR AUCTION HISTORIC DEGRADATION -->
      <article class="macro-card">
        <span class="macro-eyebrow">Macro Observation · 03</span>
        <h3 class="macro-title">Historic Demand Degradation in the U.S. Treasury's September 20-Year Auction</h3>
        <div class="macro-body">
          <div class="callout-box">
            <strong>Key Empirical Observation</strong>
            The U.S. Treasury's September 20-year bond auction experienced historic demand degradation, with primary dealers forced to absorb an unusually large share as foreign indirect bidder participation declined sharply, causing a substantial auction tail.
          </div>
          <p>
            On Wednesday, September 16, 2026, the U.S. Treasury conducted its scheduled 20-year sovereign bond auction, which resulted in the worst demand showing in the security’s history. Foreign indirect bidders—the primary proxy for foreign central banks, sovereign wealth funds, and international institutional reserve managers—withdrew significantly from the bidding book.
          </p>
          <p>
            Faced with an acute absence of foreign sponsor appetite, primary dealers were forced to warehouse an abnormally large percentage of the issued paper. The auction cleared with a dramatic tail above the pre-auction when-issued yield, signaling severe dealer balance sheet indigestion. This auction failure represents concrete empirical evidence that international sovereign allocators are unwilling to finance expanding U.S. fiscal deficits at the long end of the curve without substantial concession premiums, validating our model's structural penalization of long-duration paper.
          </p>

          <div class="selected-news-box">
            <span class="selected-news-label">Corroborating Intelligence · Selected News</span>
            <ul class="selected-news-list">
              <li class="selected-news-item">
                <a href="https://protos.com/us-20-year-bond-auction-just-had-its-worst-showing-ever/" target="_blank" rel="noopener" class="selected-news-link">US 20-year bond auction just had its worst showing ever</a>
                <span class="selected-news-meta">Protos / Cryptonews.net • September 16, 2026 • Historic auction tail, primary dealer balance-sheet indigestion & foreign buyer retreat</span>
              </li>
              <li class="selected-news-item">
                <a href="https://wolfstreet.com/2026/09/15/some-thoughts-on-the-5-42-yield-at-the-20-year-treasury-auction-bond-market-bloodbath-continues/" target="_blank" rel="noopener" class="selected-news-link">U.S. Treasury's $13 Billion 20-Year Bond Auction Yields Record 5.42%; 10-Year Tops 5% for First Time Since 2007</a>
                <span class="selected-news-meta">Wolf Street / BigGo Finance • September 16, 2026 • Long-duration sovereign bond supply overload & foreign central bank buyer strike</span>
              </li>
            </ul>
          </div>
        </div>
      </article>

      <!-- SUBSECTION 4: DE-RESERVIFICATION, NOT DE-DOLLARIZATION -->
      <article class="macro-card">
        <span class="macro-eyebrow">Macro Observation · 04</span>
        <h3 class="macro-title">De-Reservification, Not De-Dollarization</h3>
        <div class="macro-body">
          <p>
            A persistent conceptual error in financial discourse is conflating the U.S. dollar's role as a transactional clearing currency with its role as a permanent sovereign reserve anchor. As articulated by Brad Setser (Council on Foreign Relations) and corroborated by recent Federal Reserve Bank of New York research, the global economy is not abruptly abandoning the dollar for daily trade settlement. In foreign exchange turnover, trade invoicing, and SWIFT messaging, the dollar remains the undisputed operational medium of exchange.
          </p>
          <p>
            What is underway is a calculated, structural process of <strong>De-reservification</strong>: sovereign central banks and monetary authorities are systematically curtailing their long-term foreign exchange exposure to freezeable, debt-monetized G7 sovereign paper. Following the precedent of Western central bank asset freezes in 2022, sovereign reserve managers recognize that holding excess wealth in U.S. Treasuries carries existential counterparty and geopolitical risk.
          </p>
          <p>
            Consequently, sovereign balance sheets are executing an aggressive asset substitution into un-freezable, un-encumbered physical assets—foremost among them, physical gold bullion:
          </p>
          <ul style="margin: 0.8rem 0 1.2rem 1.6rem; font-size: 0.95rem; line-height: 1.65;">
            <li><strong>Sovereign Vault Repatriation:</strong> The Dutch Central Bank (DNB) formally transferred sovereign gold to domestic military vaults, affirming that when multilateral paper guarantees fail, physical bullion is the ultimate monetary anchor.</li>
            <li><strong>Uninterrupted Official Accumulation:</strong> The People's Bank of China (PBoC) expanded its physical gold holdings for 22 consecutive months, lifting official bullion reserves to 2,366 metric tons (76.73 million ounces).</li>
            <li><strong>Institutional Reallocation Intent:</strong> Global central bank surveys indicate that 45% of monetary authorities plan to expand gold reserves over the next 12 to 36 months, allowing maturing Treasury tranches to expire without reinvestment.</li>
          </ul>

          <div class="selected-news-box">
            <span class="selected-news-label">Corroborating Intelligence · Selected News</span>
            <ul class="selected-news-list">
              <li class="selected-news-item">
                <a href="https://www.europesays.com/3239271/" target="_blank" rel="noopener" class="selected-news-link">Dollar's declining reserve share reflects few countries' choices, not global shift, NY Fed says</a>
                <span class="selected-news-meta">Federal Reserve Bank of NY / EuropeSays • September 08, 2026 • Transactional clearing medium vs. sovereign reserve asset allocation dichotomy</span>
              </li>
              <li class="selected-news-item">
                <a href="https://goldsilver.com/industry-news/goldsilver-news/pboc-gold-reserves-august-2026-22-months/" target="_blank" rel="noopener" class="selected-news-link">China Just Broke Its Own Gold-Buying Record. Then Broke It Again.</a>
                <span class="selected-news-meta">GoldSilver • September 07, 2026 • PBoC official gold reserves reach 2,366 tons across 22 consecutive months of official bullion accumulation</span>
              </li>
              <li class="selected-news-item">
                <a href="https://www.cointribune.com/en/china-holds-2366-tons-of-gold-as-yuan-ambitions-grow" target="_blank" rel="noopener" class="selected-news-link">China Holds 2,366 Tons Of Gold As Yuan Ambitions Grow</a>
                <span class="selected-news-meta">Cointribune • September 17, 2026 • Physical bullion reserves as an un-freezable sovereign balance sheet shield against dollar dominance</span>
              </li>
              <li class="selected-news-item">
                <a href="https://www.inventiva.co.in/trends/where-the-worlds-gold-is-going-and-what-china-india-europe-and-america-know-about-the-next-financial-shock/" target="_blank" rel="noopener" class="selected-news-link">Where The World's Gold Is Going And What Central Banks Know About The Next Financial Shock</a>
                <span class="selected-news-meta">Inventiva • September 17, 2026 • Sovereign vault repatriation, Western asset freezes & de-reservification trends across Eurasia</span>
              </li>
            </ul>
          </div>
        </div>
      </article>

      <!-- SUBSECTION 5: QUANT MACRO DYNAMICS (K-MAX) -->
      <article class="macro-card">
        <span class="macro-eyebrow">Macro Observation · 05</span>
        <h3 class="macro-title">Quant Macro Dynamics: Capital Allocation to Dollar by Global Macro Players Remains Strong</h3>
        <div class="macro-body">
          <p>
            The mathematical findings of our institutional research report, <em>Global Macro Expansion: Institutional Quantitative Evaluation of the 9-Asset Walk-Forward Portfolio K-Max Strategy (2018–2026)</em> (evaluating 2,063 live trading sessions across <code>SPY, GLD, UUP, TLT, IEF, LSHUX, DBC, EEM, MCHI</code>), provide rigorous mathematical validation for this dual-currency reality.
          </p>
          <p>
            In the live target allocation heading into the current cycle (market close Friday, September 18, 2026), the proprietary Merlin Asset Allocation model maintains a commanding capital allocation in the U.S. dollar cash proxy (<code>UUP</code>) at <strong>+37.24% of total portfolio capital</strong> (historically averaging a <strong>33.66%</strong> mean capital weight over the trailing 3-year cycle).
          </p>

          <div class="quant-box">
            <div class="quant-label">Systemic Capital Allocation & Balance Sheet Deployment</div>
            <p>
              At this macro intelligence stage, our analysis focuses primarily on <strong>strategic capital allocation</strong> across the portfolio's core asset classes. While detailed mathematical risk allocations (including Euler percentage risk contributions, covariance decompositions, and sensitivity profiles) are generated continuously by our engine and remain available for finer institutional analysis, capital allocation provides the most direct reflection of real-world balance sheet deployment:
            </p>

            <div class="callout-box" style="margin: 1.1rem 0; border-left: 3px solid var(--gold); background: var(--bg);">
              <strong style="font-family: 'Space Mono', monospace; font-size: 0.68rem; text-transform: uppercase; color: var(--gold); letter-spacing: 0.06em; margin-bottom: 0.4rem; display: block;">
                Quant-Attractivity of the Dollar: Primary Capital Anchor
              </strong>
              <p style="font-size: 0.94rem; line-height: 1.65; margin: 0; color: var(--ink);">
                <strong>US Dollar Reserve as Primary Capital Anchor (<code>UUP</code>: +37.24% Capital, +3.14% %RC):</strong><br>
                The US Dollar holding sits at <strong>37.24%</strong> of total capital. With global central banks navigating currency fragmentation and US cash yields remaining attractive, <code>UUP</code> provides stable carry without duration risk, dampening total portfolio volatility to an ultra-low <strong>3.45%</strong> annualized.
              </p>
            </div>

            <p>
              <strong>Cash & Sovereign Safe-Haven Core:</strong> The U.S. dollar cash proxy (<code>UUP</code>: <strong>37.24%</strong>), Intermediate Treasuries (<code>IEF</code>: <strong>16.56%</strong>), and Long Treasuries (<code>TLT</code>: <strong>13.65%</strong>) together command <strong>67.45% of the fund's total capital</strong>. This massive balance-sheet anchor insulates the fund against broad market liquidity freezes, successfully dampening annualized portfolio volatility to an institutional <strong>3.45%</strong>.
            </p>
            <p>
              <strong>Real Assets & Compounding Growth:</strong> Growth capital is concentrated in <strong>Physical Gold (<code>GLD</code>: delivering 65.79% of total portfolio risk-adjusted compounding efficiency</strong>, +125.79% 3Y return), <strong>Broad Commodities (<code>DBC</code>: +18.50% capital</strong>, +18.90% 3Y return) to hedge Middle Eastern energy supply shocks and maritime choke points, and <strong>Large-Cap Equities (<code>SPY</code>: +19.71% capital</strong>, +54.67% 3Y return).
            </p>
            <p>
              <strong>Tactical Factor Hedges:</strong> Disciplined short/hedged sleeves in active growth (<code>LSHUX</code>: <strong>-2.53%</strong>) and Chinese equities (<code>MCHI</code>: <strong>-2.44%</strong>) neutralize valuation crowding and regional balance-sheet restructuring.
            </p>
            <p style="font-size: 0.84rem; color: var(--light); font-style: italic; margin-top: 0.6rem;">
              * Institutional Note: Granular Euler risk decompositions (%RC), asset beta profiles, and stress-test sensitivity matrices are available upon request for finer institutional risk due diligence.
            </p>
          </div>

          <h4 style="font-family: 'Playfair Display', serif; font-size: 1.18rem; margin: 1.8rem 0 0.8rem; color: var(--ink);">
            The 9-Asset Investment Universe: Strategic Profiles & Macro Roles
          </h4>
          <p style="font-size: 0.92rem; color: var(--light); margin-bottom: 1.2rem;">
            Each asset within the K-Max investment universe fulfills a distinct structural mandate across compounding, safe-haven liquidity, duration buffering, and factor hedging:
          </p>

          <div class="etf-grid">
            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">SPY</span>
                <span class="etf-alloc">+19.71% Capital</span>
              </div>
              <h5 class="etf-name">SPDR S&P 500 ETF Trust</h5>
              <p class="etf-desc">
                Core large-cap equity beta proxy (+54.67% 3Y return). Captures high-margin technological productivity and AI capex monetization of premier U.S. corporate balance sheets, disciplined by the model to harvest equity risk premia.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">GLD</span>
                <span class="etf-alloc">Primary Compounding Driver</span>
              </div>
              <h5 class="etf-name">SPDR Gold Shares</h5>
              <p class="etf-desc">
                Physical gold bullion vaulted in London (+125.79% 3Y return). The strategy's primary compounding pillar, delivering 65.79% of total portfolio risk-adjusted compounding efficiency as central bank de-reservification accelerates.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">UUP</span>
                <span class="etf-alloc">+37.24% Capital (+3.14% %RC)</span>
              </div>
              <h5 class="etf-name">Invesco DB US Dollar Index</h5>
              <p class="etf-desc">
                Primary Capital Anchor (37.24% capital). With global central banks navigating currency fragmentation and US cash yields remaining attractive, UUP provides stable carry without duration risk, dampening total portfolio volatility to an ultra-low 3.45% annualized.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">TLT</span>
                <span class="etf-alloc">+13.65% Capital</span>
              </div>
              <h5 class="etf-name">iShares 20+ Year Treasury</h5>
              <p class="etf-desc">
                Ultra-long sovereign duration (~16.5-year duration; -14.36% 3Y return). Constrained and disciplined by the model due to expanding federal deficits, term-premium resurgence, and severe auction demand degradation.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">IEF</span>
                <span class="etf-alloc">+16.56% Capital</span>
              </div>
              <h5 class="etf-name">iShares 7-10 Year Treasury</h5>
              <p class="etf-desc">
                Intermediate-term sovereign duration (~7.2-year duration; +4.12% 3Y return). Delivers positive carry yield and dependable safe-haven liquidity buffer without the acute convexity drawdowns inherent to the ultra-long curve.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">LSHUX</span>
                <span class="etf-alloc">-2.53% Net Capital</span>
              </div>
              <h5 class="etf-name">Loomis Sayles Growth Sleeve</h5>
              <p class="etf-desc">
                Active large-cap growth factor sleeve, tactically shorted / hedged. Deployed by the model to isolate pure market beta, strip out excessive valuation multiples, and shield capital from tech-crowding momentum unwinds.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">DBC</span>
                <span class="etf-alloc">+18.50% Capital</span>
              </div>
              <h5 class="etf-name">Invesco DB Commodity Index</h5>
              <p class="etf-desc">
                Diversified basket of 14 physical commodities across crude, metals, and agriculture (+18.90% 3Y return). Serves as the primary active inflation buffer to hedge Persian Gulf maritime blockades and terms-of-trade shocks.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">EEM</span>
                <span class="etf-alloc">Decoupling Proxy</span>
              </div>
              <h5 class="etf-name">iShares MSCI Emerging Markets</h5>
              <p class="etf-desc">
                Broad emerging market equity exposure outside the G7 (+87.10% 3Y return). Captures sovereign trade reorganization, critical mineral exporters, and semiconductor manufacturing nodes across non-aligned trading corridors.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">MCHI</span>
                <span class="etf-alloc">-2.44% Net Capital</span>
              </div>
              <h5 class="etf-name">iShares MSCI China ETF</h5>
              <p class="etf-desc">
                Comprehensive Chinese equity exposure, tactically hedged (-16.82% 3Y return). Balances bilateral trade frictions, property sector deleveraging, and deflation against asymmetric upside from state-directed liquidity.
              </p>
            </div>
          </div>

          <p>
            <strong>Institutional Takeaway:</strong> Global systematic macro players allocate heavily to the U.S. dollar not as a long-term speculative store of value, but as an indispensable <em>operational clearing liquidity and zero-beta collateral anchor</em>. Wealth preservation and compounding return generation have decisively decoupled into un-encumbered physical gold and geopolitical commodities, while the dollar provides the liquidity chassis upon which modern quantitative asset allocation operates.
          </p>
        </div>
      </article>

    </div>
  </section>

  <!-- SECTION 03: TAXONOMY OVERVIEW -->
  <section id="categories">
    <span class="sec-label">03. Indicator Categories Overview</span>
    <h2 class="section-title">The 12 Empirical Indicator Categories</h2>
    <p class="section-intro">
      Each harvested piece of news is evaluated across the 12 empirical dimensions of systemic monetary realignment:
    </p>

    <div class="taxonomy-grid">
\"\"\"

    for b in BUCKET_TAXONOMY:
        b_id = b["id"]
        b_name = html.escape(b["name"])
        b_desc = html.escape(b["desc"])
        b_count = len(df_all[df_all['assigned_bucket_id'] == b_id])
        html_content += f\"\"\"
      <div class="taxonomy-card">
        <div>
          <div class="tax-header">
            <span class="tax-badge">BUCKET {b_id}</span>
            <span class="tax-count">{b_count} Articles</span>
          </div>
          <h3 class="tax-title">{b_name}</h3>
          <p class="tax-desc">{b_desc}</p>
        </div>
      </div>
\"\"\"

    html_content += \"\"\"
    </div>
  </section>

  <!-- SECTION 04: PRIORITY INTELLIGENCE (TOP 20) -->
  <section id="top20">
    <span class="sec-label">04. Priority Intelligence (Top 20 Curated News)</span>
    <h2 class="section-title">Top 20 Priority News Articles: <em>Chronological Presentation & Structural Mechanisms</em></h2>
    <p class="section-intro">
      The 20 articles below guarantee complete representation across all 12 indicator categories. They link directly to their canonical publisher source URLs, presented chronologically starting with the <b>most recent publication date</b> down to earlier news:
    </p>

    <div class="news-cards">
\"\"\"

    for idx, row in df_top20_presented.iterrows():
        pres_num = idx + 1
        b_id = str(row['assigned_bucket_id'])
        clean_b_name = html.escape(get_clean_bucket_name(b_id))
        
        title = html.escape(str(row['Title']))
        resolved_target = html.escape(str(row.get('resolved_url', row.get('URL', ''))))
        date_val = html.escape(str(row['Date']))
        
        countries_str = str(row.get('country_tags', 'Global / Multilateral'))
        country_list = [c.strip() for c in countries_str.split(',')]
        country_badges_html = "".join([f'<span class="country-tag">{html.escape(c)}</span>' for c in country_list])
        
        raw_text = str(row.get('Extracted_Article_Text', ''))
        raw_desc = str(row.get('Description', ''))
        curated_summary, curated_mechanism = get_curated_summary_and_mechanism(row['Title'], b_id, raw_text, raw_desc)
        
        html_content += f\"\"\"
      <article class="news-card">
        <div class="card-header">
          <div class="card-badges">
            <span class="badge-date">DATE: {date_val}</span>
            <span class="badge-bucket">BUCKET {b_id}: {clean_b_name}</span>
          </div>
          <span class="nav-sub">Priority Focus • {pres_num:02d} of 20</span>
        </div>

        <h3 class="card-title"><a href="{resolved_target}" target="_blank" rel="noopener">{title}</a></h3>
        <span class="card-meta">Publication Date: {date_val} • Direct Source: <a href="{resolved_target}" target="_blank" rel="noopener" style="color:var(--gold); text-decoration:none;">{resolved_target[:75]}...</a></span>

        <div class="country-tags-wrap">
          <span class="country-label">📍 Countries Mentioned:</span>
          {country_badges_html}
        </div>

        <p class="card-summary"><b>Executive Summary:</b> {curated_summary}</p>

        <div class="card-mechanism">
          <strong>Underlying Monetary Mechanism</strong>
          {curated_mechanism}
        </div>
      </article>
\"\"\"

    html_content += \"\"\"
    </div>
  </section>

  <!-- SECTION 05: EXTENDED COVERAGE (FOLLOWING 50) -->
  <section id="next50">
    <span class="sec-label">05. Extended Coverage (Following 50 Articles)</span>
    <h2 class="section-title">Following 50 News Articles: <em>Chronological Reference</em></h2>
    <p class="section-intro">
      The table below displays extended coverage across the following 50 articles from the curated corpus, linking directly to canonical publisher source URLs, ordered by publication date (most recent first):
    </p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Indicator Category</th>
            <th>Countries Mentioned</th>
            <th>Article Title & Resolved Source Link</th>
          </tr>
        </thead>
        <tbody>
\"\"\"

    for idx, row in df_next50_presented.iterrows():
        date_val = html.escape(str(row['Date']))
        b_id = str(row['assigned_bucket_id'])
        clean_b_short = html.escape(get_clean_bucket_short(b_id))
        
        countries_str = str(row.get('country_tags', 'Global / Multilateral'))
        country_list = [c.strip() for c in countries_str.split(',')]
        country_inline = ", ".join(country_list[:3])
        if len(country_list) > 3: country_inline += f" (+{len(country_list)-3})"
        country_inline_html = html.escape(country_inline)
        
        title = html.escape(str(row['Title']))
        resolved_target = html.escape(str(row.get('resolved_url', row.get('URL', ''))))
        
        html_content += f\"\"\"
          <tr>
            <td class="td-date">{date_val}</td>
            <td class="td-bucket">[{b_id}] {clean_b_short}</td>
            <td class="td-countries">{country_inline_html}</td>
            <td class="td-title"><a href="{resolved_target}" target="_blank" rel="noopener">{title}</a></td>
          </tr>
\"\"\"

    html_content += \"\"\"
        </tbody>
      </table>
    </div>
  </section>

</main>

<footer>
  <div class="wrap--wide">
    <span>&copy; 2026 Merlin Intelligence. Geoeconomic Knowledge Infrastructure.</span>
    <span>Generated by Merlin Intelligence Pipeline</span>
  </div>
</footer>

</body>
</html>
\"\"\"

    f1 = "dedollarization_intelligence_report.html"
    f2 = "dedollarization_intelligence_report_v2.html"

    with open(f1, "w", encoding="utf-8") as f: f.write(html_content)
    with open(f2, "w", encoding="utf-8") as f: f.write(html_content)

    art_dir = r"C:\\Users\\franc\\.gemini\\antigravity-cli\\brain\\9636c74e-aff5-42a5-9d64-ac57f0c413c3"
    if os.path.exists(art_dir):
        shutil.copyfile(f1, os.path.join(art_dir, f1))
        shutil.copyfile(f2, os.path.join(art_dir, f2))

    print(f"✅ Successfully generated updated macro intelligence reports: {f1} & {f2} ({len(html_content)} bytes).")
    return True

if __name__ == "__main__":
    build_report()
"""

new_full_script = pre_code + html_builder_code

with open(TARGET_PY, "w", encoding="utf-8") as f:
    f.write(new_full_script)

print(f"✅ Successfully updated {TARGET_PY}!")

# Now run it directly to generate the HTML reports!
import subprocess
print("🚀 Executing build_simplified_report.py...")
res = subprocess.run([sys.executable, TARGET_PY], cwd=BASE_DIR, capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("Stderr:", res.stderr)
