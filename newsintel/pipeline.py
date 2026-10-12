"""Pipeline orchestration: run the stages in order inside one run directory.

    runs/<project>/<timestamp>/
        harvest.csv    articles found, with publisher URLs        (harvest: search + resolve links)
        articles.csv   + full text and extraction status           (extract)
        scored.csv     ranked articles, scores, summaries; no text (score)
        similarity.npz article × article text similarity, reused by select
        selection.csv  top + next tiers shown in the report       (select)
        report.html    self-contained report                       (report)
        run.json       config snapshot, counts, timings

Full texts are only stored in articles.csv, so scored.csv and selection.csv
stay small enough to open in a spreadsheet.

A stage whose output already exists is skipped, so re-running the same run
directory resumes an interrupted run. --from re-runs a stage and everything
after it.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from newsintel import __version__
from newsintel.config import Config
from newsintel.data import load_seeds, read_csv, write_csv

log = logging.getLogger(__name__)

STAGES = ["harvest", "extract", "score", "select", "report"]
OUTPUTS = {
    "harvest": "harvest.csv",
    "extract": "articles.csv",
    "score": "scored.csv",
    "select": "selection.csv",
    "report": "report.html",
}
SIMILARITY = "similarity.npz"
TEXT_COLUMNS = ["text", "extraction_error"]  # kept in articles.csv only
NUMERIC = ["relevance", "category_match", "novelty", "centrality", "hinge", "score", "rank", "selection_rank"]


def new_run_dir(cfg: Config) -> Path:
    return cfg.resolve_path(cfg.output_dir) / cfg.project.name / datetime.now().strftime("%Y%m%d-%H%M%S")


def latest_run_dir(cfg: Config) -> Path | None:
    root = cfg.resolve_path(cfg.output_dir) / cfg.project.name
    runs = sorted(p for p in root.glob("*") if p.is_dir()) if root.exists() else []
    return runs[-1] if runs else None


def export_name(project: str, run_dir: Path) -> str:
    """Readable report file name: <project>_<YYYY-MM-DD_HHMM>.html"""
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})\d{2}", run_dir.name)
    stamp = f"{m[1]}-{m[2]}-{m[3]}_{m[4]}{m[5]}" if m else run_dir.name
    return f"{project}_{stamp}.html"


def export_report(run_dir: Path, project: str, dest: Path) -> Path:
    """Copy report.html to dest/<project>_<YYYY-MM-DD_HHMM>.html and return the copy's path."""
    report = run_dir / OUTPUTS["report"]
    if not report.exists():
        raise FileNotFoundError(f"No report in {run_dir}: run the pipeline up to the 'report' stage first")
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / export_name(project, run_dir)
    shutil.copyfile(report, target)
    return target


def _numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in NUMERIC:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


