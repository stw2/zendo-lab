"""Prepare only E4's dedicated runtime; never copy credentials from another profile."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from claude_backend import CLI_SHA256, CLI_VERSION, STATE, digest, environment, profile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", action="store_true", help="Start the normal isolated Claude subscription login")
    args = parser.parse_args()
    for folder in ("bin", "config", "tmp", "calls", "instructions", "flags"):
        (STATE / folder).mkdir(parents=True, exist_ok=True)
    binary = STATE / "bin/claude"
    if not binary.exists():
        installed = shutil.which("claude")
        if not installed or digest(Path(installed).read_bytes()) != CLI_SHA256:
            raise SystemExit("Install the pinned official Claude Code 2.1.293 binary first; checksum mismatch.")
        shutil.copy2(Path(installed).resolve(), binary)
    if digest(binary.read_bytes()) != CLI_SHA256:
        raise SystemExit("Existing dedicated binary does not match the pinned checksum; not overwritten.")
    version = subprocess.check_output([str(binary), "--version"], env=environment(), text=True).strip()
    if not version.startswith(CLI_VERSION):
        raise SystemExit("CLI version mismatch")
    profile()
    (STATE / "setup.json").write_text(json.dumps({"claude_cli": CLI_VERSION,
                                                "claude_binary_sha256": CLI_SHA256}, indent=2) + "\n")
    print(json.dumps({"claude_cli": CLI_VERSION, "claude_binary_sha256": CLI_SHA256}))
    if args.login:
        subprocess.run([str(binary), "auth", "login", "--claudeai"], env=environment(), cwd=STATE / "calls", check=True)
    status = subprocess.run([str(binary), "auth", "status"], env=environment(), capture_output=True, text=True)
    info = json.loads(status.stdout)
    print(json.dumps({key: info.get(key) for key in ("loggedIn", "authMethod", "apiProvider")}))


if __name__ == "__main__":
    main()
