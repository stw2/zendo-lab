**gpt-6-luna-openrouter-high vs gpt-6-luna-codex-high** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Difference gpt-6-luna-openrouter-high - gpt-6-luna-codex-high, pts [95% CI] | Classes |
|---|---|---|---|---|---|---|
| T2 | 60 | 60 | 0 | 0 | 0.0 [-12.5, 12.5] | 30 |
| T3 | 150 | 150 | 0 | 0 | 8.0 [0.8, 15.2] | 75 |
| T4 | 60 | 60 | 0 | 0 | 3.3 [-5.3, 11.9] | 30 |
| T5 | 100 | 100 | 0 | 0 | 19.0 [10.7, 27.3] | 50 |
| T6 | 60 | 60 | 0 | 0 | 13.3 [0.4, 26.3] | 30 |

Headline (T2–T6, equal weights): 8.7 [4.4, 13.0]
complete: 430 of 430 headline items finished in both arms; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Difference gpt-6-luna-openrouter-high - gpt-6-luna-codex-high, pts [95% CI] | Classes |
|---|---|---|---|---|---|---|
| T1 | 30 | 30 | 0 | 0 | -3.3 [-16.0, 9.3] | 15 |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 9.1 [4.5, 13.7] | 22.2 | 1.0 [-5.5, 7.6] |

Configurations for gpt-6-luna-openrouter-high:

- 1f7145415780: `{"backend": "openai-chat-completions", "guided": null, "model": "openai/gpt-6-luna", "sampling": {"max_tokens": 65536, "reasoning": {"effort": "high"}}}`

Configurations for gpt-6-luna-codex-high:

- 9fa0c15386c1: `{"agent": "codex_backend:CodexBackend (codex exec)", "agent_config": {"auth": "ChatGPT sign-in, a Codex home of its own", "call_folder": "new and empty per call", "catalog_edit": {"apply_patch_tool_type": null, "experimental_supported_tools": [], "multi_agent_version": null, "tool_mode": "direct_only"}, "catalog_sha256": "6b1f65a0f06f02eb9a0f4632af0775a97deaf7a88a734eeeba20bb1fcd8b9ad5", "codex_binary_sha256": "112fae7a5a1223e673c8a1791d32338f37df8b527ff1159bb8adac6c4dbf1b4b", "codex_cli": "0.160.0", "config": ["include_permissions_instructions=false", "include_apps_instructions=false", "include_collaboration_mode_instructions=false", "include_environment_context=false", "skills.include_instructions=false", "tools.update_plan.enabled=false", "tools.experimental_request_user_input.enabled=false", "web_search=\"disabled\"", "project_doc_max_bytes=0", "sandbox_mode=\"read-only\""], "features_disabled": ["apps", "auth_elicitation", "browser_use", "browser_use_external", "browser_use_full_cdp_access", "code_mode_host", "compaction_image_budget", "computer_use", "content_item_kinds", "daemon_auto_start", "enable_request_compression", "fast_mode", "goals", "guardian_approval", "guardian_reuse_parent_compaction", "hooks", "image_generation", "in_app_browser", "in_app_chat", "in_app_dictation", "in_app_local_automation", "in_app_updates", "mentions_v2", "multi_agent", "plugin_sharing", "plugins", "realtime_conversation", "remote_plugin", "shell_snapshot", "shell_tool", "skill_mcp_dependency_install", "skill_search", "sleep_tool", "system_proxy_fallback", "tool_call_mcp_elicitation", "tool_suggest", "unbounded_connection_retries", "unified_exec", "unified_exec_tty", "view_image", "workspace_dependencies", "worktrees", "write_stdin_approval"], "features_sha256": "8cbf4b6d2e424fdc7a6e505dd8e326121bf43792db025441a5fedc27bb3640a9", "flags": ["--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check", "--sandbox read-only", "--json"], "harness": "codex-exec", "model": "gpt-6-luna", "output_cap": "none settable in Codex (the provider's default)", "reasoning_effort": "high", "reasoning_summary": "detailed", "retries": {"backoff_seconds": [30, 60, 120, 300, 900], "jitter": "x0.75-1.25"}, "sandbox_profile_sha256": "27e25a33d937c05b07d8da5cc4f8f73124671e466b4761bd796ec737740db712", "service_tier": "default", "timeout": 3600, "traces": "every try: Codex's events and the server's messages (deltas counted), beside the run file"}, "agent_source_sha256": "3d628ac3b5bb201aec44b5c4b257f4fe6b801faf2304198f2d47d9371914341f", "backend": "function", "per_episode": false}`
