# E03: Frontier models through Codex on dev

Room experiment: [E3](https://thesubstrate.science/experiments/b574da60-108b-4f3a-b9a1-52ebbe87c35e), in the Thread [Campaign: can training teach small models to test hypotheses?](https://thesubstrate.science/rooms/learning-to-test-hypotheses-da73e44a/threads/6cdedae4-ec06-4e7c-9462-ccf16fec373b). Locked at the commit that adds this file; changes are dated amendments at the end.

## Question

Where do OpenAI's current frontier models stand on ZendoBench 1.0.0 dev when they play through the Codex CLI with every tool off, and how do they play: how much information do their experiments gain, and how many rule classes are still alive when they submit?

E03 is descriptive: it tests no hypothesis. It extends E1's reference points upward, with E1's measures. It also checks the harness: GPT-6 Luna at effort high played E1 through OpenRouter (A2) and plays here through Codex.

## Arms

The arms run one at a time, in this order; each arm's run finishes before the next one starts.

| Order | Arm | Model (Codex's slug) |
|---|---|---|
| 1 | `gpt-6-luna-codex-high` | `gpt-6-luna` |
| 2 | `gpt-6-sol-codex-high` | `gpt-6-sol` |
| 3 | `gpt-6.1-sol-codex-high` | `gpt-6.1-sol` |
| 4 | `gpt-5.6-terra-codex-high` | `gpt-5.6-terra` (Codex lists no GPT-6 Terra) |
| 5 | `gpt-6-astra-codex-high` | `gpt-6-astra` |

**Every arm:** reasoning effort high; reasoning summaries `detailed`, kept in the call record (a summary is written beside the reasoning and does not change the answer); the default service tier; Codex's default verbosity for the model; signed in with ChatGPT.

**The harness** (`scripts/codex_backend.py`, a ZendoBench backend; ZendoBench is not patched). ZendoBench's own runner plays, records and scores the games. Each decision is one stateless `codex exec` call:
- ZendoBench's system prompt becomes Codex's instructions (`model_instructions_file`);
- its user message is the prompt;
- the turn's last agent message is the reply, read under ZendoBench's ungrammared reply policy, as E1's HTTP arms were.

The player is `model`: each call answers from its prompt alone, and no state is kept between calls. The run header names the backend `function`, ZendoBench's kind for a Python backend, with the Codex settings as its `agent_config`. That is the name under which `score --verify` reads replies ungrammared (`records.GRAMMARED`), as these replies are.

**Isolation.** The model must see nothing but the game it is playing. Five layers, checked by `scripts/00_check.py` before the first game (its output is `results/isolation-check.txt`):
1. **No tools in the request.** Every Codex feature on by default is disabled: shell, code execution, web search, apps, plugins, MCP, skills, hooks and sub-agents. The plan and user-input tools, AGENTS.md (`project_doc_max_bytes=0`) and the user's config and rules (`--ignore-user-config`, `--ignore-rules`) are off too. Even then Codex offers some tools from each model's catalog entry: `exec` and `wait` in code mode, `request_user_input` and `apply_patch`. So the catalog is frozen from Codex's server at setup with four edits to each model: no multi-agent version, tool mode `direct_only`, no experimental tools, no `apply_patch`. The server's echo of a request (`00_check.py --call`) shows an empty tool list.
2. **Nothing added to the prompt.** Codex's own context messages are switched off: permissions, apps, collaboration modes, environment context and skills. Without the multi-agent edit above, Codex would also add a sub-agent role message. With these settings `codex debug prompt-input` shows the model the user message alone, and the request echo counts only the instructions and that message.
3. **Its own Codex home.** The runs use a Codex home with its own ChatGPT login, not the owner's `~/.codex` and its sessions. Calls are `--ephemeral`, so no transcript is kept. The codex process gets no API keys and none of the owner's environment.
4. **One empty folder per call.** Each call runs in a new empty folder outside any repository, with Codex's sandbox read-only. The folder must still be empty after the call, and it is then deleted.
5. **An OS sandbox.** The whole codex process runs under macOS's sandbox (`scripts/sandbox.sb`). Every user folder (the repositories and their run files, `~/.codex`, ZendoBench's sealed salt), every temporary folder and every volume is closed to reading and writing. Only the state folder's parts that Codex needs stay open: its home and login, the call folders, the pinned CLI, the frozen catalog and the instructions files.

**Flags.** Each of these raises an isolation flag:
- a started or completed item other than an agent message, a reasoning summary or a Codex notice (a command, a file read or change, a tool, MCP or web call);
- a file left in the call's folder;
- a sandbox denial in the system log for the codex process (`scripts/04_denials.sh`, after each run part).

A flag voids the game in flight, writes the call's events to a flag file, and stops the run. Nothing resumes until the cause is understood and recorded as an amendment.

**Held fixed:**
- ZendoBench 1.0.0 (tag `v1.0.0`, commit `46c192e`), player `model`, the default reply policy, the dev manifest;
- Codex CLI 0.160.0, from npm with its lockfile (`scripts/codex-cli/`), and its binary's sha256;
- the frozen catalog and the list of disabled features (their sha256 in every run header);
- the isolation settings above;
- 12 calls in flight.

**Recorded, not held fixed:**
- which snapshot serves each slug: Codex does not report it;
- Codex's reconnects and notices;
- the waits after the usage limit.

**Codex's defaults, as the server echoes them** (`00_check.py --call`; not settable through Codex):
- **No output cap** (`max_output_tokens` null). E1's HTTP arms had 65,536 tokens a call.
- **Sampling:** temperature 1.0, top-p 0.98, verbosity low, truncation disabled.

**Before each arm:** a connection check (`SMOKE=1`, the first game of each tier). It is not a measurement and is not reported.

## Games

- **Manifest:** dev (`bench-v1-dev.json`), all 460 items: T1 30, T2 60, T3 150, T4 60, T5 100, T6 60.
- **Games per arm:** 460, one run per arm.
- **Resumes:** a stopped run resumes with `--exclude` into a new part file, and the parts are scored together. A resumed run is the same attempt. When the ChatGPT usage limit stops a part, the run waits 30 minutes and resumes (`scripts/01_run.sh`).
- **A failed call** (a failed turn, an error, a timeout) is retried 5 times with backoff. After that the game is left unfinished and played again by the next part, never scored as a loss.
- **Seeds:** the episode seeds come from the manifest; the models are not seeded.

## Measures

From `score --verify` (`results/scores/<arm>.score.json`):
- **Headline:** the equal-weight mean win rate over T2-T6, with its 95% CI.
- Wins per tier and T1; games scored, unscored and unfinished; the malformed rate; the seed-only baseline and the w0 bands beside the headline.

From `diagnose`: E1's experimenting, committing and submitted-rule measures (`results/scores/<arm>.diagnose.md`).

**The harness check:** `zendo_bench compare` of `gpt-6-luna-codex-high` with E1's A2 (`gpt-6-luna-openrouter-high`) on the same 460 games. A paired difference in win rate and in the behaviour measures separates the harness's effect from the models'.

From the run files: calls, calls without an answer, retries, and isolation flags (expected 0). As conventions rule 7 says, token counts and costs are not published.

`results/runs.md` holds one row per arm with its configuration, results and run-file sha256; `results/metrics.json` holds the headline numbers.

**Result that would change our mind.** If Luna through Codex differs from Luna through OpenRouter (A2) by more than the paired compare's interval, the harness changes play. Comparisons of E03's arms with E1's HTTP arms must then carry that caveat. Any isolation flag that turns out to be a model reading files would void every game of that arm.

## Artifacts ruled out

- **Peeking:** the five isolation layers and the flags above. `results/isolation-check.txt` holds `00_check.py`'s output before the first game.
- **Prior, not experimentation:** each headline sits beside the seed-only baseline and the w0 bands, and `p_first` shows how much of a win was decided before experimenting.
- **Contamination:** the dev rule catalogs and ZendoBench are public, and these models' training data is not known. E03 makes no claim of contamination-free reasoning.
- **Budget:** one effort, high, for every arm, and no output cap. Calls without an answer are reported.
- **Format:** the malformed rate is reported beside each headline.
- **Noise:** 460 games per arm, and arms are compared only where CIs separate. The harness check is paired.
- **Degenerate stopping:** no training here. Submissions per game and `p_first` are reported.

## Records

- **Run files** (`results/runs/`, git-ignored) hold every game with its reasoning summaries. They stay with the owner, and each attempt reports them as restricted outputs with their sha256 and size.
- **Call traces** (`results/runs/traces/<part>.traces.jsonl.gz`, git-ignored, kept for analysis after the run). Each try of each call gets one line:
  - its metadata, outcome and `trace_id`, which joins it to the call record in the run file;
  - Codex's whole event stream and its stderr lines;
  - the server's messages from Codex's websocket trace: the response objects, which echo the request's tools and settings, plus rate-limit and timing messages. Streamed deltas are counted, not kept.

  A line in which any value of Codex's login file appears is withheld. Traces are reported like the run files: restricted, with their sha256.
- **The Codex state folder** stays outside the repository (`~/.cache/zendo-lab/e03-codex`): the CLI, the login, the frozen catalog, the instructions files and the flags. Run headers record the sha256 of the catalog, the features and the sandbox profile, never paths or credentials.
- **Committed:** `results/scores/`, `results/runs.md`, `results/metrics.json`, `results/isolation-check.txt`.
- **Billing:** the owner's ChatGPT subscription, through Codex. Usage stays with the owner.

## Amendments

- **2026-10-06, A12 (`gpt-6-luna-codex-high`): part 1 stopped by the call traces; trace reading fixed before A13.**
  - **What happened:** at 21:55:54Z, one call's websocket trace held a server message that parsed as a bare number. The trace code read every message as an object and raised `AttributeError`. That stopped part 1 (exit 1) after 4,055 calls. The call itself had answered normally. The 11 games in flight were left unfinished and replayed in part 2, as the same attempt, under the resume rule above.
  - **Part 2:** `scripts/01_all.sh` started it at 21:56:33Z, at 81a4ddb, with the backend of 9939c14. It finished every game, exit 0.
  - **Fix:** the trace keeps such a message as it parsed. A failure to read the trace now leaves a note in the trace line instead of failing the call. Event lines that are not objects count as unreadable. Nothing that reaches the model or the game changed.
  - **Which code ran:** both parts of A12 ran the backend of 9939c14. The arms from A13 on run the backend of the commit that adds this amendment.
