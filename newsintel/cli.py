"""Command-line entry point: `python -m newsintel <command>` (or `newsintel <command>` once installed)."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from newsintel import __version__
from newsintel.config import ConfigError, load_config, load_dotenv
from newsintel.pipeline import STAGES, Pipeline, export_report, latest_run_dir, new_run_dir

log = logging.getLogger("newsintel")

# Streamlit widget theme matching the CogMaps palette (see newsintel/ui/styles.py).
UI_THEME = {
    "base": "light",
    "primaryColor": "#c44a28",
    "backgroundColor": "#f2ede6",
    "secondaryBackgroundColor": "#ece6de",
    "textColor": "#2a1f18",
}


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    for noisy in ("urllib3", "asyncio", "trafilatura", "htmldate", "courlan"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def cmd_run(args) -> int:
    cfg = load_config(args.config)
    if args.engine:
        cfg.extraction.engine = args.engine
    if args.days:
        cfg.harvest.days = args.days
    if args.run_dir:
        run_dir = Path(args.run_dir)
    elif args.resume or args.from_stage:
        run_dir = latest_run_dir(cfg)
        if run_dir is None:
            log.error("No previous run to resume for project '%s'", cfg.project.name)
            return 1
    else:
        run_dir = new_run_dir(cfg)
    channels = [c.strip() for c in args.channels.split(",")] if args.channels else None
    log.info("Project '%s' → %s", cfg.project.name, run_dir)
    Pipeline(cfg, run_dir, sample=args.sample, channels=channels).run(args.from_stage, args.to_stage, args.force)
    if args.export is not None:
        dest = Path(args.export).expanduser() if args.export else run_dir
        target = export_report(run_dir, cfg.project.name, dest)
        log.info("Report exported → %s", target)
    return 0


def cmd_validate(args) -> int:
    from newsintel.project import check

    cfg = load_config(args.config)
    result = check(cfg)
    print(f"✔ config OK: project '{cfg.project.name}'")
    print(f"  seeds: {result.seeds}   categories: {len(cfg.categories)}   entity tags: {len(cfg.entities)}")
    print(f"  channels: {', '.join(cfg.harvest.channels)}   extraction: {cfg.extraction.engine}")
    for w in result.warnings:
        print(f"  ⚠ {w}")
    return 0


def cmd_init(args) -> int:
    from newsintel.project import scaffold

    try:
        config_path, seeds_path = scaffold(args.name, args.title, force=args.force)
    except FileExistsError as e:
        log.error("%s", e)
        return 1
    print(f"Created {config_path} and {seeds_path}. Edit them, then run:\n  python -m newsintel run -c {config_path}")
    return 0


def cmd_ui(args) -> int:
    import subprocess

    try:
        import streamlit  # noqa: F401
    except ImportError:
        log.error('The UI needs Streamlit: pip install -e ".[ui]"')
        return 1
    app = Path(__file__).parent / "ui" / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app), "--server.port", str(args.port), "--client.toolbarMode", "minimal"]
    cmd += [f"--theme.{k}={v}" for k, v in UI_THEME.items()]
    if args.headless:
        cmd += ["--server.headless", "true"]
    # Projects (configs/, inputs/) and runs are read from the current directory.
    return subprocess.call(cmd, env={**os.environ, "NEWSINTEL_ROOT": str(Path.cwd())})


def cmd_graph(args) -> int:
    from newsintel.graph import analyze

    csv_path, md_path = analyze(Path(args.adjacency), Path(args.out), args.thresholds, args.theta_k)
    print(f"Wrote {csv_path} and {md_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="newsintel", description="Topic-agnostic news harvesting, ranking and reporting.")
    p.add_argument("--version", action="version", version=f"newsintel {__version__}")
    p.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("run", help="run the pipeline (harvest → resolve → extract → score → select → report)")
    r.add_argument("-c", "--config", required=True, help="project YAML config")
    r.add_argument("--run-dir", help="run directory (default: runs/<project>/<timestamp>)")
    r.add_argument("--resume", action="store_true", help="continue the latest run of this project")
    r.add_argument("--from", dest="from_stage", choices=STAGES, help="re-run this stage and the following ones (on the latest run unless --run-dir)")
    r.add_argument("--to", dest="to_stage", choices=STAGES, default="report", help="stop after this stage")
    r.add_argument("--force", action="store_true", help="re-run every stage even if its output exists")
    r.add_argument("--sample", type=int, help="only use the first N seeds (quick test)")
    r.add_argument("--channels", help="override harvest channels, comma-separated")
    r.add_argument("--engine", choices=["playwright", "requests"], help="override extraction engine")
    r.add_argument("--days", type=int, help="override harvest window in days")
    r.add_argument(
        "--export",
        nargs="?",
        const="",
        metavar="DIR",
        help="also save the report as <project>_<date>.html, in the run directory or in DIR",
    )
    r.set_defaults(func=cmd_run)

    v = sub.add_parser("validate", help="check a config, its seeds and the environment")
    v.add_argument("-c", "--config", required=True)
    v.set_defaults(func=cmd_validate)

    i = sub.add_parser("init", help="scaffold configs/<name>.yaml and inputs/seeds_<name>.csv")
    i.add_argument("name")
    i.add_argument("--title")
    i.add_argument("--force", action="store_true")
    i.set_defaults(func=cmd_init)

    u = sub.add_parser("ui", help="open the web interface (Streamlit)")
    u.add_argument("--port", type=int, default=8501)
    u.add_argument("--headless", action="store_true", help="do not open a browser")
    u.set_defaults(func=cmd_ui)

    g = sub.add_parser("graph", help="analyse a concept adjacency matrix with eigenmind (hinges, diverse subsets)")
    g.add_argument("adjacency", help="square CSV, node names in first row and column")
    g.add_argument("--out", default="runs/graph", help="output directory")
    g.add_argument("--thresholds", type=float, nargs="+", default=[0.5, 0.7])
    g.add_argument("--theta-k", type=int, default=10, help="size of the θ-diverse subset (0 to skip)")
    g.set_defaults(func=cmd_graph)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _setup_logging(args.verbose)
    load_dotenv()
    try:
        return args.func(args)
    except (ConfigError, FileNotFoundError, ValueError) as e:
        log.error("%s", e)
        return 1
    except KeyboardInterrupt:
        log.warning("Interrupted — re-run with --resume to continue")
        return 130


if __name__ == "__main__":
    sys.exit(main())