class Pipeline:
    def __init__(self, cfg: Config, run_dir: Path, sample: int | None = None, channels: list[str] | None = None):
        self.cfg = cfg
        self.run_dir = run_dir
        self.sample = sample
        self.channels = channels
        self.meta_path = run_dir / "run.json"
        self.meta = json.loads(self.meta_path.read_text(encoding="utf-8")) if self.meta_path.exists() else {}

    def path(self, stage: str) -> Path:
        return self.run_dir / OUTPUTS[stage]

    def _load(self, stage: str) -> pd.DataFrame:
        p = self.path(stage)
        if not p.exists():
            raise FileNotFoundError(f"Missing {p.name}: run the '{stage}' stage first (or drop --from)")
        return _numeric(read_csv(p))

    # --- stages -----------------------------------------------------------

    def harvest(self) -> None:
        from newsintel.harvest import harvest
        from newsintel.resolve import resolve

        s = self.cfg.seeds
        seeds = load_seeds(self.cfg.resolve_path(s.file) if s.file else None, s.column, s.queries, self.sample or s.limit)
        log.info("Harvesting %d seeds on %s", len(seeds), ", ".join(self.channels or self.cfg.harvest.channels))
        df = harvest(self.cfg, seeds, self.channels)
        self.meta["stats"] = {**self.meta.get("stats", {}), "seeds": len(seeds)}
        df = resolve(df, self.cfg.resolve.enabled).drop_duplicates("resolved_url")
        write_csv(df, self.path("harvest"))

    def extract(self) -> None:
        from newsintel.extract import extract

        checkpoint = self.run_dir / "articles.partial.csv"
        df = extract(self._load("harvest"), self.cfg.extraction, checkpoint, days=self.cfg.harvest.days)
        write_csv(df, self.path("extract"))
        checkpoint.unlink(missing_ok=True)

    def score(self) -> None:
        from newsintel.extract import filter_by_age
        from newsintel.scoring import save_similarity, score

        articles = filter_by_age(self._load("extract"), self.cfg.harvest.days)
        result = score(articles, self.cfg)
        save_similarity(self.run_dir / SIMILARITY, result.articles["article_id"], result.similarity)
        write_csv(result.articles.drop(columns=TEXT_COLUMNS, errors="ignore"), self.path("score"))

    def select(self) -> None:
        from newsintel.selection import select

        from newsintel.scoring import load_similarity

        scored = self._load("score")
        sim = load_similarity(self.run_dir / SIMILARITY, scored["article_id"])
        if sim is None:  # run scored by an older version: recompute from the full texts
            texts = self._load("extract")[["article_id", "text"]]
            scored = scored.drop(columns=TEXT_COLUMNS, errors="ignore").merge(texts, on="article_id", how="left")
            scored["text"] = scored["text"].fillna("")
        selected = select(scored, self.cfg, sim)
        write_csv(selected.drop(columns=TEXT_COLUMNS, errors="ignore"), self.path("select"))

    def report(self) -> None:
        from newsintel.report import render

        harvest = read_csv(self.path("harvest")) if self.path("harvest").exists() else pd.DataFrame()
        articles = read_csv(self.path("extract")) if self.path("extract").exists() else pd.DataFrame()
        stats = {
            "seeds": self.meta.get("stats", {}).get("seeds", harvest["seed"].nunique() if len(harvest) else 0),
            "harvested": len(harvest),
            "extracted": int((articles["extraction_status"] == "ok").sum()) if len(articles) else 0,
            "channels": harvest["channel"].value_counts().to_dict() if len(harvest) else {},
        }
        html = render(self._load("select"), self._load("score"), self.cfg, stats)
        self.path("report").write_text(html, encoding="utf-8")

    # --- orchestration ----------------------------------------------------

    def run(self, from_stage: str | None = None, to_stage: str = "report", force: bool = False) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        start = STAGES.index(from_stage) if from_stage else 0
        end = STAGES.index(to_stage)
        self.meta.update(
            {"version": __version__, "project": self.cfg.project.name, "config": self.cfg.to_dict(), "sample": self.sample}
        )
        timings = self.meta.setdefault("timings", {})

        for i, stage in enumerate(STAGES[: end + 1]):
            output = self.path(stage)
            rerun = force or (from_stage is not None and i >= start)
            if output.exists() and not rerun:
                log.info("▸ %s: already done (%s)", stage, output.name)
                continue
            if i < start and not output.exists():
                raise FileNotFoundError(f"Cannot start at '{from_stage}': {output.name} is missing in {self.run_dir}")
            log.info("▸ %s", stage)
            t0 = time.monotonic()
            getattr(self, stage)()
            timings[stage] = round(time.monotonic() - t0, 1)
            self.meta.setdefault("counts", {})[stage] = (
                None if stage == "report" else len(read_csv(output))
            )
            self.meta_path.write_text(json.dumps(self.meta, indent=2, ensure_ascii=False), encoding="utf-8")

        log.info("Done → %s", self.path(to_stage))
        return self.path(to_stage)
