import pytest
import yaml

from newsintel.config import load_config
from newsintel.project import check, list_projects, list_runs, run_progress, scaffold, slugify
from newsintel.ui.jobs import tail


def test_scaffold_quotes_user_text_safely(tmp_path):
    config_path, seeds_path = scaffold("Urban Cycling!", 'Bikes "now"', tmp_path, description="Lanes: policy & safety")
    assert config_path.name == "urban_cycling.yaml" and seeds_path.exists()
    cfg = load_config(config_path)
    assert cfg.project.title == 'Bikes "now"'
    assert cfg.project.description == "Lanes: policy & safety"
    assert check(cfg).seeds == 2
    with pytest.raises(FileExistsError):
        scaffold("urban_cycling", root=tmp_path)
    assert list_projects(tmp_path) == [config_path]


def test_slugify_rejects_empty_names(tmp_path):
    assert slugify(" Ça va? ") == "ça_va"
    with pytest.raises(ValueError):
        scaffold("  ", root=tmp_path)


def test_runs_and_progress(tmp_path):
    config_path, _ = scaffold("demo", root=tmp_path)
    cfg = load_config(config_path)
    assert list_runs(cfg) == []
    for name in ("20260101-000000", "20260102-000000"):
        (tmp_path / "runs" / "demo" / name).mkdir(parents=True)
    runs = list_runs(cfg)
    assert [r.name for r in runs] == ["20260102-000000", "20260101-000000"]
    (runs[0] / "harvest.csv").write_text("x\n")
    assert run_progress(runs[0]) == {"harvest": True, "extract": False, "score": False, "select": False, "report": False}


def test_tail(tmp_path):
    log = tmp_path / "run.log"
    log.write_text("\n".join(f"line {i}" for i in range(100)), encoding="utf-8")
    assert tail(log, 3) == "line 97\nline 98\nline 99"
    assert tail(tmp_path / "missing.log") == ""


def test_yaml_template_roundtrip(tmp_path):
    config_path, _ = scaffold("x", root=tmp_path)
    assert yaml.safe_load(config_path.read_text(encoding="utf-8"))["project"]["name"] == "x"


def test_update_config_keeps_comments_and_validates(tmp_path):
    from newsintel.config import ConfigError
    from newsintel.project import update_config

    config_path, _ = scaffold("demo", root=tmp_path)
    before = config_path.read_text(encoding="utf-8")
    cats = [{"id": "a", "name": "Alpha", "description": "first theme"}, {"id": "b", "name": "Beta", "description": "second"}]
    cfg = update_config(config_path, {"categories": cats})
    assert [c.name for c in cfg.categories] == ["Alpha", "Beta"]
    after = config_path.read_text(encoding="utf-8")
    assert "# Plain-language description of the topic" in after  # comments survive
    assert "# Optional: tags detected by regular expression" in after

    with pytest.raises(ConfigError, match="duplicate category id"):
        update_config(config_path, {"categories": cats + [{"id": "a", "name": "Again", "description": "x"}]})
    assert config_path.read_text(encoding="utf-8") == after  # untouched on error
    assert before != after


def test_replace_section_handles_comments_inside_and_missing_sections():
    from newsintel.project import replace_section

    text = "a: 1\ncategories:\n  - id: x\n# note between items\n  - id: y\n\n# about b\nb: 2\n"
    out = replace_section(text, "categories", [{"id": "z"}])
    assert out == "a: 1\ncategories:\n  - id: z\n\n# about b\nb: 2\n"
    assert replace_section("a: 1\n", "keywords", ["k"]) == "a: 1\n\nkeywords:\n  - k\n"
