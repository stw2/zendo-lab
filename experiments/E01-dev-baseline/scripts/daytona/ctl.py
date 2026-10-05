"""Daytona control for E01's two H100 vLLM boxes (adapted from the 2026-10-04 dev36 pilot's ctl.py).

    uv run --with daytona==0.220.0 python ctl.py BOX up        # launch, set up, serve, check: ready for 01_run.sh
    uv run --with daytona==0.220.0 python ctl.py BOX info | cost | preview | delete [REASON] | ttl MINUTES
    uv run --with daytona==0.220.0 python ctl.py BOX exec 'CMD' [--timeout S]

BOX is qwen35 or qwen38. State (ledger, preview URL, the 0600 preview token, box logs) lives in
~/.cache/zendo-lab/e01-daytona/BOX/, outside the repository; the preview token is never printed. The
organization comes from DAYTONA_ORG in the repository's .env, the credential from DAYTONA_API_KEY there
or, without it, from the Daytona CLI's login.

Spend is the list rate times wall-clock since the create request. The box's server-side TTL
(TTL_MINUTES) is renewed by guard.py while it runs, so a box outlives a dead Mac by at most that long.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BOXES = {
    "qwen35": dict(repo="Qwen/Qwen3.5-27B-FP8", pin="97f5941bf617e31c5e237364a8602ce3f03a551a", served="qwen3.5-27b-fp8"),
    "qwen38": dict(repo="Qwen/Qwen3.8-27B-FP8", pin="017b9c7af6b5689d5dd426a76e0bc077eb5ca20a", served="qwen3.8-27b-fp8"),
}
IMAGE = "nvidia/cuda:13.0.1-cudnn-devel-ubuntu24.04"
CPU, MEMORY, DISK = 16, 64, 150
# daytona.io/pricing as the pilot read it (2026-10-02): H100 on-demand $3.95/h, vCPU $0.0504/h, GiB RAM $0.0162/h,
# GiB disk $0.000108/h (first 5 GiB free): $5.809/h.
RATE = 3.95 + CPU * 0.0504 + MEMORY * 0.0162 + max(DISK - 5, 0) * 0.000108
CAP_DOLLARS = 240.0  # raised from $200 on 2026-10-05 for A5's tiers T5-T6 (DESIGN.md amendment)
CAP_HOURS = 34.0
TTL_MINUTES = 180
REMOTE = "/workspace/e01"


def state_dir(box):
    d = Path.home() / ".cache/zendo-lab/e01-daytona" / box
    d.mkdir(parents=True, exist_ok=True)
    return d


def env(name):
    if os.environ.get(name):
        return os.environ[name]
    for line in (REPO / ".env").read_text().splitlines():
        if line.strip().startswith(f"{name}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"{name} is not set (environment or .env)")


def client():
    """DAYTONA_API_KEY (environment or .env) if set: it does not expire with the CLI's 24-hour login. Else the
    Daytona CLI's login."""
    from daytona import Daytona, DaytonaConfig
    try:
        key = env("DAYTONA_API_KEY")
    except SystemExit:
        key = None
    if key:
        return Daytona(DaytonaConfig(api_key=key, organization_id=env("DAYTONA_ORG")))
    config = Path.home() / "Library/Application Support/daytona/config.json"
    state = json.loads(config.read_text())
    profile = next(p for p in state["profiles"] if p["id"] == state["activeProfile"])
    return Daytona(DaytonaConfig(jwt_token=profile["api"]["token"]["accessToken"],
                                 organization_id=env("DAYTONA_ORG"), api_url=profile["api"]["url"]))


