"""E03 setup, once, before any game: the pinned Codex CLI, its own home and login, and the frozen settings.

`python 00_setup.py` (from the repository root, `uv run python ...`):
1. installs @openai/codex 0.160.0 (codex-cli/package.json and its lock) into the state folder
   (~/.cache/zendo-lab/e03-codex, outside any repository: the sandbox closes the repositories);
2. checks the login of Codex's own home there (not the owner's ~/.codex); if there is none, it prints the
   command that logs in with ChatGPT, and stops;
3. freezes, with their sha256 in setup.json: features.json, every feature on by default in this CLI (all are
   disabled in the runs), and catalog.json, the server's model catalog with codex_backend.CATALOG_EDIT applied
   to each model. A second call keeps them; `--refreeze` writes them again.
"""

import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from codex_backend import CATALOG_EDIT, CODEX_VERSION, HERE, STATE, binary, environment, file_sha256  # noqa: E402


def run(*args, **kw):
    return subprocess.run([str(binary()), *args], capture_output=True, text=True, env=environment(), **kw)


def main():
    for folder in ("codex-cli", "codex-home", "home", "tmp", "calls", "instructions"):
        (STATE / folder).mkdir(parents=True, exist_ok=True)
    cli = STATE / "codex-cli"
    shutil.copy(HERE / "codex-cli" / "package.json", cli / "package.json")
    lock = HERE / "codex-cli" / "package-lock.json"
    if lock.exists():
        shutil.copy(lock, cli / "package-lock.json")
        subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=cli, check=True)
    else:
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=cli, check=True)
        shutil.copy(cli / "package-lock.json", lock)
    version = run("--version").stdout.split()
    assert version and version[-1] == CODEX_VERSION, version
    print(f"codex {version[-1]}, binary sha256 {file_sha256(binary())[:16]}…")

    status = run("login", "status")
    if status.returncode != 0 or "logged in" not in (status.stdout + status.stderr).lower():
        print("Codex's own home has no login. Log in with ChatGPT, then run this again:\n"
              f"  CODEX_HOME={STATE / 'codex-home'} {binary()} login --device-auth")
        return 2
    print("login:", (status.stdout + status.stderr).strip().splitlines()[0])

    setup_path = STATE / "setup.json"
    if setup_path.exists() and "--refreeze" not in sys.argv:
        print("setup.json exists; kept (--refreeze writes it again):", setup_path.read_text())
        return 0
    rows = run("features", "list", check=True).stdout.splitlines()
    enabled = [cols[0] for cols in (row.split() for row in rows)
               if len(cols) >= 3 and cols[-1] == "true" and cols[1] != "removed"]
    (STATE / "features.json").write_text(json.dumps(enabled, indent=1) + "\n")
    catalog = json.loads(run("debug", "models", check=True).stdout)
    models = catalog["models"] if isinstance(catalog, dict) else catalog
    for model in models:
        model.update(CATALOG_EDIT)
    (STATE / "catalog.json").write_text(json.dumps(catalog, indent=1) + "\n")
    setup = {"codex_cli": CODEX_VERSION, "codex_binary_sha256": file_sha256(binary()),
             "features.json": file_sha256(STATE / "features.json"), "catalog.json": file_sha256(STATE / "catalog.json"),
             "models": sorted(m["slug"] for m in models)}
    setup_path.write_text(json.dumps(setup, indent=1) + "\n")
    print(json.dumps(setup, indent=1))
    print(f"{len(enabled)} features to disable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
