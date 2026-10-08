"""The scheduler overlaps three arms and keeps Fable behind verification."""
import importlib.util
from pathlib import Path
import sys
import threading

SCRIPT = Path(__file__).resolve().parents[1] / "experiments/E04-claude-baselines/scripts/07_parallel.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("e04_parallel", SCRIPT)
parallel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parallel)


def coordinator(monkeypatch, tmp_path):
    monkeypatch.setattr(parallel, "R", tmp_path)
    instance = parallel.Coordinator.__new__(parallel.Coordinator)
    instance.handoff = {"worker_pid": 123}
    instance.blocked = threading.Event()
    instance.check = lambda: None
    instance.status = lambda *args, **kwargs: None
    return instance


def test_three_arms_overlap_fable_waits(monkeypatch, tmp_path):
    instance = coordinator(monkeypatch, tmp_path)
    arms = list(parallel.ARMS)
    barrier = threading.Barrier(3, timeout=3)
    done = set()
    lock = threading.Lock()

    def run(arm, adopt=False):
        assert adopt == (arm == arms[0])
        if arm == arms[3]:
            assert done == set(arms[:3])
        else:
            barrier.wait()
        with lock:
            done.add(arm)
        return True

    instance.arm = run
    assert instance.run() == 0
    assert done == set(arms)


def test_failure_prevents_fable(monkeypatch, tmp_path):
    instance = coordinator(monkeypatch, tmp_path)
    arms = list(parallel.ARMS)
    called = []

    def run(arm, adopt=False):
        called.append(arm)
        return arm != arms[1]

    instance.arm = run
    assert instance.run() == 1
    assert set(called) == set(arms[:3])


def test_adopted_exit_uses_numeric_part_order(tmp_path):
    for part, code in [("", 4), (".part9", 3), (".part10", 0)]:
        (tmp_path / ("haiku" + part + ".exit")).write_text(str(code))
    assert parallel.last_exit(tmp_path, "haiku") == 0
