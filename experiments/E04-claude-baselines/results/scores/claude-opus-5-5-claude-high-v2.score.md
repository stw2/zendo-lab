**claude-opus-5-5-claude-high-v2** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T2 | 60 | 60 | 0 | 0 | 100.0 [88.4, 100.0] | 30 | 0.0% |
| T3 | 150 | 150 | 0 | 0 | 98.0 [92.9, 99.8] | 75 | 0.0% |
| T4 | 60 | 60 | 0 | 0 | 75.0 [60.4, 86.4] | 30 | 0.1% |
| T5 | 100 | 100 | 0 | 0 | 96.0 [87.4, 99.4] | 50 | 0.0% |
| T6 | 60 | 60 | 0 | 0 | 85.0 [69.2, 94.7] | 30 | 0.1% |

Headline (T2–T6, equal weights): 90.8 [85.5, 93.9]
complete: 430 of 430 headline items finished; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T1 | 30 | 30 | 0 | 0 | 100.0 [78.2, 100.0] | 15 | 0.0% |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 90.5 [85.1, 93.7] | 100.0 | 100.0 [62.7, 100.0] |

Configurations for claude-opus-5-5-claude-high-v2:

- 9999422f8ce8: `{"agent": "claude_backend:ClaudeBackend (claude -p)", "agent_config": {"auth": "Claude subscription; dedicated configuration and login", "claude_binary_sha256": "4e21122a227857da1178aca3299700c1fd7f2b77c93f12e73c2c76db796a105e", "claude_cli": "2.1.293", "flags": ["--safe-mode", "--restricted", "--setting-sources", "", "--settings", "{\"disableAllHooks\":true,\"showThinkingSummaries\":true,\"ultracode\":false,\"autoMemoryEnabled\":false,\"fastMode\":false}", "--strict-mcp-config", "--mcp-config", "{\"mcpServers\":{}}", "--tools", "", "--disallowedTools", "*", "--disable-slash-commands", "--no-chrome", "--no-session-persistence", "--permission-prompts", "none", "--effort", "high", "--output-format", "stream-json", "--verbose", "--include-partial-messages", "--max-turns", "1"], "harness": "claude-print", "max_tokens": 128000, "model": "claude-opus-5-5", "prompt_substitution": "CLAUDE_CODE_EXTRA_BODY; unchanged benchmark messages plus fixed SDK identity", "reasoning_effort": "high", "request_guard": "loopback capture; validate before forwarding unchanged bytes to Anthropic", "response_policy": "first complete API response, unchanged; block all CLI continuations/repairs", "retries": {"backoff_seconds": [30, 60, 120, 300, 900], "jitter": "x0.75-1.25"}, "sampling": "provider defaults; temperature, top_p, top_k omitted", "sandbox_profile_sha256": "366cc296c2ec0281f7fa3d605d2a253e1d4494b301310fc0a84cb4f252404028", "sdk_identity": "You are a Claude agent, built on Anthropic's Claude Agent SDK.", "show_thinking_summaries": true, "thinking": {"display": "summarized", "type": "adaptive"}, "timeout": 3600, "traces": "incremental requests, full provider and CLI streams, stderr, every try"}, "agent_source_sha256": "27071effb8cca3480b9af17dc98991129341cb1b28665d66c69a0f725af6e3e5", "backend": "function", "per_episode": false}`

Coverage (scored / manifest): T1: 15/15 classes, 5/5 families; T2: 30/30 classes, 7/7 families; T3: 75/75 classes, 10/10 families; T4: 30/30 classes, 5/5 families; T5: 50/50 classes, 17/17 families; T6: 30/30 classes, 7/7 families.
Seed-only MAP baseline on the scored items: 4.7%. One submission from seeds, no experiments; expected win rate with uniform MAP tie breaking on scored items, equal weight per headline tier.
T1-T4 share the 3-piece catalog prior because their tier is not revealed; T5 and T6 use their registered tier classes.
Rule catalogs are public and include classes used in experiments while this benchmark was developed. Sealed items hide seed pairs, not the rule universe. This benchmark does not establish contamination-free reasoning.
