"""Coordinate the approved E4 schedule without changing inference.

Use --adopt-haiku with a private parallel-handoff.json to monitor an existing
01_run.sh child after its old outer controller has exited. --check is read-only.
After manual diagnosis, --resume-reviewed reads reviewed-continuation.json:
running arms are adopted and stopped arms continue only after evidence checks.
--remaining-parallel uses remaining-continuation.json to resume Haiku alongside
Fable and skip the already verified Sonnet and Opus attempts entirely. Fable
may also have reviewed continuation evidence once its initial run has started.
The user must authorize the scheduling amendment and register attempts first.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid

from claude_backend import ARMS, STATE

E = Path(__file__).resolve().parents[1]
REPO = E.parents[1]
R = E / "results/runs"
S = E / "scripts"
ORIGIN = "https://thesubstrate.science"
MEASUREMENT_FILES = ("claude_backend.py", "sandbox.sb", "01_play.py", "01_run.sh",
                     "02_score.sh", "03_table.py", "04_denials.py", "05_audit.py", "06_compare.py")


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def process_signature(pid):
    result = subprocess.run(["ps", "-p", str(pid), "-o", "stat=,lstart=,command="],
                            capture_output=True, text=True, check=False)
    value = result.stdout.strip()
    if result.returncode or not value or value.split()[0].startswith("Z"):
        return None
    # Scheduling state changes between observations; start time and command do not.
    return value.split(None, 1)[1]


def last_exit(folder, arm):
    paths = [folder / (arm + ".exit"),
             *sorted(folder.glob(arm + ".part*.exit"),
                     key=lambda p: int(p.stem.rsplit(".part", 1)[1]))]
    paths = [p for p in paths if p.exists()]
    if not paths:
        raise RuntimeError("Worker ended without a recorded exit; inspect before resuming")
    return int(paths[-1].read_text().strip())


def token():
    if os.environ.get("SUBSTRATE_TOKEN"):
        return os.environ["SUBSTRATE_TOKEN"]
    for line in (REPO / ".env").read_text().splitlines():
        key, sep, raw = line.strip().removeprefix("export ").partition("=")
        if sep and key.strip() == "SUBSTRATE_TOKEN":
            return shlex.split(raw, comments=True)[0]
    raise RuntimeError("SUBSTRATE_TOKEN unavailable")


def request(path, body=None):
    req = urllib.request.Request(ORIGIN + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        return {"httpStatus": error.code, "error": json.loads(error.read())}


class Coordinator:
    def __init__(self, adopt, resume_reviewed=False, remaining_parallel=False):
        self.registrations = json.loads((E / "results/attempts.json").read_text())
        self.handoff = json.loads((R / "parallel-handoff.json").read_text()) if adopt else None
        self.remaining_parallel = remaining_parallel
        continuation_file = "remaining-continuation.json" if remaining_parallel else "reviewed-continuation.json"
        self.continuation = json.loads((R / continuation_file).read_text()) if resume_reviewed else None
        self.states = {arm: {"phase": "queued"} for arm in ARMS}
        self.status_lock = threading.Lock()
        self.scoring_lock = threading.Lock()
        self.blocked = threading.Event()
        self.events = R / "controller-events"

    def check(self):
        if list(self.registrations) != list(ARMS):
            raise RuntimeError("Attempt mapping must include all four arms in order")
        for arm, row in self.registrations.items():
            if row["model"] != ARMS[arm] or not row["attemptId"]:
                raise RuntimeError("Registered model/attempt differs")
            for name in MEASUREMENT_FILES:
                path = S / name
                original = subprocess.check_output(
                    ["git", "show", row["commit"] + ":" + path.relative_to(REPO).as_posix()], cwd=REPO)
                if path.read_bytes() != original:
                    raise RuntimeError("Measurement source changed: " + name)
        if list((STATE / "flags").glob("*.json")):
            raise RuntimeError("Unresolved isolation flags require review")
        if self.handoff:
            arm = next(iter(ARMS))
            expected = "bash experiments/E04-claude-baselines/scripts/01_run.sh " + arm
            if not self.handoff["worker_signature"].endswith(expected):
                raise RuntimeError("Handoff does not identify Haiku's run wrapper")
            actual = process_signature(self.handoff["worker_pid"])
            if actual is not None and actual != self.handoff["worker_signature"]:
                raise RuntimeError("Handoff PID belongs to a different process")
            if actual is None and last_exit(R, arm) != 0:
                raise RuntimeError("Haiku worker stopped before handoff; diagnose first")
        if self.continuation:
            covered = set(self.continuation["arms"])
            allowed = [set(list(ARMS)[:3])]
            if self.remaining_parallel:
                allowed.append(set(ARMS))
            if self.handoff or covered not in allowed:
                raise RuntimeError("Reviewed continuation must cover the first three arms, plus optional Fable in remaining mode")
            for arm, row in self.continuation["arms"].items():
                if row.get("worker_pid"):
                    expected = "bash experiments/E04-claude-baselines/scripts/01_run.sh " + arm
                    actual = process_signature(row["worker_pid"])
                    if not row["worker_signature"].endswith(expected) or actual != row["worker_signature"]:
                        raise RuntimeError("Running-arm handoff does not match its live worker")
                elif row.get("resume_reviewed") or row.get("verified_complete"):
                    if not row.get("evidence") or not row.get("review_summary"):
                        raise RuntimeError("Stopped-arm continuation needs retained review evidence")
                    for evidence in row["evidence"]:
                        path = (REPO / evidence["path"]).resolve()
                        if not path.is_relative_to(R.resolve()):
                            raise RuntimeError("Continuation evidence must be a private run artifact")
                        h = sha256()
                        with path.open("rb") as stream:
                            while chunk := stream.read(1024 * 1024):
                                h.update(chunk)
                        if h.hexdigest() != evidence["sha256"]:
                            raise RuntimeError("Continuation evidence changed")
                    score = json.loads((R / row["score_file"]).read_text())
                    audit = json.loads((R / row["audit_file"]).read_text())
                    if (not score["verified"] or audit["missing_joins"] or audit["interrupted_traces"]
                            or sum(t["finished"] for t in score["tiers"].values()) != row["finished"]):
                        raise RuntimeError("Partial games or their transcripts have not verified")
                    if row.get("verified_complete"):
                        if row["finished"] != 460 or last_exit(R, arm) != 0:
                            raise RuntimeError("Completed arm must contain all 460 verified games")
                        current = request("/api/research/attempts/" + self.registrations[arm]["attemptId"])
                        if current.get("status") != "succeeded":
                            raise RuntimeError("Completed arm lacks its succeeded attempt receipt")
                    smoke_audit = json.loads((R / "smoke" / (arm + ".audit.json")).read_text())
                    if (last_exit(R / "smoke", arm) != 0 or smoke_audit["missing_joins"]
                            or smoke_audit["interrupted_traces"]):
                        raise RuntimeError("Existing smoke evidence does not pass")
                else:
                    raise RuntimeError("Each continuation arm must be running or explicitly reviewed")
        if self.remaining_parallel:
            arms = list(ARMS)
            if (self.handoff or not self.continuation
                    or not self.continuation["arms"][arms[0]].get("resume_reviewed")
                    or not all(self.continuation["arms"][arm].get("verified_complete") for arm in arms[1:3])):
                raise RuntimeError("Remaining-arm schedule requires reviewed Haiku and completed Sonnet/Opus")
            fable = self.continuation["arms"].get(arms[3])
            if fable and not fable.get("resume_reviewed"):
                raise RuntimeError("An existing Fable run needs reviewed continuation evidence")
        return {"measurement_sources_match": True, "adopting_haiku": bool(self.handoff),
                "reviewed_continuation": bool(self.continuation),
                "models": list(ARMS.values()), "batch_per_arm": 12,
                "maximum_active_arms": 2 if self.remaining_parallel else 3}

    def status(self, arm, phase, code=None, worker_pid=None):
        with self.status_lock:
            if arm:
                self.states[arm] = {"phase": phase, "exit_code": code,
                                    "worker_pid": worker_pid, "updated_at": now()}
            value = {"phase": "running_parallel" if arm else phase, "pid": os.getpid(),
                     "arms": self.states, "updated_at": now()}
            atomic_json(R / "controller.status.json", value)
            print(json.dumps({"arm": arm, "phase": phase, "exit_code": code, "at": now()}), flush=True)

    def event(self, arm, kind, summary, metrics=None, outputs=None, code=None):
        row = self.registrations[arm]
        current = request("/api/research/attempts/" + row["attemptId"])
        if kind == "started" and current.get("status") == "started":
            return
        body = {"schemaVersion": 4, "requestId": str(uuid.uuid4()),
                **current["affordances"]["expected"], "kind": kind, "summary": summary,
                "reportedAt": now(), "detail": {"exitCode": code, "signal": None,
                "error": None, "durationMs": None}, "outputs": outputs or [],
                "client": {"name": "codex", "version": "1", "model": "GPT-6",
                           "sessionId": "zendo-claude-baselines", "runId": row["label"].lower()}}
        if metrics:
            body["detail"]["metrics"] = metrics
        self.events.mkdir(exist_ok=True)
        (self.events / (body["requestId"] + ".request.json")).write_text(json.dumps(body, indent=2))
        for _ in range(6):
            try:
                result = request("/api/agent/research/report_attempt_event", body)
            except (OSError, TimeoutError):
                time.sleep(30)
                continue
            (self.events / (body["requestId"] + ".response.json")).write_text(json.dumps(result, indent=2))
            if result.get("result", {}).get("attemptId") == row["attemptId"] and not result.get("error"):
                return
            if result.get("httpStatus", 0) >= 500:
                time.sleep(30)
                continue
            raise RuntimeError("Substrate refused event; exact request and response retained")
        raise RuntimeError("Substrate delivery uncertain; retained request must be reconciled")

    def command(self, argv, output=None):
        if output:
            with output.open("w") as stream:
                subprocess.run(argv, cwd=REPO, stdout=stream, check=True)
        else:
            subprocess.run(argv, cwd=REPO, check=True)

    def run_part(self, arm, smoke=False):
        if self.blocked.is_set() or list((STATE / "flags").glob("*.json")):
            raise RuntimeError("A prior stop or isolation flag requires diagnosis before a new launch")
        process = subprocess.Popen(["bash", str((S / "01_run.sh").relative_to(REPO)), arm],
                                   cwd=REPO, env={**os.environ, "SMOKE": "1" if smoke else "0"})
        self.status(arm, "running_smoke" if smoke else "running_full_baseline", worker_pid=process.pid)
        return process.wait()

    def artifacts(self, arm):
        paths = set()
        for folder in (R, R / "traces", R / "smoke", R / "smoke/traces",
                       E / "results/scores", E / "results/comparisons"):
            paths.update(p for p in folder.glob(arm + "*") if p.is_file())
        outputs = []
        for path in sorted(paths):
            h = sha256()
            with path.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    h.update(chunk)
            outputs.append({"label": str(path.relative_to(E / "results")),
                "reference": "Private artifact held by owner; repository-relative path: "
                             + path.relative_to(REPO).as_posix() + "; not public; ask reporter.",
                "access": "restricted", "digest": h.hexdigest(), "bytes": path.stat().st_size})
        return outputs

    def arm(self, arm, adopt=False):
        continuation = (self.continuation or {}).get("arms", {}).get(arm)
        if continuation and continuation.get("verified_complete"):
            self.status(arm, "verified", 0)
            return True
        schedule = ("Owner-authorized Haiku/Fable overlap; Sonnet and Opus already verified. "
                    if self.remaining_parallel else "Owner-authorized Haiku/Sonnet/Opus overlap, followed by Fable. ")
        context = (f"Arm {arm}, model {ARMS[arm]}, high effort, adaptive summarized thinking, "
                   "provider-default sampling, max_tokens 128000, Claude Code 2.1.293 function backend; "
                   "dev manifest, 460 full-run games, 12 concurrent calls per arm; manifest episode seeds, "
                   "model unseeded; Apple M4 Max 128 GB local orchestration, hosted inference hardware unknown. "
                   + schedule + "Fixed SDK identity, "
                   "disabled tools and full private transcript capture unchanged.")
        try:
            code = None
            running = continuation if continuation and continuation.get("worker_pid") else self.handoff if adopt else None
            if running:
                self.status(arm, "running_full_baseline", worker_pid=running["worker_pid"])
                self.event(arm, "progress", "Outer scheduling controller transferred without stopping or restarting "
                    "this arm's live worker. Its original attempt and configuration continue; no games rerun. " + context)
                while process_signature(running["worker_pid"]) == running["worker_signature"]:
                    time.sleep(15)
                if process_signature(running["worker_pid"]) is not None:
                    raise RuntimeError("Adopted worker PID was reused; inspect before continuation")
                code = last_exit(R, arm)
            elif continuation and continuation.get("resume_reviewed"):
                self.status(arm, "resuming_after_review")
                if continuation.get("report_resume_progress", True):
                    self.event(arm, "progress", continuation["review_summary"] + " Continuing only unfinished games "
                        "in a fresh immutable part under the same attempt and byte-identical measurement configuration. "
                        "Completed games and verified smoke evidence are retained, not resampled. " + context)
            else:
                self.status(arm, "starting_registered_arm")
                self.event(arm, "started", "Starting separate six-game smoke; full measurement follows only after "
                           "score --verify and transcript audit pass. " + context)
                code = self.run_part(arm, smoke=True)
                if code:
                    raise subprocess.CalledProcessError(code, "smoke 01_run.sh")
                parts = sorted((R / "smoke").glob(arm + "*.jsonl"))
                self.command([sys.executable, "-m", "zendo_bench", "score", "--manifest", "dev", "--verify",
                              *map(str, parts)], output=R / "smoke" / (arm + ".verify.log"))
                self.command([sys.executable, str(S / "05_audit.py"), *map(str, parts)],
                             output=R / "smoke" / (arm + ".audit.json"))
                code = None
            for retry in range(4):
                if code is None:
                    code = self.run_part(arm)
                if code == 4 and retry < 3:
                    self.status(arm, "waiting_after_infrastructure_breaker", code)
                    time.sleep(1800)
                    code = None
                    continue
                if code:
                    raise subprocess.CalledProcessError(code, "01_run.sh")
                break
            # Tables combine arms, so their read/modify/write work must not overlap.
            with self.scoring_lock:
                self.status(arm, "verifying_full_baseline")
                self.command(["bash", str(S / "02_score.sh"), arm])
                score = json.loads((E / "results/scores" / (arm + ".score.json")).read_text())
                if not score["verified"] or sum(t["finished"] for t in score["tiers"].values()) != 460:
                    raise RuntimeError("Full coverage or verification failed")
                self.status(arm, "running_paired_comparisons")
                self.command([sys.executable, str(S / "06_compare.py"), "--arm", arm])
                self.command([sys.executable, str(S / "03_table.py")])
                metrics = {k: v for k, v in json.loads((E / "results/metrics.json").read_text()).items()
                           if k.startswith(arm + ".") and isinstance(v, (int, float))}
                self.event(arm, "succeeded", "Full baseline completed, score --verify and transcript audit passed; "
                           "paired E3 comparisons completed. " + context,
                           metrics=metrics, outputs=self.artifacts(arm), code=0)
            self.status(arm, "verified", 0)
            return True
        except Exception as error:
            self.blocked.set()
            code = getattr(error, "returncode", 1)
            self.status(arm, "stopped_requires_diagnosis", code)
            print(arm, type(error).__name__, str(error), flush=True)
            try:
                self.event(arm, "progress", "This arm stopped and requires diagnosis. Other already-running arms "
                    "may finish; no new arm or part starts until reviewed. No model loss inferred. " + context, code=code)
            except Exception as delivery:
                print("Stop-event delivery needs review:", type(delivery).__name__, flush=True)
            return False

    def run(self):
        with (R / "controller.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.check()
            arms = list(ARMS)
            if self.remaining_parallel:
                for arm in arms[1:3]:
                    self.status(arm, "verified", 0)
                with ThreadPoolExecutor(max_workers=2) as pool:
                    pending = [pool.submit(self.arm, arm) for arm in (arms[0], arms[3])]
                    passed = [future.result() for future in pending]
                self.status(None, "results_ready_for_review" if all(passed) else "stopped_requires_diagnosis")
                return 0 if all(passed) else 1
            with ThreadPoolExecutor(max_workers=3) as pool:
                pending = [pool.submit(self.arm, arm, i == 0 and bool(self.handoff))
                           for i, arm in enumerate(arms[:3])]
                passed = [future.result() for future in pending]
            if all(passed) and not self.blocked.is_set():
                passed.append(self.arm(arms[3]))
            self.status(None, "results_ready_for_review" if all(passed) else "stopped_requires_diagnosis")
            return 0 if all(passed) else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adopt-haiku", action="store_true")
    parser.add_argument("--resume-reviewed", action="store_true")
    parser.add_argument("--remaining-parallel", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.remaining_parallel and (not args.resume_reviewed or args.adopt_haiku):
        parser.error("--remaining-parallel requires --resume-reviewed and excludes --adopt-haiku")
    coordinator = Coordinator(args.adopt_haiku, args.resume_reviewed, args.remaining_parallel)
    if args.check:
        print(json.dumps(coordinator.check(), indent=2))
        return 0
    return coordinator.run()


if __name__ == "__main__":
    raise SystemExit(main())
