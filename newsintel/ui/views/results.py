"""Results page: top stories, filterable article table, HTML report, files."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from newsintel.data import read_csv
from newsintel.pipeline import OUTPUTS, STAGES, export_name
from newsintel.project import list_runs, run_meta, run_progress
from newsintel.ui.components import badge, empty_state, job_manager, load_selected, metric_row, section_header, selected_project


@st.cache_data(show_spinner=False)
def _read(path: str, mtime: float) -> pd.DataFrame:  # mtime: cache key, refreshed when the file changes
    return read_csv(Path(path))


def read(run_dir: Path, stage: str) -> pd.DataFrame:
    p = run_dir / OUTPUTS[stage]
    if not p.exists():
        return pd.DataFrame()
    df = _read(str(p), p.stat().st_mtime).copy()
    for c in ("score", "rank", "relevance", "category_match", "novelty", "centrality", "hinge"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _run_label(run_dir: Path, running_dir: Path | None) -> str:
    if run_dir == running_dir:
        return f"{run_dir.name} · running"
    done = run_progress(run_dir)
    return run_dir.name if done["report"] else f"{run_dir.name} · incomplete ({sum(done.values())}/{len(STAGES)})"


def _story_card(r: dict) -> str:
    badges = ""
    if r.get("category_name"):
        badges += badge(r["category_name"], "sim")
    badges += badge(r.get("channel", ""), "theta")
    if r.get("hinge", 0) and r["hinge"] >= 50:
        badges += badge("hinge", "hinge")
    meta = " · ".join(escape(str(x)) for x in (f"#{int(r['rank'])}", r.get("source") or r.get("domain"), r.get("published_at"), r.get("entities")) if x)
    return (
        '<div class="story-card"><div class="head">'
        f'<div class="title"><a href="{escape(r["resolved_url"])}" target="_blank" rel="noopener">{escape(r["title"])}</a></div>'
        f'<div class="score">{r["score"]:.0f}</div></div>'
        f'<div class="meta">{meta}</div>{badges}'
        f'<p class="summary">{escape(r.get("summary", ""))}</p></div>'
    )


def _top_tab(selection: pd.DataFrame) -> None:
    top = selection[selection["tier"] == "top"]
    if top.empty:
        empty_state("🗞️", "No article selected in this run.")
        return
    st.markdown("".join(_story_card(r) for r in top.to_dict("records")), unsafe_allow_html=True)


def _table_tab(scored: pd.DataFrame, name: str) -> None:
    c1, c2, c3 = st.columns([2, 2, 1])
    query = c1.text_input("search", placeholder="words in title or summary", key=f"q_{name}")
    cats = sorted(c for c in scored["category_name"].unique() if c)
    chosen = c2.multiselect("categories", cats, key=f"cats_{name}")
    min_score = c3.number_input("min score", 0, 100, 0, step=5, key=f"min_{name}")

    df = scored[scored["score"] >= min_score]
    if chosen:
        df = df[df["category_name"].isin(chosen)]
    if query:
        hay = (df["title"] + " " + df["summary"]).str.lower()
        df = df[hay.str.contains(query.lower(), regex=False)]

    columns = ["rank", "score", "title", "category_name", "source", "published_at", "channel", "entities", "resolved_url"]
    columns += [c for c in ("relevance", "category_match", "novelty", "centrality", "hinge") if c in df.columns and df[c].any()]
    st.caption(f"{len(df)} of {len(scored)} articles")
    st.dataframe(
        df[[c for c in columns if c in df.columns]],
        hide_index=True,
        use_container_width=True,
        height=560,
        column_config={
            "score": st.column_config.ProgressColumn("score", min_value=0, max_value=100, format="%.0f"),
            "title": st.column_config.TextColumn("title", width="large"),
            "category_name": "category",
            "published_at": "date",
            "resolved_url": st.column_config.LinkColumn("link", display_text="open ↗"),
        },
    )


FILE_HELP = {
    "harvest": "articles found",
    "extract": "full texts",
    "score": "all ranked articles",
    "select": "report selection",
    "report": "HTML report",
}


def _files_tab(run_dir: Path) -> None:
    st.caption(f"`{run_dir}` — CSV files are UTF-8 with commas as separators")
    cols = st.columns(2)
    for i, stage in enumerate(STAGES):
        p = run_dir / OUTPUTS[stage]
        if p.exists():
            mime = "text/html" if p.suffix == ".html" else "text/csv"
            label = f"{p.name} — {FILE_HELP[stage]}"
            cols[i % len(cols)].download_button(label, p.read_bytes(), file_name=p.name, mime=mime, key=f"dl_{run_dir.name}_{stage}")


def render() -> None:
    section_header("/results/", "ranked articles of a run")
    cfg = load_selected()
    if cfg is None:
        return
    name, _ = selected_project()
    runs = list_runs(cfg)
    if not runs:
        empty_state("⏳", "No run yet for this project. Launch one on the /run/ page.")
        return

    job = job_manager().get(name)
    running_dir = job.run_dir if job and job.running else None
    run_dir = st.selectbox("run", runs, format_func=lambda p: _run_label(p, running_dir))

    scored = read(run_dir, "score")
    selection = read(run_dir, "select")
    if scored.empty or selection.empty:
        empty_state("⏳", "This run has not been ranked yet. Resume it on the /run/ page.")
        return

    harvest = read(run_dir, "harvest")
    articles = read(run_dir, "extract")
    meta = run_meta(run_dir)
    extracted = int((articles["extraction_status"] == "ok").sum()) if len(articles) else 0
    metric_row(
        [
            ("queries", meta.get("stats", {}).get("seeds", harvest["seed"].nunique() if len(harvest) else 0), "searched"),
            ("found", len(harvest), "unique articles"),
            ("read", extracted, f"{extracted / max(len(articles), 1):.0%} full texts"),
            ("ranked", len(scored), "scored articles"),
            ("top", int((selection["tier"] == "top").sum()), "selected stories"),
        ]
    )
    st.markdown("")

    top_tab, table_tab, report_tab, files_tab = st.tabs(["top stories", "all articles", "report", "files"])
    with top_tab:
        _top_tab(selection)
    with table_tab:
        _table_tab(scored, name)
    with report_tab:
        report = run_dir / OUTPUTS["report"]
        if report.exists():
            html = report.read_text(encoding="utf-8")
            st.download_button(
                "download report",
                html.encode("utf-8"),
                file_name=export_name(name, run_dir),
                mime="text/html",
                type="primary",
                help="Self-contained HTML file: opens in any browser, can be sent by e-mail.",
            )
            components.html(html, height=1000, scrolling=True)
        else:
            empty_state("📄", "The report has not been generated yet.")
    with files_tab:
        _files_tab(run_dir)
