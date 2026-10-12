"""Project configuration: one YAML file describes one watch topic.

Everything topic-specific (seeds, categories, entity tags, report wording) lives
in the config file, never in the code. The schema is a set of Pydantic models:
unknown keys, wrong types and invalid values are rejected, and errors point to
the YAML line when the config comes from a file.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationError, field_validator, model_validator

CHANNELS = ("google_news", "brave_news", "brave_web")
DEFAULT_WEIGHTS = {"relevance": 0.20, "category_match": 0.35, "novelty": 0.25, "centrality": 0.20, "hinge": 0.0}


class Section(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Category(Section):
    id: str
    name: str
    description: str

    @field_validator("id", mode="before")
    @classmethod
    def _id_as_text(cls, v: Any) -> str:
        return str(v)


class SiteChannel(Section):
    """A Brave web search restricted to one site, e.g. LinkedIn articles."""

    name: str
    site: str


class ProjectConfig(Section):
    name: str = "my_topic"
    title: str = "News Intelligence Report"
    description: str = ""


class SeedsConfig(Section):
    file: str | None = None
    column: str | None = None
    queries: list[str] = Field(default_factory=list)
    limit: int | None = Field(default=None, ge=1)


class GoogleNewsConfig(Section):
    language: str = "en"
    country: str = "US"


class BraveConfig(Section):
    count: int = Field(default=5, ge=1, le=20)
    site_channels: list[SiteChannel] = Field(default_factory=list)


class HarvestConfig(Section):
    channels: list[str] = Field(default_factory=lambda: ["google_news"], min_length=1)
    days: int = Field(default=20, ge=1)
    max_results_per_seed: int = Field(default=20, ge=1)
    request_delay: float = Field(default=0.2, ge=0)
    google_news: GoogleNewsConfig = Field(default_factory=GoogleNewsConfig)
    brave: BraveConfig = Field(default_factory=BraveConfig)

    @model_validator(mode="after")
    def _known_channels(self) -> HarvestConfig:
        sites = {s.name for s in self.brave.site_channels}
        bad = [c for c in self.channels if c not in CHANNELS and c not in sites]
        if bad:
            raise ValueError(
                f"unknown channel(s) {', '.join(bad)}; use {', '.join(CHANNELS)} "
                "or a name from harvest.brave.site_channels"
            )
        return self


class ResolveConfig(Section):
    enabled: bool = True


class ExtractionConfig(Section):
    engine: Literal["playwright", "requests"] = "playwright"
    workers: int = Field(default=8, ge=1)
    timeout: int = Field(default=20, ge=1)
    min_chars: int = Field(default=250, ge=0)
    checkpoint_every: int = Field(default=20, ge=1)


class ScoringConfig(Section):
    weights: dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    keyword_weight: float = Field(default=0.30, ge=0, le=1)
    graph_threshold: float = Field(default=0.22, ge=0, le=1)
    max_features: int = Field(default=5000, ge=100)
    stop_words: str | None = "english"  # scikit-learn stop-word list, or null
    require_text: bool = True  # drop articles whose full text could not be extracted

    @field_validator("weights", mode="before")
    @classmethod
    def _merge_default_weights(cls, v: Any) -> Any:
        """A partial `weights:` mapping only overrides the components it names."""
        if not isinstance(v, dict):
            return v
        unknown = set(v) - set(DEFAULT_WEIGHTS)
        if unknown:
            raise ValueError(f"unknown component(s) {', '.join(sorted(unknown))}; use {', '.join(DEFAULT_WEIGHTS)}")
        return {**DEFAULT_WEIGHTS, **v}

    @field_validator("weights")
    @classmethod
    def _some_weight_positive(cls, v: dict[str, float]) -> dict[str, float]:
        if any(w < 0 for w in v.values()):
            raise ValueError("weights cannot be negative")
        if sum(v.values()) <= 0:
            raise ValueError("at least one scoring weight must be positive")
        return v


class SelectionConfig(Section):
    top_n: int = Field(default=20, ge=1)
    next_n: int = Field(default=50, ge=0)
    ensure_category_coverage: bool = True
    max_pairwise_similarity: float = Field(default=0.80, gt=0, le=1)
    method: Literal["score", "theta"] = "score"  # theta: θ-diverse subset of the best articles
    theta_pool: int = Field(default=3, ge=1)  # theta: pick top_n among the top_n × theta_pool best articles
    theta_conflict_threshold: float = Field(default=0.30, gt=0, le=1)  # theta: similarity above which two articles overlap


class ReportConfig(Section):
    subtitle: str = ""
    sort_by: Literal["score", "date"] = "score"


class Config(Section):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    seeds: SeedsConfig = Field(default_factory=SeedsConfig)
    keywords: list[str] = Field(default_factory=list)
    categories: list[Category] = Field(default_factory=list)
    entities: dict[str, list[str]] = Field(default_factory=dict)
    harvest: HarvestConfig = Field(default_factory=HarvestConfig)
    resolve: ResolveConfig = Field(default_factory=ResolveConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    selection: SelectionConfig = Field(default_factory=SelectionConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)
    output_dir: str = "runs"
    _base_dir: Path = PrivateAttr(default=Path("."))  # relative paths are resolved from here

    @model_validator(mode="before")
    @classmethod
    def _default_category_ids(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("categories"), list):
            data = {**data, "categories": [
                {"id": str(i + 1), **c} if isinstance(c, dict) and "id" not in c else c
                for i, c in enumerate(data["categories"])
            ]}  # fmt: skip
        return data

    @field_validator("categories")
    @classmethod
    def _unique_ids(cls, v: list[Category]) -> list[Category]:
        ids = [c.id for c in v]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"duplicate category id(s) {', '.join(dupes)}")
        return v

    @field_validator("entities")
    @classmethod
    def _patterns_compile(cls, v: dict[str, list[str]]) -> dict[str, list[str]]:
        for label, patterns in v.items():
            for p in patterns:
                try:
                    re.compile(p)
                except re.error as e:
                    raise ValueError(f"'{label}': invalid regular expression {p!r} ({e})") from e
        return v

    @model_validator(mode="after")
    def _has_seeds(self) -> Config:
        if not self.seeds.file and not self.seeds.queries:
            raise ValueError("provide seeds.file or seeds.queries")
        return self

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def resolve_path(self, path: str | os.PathLike) -> Path:
        p = Path(path)
        return p if p.is_absolute() else (self._base_dir / p)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ConfigError(ValueError):
    pass


def _yaml_line(root: yaml.Node | None, loc: tuple) -> int | None:
    """1-based line of the deepest YAML node matching a Pydantic error location."""
    node, line = root, None
    for part in loc:
        if isinstance(node, yaml.MappingNode):
            nxt = next(((k, v) for k, v in node.value if k.value == str(part)), None)
            if nxt is None:
                break
            key, node = nxt
            line = key.start_mark.line + 1
        elif isinstance(node, yaml.SequenceNode) and isinstance(part, int) and part < len(node.value):
            node = node.value[part]
            line = node.start_mark.line + 1
        else:
            break
    return line


def _format_errors(e: ValidationError, source: str | None, root: yaml.Node | None) -> str:
    lines = []
    for err in e.errors():
        loc = err["loc"]
        where = ".".join(f"[{p}]" if isinstance(p, int) else str(p) for p in loc).replace(".[", "[") or "config"
        msg = err["msg"].removeprefix("Value error, ")
        if err["type"] == "extra_forbidden":
            msg = "unknown key"
        line = _yaml_line(root, loc) if root is not None and loc else None
        lines.append(f"  {f'line {line}, ' if line else ''}{where}: {msg}")
    head = f"{source}: invalid configuration" if source else "Invalid configuration"
    return head + "\n" + "\n".join(lines)


def config_from_dict(
    data: dict[str, Any], base_dir: Path = Path("."), source: str | None = None, root: yaml.Node | None = None
) -> Config:
    try:
        cfg = Config.model_validate(data or {})
    except ValidationError as e:
        raise ConfigError(_format_errors(e, source, root)) from None
    cfg._base_dir = Path(base_dir)
    return cfg


def parse_config_text(text: str, base_dir: Path = Path("."), source: str | None = None) -> Config:
    """Validate YAML text (e.g. from an editor) and return the Config."""
    try:
        root = yaml.compose(text)
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"{source or 'config'}: invalid YAML — {e}") from None
    if not isinstance(data, dict):
        raise ConfigError(f"{source or 'config'}: the top level must be a mapping of sections")
    return config_from_dict(data, base_dir, source, root)


def config_base_dir(path: Path) -> Path:
    """Relative paths are relative to the repository root when the config sits
    in configs/, otherwise to the config's own directory."""
    return (path.parent.parent if path.parent.name == "configs" else path.parent).resolve()


def load_config(path: str | os.PathLike) -> Config:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    return parse_config_text(path.read_text(encoding="utf-8"), config_base_dir(path), source=str(path))


def load_dotenv(path: str | os.PathLike = ".env") -> None:
    """Minimal .env loader: KEY=VALUE lines, existing env vars win."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
