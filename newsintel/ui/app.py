"""Streamlit entry point. Start it with `python -m newsintel ui`."""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit runs this file as a script: make the package importable when it is not installed.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st  # noqa: E402

from newsintel.config import load_dotenv  # noqa: E402
from newsintel.ui.components import ROOT, render_sidebar  # noqa: E402
from newsintel.ui.styles import apply_global_styles  # noqa: E402
from newsintel.ui.views import home, projects, results, run  # noqa: E402

load_dotenv(ROOT / ".env")

st.set_page_config(
    layout="wide",
    page_title="newsintel · signal from noise",
    page_icon="⬡",
    initial_sidebar_state="expanded",
)
apply_global_styles()

page = st.navigation(
    [
        st.Page(home.render, title="newsintel", icon=":material/newspaper:", url_path="home", default=True),
        st.Page(projects.render, title="/projects/", icon=":material/folder_open:", url_path="projects"),
        st.Page(run.render, title="/run/", icon=":material/play_arrow:", url_path="run"),
        st.Page(results.render, title="/results/", icon=":material/leaderboard:", url_path="results"),
    ]
)
render_sidebar()
page.run()
