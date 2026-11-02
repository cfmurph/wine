"""Unit tests for the data import scheduler (no DB or network required)."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts import scheduler
from scripts.scheduler import JOBS, SCRIPTS, Job, is_due, run_due, run_job

NOW = datetime(2026, 11, 2, tzinfo=timezone.utc)
JOB = Job("test-job", every_days=7, steps=("first", "second"))


def _ago(**kwargs):
    return (NOW - timedelta(**kwargs)).isoformat()


@pytest.mark.parametrize(
    "entry,due",
    [
        ({}, True),
        ({"succeeded_at": _ago(days=1)}, False),
        ({"succeeded_at": _ago(days=8)}, True),
        ({"failed_at": _ago(hours=1)}, False),
        ({"failed_at": _ago(hours=25)}, True),
        ({"succeeded_at": _ago(days=8), "failed_at": _ago(hours=1)}, False),
    ],
)
def test_is_due(entry, due):
    assert is_due(JOB, {"test-job": entry}, NOW) is due


def test_failed_step_stops_the_rest():
    ran = []

    def step(name):
        ran.append(name)
        return False

    assert run_job(JOB, step) is False
    assert ran == ["first"]


def test_every_step_is_a_real_script():
    for job in JOBS:
        for step in job.steps:
            assert (SCRIPTS / f"{step}.py").exists(), step


def test_failure_is_recorded_and_success_clears_it(tmp_path, monkeypatch):
    monkeypatch.setattr(scheduler, "STATE_FILE", tmp_path / "state" / "scheduler.json")
    monkeypatch.setattr(scheduler, "JOBS", (JOB,))
    monkeypatch.setattr(scheduler, "run_job", lambda job: False)
    assert run_due() is False
    assert "failed_at" in scheduler.load_state()["test-job"]

    monkeypatch.setattr(scheduler, "run_job", lambda job: True)
    assert run_due(force=True) is True
    state = scheduler.load_state()["test-job"]
    assert "succeeded_at" in state and "failed_at" not in state


def test_corrupt_state_file_means_start_over(tmp_path, monkeypatch):
    path = tmp_path / "scheduler.json"
    path.write_text("{not json")
    monkeypatch.setattr(scheduler, "STATE_FILE", path)
    assert scheduler.load_state() == {}
