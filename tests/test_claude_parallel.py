"""The scheduler overlaps three arms and keeps Fable behind verification."""
import importlib.util
from hashlib import sha256
import json
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
    instance.continuation = None
    instance.remaining_parallel = False
    instance.only = None
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


def test_reviewed_continuation_skips_smoke(monkeypatch, tmp_path):
    instance = coordinator(monkeypatch, tmp_path)
    arm = list(parallel.ARMS)[1]
    instance.handoff = None
    instance.continuation = {"arms": {arm: {"resume_reviewed": True, "review_summary": "Reviewed."}}}
    events, launches = [], []
    instance.event = lambda arm, kind, summary, **kwargs: events.append(kind)

    def launch(arm, smoke=False):
        launches.append(smoke)
        return 77  # End before scoring; this test must never invoke inference.

    instance.run_part = launch
    assert instance.arm(arm) is False
    assert launches == [False]
    assert events == ["progress", "progress"]


def test_running_opus_is_adopted_without_duplicate_launch(monkeypatch, tmp_path):
    instance = coordinator(monkeypatch, tmp_path)
    arm = list(parallel.ARMS)[2]
    instance.handoff = None
    instance.continuation = {"arms": {arm: {"worker_pid": 42, "worker_signature": "existing-opus"}}}
    instance.event = lambda *args, **kwargs: None
    signatures = iter(["existing-opus", None, None])
    monkeypatch.setattr(parallel, "process_signature", lambda pid: next(signatures))
    monkeypatch.setattr(parallel.time, "sleep", lambda delay: None)
    monkeypatch.setattr(parallel, "last_exit", lambda folder, arm: 5)
    instance.run_part = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("duplicate launch"))
    assert instance.arm(arm) is False


def test_remaining_models_overlap_without_relaunching_completed_models(monkeypatch, tmp_path):
    instance = coordinator(monkeypatch, tmp_path)
    instance.remaining_parallel = True
    arms = list(parallel.ARMS)
    barrier = threading.Barrier(2, timeout=3)
    called, states = [], []
    instance.status = lambda arm, phase, *args: states.append((arm, phase))

    def run(arm):
        assert arm in (arms[0], arms[3])
        called.append(arm)
        barrier.wait()
        return True

    instance.arm = run
    assert instance.run() == 0
    assert set(called) == {arms[0], arms[3]}
    assert (arms[1], "verified") in states and (arms[2], "verified") in states


def test_completed_arm_sends_no_new_event_or_inference(monkeypatch, tmp_path):
    instance = coordinator(monkeypatch, tmp_path)
    arm = list(parallel.ARMS)[1]
    instance.continuation = {"arms": {arm: {"verified_complete": True}}}
    instance.event = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("terminal attempt event"))
    instance.run_part = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("completed arm rerun"))
    assert instance.arm(arm) is True


def test_haiku_only_never_launches_fable(monkeypatch, tmp_path):
    instance = coordinator(monkeypatch, tmp_path)
    arms = list(parallel.ARMS)
    instance.remaining_parallel = True
    instance.only = arms[0]
    calls, states = [], []
    instance.arm = lambda arm: calls.append(arm) or True
    instance.status = lambda arm, phase, *args: states.append((arm, phase))
    assert instance.run() == 0
    assert calls == [arms[0]]
    assert (arms[3], "waiting_for_owner_resume") in states
    assert (None, "selected_arm_verified") in states


def test_remaining_check_accepts_verified_fable_continuation(monkeypatch, tmp_path):
    instance = coordinator(monkeypatch, tmp_path)
    instance.handoff = None
    instance.remaining_parallel = True
    instance.registrations = {arm: {"model": model, "attemptId": arm} for arm, model in parallel.ARMS.items()}
    monkeypatch.setattr(parallel, "REPO", tmp_path)
    monkeypatch.setattr(parallel, "STATE", tmp_path)
    monkeypatch.setattr(parallel, "MEASUREMENT_FILES", ())
    monkeypatch.setattr(parallel, "request", lambda path: {"status": "succeeded"})
    (tmp_path / "smoke").mkdir()
    rows = {}
    for index, arm in enumerate(parallel.ARMS):
        complete = index in (1, 2)
        finished = 460 if complete else 200
        score = tmp_path / (arm + ".score.json")
        score.write_text(json.dumps({"verified": True, "tiers": {"T1": {"finished": finished}}}))
        audit = tmp_path / (arm + ".audit.json")
        audit.write_text(json.dumps({"missing_joins": 0, "interrupted_traces": 0}))
        (tmp_path / "smoke" / audit.name).write_text(audit.read_text())
        (tmp_path / "smoke" / (arm + ".exit")).write_text("0")
        (tmp_path / (arm + ".exit")).write_text("0" if complete else "1")
        rows[arm] = {"verified_complete": complete, "resume_reviewed": not complete,
                     "finished": finished, "review_summary": "Verified retained games.",
                     "score_file": score.name, "audit_file": audit.name,
                     "evidence": [{"path": p.name, "sha256": sha256(p.read_bytes()).hexdigest()}
                                  for p in (score, audit)]}
    instance.continuation = {"arms": rows}
    assert parallel.Coordinator.check(instance)["maximum_active_arms"] == 2
    instance.only = next(iter(parallel.ARMS))
    assert parallel.Coordinator.check(instance)["maximum_active_arms"] == 1


def test_fable_continuation_skips_smoke_and_keeps_resume_progress_local(monkeypatch, tmp_path):
    instance = coordinator(monkeypatch, tmp_path)
    arm = list(parallel.ARMS)[3]
    instance.handoff = None
    instance.continuation = {"arms": {arm: {"resume_reviewed": True,
        "report_resume_progress": False, "review_summary": "Local continuation."}}}
    events, launches = [], []
    instance.event = lambda arm, kind, summary, **kwargs: events.append(summary)

    def launch(arm, smoke=False):
        launches.append(smoke)
        return 77  # Deliberately stop before scoring or model calls.

    instance.run_part = launch
    assert instance.arm(arm) is False
    assert launches == [False]
    assert len(events) == 1 and events[0].startswith("This arm stopped")
