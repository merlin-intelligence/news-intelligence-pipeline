from pathlib import Path

import pytest

from newsintel.project import CONFIG_TEMPLATE
from newsintel.config import ConfigError, config_from_dict, load_config, parse_config_text

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", ["ai_regulation"])
def test_shipped_configs_load(name):
    cfg = load_config(ROOT / "configs" / f"{name}.yaml")
    assert cfg.project.name == name
    assert cfg.categories
    assert cfg.resolve_path(cfg.seeds.file).exists()


def test_site_channels_are_valid_channels():
    cfg = load_config(ROOT / "configs" / "ai_regulation.yaml")
    assert {s.name for s in cfg.harvest.brave.site_channels} == {"linkedin_pulse", "linkedin_posts"}


def test_unknown_keys_are_rejected():
    with pytest.raises(ConfigError, match="harvest"):
        config_from_dict({"seeds": {"queries": ["x"]}, "harvest": {"chanels": ["google_news"]}})
    with pytest.raises(ConfigError, match="sedes: unknown key"):
        config_from_dict({"seeds": {"queries": ["x"]}, "sedes": {}})


def test_unknown_channel_is_rejected():
    with pytest.raises(ConfigError, match="channel"):
        config_from_dict({"seeds": {"queries": ["x"]}, "harvest": {"channels": ["twitter"]}})


def test_partial_weights_are_merged_with_defaults():
    cfg = config_from_dict({"seeds": {"queries": ["x"]}, "scoring": {"weights": {"centrality": 0}}})
    assert cfg.scoring.weights["centrality"] == 0
    assert cfg.scoring.weights["novelty"] == 0.25


def test_seeds_are_required():
    with pytest.raises(ConfigError, match="seeds"):
        config_from_dict({})


def test_init_template_is_a_valid_config(tmp_path):
    import yaml

    data = yaml.safe_load(CONFIG_TEMPLATE.format(name="demo", title='"Demo"', description='"A: tricky \\"topic\\""'))
    cfg = config_from_dict(data, base_dir=tmp_path)
    assert cfg.project.name == "demo" and len(cfg.categories) == 2


def test_selection_method_is_validated():
    with pytest.raises(ConfigError, match="selection.method"):
        config_from_dict({"seeds": {"queries": ["x"]}, "selection": {"method": "random"}})


def test_errors_point_to_the_yaml_line():
    text = "seeds:\n  queries: [a]\nharvest:\n  days: 0\nextraction:\n  engine: chrome\n"
    with pytest.raises(ConfigError) as e:
        parse_config_text(text, source="configs/x.yaml")
    msg = str(e.value)
    assert msg.startswith("configs/x.yaml: invalid configuration")
    assert "line 4, harvest.days" in msg and "line 6, extraction.engine" in msg


def test_invalid_regex_and_duplicate_ids_are_rejected():
    with pytest.raises(ConfigError, match="invalid regular expression"):
        config_from_dict({"seeds": {"queries": ["x"]}, "entities": {"A": ["(unclosed"]}})
    with pytest.raises(ConfigError, match="duplicate category id"):
        config_from_dict(
            {"seeds": {"queries": ["x"]}, "categories": [{"name": "A", "description": "a"}, {"id": 1, "name": "B", "description": "b"}]}
        )


def test_invalid_yaml_is_reported():
    with pytest.raises(ConfigError, match="invalid YAML"):
        parse_config_text("project: [unclosed")
