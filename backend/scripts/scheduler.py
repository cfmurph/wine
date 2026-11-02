#!/usr/bin/env python3
"""
Run the public data imports on a schedule.

Usage (from backend/):
    python3 scripts/scheduler.py              # Keep running, and run jobs when they're due
    python3 scripts/scheduler.py --once       # Run anything due, then exit
    python3 scripts/scheduler.py --force      # Run everything now, then exit

Times are kept in STATE_FILE, so a restart doesn't repeat recent work. A failed job stops the rest of its
steps and is retried after RETRY_HOURS. Results go to the service log only; nothing sends alerts.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).parent
STATE_FILE = Path(os.environ.get("SCHEDULER_STATE_FILE", "/var/lib/wineapp/scheduler.json"))
CHECK_EVERY_SECONDS = 15 * 60
RETRY_HOURS = 24
STEP_TIMEOUT_SECONDS = 60 * 60


@dataclass(frozen=True)
class Job:
    name: str
    every_days: int
    steps: tuple[str, ...]


JOBS = (
    Job(
        "refresh-public-data",
        every_days=7,
        steps=(
            "import_bc_wineries", "import_bc_prices", "import_market_stats",
            "import_listings", "import_sales", "link_wineries", "check_land",
        ),
    ),
    # Reports listing pages that changed; a person decides what to update.
    Job("check-listing-pages", every_days=7, steps=("check_listings",)),
)


def log(message: str) -> None:
    print(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {message}", flush=True)


def is_due(job: Job, state: dict, now: datetime) -> bool:
    """Due once its interval has passed since success, but no sooner than the retry delay after a failure."""
    entry = state.get(job.name, {})
    succeeded = entry.get("succeeded_at")
    failed = entry.get("failed_at")
    if succeeded and now - datetime.fromisoformat(succeeded) < timedelta(days=job.every_days):
        return False
    if failed and now - datetime.fromisoformat(failed) < timedelta(hours=RETRY_HOURS):
        return False
    return True


def run_job(job: Job, run_step=None) -> bool:
    run_step = run_step or _run_script
    for step in job.steps:
        log(f"{job.name}: starting {step}")
        if not run_step(step):
            log(f"{job.name}: FAILED at {step}")
            return False
    log(f"{job.name}: finished")
    return True


def _run_script(step: str) -> bool:
    try:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / f"{step}.py")], timeout=STEP_TIMEOUT_SECONDS, cwd=SCRIPTS.parent
        ).returncode == 0
    except subprocess.TimeoutExpired:
        log(f"{step}: timed out")
        return False


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, ValueError):
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2))
    temporary.replace(STATE_FILE)


def run_due(force: bool = False) -> bool:
    state = load_state()
    all_ok = True
    for job in JOBS:
        now = datetime.now(timezone.utc)
        if not force and not is_due(job, state, now):
            continue
        succeeded = run_job(job)
        all_ok = all_ok and succeeded
        finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
        entry = state.setdefault(job.name, {})
        if succeeded:
            entry["succeeded_at"] = finished
            entry.pop("failed_at", None)
        else:
            entry["failed_at"] = finished
        save_state(state)
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.once or args.force:
        sys.exit(0 if run_due(force=args.force) else 1)
    log("scheduler started")
    while True:
        run_due()
        time.sleep(CHECK_EVERY_SECONDS)
