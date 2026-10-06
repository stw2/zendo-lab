# E03: Frontier models through Codex on dev

Five OpenAI models through the Codex CLI with every tool off, on ZendoBench 1.0.0's full dev set (460 games): [DESIGN.md](DESIGN.md). Room experiment: [E3](https://thesubstrate.science/experiments/b574da60-108b-4f3a-b9a1-52ebbe87c35e).

- **Backend:** `scripts/codex_backend.py`, a ZendoBench backend around `codex exec` (Codex CLI 0.160.0, pinned with its lockfile in `scripts/codex-cli/`). ZendoBench is not patched; its own runner plays and records the games.
- **Isolation:** no tools in the request, nothing added to the prompt, a Codex home of its own, one empty folder per call, and a macOS sandbox (`scripts/sandbox.sb`) that closes the repositories and run files. Anything else the model does raises a flag and stops the run. `results/isolation-check.txt` holds the checks before the first game.
- **State outside the repository** (`~/.cache/zendo-lab/e03-codex`): the CLI, Codex's own login, the frozen model catalog and feature list, the instructions files and any flags. Run files stay with the owner (`results/runs/`, git-ignored); `results/scores/<arm>.files.json` holds their sha256.
- **Needs:** macOS, Node/npm, and a ChatGPT login with Codex access.
- **Run:**
  1. **Setup, once:** `uv run python experiments/E03-codex-frontier/scripts/00_setup.py` installs the CLI and freezes the catalog and features; the first call prints the login command for Codex's own home.
  2. **Checks:** `uv run python experiments/E03-codex-frontier/scripts/00_check.py --call > experiments/E03-codex-frontier/results/isolation-check.txt`.
  3. **Each arm, one at a time, in DESIGN.md's order:** `SMOKE=1` first for a one-game-per-tier connection check, then `bash experiments/E03-codex-frontier/scripts/01_run.sh ARM`. The script resumes by itself after the ChatGPT usage limit, and stops on an isolation flag (exit 5). `scripts/01_all.sh` chains every arm not yet complete in that order, smoke first. It waits for a running arm, and stops at the first flag or failure.
  4. **Scoring:** `bash experiments/E03-codex-frontier/scripts/02_score.sh ARM`.
