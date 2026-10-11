"""Projects page: create a topic, edit its search queries, categories and YAML config.

Editor widgets are keyed on the file's modification time, so saving from one
tab reloads the others instead of leaving them on stale content.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from newsintel.config import ConfigError, parse_config_text
from newsintel.data import SEED_COLUMN_CANDIDATES
from newsintel.project import check, scaffold, slugify, update_config
from newsintel.ui.components import ROOT, load_selected, metric_row, projects, section_header, selected_project


def _new_project_form() -> None:
    with st.expander("+ new project", expanded=not projects()):
        with st.form("new_project", clear_on_submit=True):
            name = st.text_input("name", placeholder="urban_cycling", help="Lowercase identifier, used for file names.")
            title = st.text_input("report title", placeholder="Urban Cycling Watch")
            description = st.text_area(
                "topic description",
                placeholder="Two or three sentences describing what you want to follow. It drives the relevance score.",
            )
            if st.form_submit_button("create", type="primary"):
                try:
                    config_path, _ = scaffold(name, title or None, ROOT, description=description or None)
                except (FileExistsError, ValueError) as e:
                    st.error(str(e))
                else:
                    st.session_state["_select_project"] = config_path.stem
                    st.rerun()


def _seed_column(df: pd.DataFrame, column: str | None) -> str:
    if column:
        return column
    lower = {c.lower(): c for c in df.columns}
    return next((lower[c] for c in SEED_COLUMN_CANDIDATES if c in lower), df.columns[0])


def _seeds_tab(cfg, name: str) -> None:
    if not cfg.seeds.file:
        st.info("This project lists its queries in the configuration (seeds.queries).")
        return
    path = cfg.resolve_path(cfg.seeds.file)
    st.caption(f"`{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}` — one search query per row")
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig") if path.exists() else pd.DataFrame({"query": []})
    col = _seed_column(df, cfg.seeds.column)
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"seeds_{name}_{path.stat().st_mtime_ns if path.exists() else 0}",
        column_config={col: st.column_config.TextColumn(col, width="large", required=True)},
    )
    if st.button("save queries", type="primary", key=f"save_seeds_{name}"):
        edited = edited.fillna("")
        edited = edited[edited[col].str.strip() != ""]
        path.parent.mkdir(parents=True, exist_ok=True)
        edited.to_csv(path, index=False, encoding="utf-8-sig")
        st.success(f"Saved {len(edited)} queries.")


def _categories_tab(cfg, name: str, path) -> None:
    st.caption(
        "Each article goes to the closest category. Describe a category with the words and phrases "
        "its articles typically contain: the more specific, the better. Leave the id empty to derive it from the name."
    )
    df = pd.DataFrame([c.model_dump() for c in cfg.categories], columns=["id", "name", "description"])
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"categories_{name}_{path.stat().st_mtime_ns}",
        column_config={
            "id": st.column_config.TextColumn("id", width="small"),
            "name": st.column_config.TextColumn("name", width="medium", required=True),
            "description": st.column_config.TextColumn("description", width="large", required=True),
        },
    )
    if st.button("save categories", type="primary", key=f"save_categories_{name}"):
        rows = []
        for r in edited.fillna("").to_dict("records"):
            if not str(r["name"]).strip():
                continue
            rows.append(
                {
                    "id": str(r["id"]).strip() or slugify(r["name"]),
                    "name": str(r["name"]).strip(),
                    "description": str(r["description"]).strip(),
                }
            )
        try:
            update_config(path, {"categories": rows})
        except ConfigError as e:
            st.error("Not saved.")
            st.code(str(e), language=None)
            return
        st.toast(f"Saved {len(rows)} categories. Re-rank a run (/run/ → re-run from 'score') to apply them.")
        st.rerun()


def _config_tab(cfg, name: str, path) -> None:
    st.caption(f"`configs/{path.name}` — every option is documented in the README")
    text = st.text_area("configuration", path.read_text(encoding="utf-8"), height=560, key=f"yaml_{name}_{path.stat().st_mtime_ns}", label_visibility="collapsed")
    if st.button("save configuration", type="primary", key=f"save_yaml_{name}"):
        try:
            new_cfg = parse_config_text(text, cfg.base_dir, source=f"configs/{path.name}")
        except ConfigError as e:
            st.error("Not saved.")
            st.code(str(e), language=None)
            return
        if new_cfg.project.name != cfg.project.name:
            st.warning("project.name changed: earlier runs stay under the old name in runs/.")
        path.write_text(text, encoding="utf-8")
        st.toast("Configuration saved.")
        st.rerun()


def render() -> None:
    section_header("/projects/", "watch topics, queries and settings")
    _new_project_form()
    cfg = load_selected()
    if cfg is None:
        return
    name, path = selected_project()

    try:
        result = check(cfg)
    except (FileNotFoundError, ValueError) as e:
        st.error(str(e))
        result = None
    st.markdown(f"### {cfg.project.title}")
    if cfg.project.description:
        st.caption(cfg.project.description)
    metric_row(
        [
            ("queries", result.seeds if result else "—", "search queries"),
            ("categories", len(cfg.categories), "classification themes"),
            ("channels", len(cfg.harvest.channels), ", ".join(cfg.harvest.channels)),
            ("window", f"{cfg.harvest.days}d", "harvest period"),
        ]
    )
    for w in result.warnings if result else []:
        st.warning(w)

    seeds_tab, categories_tab, config_tab = st.tabs(["queries", "categories", "configuration"])
    with seeds_tab:
        _seeds_tab(cfg, name)
    with categories_tab:
        _categories_tab(cfg, name, path)
    with config_tab:
        _config_tab(cfg, name, path)
