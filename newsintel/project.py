"""Project helpers shared by the CLI and the UI: scaffold, list, check, runs."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from newsintel.config import Config, config_base_dir, parse_config_text
from newsintel.data import load_seeds
from newsintel.pipeline import OUTPUTS, STAGES

CONFIG_TEMPLATE = """\
# newsintel project configuration — see README.md for every option.
project:
  name: {name}
  title: {title}
  # Plain-language description of the topic: drives the relevance score.
  description: {description}

seeds:
  file: inputs/seeds_{name}.csv   # one search query per row (column 'query')

# Optional: terms whose frequency boosts relevance.
keywords: []

# Optional: themes to classify articles into. Description = a few sentences or
# a list of characteristic terms; the more specific, the better.
categories:
  - id: "1"
    name: First theme
    description: Words and phrases that characterise articles about the first theme.
  - id: "2"
    name: Second theme
    description: Words and phrases that characterise articles about the second theme.

# Optional: tags detected by regular expression (case-insensitive).
entities: {{}}

harvest:
  channels: [google_news]        # + brave_news, brave_web (need BRAVE_API_KEY)
  days: 20

selection:
  top_n: 20
  next_n: 50
"""


def slugify(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.strip().lower()).strip("_")


def scaffold(
    name: str, title: str | None = None, root: Path = Path("."), force: bool = False, description: str | None = None
) -> tuple[Path, Path]:
    """Create configs/<name>.yaml and inputs/seeds_<name>.csv from the template."""
    name = slugify(name)
    if not name:
        raise ValueError("Project name is empty")
    config_path = root / "configs" / f"{name}.yaml"
    seeds_path = root / "inputs" / f"seeds_{name}.csv"
    for p in (config_path, seeds_path):
        if p.exists() and not force:
            raise FileExistsError(f"{p} already exists (use --force to overwrite)")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    seeds_path.parent.mkdir(parents=True, exist_ok=True)
    title = title or name.replace("_", " ").title()
    description = description or "Describe the topic you want to monitor in two or three sentences."
    # JSON strings are valid double-quoted YAML scalars: safe for any user text.
    text = CONFIG_TEMPLATE.format(name=name, title=json.dumps(title), description=json.dumps(description.strip()))
    config_path.write_text(text, encoding="utf-8")
    seeds_path.write_text("query\nfirst search query\nsecond search query\n", encoding="utf-8")
    return config_path, seeds_path


class _IndentedDumper(yaml.SafeDumper):
    """Indent lists under their key (`key:\n  - item`), like the shipped configs."""

    def increase_indent(self, flow: bool = False, indentless: bool = False):
        return super().increase_indent(flow, False)


def replace_section(text: str, key: str, value) -> str:
    """Rewrite one top-level YAML section in place. Every other line —
    comments included — is kept as is; the section is appended if missing."""
    block = yaml.dump({key: value}, Dumper=_IndentedDumper, sort_keys=False, allow_unicode=True, width=4096)
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if re.match(rf"{re.escape(key)}\s*:", line)), None)
    if start is None:
        return text.rstrip("\n") + "\n\n" + block
    last = start
    for j in range(start + 1, len(lines)):
        line = lines[j]
        if not line.strip() or line.startswith("#"):
            continue  # blank lines and comments may sit between list items
        if line[0] in " \t-":
            last = j
        else:
            break  # next top-level key
    return "".join(lines[:start]) + block + "".join(lines[last + 1 :])


def update_config(path: Path, changes: dict) -> Config:
    """Replace top-level sections of a YAML config after checking that the
    result is valid. Raises ConfigError and leaves the file untouched if not."""
    text = path.read_text(encoding="utf-8")
    for key, value in changes.items():
        text = replace_section(text, key, value)
    cfg = parse_config_text(text, config_base_dir(path), source=str(path))
    path.write_text(text, encoding="utf-8")
    return cfg


def list_projects(root: Path = Path(".")) -> list[Path]:
    return sorted((root / "configs").glob("*.yaml"))


@dataclass
class Check:
    seeds: int
    warnings: list[str]


def check(cfg: Config) -> Check:
    """Count seeds and list what is missing in the environment."""
    s = cfg.seeds
    seeds = load_seeds(cfg.resolve_path(s.file) if s.file else None, s.column, s.queries, s.limit)
    warnings = []
    if not seeds:
        warnings.append("No search query: add some to the seeds file")
    if not os.environ.get("BRAVE_API_KEY"):
        brave_channels = [c for c in cfg.harvest.channels if c != "google_news"]
        if brave_channels:
            warnings.append(f"BRAVE_API_KEY not set: channel(s) {', '.join(brave_channels)} will be skipped")
    if cfg.extraction.engine == "playwright":
        try:
            import playwright  # noqa: F401
        except ImportError:
            warnings.append("playwright not installed (pip install playwright && playwright install chromium)")
    return Check(seeds=len(seeds), warnings=warnings)


def list_runs(cfg: Config) -> list[Path]:
    """Run directories of a project, most recent first."""
    root = cfg.resolve_path(cfg.output_dir) / cfg.project.name
    return sorted((p for p in root.glob("*") if p.is_dir()), reverse=True) if root.exists() else []


def run_progress(run_dir: Path) -> dict[str, bool]:
    """Which stages already produced their output."""
    return {stage: (run_dir / OUTPUTS[stage]).exists() for stage in STAGES}


def run_meta(run_dir: Path) -> dict:
    p = run_dir / "run.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except json.JSONDecodeError:  # being written
        return {}

