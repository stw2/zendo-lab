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
  4. **Scoring:** `bash experiments/E03-codex-frontier/scripts/02_score.sh ARM`, then the table (`uv run python experiments/E03-codex-frontier/scripts/03_table.py`: `results/runs.md`, `results/metrics.json`) and the harness check (`bash experiments/E03-codex-frontier/scripts/05_compare_a2.sh E01_RUNS`, with E1's A2 run files).

## Result

All 460 dev games per arm, every game verified by `score --verify`. ZendoBench 1.0.0, through the Codex CLI with no tools, reasoning effort high, Codex's defaults otherwise: no output cap, top_p 0.98, verbosity low. The seed-only baseline, one submission from the two seed scenes, wins 4.7 ([P1](https://thesubstrate.science/records/7f391bde-3e66-43b6-9a50-d299f7b7e5b2)).

| Arm | Attempt | Headline T2-T6 [95% CI] | Experiments per game | Classes alive at first submission (median) | Room records |
|---|---|---|---|---|---|
| `gpt-6-astra-codex-high` | A16 | 94.3 [90.3, 96.3] | 17.14 | 1 | [P17](https://thesubstrate.science/records/3143857e-1e97-4667-88f1-16c8228d167f), [P18](https://thesubstrate.science/records/1b1d403d-5ca4-47a0-bf4d-b020e57fdb0a) |
| `gpt-6.1-sol-codex-high` | A14 | 89.7 [84.7, 92.7] | 18.10 | 1 | [P19](https://thesubstrate.science/records/8117a6b7-ce4c-46c7-9cfc-1b2fe62afcd9), [P20](https://thesubstrate.science/records/f11a20c9-8758-461d-a3cb-624ca6b2500b) |
| `gpt-6-sol-codex-high` | A13 | 69.2 [64.6, 73.5] | 19.23 | 2 | [P21](https://thesubstrate.science/records/83d200cc-3c36-4cde-8eae-3c1ad5268afb), [P22](https://thesubstrate.science/records/afbcc984-197a-4e2c-89ab-3150d42e6c69) |
| `gpt-5.6-terra-codex-high` | A15 | 40.8 [36.9, 45.1] | 11.08 | 3.5 | [P23](https://thesubstrate.science/records/602a6b09-0683-4dc2-aebd-d042736f2922), [P24](https://thesubstrate.science/records/73127491-c89e-4685-bcad-48a9ff5e5cf4) |
| `gpt-6-luna-codex-high` | A12 | 36.2 [32.0, 41.1] | 15.38 | 2 | [P25](https://thesubstrate.science/records/37b35a96-4080-4119-afc4-aedf1144cc63), [P26](https://thesubstrate.science/records/80a9d061-2941-46bc-b9b5-5596f5ab324b) |

**The harness changes play** ([P27](https://thesubstrate.science/records/f4ff537a-9cc4-4b5c-8550-ed3022a83291); `results/scores/luna-codex-vs-a2.compare.md`). GPT-6 Luna at effort high wins 8.7 points more [4.4, 13.0] through OpenRouter (E1's A2, 44.9) than through Codex (A12) on the same games, mostly on T5 and T6. Every Codex call returned a complete answer, so the gap is in play. Which difference between the harnesses causes it is not identified: the request shape, the sampling defaults, how the system prompt is passed, or the snapshot served. E3's arms therefore compare with each other, and with E1's HTTP arms only with this caveat.

No arm raised an isolation flag. Full table: [results/runs.md](results/runs.md). Records and digests: [results/findings.json](results/findings.json). Caveats: DESIGN.md amendments (A12's two parts).
