# news-intelligence-pipeline

**Merlin Intelligence — Multi-Channel Real-World Signal Ingestion, Novelty Ranking & Editorial Reporting Pipeline**

`news-intelligence-pipeline` is the downstream signal ingestion and ranking engine of Merlin Intelligence. It ingests singular seeds produced by `ontograph-seed-engine`, harvests real-world signals across multi-channel sources (Google News, Brave News/Web, and LinkedIn Pulse/Posts), resolves canonical sources, extracts clean full text via Playwright, and ranks intelligence using Equi-Weighted Concept Immersion and Lovász submodular novelty scoring.

---

## Architecture Overview

```
news-intelligence-pipeline/
├── inputs/
│   └── seeds_dedollarization.csv             <── Handshake input from ontograph-seed-engine
│
├── harvesting/
│   ├── harvest_brave_linkedin.py             <── Brave Web, News, and LinkedIn Pulse/Posts
│   ├── to_execute_googlenews_merlin_...      <── Google News RSS Ingestion
│   ├── to_execute_resolveggmerlin_...        <── Brave Canonical URL Resolver & Playwright Worker
│   ├── extract_text_for_resolved.py          <── Playwright Headless Chromium Extraction
│   └── run_google_news_pipeline.py           <── Harvesting Orchestrator
│
├── ranking/
│   ├── compile_eigenmind_scores.py           <── Composite Singularity & Lovász Novelty Engine
│   └── run_diversity_picker.py               <── 12-Bucket Balanced Diversity Picker
│
├── reporting/
│   ├── build_simplified_report.py            <── Editorial Report Builder (HTML / TeX)
│   └── dedollarization_intelligence_report.html
│
├── tools/                                    <── Scoring, filtering, and country geotagging utilities
├── requirements.txt
└── README.md
```

---

## Multi-Channel Ingestion Strategy

1. **Google News RSS:** Captures mainstream financial news wires across 100 singular seeds.
2. **Brave Web & News:** Independent web index capturing think-tank analyses, policy papers, and non-Western financial media.
3. **LinkedIn Pulse & Posts:** Captures practitioner commentary, market desk notes, and executive insights from central bank officials, bank treasurers, and macro strategists.
4. **Playwright Extraction:** Concurrent headless Chromium workers extract un-gated clean article bodies.

---

## Mathematical Ranking Methodology

* **Equi-Weighted Multi-Anchor Concept Immersion ($S_{	ext{concept}}^{	ext{equi}}$):** Vectorizes full texts against 12 empirical indicator bucket descriptors.
* **Lovász Submodular Greedy Novelty ($N_{	ext{Lovász}}$):** Penalizes redundancy and maximizes information entropy.
* **Hinge Centrality ($H_{	ext{hinge}}$):** Identifies articles connecting disparate monetary topics.
* **Surface Proximity ($S_{	ext{surface}}$):** Recency and direct seed keyword alignment.

---

## Quickstart

```bash
git clone https://github.com/merlin-intelligence/news-intelligence-pipeline.git
cd news-intelligence-pipeline
pip install -r requirements.txt
playwright install chromium

# 1. Harvest multi-channel signals (Brave + LinkedIn)
python harvesting/harvest_brave_linkedin.py --sample 10

# 2. Run Google News harvest & Playwright extraction
python harvesting/run_google_news_pipeline.py --seeds inputs/seeds_dedollarization.csv

# 3. Rank & generate intelligence report
python reporting/build_simplified_report.py
```

---

## License

Proprietary — &copy; 2026 Merlin Intelligence. All rights reserved.
