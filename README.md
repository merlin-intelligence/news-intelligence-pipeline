# newsintel: topic-agnostic news monitoring

`newsintel` monitors the news on **any topic**. You give it a list of search queries and, optionally, a set of categories. It then:

1. **harvests** recent articles (Google News, Brave News / Web, site-restricted search such as LinkedIn) and resolves Google News links to the publisher URL;
2. **extracts** the full text and publication date of each article (headless Playwright browser or plain HTTP, then [trafilatura](https://trafilatura.readthedocs.io));
3. **scores** articles on relevance, category match, novelty, centrality and, optionally, the [eigenmind](https://github.com/merlin-intelligence/eigenmind) hinge score;
4. **selects** a duplicate-free "top" tier that includes at least one article per category (optionally a θ-diverse subset, also from eigenmind);
5. **renders** a self-contained HTML report.

Everything topic-specific (queries, categories, keywords, tags, report title) lives in **one YAML file per project**. None of it is in the code.

It can be driven from the command line or from a **web interface** (Streamlit, with the CogMaps visual identity).

```
inputs/seeds_<project>.csv ─┐
configs/<project>.yaml ─────┴─► python -m newsintel run -c configs/<project>.yaml
                                    │
                                    ▼
runs/<project>/<timestamp>/
  harvest.csv → articles.csv → scored.csv → selection.csv → report.html
  similarity.npz  (internal, reused between stages)
  run.json        (effective config, row counts, timings)
  run.log         (log, for runs started from the web interface)
```

---

## Installation

Python 3.10 or later.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[ui,dev]"         # or: pip install -r requirements.txt  (drop "ui" if you only need the CLI)
playwright install chromium        # browser used for extraction
cp .env.example .env               # optional: set BRAVE_API_KEY
```

The **Brave Search API key** is optional. The `google_news` channel works without it. The key is required for the `brave_news`, `brave_web` and site channels. It is also the fallback for resolving Google News links.

## Quick start

```bash
# 1. Scaffold a project: configs/urban_cycling.yaml + inputs/seeds_urban_cycling.csv
python -m newsintel init urban_cycling --title "Urban Cycling Watch"

# 2. Edit both files (topic description, queries, categories), then check them
python -m newsintel validate -c configs/urban_cycling.yaml

# 3. Quick test on 3 queries, then a full run
python -m newsintel run -c configs/urban_cycling.yaml --sample 3
python -m newsintel run -c configs/urban_cycling.yaml
```

The report is written to `runs/urban_cycling/<timestamp>/report.html`. Add `--export` to also save it under a readable name in the same folder, e.g. `urban_cycling_2026-10-11_1835.html`, or `--export DIR` to save that copy in another folder.

Or do all of the above from the web interface:

```bash
python -m newsintel ui             # opens http://localhost:8501
```

An example project is included:
 
| Config | Topic |
|---|---|
| [configs/ai_regulation.yaml](configs/ai_regulation.yaml) | AI regulation (Google News, Brave + LinkedIn) |

Once the package is installed (`pip install -e .`), the `newsintel` command replaces `python -m newsintel`.

---

## Commands

### `run`: run the pipeline

```bash
python -m newsintel run -c CONFIG [options]
```

| Option | Effect |
|---|---|
| `--sample N` | only use the first N queries (for testing) |
| `--resume` | continue the latest run of this project; completed stages are skipped |
| `--from STAGE` | re-run this stage and the following ones on the latest run (e.g. `--from score` after changing the weights) |
| `--to STAGE` | stop after this stage (e.g. `--to extract`) |
| `--run-dir DIR` | use this run directory instead of creating a new one |
| `--force` | re-run every stage |
| `--channels a,b` | override `harvest.channels` |
| `--engine requests` | override the extraction engine |
| `--days N` | override the harvest window |
| `--export [DIR]` | also save the report as `<project>_<YYYY-MM-DD_HHMM>.html`, in the run directory, or in `DIR` if given. With `--resume` on a finished run, nothing is recomputed and only the copy is made |
| `-v` | verbose logging |

Stages: `harvest` (search + link resolution), `extract`, `score`, `select`, `report`.

A stage whose output file already exists is **skipped**, so an interrupted run (Ctrl+C, network failure) picks up where it stopped with `--resume`. Extraction also saves its progress as it goes (`articles.partial.csv`).

### `ui`: web interface

```bash
python -m newsintel ui [--port 8501] [--headless]
```

Run it from the repository root: projects and runs are read from the current directory, and `.env` is loaded from there. The interface has four pages:

| Page | What it does |
|---|---|
| **newsintel** | overview and latest runs of every project |
| **/projects/** | create a project (name, title, topic description), edit its search queries and its categories in tables, edit its YAML configuration (validated before saving; saving a table only rewrites its own section and keeps the rest of the file, comments included) |
| **/run/** | start a new run, resume the latest one or re-run from a stage, with the same overrides as the CLI (queries to use, days back, extraction engine, channels). The log and stage progress update live. Runs execute in a separate process, so they keep going if the tab is closed |
| **/results/** | pick a run: key figures, top-story cards, a filterable table of all ranked articles, the HTML report with a **download report** button (same readable file name as `--export`), and the CSV downloads |

The project picked in the sidebar applies to every page. The sidebar also shows whether a Brave key and Playwright are available. The interface has no login: run it locally or behind your own access control.

### `validate`: check a config

Validates the YAML, counts queries and categories, and reports anything missing: Brave key, Playwright. Unknown keys, wrong types and invalid values (including broken regular expressions in `entities`) are rejected with the YAML line, for example:

```
configs/my_topic.yaml: invalid configuration
  line 6, harvest.chanels: unknown key
  line 9, extraction.engine: Input should be 'playwright' or 'requests'
```

### `init`: scaffold a project

`python -m newsintel init NAME [--title "..."]` creates `configs/NAME.yaml` and `inputs/seeds_NAME.csv` from a commented template.

### `graph`: analyze a concept graph (optional)

```bash
python -m newsintel graph adjacency.csv --out runs/graph --thresholds 0.5 0.7
```

This command is independent of the article pipeline. It takes a square concept adjacency matrix (node names in the first row and first column, weights between 0 and 1) and writes `graph_scores.csv` and `graph_report.md`, using eigenmind for the graph math:

- `spectral`: peak coordinate over the first eigenvectors of the normalized Laplacian;
- `connectivity`: position x* in [-1, 1] along the graph's main axis (eigenmind ℓ∞-connectivity optimizer);
- `hinge`: concepts near the centre that link both poles (eigenmind hinge ranking).

For each `--thresholds` value, the report also lists a diverse subset (greedy independent set of the conflict graph). It also lists a θ-diverse subset of `--theta-k` concepts (eigenmind; experimental, see [Known limitations](#known-limitations)). Both are useful when choosing queries or categories.

---

## Configuration

Every key is listed below with its default value. Only `seeds.file` or `seeds.queries` is required. Relative paths are resolved from the repository root when the config sits in `configs/`.

```yaml
project:
  name: my_topic               # folder name under runs/
  title: News Intelligence Report
  description: ""              # plain-language topic description: drives the relevance score

seeds:
  file: inputs/seeds_x.csv     # CSV (query/seed/keyword… column auto-detected) or .txt (one per line)
  column: null                 # column to use if auto-detection picks the wrong one
  queries: []                  # extra queries written directly in the YAML
  limit: null                  # only use the first N

keywords: []                   # terms whose frequency raises relevance

categories:                    # optional; each article goes to the closest one
  - id: "1"
    name: Display name
    description: terms and phrases characteristic of the category

entities:                      # optional; tags detected by regex (case-insensitive)
  France: ['\bfrance\b', '\bparis\b']

harvest:
  channels: [google_news]      # google_news | brave_news | brave_web | <site_channel name>
  days: 20                     # harvest window
  max_results_per_seed: 20     # Google News
  request_delay: 0.2           # pause between Google News requests (seconds)
  google_news: {language: en, country: US}
  brave:
    count: 5                   # results per query and per Brave channel
    site_channels:             # Brave search restricted to one site
      - {name: linkedin_pulse, site: linkedin.com/pulse/}

resolve:
  enabled: true                # decode news.google.com links

extraction:
  engine: playwright           # playwright (renders JavaScript) | requests (fast, no browser)
  workers: 8
  timeout: 20                  # seconds per page
  min_chars: 250               # shorter articles are marked too_short
  checkpoint_every: 20

scoring:
  weights: {relevance: 0.20, category_match: 0.35, novelty: 0.25, centrality: 0.20, hinge: 0.0}
  keyword_weight: 0.30         # share of keyword frequency in relevance
  graph_threshold: 0.22        # minimum similarity to link two articles (centrality, hinge)
  max_features: 5000
  stop_words: english          # scikit-learn stop-word list, or null for other languages
  require_text: true           # only keep articles whose text was extracted

selection:
  top_n: 20
  next_n: 50
  ensure_category_coverage: true
  max_pairwise_similarity: 0.80   # above this, two articles count as the same story
  method: score                # score | theta (experimental, see Known limitations)
  theta_pool: 3                # theta: choose top_n among the top_n × theta_pool best articles
  theta_conflict_threshold: 0.30  # theta: similarity above which two articles overlap

report:
  subtitle: ""                 # defaults to project.description
  sort_by: score               # score | date

output_dir: runs
```

**Topics in another language**: set `harvest.google_news` (e.g. `{language: fr, country: FR}`) and `scoring.stop_words: null`, then write the description and categories in that language.

## How articles are scored

Every component ranges from 0 to 100. They all rely on TF-IDF and cosine similarity: fast and deterministic, with no model to download and no LLM call. The graph algorithms behind `hinge` and the `theta` selection come from [eigenmind](https://github.com/merlin-intelligence/eigenmind).

| Component | Computation |
|---|---|
| `relevance` | similarity to `project.title + description + keywords`, blended with the frequency of `keywords` |
| `category_match` | similarity to the closest category. Each category is normalized separately so no category drowns out the others |
| `novelty` | articles are walked from most to least relevant; each one scores `1 − max similarity to the ones already walked`. A rewrite of a better article therefore scores low |
| `centrality` | betweenness centrality in the graph of similar articles: articles that bridge several stories |
| `hinge` | eigenmind hinge score on the same graph: articles near the centre of the coverage's main axis that link both of its poles ("relevant but not obvious"). Tends to surface roundups and cross-cutting analyses. **Weight 0 by default**: set `scoring.weights.hinge` to use it |

`score` is the weighted sum of the active components, rescaled so the best article scores 100. A component with weight 0, or `category_match` when there are no categories, is ignored.

**Selection** (`selection.method: score`, the default) works in this order: it drops near-duplicates, guarantees the best article of each category a place, then fills the top tier by score. With `method: theta`, the top tier is instead a θ-diverse subset (eigenmind) of the `top_n × theta_pool` best articles. The subset starts from the best-scored article, and missing categories are then swapped in. In both modes, the `next` tier takes the following articles by score.

## Output files

| File | Contents | Use |
|---|---|---|
| `report.html` | the report | **the deliverable**: self-contained, opens in any browser, can be sent by e-mail |
| `selection.csv` | the articles shown in the report (`tier`: `top` / `next`) with scores, category, tags and summary | share the reading list as a spreadsheet |
| `scored.csv` | **every** ranked article: `relevance, category_match, novelty, centrality, hinge, score, rank, category_id, category_name, entities, summary` | the full ranking, for analysis or reuse |
| `articles.csv` | every harvested article with its full `text` and `extraction_status` (`ok`, `blocked`, `too_short`, `error`, `unresolved`) | the raw corpus; shows which sites block extraction |
| `similarity.npz` | article × article text similarity computed by the score stage | internal: reused by the select stage, so the matrix is computed once |
| `harvest.csv` | every article found: `article_id, channel, seed, title, description, url, resolved_url, source, domain, published_at, harvested_at` | diagnose the queries (which ones return nothing, from which channel) |

Full texts are stored **only** in `articles.csv`, which keeps `scored.csv` and `selection.csv` small. The CSV files are UTF-8 with a BOM, so Excel shows accents correctly. They use commas as separators: in a French-locale Excel, open them with *Data → From Text/CSV* instead of double-clicking.

The CSV files are also what makes resuming possible: `--resume` skips every stage whose file exists, and `--from score` re-ranks from `articles.csv` without downloading anything again.

`run.log` holds the log of runs started from the web interface. `run.json` holds the effective configuration, the row count of each stage and the duration of each stage.

## Known limitations

- **Google News links** are decoded through an undocumented internal Google endpoint ([newsintel/harvest/gnews_decode.py](newsintel/harvest/gnews_decode.py)). If Google changes it, resolution falls back to Brave (key required). Otherwise the affected articles are marked `unresolved`.
- **Paywalls and bot walls**: these pages are detected, marked `blocked` or `error`, and excluded from ranking. LinkedIn often requires a login, so expect many `blocked` results there.
- **Summaries** are extractive (the first clean sentences of the article). No text is generated.
- **Publication dates**: when the search result has no date (frequent with Brave web results), the date found in the page by trafilatura is used.
- **Brave**: the free plan allows 1 request per second (adjustable with `BRAVE_MIN_INTERVAL`).
- **θ diversity is experimental** (`selection.method: theta`, `graph --theta-k`). In eigenmind 0.1.1, `theta_diversity_picker` runs farthest-point selection on a factor in which conflicting nodes are *anti-correlated*. On clearly clustered data it can therefore pick several items from the same cluster (see the `xfail` test in [tests/test_graph.py](tests/test_graph.py)). In the article pipeline, near-duplicates are filtered out before the θ step, so they never reach the report. The default `score` method does not use θ.
- **Hinge cost**: eigenmind's shortest-path search is pure Python, so the hinge score takes about 1 s for 400 articles and grows roughly with n³. It is only computed when its weight is above 0.

---

## Code layout

```
newsintel/
├── cli.py              run / ui / validate / init / graph commands
├── config.py           YAML schema (Pydantic models), validation with YAML line numbers, .env loading
├── pipeline.py         stage orchestration, resume, run.json
├── data.py             column schema, CSV helpers, URL normalization, query loading
├── harvest/
│   ├── __init__.py     harvest stage: queries × channels loop, deduplication, date window
│   ├── google_news.py  Google News RSS feed
│   ├── brave.py        Brave Search client (web, news, rate limit, retries)
│   └── gnews_decode.py news.google.com link decoding
├── resolve.py          Google News link resolution (part of the harvest stage)
├── extract.py          extract stage (Playwright / requests, parallel, checkpoint)
├── text.py             HTML → text and date (trafilatura, with a fallback), blocked-page detection, summary, entity tags
├── scoring.py          score stage
├── selection.py        select stage
├── report.py           report stage: prepares the values shown in the report
├── templates/          report.html.j2 (Jinja2 layout) and report.css, inlined into one self-contained HTML file
├── project.py          project helpers shared by CLI and UI (scaffold, check, list runs, update a config section)
├── graph.py            eigenmind wrappers (hinge, θ pick) + concept graph analysis (graph command)
└── ui/                 web interface (Streamlit)
    ├── app.py          entry point and navigation
    ├── styles.py       CSS, CogMaps visual identity
    ├── components.py   shared sidebar, cards, badges, stage pills
    ├── jobs.py         background runs (one subprocess per run, log in run.log)
    └── views/          home, projects, run, results pages
configs/                one YAML config per project
inputs/                 query files
tests/                  pytest, no network access
```

## Tests

```bash
pytest
```

The tests never touch the network: the RSS feed is mocked and the article corpus is synthetic. When Streamlit is installed, every UI page is also rendered headlessly ([tests/test_ui.py](tests/test_ui.py)).

