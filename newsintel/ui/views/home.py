"""Home page: what the tool does and the latest runs."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from newsintel.config import ConfigError, load_config
from newsintel.pipeline import STAGES
from newsintel.project import list_runs, run_progress
from newsintel.ui.components import info_box, metric_row, projects


def _latest_runs() -> pd.DataFrame:
    rows = []
    for name, path in projects().items():
        try:
            cfg = load_config(path)
        except (ConfigError, ValueError):
            continue
        for run_dir in list_runs(cfg)[:5]:
            done = run_progress(run_dir)
            rows.append(
                {
                    "project": name,
                    "run": run_dir.name,
                    "status": "complete" if done["report"] else f"stopped after {sum(done.values())}/{len(STAGES)} stages",
                    "updated": datetime.fromtimestamp(run_dir.stat().st_mtime),
                }
            )
    return pd.DataFrame(rows).sort_values("run", ascending=False) if rows else pd.DataFrame()


def render() -> None:
    st.markdown(
        '<h1 style="font-family:\'Playfair Display\',Georgia,serif;font-weight:900;font-size:2.4rem;'
        'letter-spacing:-0.03em;color:#2a1f18;margin-bottom:0">newsintel</h1>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="hero-tagline">/ signal from noise /</div>', unsafe_allow_html=True)
    info_box(
        "Monitor the news on any topic: search queries go in, a ranked, de-duplicated reading list comes out."
        '<ul style="margin-top:0.5rem">'
        "<li><strong>/projects/</strong> — create a watch topic, edit its search queries and settings.</li>"
        "<li><strong>/run/</strong> — harvest, read and rank the latest articles.</li>"
        "<li><strong>/results/</strong> — browse the top stories, filter all articles, open the report.</li>"
        "</ul>"
    )
    runs = _latest_runs()
    metric_row(
        [
            ("projects", len(projects()), "configs/*.yaml"),
            ("runs", len(runs), "5 latest per project"),
            ("last run", runs.iloc[0]["project"] if len(runs) else "—", runs.iloc[0]["run"] if len(runs) else ""),
        ]
    )
    if len(runs):
        st.markdown("## recent runs")
        st.dataframe(runs, hide_index=True, use_container_width=True)
