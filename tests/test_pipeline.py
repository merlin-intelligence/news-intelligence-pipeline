import json

import pytest

from newsintel.cli import main
from newsintel.data import read_csv, write_csv
from newsintel.pipeline import Pipeline


def test_pipeline_from_extracted_articles_to_report(articles, cfg, tmp_path):
    run_dir = tmp_path / "run"
    articles["title"] = "<script>alert(1)</script> " + articles["title"]
    write_csv(articles, run_dir / "articles.csv")
    write_csv(articles.drop(columns=["text", "extraction_status", "extraction_error"]), run_dir / "harvest.csv")

    report = Pipeline(cfg, run_dir).run()
    html = report.read_text(encoding="utf-8")
    assert "<script>alert" not in html and "&lt;script&gt;" in html
    assert "Infrastructure watch" in html
    assert len(read_csv(run_dir / "selection.csv")) > 0
    meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert set(meta["timings"]) == {"score", "select", "report"}


def test_full_texts_stay_in_articles_csv(articles, cfg, tmp_path):
    run_dir = tmp_path / "run"
    write_csv(articles, run_dir / "articles.csv")
    write_csv(articles.drop(columns=["text", "extraction_status", "extraction_error"]), run_dir / "harvest.csv")
    Pipeline(cfg, run_dir).run()
    for name in ("scored.csv", "selection.csv"):
        df = read_csv(run_dir / name)
        assert "text" not in df.columns and "summary" in df.columns
    assert "text" in read_csv(run_dir / "articles.csv").columns
    # UTF-8 BOM so that Excel reads accents correctly; read_csv strips it
    assert (run_dir / "scored.csv").read_bytes().startswith(b"\xef\xbb\xbf")
    assert read_csv(run_dir / "scored.csv").columns[0] == "article_id"
    # selection still drops the near-duplicate even though scored.csv has no text
    assert not {"Rail story 0", "Rail story copy"} <= set(read_csv(run_dir / "selection.csv")["title"])


def test_cli_export_copies_the_report(articles, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "demo"]) == 0
    run_dir = tmp_path / "runs" / "demo" / "20261011-183500"
    write_csv(articles, run_dir / "articles.csv")
    write_csv(articles.drop(columns=["text", "extraction_status", "extraction_error"]), run_dir / "harvest.csv")
    assert main(["run", "-c", "configs/demo.yaml", "--run-dir", str(run_dir), "--export", "out"]) == 0
    exported = tmp_path / "out" / "demo_2026-10-11_1835.html"
    assert exported.read_bytes() == (run_dir / "report.html").read_bytes()
    # without DIR: next to the run's own files
    assert main(["run", "-c", "configs/demo.yaml", "--run-dir", str(run_dir), "--export"]) == 0
    assert (run_dir / "demo_2026-10-11_1835.html").exists()


def test_pipeline_from_stage_requires_previous_outputs(cfg, tmp_path):
    with pytest.raises(FileNotFoundError, match="missing"):
        Pipeline(cfg, tmp_path / "empty").run(from_stage="score")


def test_cli_init_and_validate(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "city_transport"]) == 0
    assert (tmp_path / "configs" / "city_transport.yaml").exists()
    assert main(["init", "city_transport"]) == 1  # refuses to overwrite
    assert main(["validate", "-c", "configs/city_transport.yaml"]) == 0
    assert "seeds: 2" in capsys.readouterr().out
