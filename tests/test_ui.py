"""Render every UI page headlessly (Streamlit AppTest) on a project with a finished run."""

import shutil
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from newsintel.data import write_csv  # noqa: E402
from newsintel.pipeline import Pipeline  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

PAGE = """
from newsintel.ui.styles import apply_global_styles
from newsintel.ui.components import render_sidebar
from newsintel.ui.views import {view}
apply_global_styles()
render_sidebar()
{view}.render()
"""


@pytest.fixture(scope="module")
def workspace(tmp_path_factory):
    import newsintel.ui.components as components
    from tests.conftest import make_articles

    root = tmp_path_factory.mktemp("ws")
    shutil.copytree(ROOT / "configs", root / "configs")
    shutil.copytree(ROOT / "inputs", root / "inputs")
    from newsintel.config import load_config

    cfg = load_config(root / "configs" / "ai_regulation.yaml")
    run_dir = root / "runs" / "ai_regulation" / "20260101-000000"
    articles = make_articles()
    write_csv(articles, run_dir / "articles.csv")
    write_csv(articles.drop(columns=["text", "extraction_status", "extraction_error"]), run_dir / "harvest.csv")
    Pipeline(cfg, run_dir).run()
    components.ROOT = root  # pages read projects and runs from here
    return root


@pytest.mark.parametrize("view", ["home", "projects", "run", "results"])
def test_page_renders_without_error(workspace, view):
    at = AppTest.from_string(PAGE.format(view=view), default_timeout=30)
    at.session_state["project"] = "ai_regulation"
    at.run()
    assert not at.exception, at.exception


def test_results_page_shows_run_metrics(workspace):
    at = AppTest.from_string(PAGE.format(view="results"), default_timeout=30)
    at.session_state["project"] = "ai_regulation"
    at.run()
    html = " ".join(m.value for m in at.markdown)
    assert "story-card" in html and "metric-card" in html