class Box:
    def __init__(self, name):
        if name not in BOXES:
            raise SystemExit(f"unknown box {name}: {sorted(BOXES)}")
        self.name, self.spec, self.dir = name, BOXES[name], state_dir(name)
        self.ledger_path = self.dir / "ledger.json"
        self.token_file, self.url_file = self.dir / "preview-token", self.dir / "preview-url.txt"

    def load(self):
        return json.loads(self.ledger_path.read_text()) if self.ledger_path.exists() else {"sandboxes": []}

    def save(self, ledger):
        tmp = self.ledger_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(ledger, indent=1))
        tmp.replace(self.ledger_path)

    def live(self, ledger=None):
        return [s for s in (ledger or self.load())["sandboxes"] if not s.get("deleted_unix")]

    def spent(self, ledger=None, now=None):
        now = now or time.time()
        return sum(((s.get("deleted_unix") or now) - s["requested_unix"]) / 3600 * s["rate"]
                   for s in (ledger or self.load())["sandboxes"])

    def sandbox(self, c=None):
        (entry,) = self.live()
        return (c or client()).get(entry["id"])

    def launch(self):
        from daytona import CreateSandboxFromImageParams, GpuType, Resources
        ledger = self.load()
        if self.live(ledger):
            raise SystemExit(f"{self.name}: a sandbox is already live")
        entry = dict(requested_unix=time.time(), image=IMAGE, ttl_minutes=TTL_MINUTES, rate=RATE, gpus=1,
                     gpu_type="H100", cpu=CPU, memory=MEMORY, disk=DISK, tier="on-demand", model=self.spec["repo"])
        ledger["sandboxes"].append(entry)
        self.save(ledger)  # charged from the request on
        c = client()
        sandbox_name = f"e01-{self.name}-h100-{len(ledger['sandboxes'])}"  # unique: a replaced box may still be destroying
        try:
            box = c.create(CreateSandboxFromImageParams(
                image=IMAGE, name=sandbox_name, public=False,
                resources=Resources(cpu=CPU, memory=MEMORY, disk=DISK, gpu=1, gpu_type=[GpuType.H100]),
                spot=False, auto_stop_interval=0, auto_delete_interval=0, ttl_minutes=TTL_MINUTES,
                labels={"purpose": f"zendo-lab-e01-{self.name}"}), timeout=1800)
        except Exception as exc:
            entry["error"] = f"create failed: {type(exc).__name__}: {str(exc)[:300]}"
            self.save(ledger)
            try:  # a half-created box would still bill: find it by name and delete it
                for b in list(c.list()):
                    if getattr(b, "name", None) == sandbox_name:
                        entry["id"] = b.id
                        c.delete(b)
            except Exception as exc2:
                entry["cleanup_error"] = f"{type(exc2).__name__}: {str(exc2)[:300]}"
            entry["deleted_unix"] = time.time()
            self.save(ledger)
            raise
        entry.update(id=box.id, created_unix=time.time())
        self.save(ledger)
        say(self.name, f"launched in {entry['created_unix'] - entry['requested_unix']:.0f} s at ${RATE:.3f}/h")

    def exec(self, cmd, timeout=600):
        r = self.sandbox().process.exec(cmd, timeout=timeout)
        return r.exit_code, r.result

    def background(self, session, cmd):
        from daytona import SessionExecuteRequest
        box = self.sandbox()
        try:
            box.process.create_session(session)
        except Exception as exc:
            say(self.name, f"session {session}: {str(exc)[:160]}")
        box.process.execute_session_command(session, SessionExecuteRequest(command=cmd, run_async=True))

    def preview(self, port=8000):
        link = self.sandbox().get_preview_link(port)
        fd = os.open(self.token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(link.token or "")
        self.url_file.write_text(link.url + "\n")

    def request(self, path, body=None, timeout=60):
        url = self.url_file.read_text().strip().rstrip("/") + path
        headers = {"x-daytona-preview-token": self.token_file.read_text().strip(),
                   "X-Daytona-Skip-Preview-Warning": "true", "Content-Type": "application/json"}
        req = urllib.request.Request(url, headers=headers, data=None if body is None else json.dumps(body).encode())
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())

    def up(self):
        """Launch, install vLLM and the pinned model (hashes checked), serve, wait for the model, one chat check."""
        if not self.live():
            self.launch()
        spec = self.spec
        self.exec(f"mkdir -p {REMOTE}/logs")
        box = self.sandbox()
        for f in ("setup.sh", "serve.sh"):
            box.fs.upload_file(str(HERE / f), f"{REMOTE}/{f}")
        self.background("setup", f"bash {REMOTE}/setup.sh {spec['repo']} {spec['pin']} {spec['served']} "
                                 f"> {REMOTE}/logs/setup.out 2>&1")
        say(self.name, "setup started (vLLM install and model download)")
        wait(self.name, lambda: self.exec(f"test -f {REMOTE}/setup.done")[0] == 0, minutes=75, what="setup")
        code, out = self.exec(f"tail -1 {REMOTE}/logs/model-sha256-check.txt; cat {REMOTE}/logs/versions.txt")
        say(self.name, f"setup done: {out.strip()}")
        if "ALL_OK" not in out:
            raise SystemExit(f"{self.name}: model files do not match the Hub's hashes; box left up for inspection")
        self.background("serve", f"bash {REMOTE}/serve.sh {spec['served']}")
        self.preview()

        def ready():
            try:
                return self.request("/v1/models")[0] == 200
            except Exception:
                return False
        wait(self.name, ready, minutes=40, what="vLLM /v1/models")
        status, out = self.request("/v1/chat/completions", dict(
            model=spec["served"], max_tokens=2048, messages=[{"role": "user", "content": "Reply with the word ready."}]),
            timeout=600)
        msg = out["choices"][0]["message"]
        say(self.name, f"chat check: status {status}, finish {out['choices'][0]['finish_reason']}, "
                       f"reasoning {len(msg.get('reasoning_content') or msg.get('reasoning') or '')} chars, "
                       f"content {(msg.get('content') or '')[:40]!r}, usage {out.get('usage')}")
        say(self.name, f"ready; spent ${self.spent():.2f}")

    def delete(self, reason="requested"):
        ledger = self.load()
        c = client()
        for entry in self.live(ledger):
            try:
                c.delete(c.get(entry["id"]), wait=True, timeout=300)
            except Exception as exc:  # already gone (TTL): still close the entry
                entry["delete_error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
            entry.update(deleted_unix=time.time(), delete_reason=reason)
        self.save(ledger)
        self.token_file.unlink(missing_ok=True)
        say(self.name, f"deleted ({reason}); spent ${self.spent(ledger):.2f}")


def say(box, msg):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {box}: {msg}", flush=True)


def wait(box, check, minutes, what):
    end = time.time() + minutes * 60
    while time.time() < end:
        if check():
            return
        time.sleep(30)
    raise SystemExit(f"{box}: {what} not ready after {minutes} min; box left up for inspection")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("box")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("up", "launch", "info", "cost", "preview"):
        sub.add_parser(name)
    e = sub.add_parser("exec")
    e.add_argument("command")
    e.add_argument("--timeout", type=int, default=600)
    d = sub.add_parser("delete")
    d.add_argument("reason", nargs="?", default="requested")
    t = sub.add_parser("ttl")
    t.add_argument("minutes", type=int)
    a = p.parse_args()
    box = Box(a.box)
    if a.cmd == "up":
        box.up()
    elif a.cmd == "launch":
        box.launch()
    elif a.cmd == "info":
        s = box.sandbox()
        print(json.dumps({k: str(getattr(s, k, "n/a")) for k in ("state", "gpu", "gpu_type", "auto_destroy_at", "created_at")}
                         | {"spent_list_dollars": round(box.spent(), 2)}, indent=1))
    elif a.cmd == "cost":
        print(json.dumps(dict(spent_list_dollars=round(box.spent(), 2), rate=round(RATE, 4), live=len(box.live()))))
    elif a.cmd == "preview":
        box.preview()
    elif a.cmd == "exec":
        code, out = box.exec(a.command, a.timeout)
        print(out)
        sys.exit(code)
    elif a.cmd == "delete":
        box.delete(a.reason)
    elif a.cmd == "ttl":
        box.sandbox().set_ttl(a.minutes)


if __name__ == "__main__":
    main()
