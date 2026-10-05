"""guard.py BOX ARM   cost and lifetime guard for one E01 box (runs on the Mac, every 60 s; from the pilot's guard.py).

Every minute: the sandbox's state and list-price spend. Every 10 minutes: renew the server-side TTL
(ctl.TTL_MINUTES from now) and pull the box's logs into the state folder. When ARM's latest run file
has its .exit and no harness has run for GRACE_MINUTES (time to resume it), pull the logs and delete
the sandbox. At ctl.CAP_DOLLARS or ctl.CAP_HOURS: stop the harness (SIGTERM; finished games stay on
disk and the run resumes with 01_run.sh), pull the logs, delete the sandbox.

    uv run --with daytona==0.220.0 python guard.py qwen38 qwen3.8-27b-fp8-vllm-h100
"""
from pathlib import Path
import subprocess
import sys
import tarfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctl  # noqa: E402

GRACE_MINUTES = 15
STOP_DOLLARS = ctl.CAP_DOLLARS - 2   # list estimate, under the cap
STOP_MINUTES = ctl.CAP_HOURS * 60 - 10


def main():
    name, arm = sys.argv[1], sys.argv[2]
    box = ctl.Box(name)
    runs = ctl.REPO / "experiments/E01-dev-baseline/results/runs"
    logdir = box.dir / "box-logs"
    guard_log = box.dir / "guard.log"

    def say(msg):
        line = f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {msg}"
        print(line, flush=True)
        with guard_log.open("a") as f:
            f.write(line + "\n")

    def harness_alive():
        return subprocess.run(["pgrep", "-f", f"results/runs/{arm}"], capture_output=True).returncode == 0

    def run_exited():
        files = sorted(runs.glob(f"{arm}*.cmd"), key=lambda p: p.stat().st_mtime)
        return bool(files) and files[-1].with_suffix(".exit").exists()

    def pull_logs(sandbox):
        archive = "/tmp/e01-logs.tar.gz"
        sandbox.process.exec(f"cd {ctl.REMOTE} && tar -czf {archive} logs 2>/dev/null; true", timeout=120)
        logdir.mkdir(exist_ok=True)
        local = logdir / "logs-latest.tar.gz"
        sandbox.fs.download_file(archive, str(local))
        with tarfile.open(local) as tar:
            tar.extractall(logdir, filter="data")

    def finish(reason, c):
        try:
            pull_logs(box.sandbox(c))
            say("final log pull done")
        except Exception as exc:
            say(f"final log pull failed: {type(exc).__name__}: {str(exc)[:200]}")
        box.delete(f"guard: {reason}")
        say(f"sandbox deleted: {reason}")

    c = ctl.client()
    n, idle_since = 0, None
    while True:
        ledger = box.load()
        entries = box.live(ledger)
        if not entries:
            say(f"nothing live; spent ${box.spent(ledger):.2f}; guard exits")
            return
        minutes = (time.time() - entries[0]["requested_unix"]) / 60
        cost = box.spent(ledger)
        state = None
        try:
            sandbox = c.get(entries[0]["id"])
            state = str(sandbox.state)
            if n % 10 == 0:
                sandbox.set_ttl(ctl.TTL_MINUTES)
                pull_logs(sandbox)
        except Exception as exc:
            say(f"guard error: {type(exc).__name__}: {str(exc)[:200]}")
            if "Authentication" in type(exc).__name__:  # the CLI login expired: re-read it after `daytona login`
                try:
                    c = ctl.client()
                except Exception as exc2:
                    say(f"client rebuild failed: {type(exc2).__name__}: {str(exc2)[:120]}")
        alive = harness_alive()
        say(f"{name} state={state} minutes={minutes:.0f} spent=${cost:.2f} harness={'up' if alive else 'down'}")
        if state and any(s in state.lower() for s in ("destroyed", "error", "stopped", "archived")):
            entries[0].update(deleted_unix=time.time(), delete_reason=f"guard observed state {state}")
            box.save(ledger)
            say(f"sandbox {state}: ledger closed; guard exits")
            return
        if run_exited() and not alive:
            idle_since = idle_since or time.time()
            if time.time() - idle_since >= GRACE_MINUTES * 60:
                finish(f"{arm} exited and was not resumed within {GRACE_MINUTES} min "
                       f"(spent ${cost:.2f}, {minutes:.0f} min)", c)
                return
        else:
            idle_since = None
        if cost >= STOP_DOLLARS or minutes >= STOP_MINUTES:
            say("CAP REACHED: stopping the harness")
            subprocess.run(["pkill", "-TERM", "-f", f"results/runs/{arm}"])
            for _ in range(60):
                time.sleep(1)
                if not harness_alive():
                    break
            finish(f"cap (spent ${cost:.2f}, {minutes:.0f} min)", c)
            return
        n += 1
        time.sleep(60)


if __name__ == "__main__":
    main()
