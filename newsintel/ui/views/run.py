"""Run page: launch the pipeline in the background and follow it live."""

from __future__ import annotations

import streamlit as st

from newsintel.config import CHANNELS
from newsintel.pipeline import STAGES, new_run_dir
from newsintel.project import list_runs, run_progress
from newsintel.ui.components import job_manager, load_selected, section_header, selected_project, stage_pills
from newsintel.ui.jobs import tail

MODES = {
    "new": "new run",
    "resume": "resume latest run",
    "from": "re-run from a stage",
}


def _launch_form(cfg, name: str, config_path) -> None:
    runs = list_runs(cfg)
    modes = list(MODES) if runs else ["new"]
    mode = st.radio("mode", modes, format_func=MODES.get, horizontal=True, label_visibility="collapsed")

    from_stage = None
    if mode == "from":
        from_stage = st.selectbox(
            "re-run from",
            STAGES,
            index=STAGES.index("score"),
            help="This stage and the following ones are re-run on the latest run. "
            "'score' re-ranks without downloading anything.",
        )
    if mode != "new":
        st.caption(f"on run `{runs[0].name}`")

    c1, c2, c3 = st.columns(3)
    sample = c1.number_input("queries to use", min_value=0, value=0, help="0 = all; a few are enough for a test.")
    days = c2.number_input("days back", min_value=1, max_value=365, value=cfg.harvest.days)
    engines = ["playwright", "requests"]
    engine = c3.radio("text extraction", engines, index=engines.index(cfg.extraction.engine), horizontal=True)
    available = list(CHANNELS) + [s.name for s in cfg.harvest.brave.site_channels]
    channels = st.multiselect("channels", available, default=cfg.harvest.channels)

    if st.button("launch", type="primary", disabled=not channels):
        options = []
        if sample:
            options += ["--sample", str(sample)]
        if days != cfg.harvest.days:
            options += ["--days", str(days)]
        if engine != cfg.extraction.engine:
            options += ["--engine", engine]
        if channels != cfg.harvest.channels:
            options += ["--channels", ",".join(channels)]
        if from_stage:
            options += ["--from", from_stage]
        run_dir = new_run_dir(cfg) if mode == "new" else runs[0]
        try:
            job_manager().start(name, config_path, run_dir, options)
        except RuntimeError as e:
            st.error(str(e))
            return
        st.rerun()


def _job_panel(name: str) -> None:
    job = job_manager().get(name)
    if job is None:
        return
    running = job.running
    st.markdown(f"## run {job.run_dir.name}")
    stage_pills(run_progress(job.run_dir), running=running, failed=not running and job.returncode != 0)
    st.code(tail(job.log_path) or "starting…", language=None)

    flag = f"_was_running_{name}"
    if running:
        st.session_state[flag] = True
        if st.button("stop", key=f"stop_{name}"):
            job_manager().stop(name)
            st.rerun(scope="app")
    else:
        if st.session_state.pop(flag, False):
            st.rerun(scope="app")  # leave live mode now that the run is over
        if job.returncode == 0:
            st.success("Run finished — open /results/ to browse the articles.")
        else:
            st.error(f"Run stopped (exit code {job.returncode}). See the log above; launch again to resume.")


def render() -> None:
    section_header("/run/", "harvest, read and rank the news")
    cfg = load_selected()
    if cfg is None:
        return
    name, config_path = selected_project()
    job = job_manager().get(name)
    running = bool(job and job.running)

    if running:
        st.info(f"A run of **{name}** is in progress. You can leave this page: it keeps running.")
    else:
        _launch_form(cfg, name, config_path)

    st.fragment(run_every=2.0 if running else None)(_job_panel)(name)
