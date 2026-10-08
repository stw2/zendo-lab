# E04: Claude baselines at high effort

Room experiment: [E4](https://thesubstrate.science/experiments/f8519620-4f56-49b5-a14a-4ca9b3e4ecee), in [Thread 1](https://thesubstrate.science/rooms/learning-to-test-hypotheses-da73e44a/threads/6cdedae4-ec06-4e7c-9462-ccf16fec373b). Prospective: locked by the first commit containing this design, before live inference. Changes afterward are dated amendments below.

## Question

Where do Haiku, Sonnet, Opus and Fable stand on ZendoBench 1.0.0 dev at high reasoning effort, with tools disabled and game prompts matched to E3's Codex runs? This is a descriptive baseline experiment, with no training or selected hypothesis. E3 supplies comparisons, not premises. Different model families and serving stacks prevent attributing cross-provider differences solely to model weights.

## Arms

Arms run strictly in this order. An arm's full run and verification finish before the next begins. Within one arm, at most 12 calls run concurrently, as in E3.

| Order | Arm | Explicit model ID |
|---|---|---|
| 1 | `claude-haiku-5-5-claude-high` | `claude-haiku-5-5` |
| 2 | `claude-sonnet-5-5-claude-high` | `claude-sonnet-5-5` |
| 3 | `claude-opus-5-5-claude-high` | `claude-opus-5-5` |
| 4 | `claude-fable-5-1-claude-high` | `claude-fable-5-1` |

All arms use native Claude Code 2.1.293, binary SHA-256 `4e21122a227857da1178aca3299700c1fd7f2b77c93f12e73c2c76db796a105e`, the owner's Claude subscription, effort `high`, adaptive thinking and `showThinkingSummaries: true`. No model alias, fallback, fast mode or effort downgrade is accepted. Check the response model and outgoing request every decision. Model IDs name provider models, not independently immutable weight snapshots.

### Matched to E3

- Unmodified ZendoBench 1.0.0, tag `v1.0.0`, commit `46c192e0ea10a5140a33c1280edb97b0127cc68c`; standard runner, player `model`, Python backend recorded as `function`, ungrammared reply policy.
- Exactly the benchmark system and user messages: no CLI identity, environment, date, memory, skills, role or extra budget text. No output schema or reformatting.
- Fresh CLI process and empty working directory per decision, no conversation state across calls.
- Empty tools: no Bash, files, web, MCP, plugin tools, skills or delegation callable by the model.
- Same dev manifest, game IDs, episode seeds and 12-call concurrency.
- Timeout 3,600 seconds; at most five wrapper retries after infrastructure failures, delays 30, 60, 120, 300 and 900 seconds times independent 0.75–1.25 jitter. Native API retries disabled. Exhaustion leaves the game unfinished. Never resample malformed replies or poor play.

### Declared differences

E3's outgoing settings were temperature 1, top-p 0.98, verbosity low and a null output cap. Current Claude models reject nondefault sampling controls, so temperature, top-p and top-k are omitted. Provider defaults are recorded without claiming their unknown values equal Codex's. Claude requires a finite output maximum: `max_tokens=128000`, the documented maximum for all four models, is checked on the wire. Cap-stopped output is retained and classified as truncated, never retried as infrastructure failure.

High effort is model-specific, not equal compute. Preserve all exposed thinking, summaries and redaction notices; hidden reasoning is unavailable. Serving, authentication, caching and response formats also differ. No service-tier override is imposed on Claude; returned service metadata stays in private traces. Inference hardware is provider-managed and unknown. The local orchestrator is an Apple M4 Max with 128 GB memory.

## Harness and preflight

`scripts/claude_backend.py` adapts Claude Code without patching ZendoBench or the pinned CLI. Its environment is allowlisted. Dedicated configuration and login live outside repositories; the actual home environment is not repurposed. User/project settings, CLAUDE.md, memory, hooks, discovery, IDE integration and remote MCP are disabled. Combine `--safe-mode`, `--restricted`, `--setting-sources ''`, strict empty MCP configuration and `--tools ''`. Built-in plugin/agent names may appear in CLI metadata, but must offer no tools or prompt text.

`--system-prompt-file` alone still adds SDK identity and environment messages. The documented `CLAUDE_CODE_EXTRA_BODY` override supplies the exact benchmark system and user messages; it does not alter provider safeguards. A loopback guard validates model, prompt roles/content, empty tools, high effort, adaptive thinking and output maximum BEFORE forwarding request bytes unchanged to `api.anthropic.com`. Extra requests or model fallback are rejected. Credentials pass only in memory to that fixed official origin; credential headers are never logged.

The entire CLI runs under `scripts/sandbox.sb`: user folders, repositories, raw results, sealed data, temporary folders and mounted volumes are inaccessible, except the dedicated runtime configuration, temporary files, call directories, pinned binary and prompt files. Each call directory must remain empty. Denied startup probes observed offline are explicitly classified in `04_denials.py`; other denials stop the run. No exception exposes repository or game files.

Before live inference: unit checks, sandbox read/write denial probes and offline mock API calls for all four IDs. Fixtures establish harness behavior, not model access or capability. Their traces are labelled `offline_fixture: true` and never enter results. Before each full arm: one complete dev game per tier (`--first 1`), saved in `results/runs/smoke/`, scored with `--verify`, and excluded from measurement. This verifies subscription access, accepted settings and transcript capture. No full arm proceeds after failed access, parity or transcript checks. A material protocol change requires a dated amendment before measuring.

An isolation flag, unexpected tool block, model change or failed transcript write stops the run. Infrastructure failure is distinct from a model refusal or malformed answer. All exposed output is preserved in either case.

Primary references: [CLI flags](https://code.claude.com/docs/en/cli-reference), [environment variables](https://code.claude.com/docs/en/env-vars), [model settings](https://code.claude.com/docs/en/model-config), [streaming](https://code.claude.com/docs/en/headless), [model limits](https://platform.claude.com/docs/en/models/overview). Captured requests determine whether preflight passes.

## Games and continuation

- Dev `bench-v1-dev.json`, all 460 games per arm: T1 30, T2 60, T3 150, T4 60, T5 100, T6 60. No train or sealed evaluation.
- Episode seeds from the manifest; model sampling unseeded.
- Continue a stopped run into a new part with `--exclude` over earlier parts. Exclude finished games; replay unfinished games from the beginning. Continuation is the same attempt. A deliberate rerun is a new Room attempt. Never overwrite or edit raw files after hashing.
- Subscription limits pause the arm; later arms do not overtake it. Persistent infrastructure breakers or isolation flags require diagnosis before continuation.
- On a runner stop, terminate and drain in-flight CLI processes so abandoned calls retain partial transcripts.

## Measures

Score every full run with `score --manifest dev --verify`. Headline: equal-weight T2–T6 mean win rate with 95% CI. Beside it: per-tier wins, T1, scored/unscored/unfinished counts, malformed rate, seed-only baseline and w0 bands. `diagnose` supplies the same experimenting, committing and submitted-rule measures as E3.

Report paired `zendo_bench compare` results on matching game IDs against E3's five Codex arms (A12–A16), retaining intervals. This is a descriptive comparison matrix, without post-hoc winner selection or a causal harness claim. State the sampling, output-cap and provider differences beside comparisons.

Harness diagnostics: failures/retries, incomplete answers, truncations, request mismatches and transcript completeness. Costs and token consumption remain private. Cap hits or appreciable formatting differences limit interpretation, rather than being silently corrected. Actual data-access violations void the affected arm; unresolved request mismatches prevent launch.

## Artifacts and provenance

Register each arm attempt against the accepted plan and full public commit before its smoke or measurement launch. Commit and push design/source first. Preserve E3's published history. E2 and other worktrees remain untouched.

Raw runs, smoke games, per-game diagnostics and compressed traces stay in git-ignored `results/runs/`. Every call try records `trace_id`, episode/decision, exact prompts/hashes, request settings, full provider SSE and CLI streams including partial thinking, stderr, response model, stop reason, timing and outcome. An incremental start without an end marks a hard interruption honestly. Flush traces throughout calls, not only on success. The final audit joins calls and retries to traces and checks complete outcomes or explicit interruptions. Hash raw files and compressed traces and register them as restricted outputs.

Public outputs are aggregate scores, comparisons, `results/runs.md`, flat `results/metrics.json`, sanitized preflight checks, source commits and hashes. No credentials, host names, absolute home paths, raw prompts/transcripts, private data, costs or token consumption enter commits or Room records. Publish findings/completion in Thread 1 with typed E4 plan/attempt provenance and E3 baseline attempt links.

## Artifacts ruled out

Peeking: empty tools, exact request guards, fresh directories and OS sandbox. Public benchmarks and unknown training corpora preclude a contamination-free claim. Seed-only and w0 comparisons separate prior guessing from testing. Malformed rates and truncation counts expose format/budget effects. Equal effort labels do not establish equal reasoning budgets. Full manifest coverage and paired intervals constrain noise. Submission and information-gain diagnostics expose early stopping or uninformative experimentation.

## Amendments

None.
