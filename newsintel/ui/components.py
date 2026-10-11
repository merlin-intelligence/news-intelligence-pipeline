"""Reusable UI pieces: page helpers, shared sidebar, job manager, stage pills."""

from __future__ import annotations

import os
from html import escape
from pathlib import Path

import streamlit as st

from newsintel.config import Config, ConfigError, load_config
from newsintel.pipeline import STAGES
from newsintel.project import list_projects
from newsintel.ui.jobs import JobManager

ROOT = Path(os.environ.get("NEWSINTEL_ROOT", Path.cwd())).resolve()


@st.cache_resource
def job_manager() -> JobManager:
    return JobManager(ROOT)


# --- small HTML helpers (same markup as CogMaps) ---------------------------


def section_header(title: str, tag: str) -> None:
    st.markdown(
        f'<div class="section-header"><span class="title">{escape(title)}</span>'
        f'<span class="tag">→ {escape(tag)}</span></div>',
        unsafe_allow_html=True,
    )


def empty_state(icon: str, message: str) -> None:
    st.markdown(f'<div class="empty-state"><span class="icon">{icon}</span>{escape(message)}</div>', unsafe_allow_html=True)


def info_box(html: str) -> None:
    st.markdown(f'<div class="info-box">{html}</div>', unsafe_allow_html=True)


def metric_card(label: str, value, sub: str = "") -> str:
    return (
        f'<div class="metric-card"><div class="label">{escape(label)}</div>'
        f'<div class="value">{escape(str(value))}</div><div class="sub">{escape(sub)}</div></div>'
    )


def metric_row(items: list[tuple[str, object, str]]) -> None:
    for col, (label, value, sub) in zip(st.columns(len(items)), items):
        col.markdown(metric_card(label, value, sub), unsafe_allow_html=True)


def badge(text: str, variant: str = "sim") -> str:
    return f'<span class="badge badge-{variant}">{escape(str(text))}</span>'


def pill(text: str, ok: bool) -> str:
    return f'<span class="status-pill {"online" if ok else "offline"}">{escape(text)}</span>'


def stage_pills(done: dict[str, bool], running: bool = False, failed: bool = False) -> None:
    current = next((s for s in STAGES if not done.get(s)), None)
    parts = []
    for s in STAGES:
        cls = "done" if done.get(s) else ("running" if running and s == current else ("failed" if failed and s == current else ""))
        parts.append(f'<span class="stage {cls}">{s}</span>')
    st.markdown(f'<div class="stage-row">{"".join(parts)}</div>', unsafe_allow_html=True)


# --- project selection (shared across pages through session state) ---------


def projects() -> dict[str, Path]:
    return {p.stem: p for p in list_projects(ROOT)}


def selected_project() -> tuple[str | None, Path | None]:
    name = st.session_state.get("project")
    path = projects().get(name) if name else None
    return (name, path) if path else (None, None)


def load_selected() -> Config | None:
    """Load the selected project's config, or explain why it cannot be."""
    name, path = selected_project()
    if not path:
        empty_state("📂", "No project yet. Create one on the /projects/ page.")
        return None
    try:
        return load_config(path)
    except (ConfigError, ValueError) as e:
        st.error(f"configs/{path.name} is invalid: {e}")
        return None


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<p class="sidebar-label">⬡ project</p>', unsafe_allow_html=True)
        names = list(projects())
        if "_select_project" in st.session_state:  # set by a page before a rerun
            st.session_state["project"] = st.session_state.pop("_select_project")
        if names:
            if st.session_state.get("project") not in names:
                st.session_state["project"] = names[0]
            st.selectbox("project", names, key="project", label_visibility="collapsed")
        else:
            st.caption("no project yet")

        st.markdown("---")
        st.markdown('<p class="sidebar-label">⚙ environment</p>', unsafe_allow_html=True)
        try:
            import playwright  # noqa: F401

            has_playwright = True
        except ImportError:
            has_playwright = False
        st.markdown(
            pill("brave key", bool(os.environ.get("BRAVE_API_KEY"))) + pill("playwright", has_playwright),
            unsafe_allow_html=True,
        )
        running = job_manager().running()
        if running:
            st.markdown("---")
            st.markdown('<p class="sidebar-label">▶ running</p>', unsafe_allow_html=True)
            for job in running:
                st.caption(f"{job.project} · {job.run_dir.name}")
