**claude-haiku-5-5-claude-high-v2 vs gpt-6.1-sol-codex-high** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Difference claude-haiku-5-5-claude-high-v2 - gpt-6.1-sol-codex-high, pts [95% CI] | Classes |
|---|---|---|---|---|---|---|
| T2 | 60 | 60 | 0 | 0 | -28.3 [-41.3, -15.4] | 30 |
| T3 | 150 | 150 | 0 | 0 | -37.3 [-45.0, -29.7] | 75 |
| T4 | 60 | 60 | 0 | 0 | -66.7 [-79.1, -54.2] | 30 |
| T5 | 100 | 100 | 0 | 0 | -54.0 [-63.6, -44.4] | 50 |
| T6 | 60 | 60 | 0 | 0 | -66.7 [-79.3, -54.1] | 30 |

Headline (T2–T6, equal weights): -50.6 [-55.4, -45.8]
complete: 430 of 430 headline items finished in both arms; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Difference claude-haiku-5-5-claude-high-v2 - gpt-6.1-sol-codex-high, pts [95% CI] | Classes |
|---|---|---|---|---|---|---|
| T1 | 30 | 30 | 0 | 0 | -13.3 [-29.8, 3.1] | 15 |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | -50.4 [-55.4, -45.5] | -100.0 | -37.8 [-87.8, 12.1] |

Configurations for claude-haiku-5-5-claude-high-v2:

- 6879f174fed1: `{"agent": "claude_backend:ClaudeBackend (claude -p)", "agent_config": {"auth": "Claude subscription; dedicated configuration and login", "claude_binary_sha256": "4e21122a227857da1178aca3299700c1fd7f2b77c93f12e73c2c76db796a105e", "claude_cli": "2.1.293", "flags": ["--safe-mode", "--restricted", "--setting-sources", "", "--settings", "{\"disableAllHooks\":true,\"showThinkingSummaries\":true,\"ultracode\":false,\"autoMemoryEnabled\":false,\"fastMode\":false}", "--strict-mcp-config", "--mcp-config", "{\"mcpServers\":{}}", "--tools", "", "--disallowedTools", "*", "--disable-slash-commands", "--no-chrome", "--no-session-persistence", "--permission-prompts", "none", "--effort", "high", "--output-format", "stream-json", "--verbose", "--include-partial-messages", "--max-turns", "1"], "harness": "claude-print", "max_tokens": 128000, "model": "claude-haiku-5-5", "prompt_substitution": "CLAUDE_CODE_EXTRA_BODY; unchanged benchmark messages plus fixed SDK identity", "reasoning_effort": "high", "request_guard": "loopback capture; validate before forwarding unchanged bytes to Anthropic", "response_policy": "first complete API response, unchanged; block all CLI continuations/repairs", "retries": {"backoff_seconds": [30, 60, 120, 300, 900], "jitter": "x0.75-1.25"}, "sampling": "provider defaults; temperature, top_p, top_k omitted", "sandbox_profile_sha256": "366cc296c2ec0281f7fa3d605d2a253e1d4494b301310fc0a84cb4f252404028", "sdk_identity": "You are a Claude agent, built on Anthropic's Claude Agent SDK.", "show_thinking_summaries": true, "thinking": {"display": "summarized", "type": "adaptive"}, "timeout": 3600, "traces": "incremental requests, full provider and CLI streams, stderr, every try"}, "agent_source_sha256": "27071effb8cca3480b9af17dc98991129341cb1b28665d66c69a0f725af6e3e5", "backend": "function", "per_episode": false}`

Configurations for gpt-6.1-sol-codex-high:

- 22238c6821a8: `{"agent": "codex_backend:CodexBackend (codex exec)", "agent_config": {"auth": "ChatGPT sign-in, a Codex home of its own", "call_folder": "new and empty per call", "catalog_edit": {"apply_patch_tool_type": null, "experimental_supported_tools": [], "multi_agent_version": null, "tool_mode": "direct_only"}, "catalog_sha256": "6b1f65a0f06f02eb9a0f4632af0775a97deaf7a88a734eeeba20bb1fcd8b9ad5", "codex_binary_sha256": "112fae7a5a1223e673c8a1791d32338f37df8b527ff1159bb8adac6c4dbf1b4b", "codex_cli": "0.160.0", "config": ["include_permissions_instructions=false", "include_apps_instructions=false", "include_collaboration_mode_instructions=false", "include_environment_context=false", "skills.include_instructions=false", "tools.update_plan.enabled=false", "tools.experimental_request_user_input.enabled=false", "web_search=\"disabled\"", "project_doc_max_bytes=0", "sandbox_mode=\"read-only\""], "features_disabled": ["apps", "auth_elicitation", "browser_use", "browser_use_external", "browser_use_full_cdp_access", "code_mode_host", "compaction_image_budget", "computer_use", "content_item_kinds", "daemon_auto_start", "enable_request_compression", "fast_mode", "goals", "guardian_approval", "guardian_reuse_parent_compaction", "hooks", "image_generation", "in_app_browser", "in_app_chat", "in_app_dictation", "in_app_local_automation", "in_app_updates", "mentions_v2", "multi_agent", "plugin_sharing", "plugins", "realtime_conversation", "remote_plugin", "shell_snapshot", "shell_tool", "skill_mcp_dependency_install", "skill_search", "sleep_tool", "system_proxy_fallback", "tool_call_mcp_elicitation", "tool_suggest", "unbounded_connection_retries", "unified_exec", "unified_exec_tty", "view_image", "workspace_dependencies", "worktrees", "write_stdin_approval"], "features_sha256": "8cbf4b6d2e424fdc7a6e505dd8e326121bf43792db025441a5fedc27bb3640a9", "flags": ["--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check", "--sandbox read-only", "--json"], "harness": "codex-exec", "model": "gpt-6.1-sol", "output_cap": "none settable in Codex (the provider's default)", "reasoning_effort": "high", "reasoning_summary": "detailed", "retries": {"backoff_seconds": [30, 60, 120, 300, 900], "jitter": "x0.75-1.25"}, "sandbox_profile_sha256": "27e25a33d937c05b07d8da5cc4f8f73124671e466b4761bd796ec737740db712", "service_tier": "default", "timeout": 3600, "traces": "every try: Codex's events and the server's messages (deltas counted), beside the run file"}, "agent_source_sha256": "d7dd576873089c2ce59d3794f8c672376aecdfc83a321c9ff5cd189f4f79f3ff", "backend": "function", "per_episode": false}`
