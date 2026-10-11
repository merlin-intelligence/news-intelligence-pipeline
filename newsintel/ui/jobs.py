"""Background pipeline runs.

Each run is a separate `python -m newsintel run` process whose output goes to
<run_dir>/run.log. A process keeps running if the browser tab is closed or the
page reruns; the manager is shared by all sessions (st.cache_resource).
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

LOG_NAME = "run.log"


@dataclass
class Job:
    project: str
    run_dir: Path
    cmd: list[str]
    proc: subprocess.Popen
    started: float = field(default_factory=time.time)

    @property
    def running(self) -> bool:
        return self.proc.poll() is None

    @property
    def returncode(self) -> int | None:
        return self.proc.poll()

    @property
    def log_path(self) -> Path:
        return self.run_dir / LOG_NAME


class JobManager:
    def __init__(self, root: Path):
        self.root = root
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def get(self, project: str) -> Job | None:
        return self._jobs.get(project)

    def running(self) -> list[Job]:
        return [j for j in self._jobs.values() if j.running]

    def start(self, project: str, config: Path, run_dir: Path, options: list[str]) -> Job:
        with self._lock:
            current = self._jobs.get(project)
            if current and current.running:
                raise RuntimeError(f"A run is already in progress for '{project}'")
            run_dir.mkdir(parents=True, exist_ok=True)
            cmd = [sys.executable, "-m", "newsintel", "run", "-c", str(config), "--run-dir", str(run_dir), *options]
            env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"}
            with (run_dir / LOG_NAME).open("a", encoding="utf-8") as log:
                log.write(f"$ newsintel run -c {config.name} {' '.join(options)}\n".rstrip() + "\n")
                log.flush()
                proc = subprocess.Popen(cmd, cwd=self.root, env=env, stdout=log, stderr=subprocess.STDOUT)
            job = Job(project, run_dir, cmd, proc)
            self._jobs[project] = job
            return job

    def stop(self, project: str) -> None:
        job = self._jobs.get(project)
        if job and job.running:
            job.proc.terminate()
            try:
                job.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                job.proc.kill()


def tail(path: Path, lines: int = 40) -> str:
    if not path.exists():
        return ""
    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        f.seek(max(0, f.tell() - 16_000))
        text = f.read().decode("utf-8", errors="replace")
    return "\n".join(text.splitlines()[-lines:])
