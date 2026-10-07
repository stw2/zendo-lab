**gpt-6-sol-codex-high** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T2 | 60 | 60 | 0 | 0 | 96.7 [87.8, 99.7] | 30 | 0.0% |
| T3 | 150 | 150 | 0 | 0 | 98.0 [92.9, 99.8] | 75 | 0.0% |
| T4 | 60 | 60 | 0 | 0 | 28.3 [17.2, 41.8] | 30 | 0.0% |
| T5 | 100 | 100 | 0 | 0 | 73.0 [62.8, 81.7] | 50 | 0.0% |
| T6 | 60 | 60 | 0 | 0 | 50.0 [36.2, 63.8] | 30 | 0.0% |

Headline (T2–T6, equal weights): 69.2 [64.6, 73.5]
complete: 430 of 430 headline items finished; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T1 | 30 | 30 | 0 | 0 | 100.0 [78.2, 100.0] | 15 | 0.0% |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 68.7 [64.0, 73.1] | 88.9 | 100.0 [62.7, 100.0] |

Configurations for gpt-6-sol-codex-high:

- e84f7b7cd75f: `{"agent": "codex_backend:CodexBackend (codex exec)", "agent_config": {"auth": "ChatGPT sign-in, a Codex home of its own", "call_folder": "new and empty per call", "catalog_edit": {"apply_patch_tool_type": null, "experimental_supported_tools": [], "multi_agent_version": null, "tool_mode": "direct_only"}, "catalog_sha256": "6b1f65a0f06f02eb9a0f4632af0775a97deaf7a88a734eeeba20bb1fcd8b9ad5", "codex_binary_sha256": "112fae7a5a1223e673c8a1791d32338f37df8b527ff1159bb8adac6c4dbf1b4b", "codex_cli": "0.160.0", "config": ["include_permissions_instructions=false", "include_apps_instructions=false", "include_collaboration_mode_instructions=false", "include_environment_context=false", "skills.include_instructions=false", "tools.update_plan.enabled=false", "tools.experimental_request_user_input.enabled=false", "web_search=\"disabled\"", "project_doc_max_bytes=0", "sandbox_mode=\"read-only\""], "features_disabled": ["apps", "auth_elicitation", "browser_use", "browser_use_external", "browser_use_full_cdp_access", "code_mode_host", "compaction_image_budget", "computer_use", "content_item_kinds", "daemon_auto_start", "enable_request_compression", "fast_mode", "goals", "guardian_approval", "guardian_reuse_parent_compaction", "hooks", "image_generation", "in_app_browser", "in_app_chat", "in_app_dictation", "in_app_local_automation", "in_app_updates", "mentions_v2", "multi_agent", "plugin_sharing", "plugins", "realtime_conversation", "remote_plugin", "shell_snapshot", "shell_tool", "skill_mcp_dependency_install", "skill_search", "sleep_tool", "system_proxy_fallback", "tool_call_mcp_elicitation", "tool_suggest", "unbounded_connection_retries", "unified_exec", "unified_exec_tty", "view_image", "workspace_dependencies", "worktrees", "write_stdin_approval"], "features_sha256": "8cbf4b6d2e424fdc7a6e505dd8e326121bf43792db025441a5fedc27bb3640a9", "flags": ["--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check", "--sandbox read-only", "--json"], "harness": "codex-exec", "model": "gpt-6-sol", "output_cap": "none settable in Codex (the provider's default)", "reasoning_effort": "high", "reasoning_summary": "detailed", "retries": {"backoff_seconds": [30, 60, 120, 300, 900], "jitter": "x0.75-1.25"}, "sandbox_profile_sha256": "27e25a33d937c05b07d8da5cc4f8f73124671e466b4761bd796ec737740db712", "service_tier": "default", "timeout": 3600, "traces": "every try: Codex's events and the server's messages (deltas counted), beside the run file"}, "agent_source_sha256": "d7dd576873089c2ce59d3794f8c672376aecdfc83a321c9ff5cd189f4f79f3ff", "backend": "function", "per_episode": false}`

Coverage (scored / manifest): T1: 15/15 classes, 5/5 families; T2: 30/30 classes, 7/7 families; T3: 75/75 classes, 10/10 families; T4: 30/30 classes, 5/5 families; T5: 50/50 classes, 17/17 families; T6: 30/30 classes, 7/7 families.
Seed-only MAP baseline on the scored items: 4.7%. One submission from seeds, no experiments; expected win rate with uniform MAP tie breaking on scored items, equal weight per headline tier.
T1-T4 share the 3-piece catalog prior because their tier is not revealed; T5 and T6 use their registered tier classes.
Rule catalogs are public and include classes used in experiments while this benchmark was developed. Sealed items hide seed pairs, not the rule universe. This benchmark does not establish contamination-free reasoning.
