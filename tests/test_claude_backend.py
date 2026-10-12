"""E4's protocol guards and raw-stream reconstruction, without model inference."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "experiments/E04-claude-baselines/scripts"
spec = importlib.util.spec_from_file_location("e04_claude_backend", SCRIPTS / "claude_backend.py")
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)
MODEL = cb.MODELS[0]


@pytest.fixture(autouse=True)
def isolated_flags(tmp_path, monkeypatch):
    monkeypatch.setattr(cb, "STATE", tmp_path)


def valid_request():
    return {"model": MODEL, "system": [{"type": "text", "text": cb.SDK_IDENTITY}, {"type": "text", "text": "system"}],
            "messages": [{"role": "user", "content": "user"}], "tools": [],
            "max_tokens": 128000, "thinking": cb.THINKING,
            "output_config": {"effort": "high"}, "stream": True}


@pytest.mark.parametrize("field,value", [
    ("model", cb.MODELS[1]), ("tools", [{"name": "Bash"}]),
    ("system", [{"type": "text", "text": "system\nCLI identity"}]),
    ("messages", [{"role": "user", "content": "user\ncontext"}]),
    ("output_config", {"effort": "medium"}), ("max_tokens", 64000),
    ("temperature", 0.7), ("top_p", 0.98), ("service_tier", "priority"),
])
def test_guard_rejects_changed_protocol(field, value):
    body = valid_request()
    cb.validate_request(body, MODEL, "system", "user")
    body[field] = value
    with pytest.raises(ValueError):
        cb.validate_request(body, MODEL, "system", "user")


def events():
    stream = [json.loads(chunk.decode().split("data: ", 1)[1]) for chunk in cb.mock_response(MODEL)]
    return [{"type": "system", "subtype": "init", "model": MODEL, "claude_code_version": cb.CLI_VERSION,
             "tools": [], "mcp_servers": [], "skills": [], "slash_commands": []},
            *[{"type": "stream_event", "event": event} for event in stream],
            {"type": "result", "is_error": False, "terminal_reason": "completed"}]


def test_reconstruct_thinking_and_answer_from_partial_stream():
    reply = cb.read_reply(events(), "", 0, {}, MODEL)
    assert (reply.text, reply.record["reasoning"], reply.record["stop_reason"]) == ("OK", "Offline fixture.", "end_turn")


def test_truncated_output_is_not_retryable_infrastructure_failure():
    es = events()
    next(e["event"] for e in es if e.get("event", {}).get("type") == "message_delta")["delta"]["stop_reason"] = "max_tokens"
    reply = cb.read_reply(es, "", 0, {}, MODEL)
    assert reply.text == "OK" and reply.finish == cb.FINISH_CUT_IN_ACTION


def test_incomplete_stream_is_failure_not_a_scored_answer():
    es = [e for e in events() if e.get("event", {}).get("type") != "message_stop"]
    with pytest.raises(cb.BackendFailure):
        cb.read_reply(es, "", 0, {}, MODEL)


def test_synthetic_api_error_is_not_model_output():
    es = events()
    es[-1].update(is_error=True, terminal_reason="api_error", result="API error")
    with pytest.raises(cb.BackendFailure):
        cb.read_reply(es, "", 1, {}, MODEL)


def test_temporary_provider_rate_limit_is_retryable_not_subscription_quota():
    es = events()
    es[-1].update(is_error=True, terminal_reason="api_error", api_error_status=429,
                  result="API Error: Server is temporarily limiting requests (not your usage limit) · Error")
    with pytest.raises(cb.BackendFailure):
        cb.read_reply(es, "", 1, {}, MODEL)


def test_actual_subscription_limit_stops_the_arm():
    es = events()
    es[-1].update(is_error=True, terminal_reason="api_error", result="You've hit your usage limit")
    with pytest.raises(cb.UsageLimitReached):
        cb.read_reply(es, "", 1, {}, MODEL)


def test_first_provider_response_survives_blocked_cli_repair_unchanged():
    es = events()
    raw = [e["event"] for e in es if e.get("type") == "stream_event"]
    next(e for e in raw if e["type"] == "message_delta")["delta"]["stop_reason"] = "tool_use"
    malformed = '<parameter name="experiment">malformed</parameter>'
    next(e for e in raw if e.get("delta", {}).get("type") == "text_delta")["delta"]["text"] = malformed
    es[-1].update(is_error=True, terminal_reason="api_error", result="409: continuation blocked")
    reply = cb.read_reply(es, "", 1, {}, MODEL, provider_events=raw)
    assert reply.text == malformed and reply.finish == cb.FINISH_ACTION
    assert reply.record["stop_reason"] == "tool_use"
    assert reply.record["reasoning"] == "Offline fixture."


def test_actual_provider_tool_block_still_stops_the_run():
    es = events()
    raw = [e["event"] for e in es if e.get("type") == "stream_event"]
    next(e for e in raw if e["type"] == "content_block_start")["content_block"] = {"type":"tool_use","name":"Bash"}
    with pytest.raises(cb.IsolationFlag):
        cb.read_reply(es, "", 0, {}, MODEL, provider_events=raw)


def test_streamed_tool_call_stops_run():
    es = events()
    next(e["event"] for e in es if e.get("event", {}).get("type") == "content_block_start")["content_block"] = {"type": "tool_use", "name": "Bash"}
    with pytest.raises(cb.IsolationFlag):
        cb.read_reply(es, "", 0, {}, MODEL)


def test_retry_trace_id_is_preserved_and_exhaustion_unfinished():
    backend = object.__new__(cb.ClaudeBackend)
    backend.backoff = []
    backend._try = lambda *args: (_ for _ in ()).throw(cb.BackendFailure("offline failure", {"trace_id": "failed-try"}))
    request = SimpleNamespace(messages=({"role": "system", "content": "s"}, {"role": "user", "content": "u"}), decision=0, episode_id="game")
    with pytest.raises(cb.GameStopped) as stopped:
        backend._call(request)
    assert stopped.value.record["retries"][0]["trace_id"] == "failed-try"


def test_trace_retains_partial_output_and_redacts_credentials(tmp_path):
    path = tmp_path / "trace.jsonl"
    trace = cb.Trace(path, "join-id")
    trace.secrets.add("fake-secret-for-test")
    trace.write("start", {"episode": "fixture"})
    trace.write("provider_stream", "partial thinking fake-secret-for-test")
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert all(row["trace_id"] == "join-id" for row in rows)
    assert "partial thinking" in rows[-1]["value"]
    assert "fake-secret-for-test" not in path.read_text()


def test_environment_does_not_inherit_credentials_or_effort(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "unrelated-secret")
    monkeypatch.setenv("CLAUDE_CODE_EFFORT_LEVEL", "low")
    env = cb.environment()
    assert "ANTHROPIC_API_KEY" not in env and env["CLAUDE_CODE_EFFORT_LEVEL"] == "high"


@pytest.mark.parametrize("failure", ["http401", "http429", "http500", "stream", "transport"])
def test_known_provider_failure_qualifies_for_blocked_recovery(failure):
    guard = object.__new__(cb.Guard)
    import threading
    guard.response_complete = threading.Event()
    guard.responses = [int(failure[4:])] if failure.startswith("http") else [200]
    guard.events = [{"type": "error", "error": {"type": "api_error"}}] if failure == "stream" else []
    guard.transport_failed = failure == "transport"
    assert guard.recovery_reason()
    # A completed response, including an output-cap stop, is never retried.
    guard.response_complete.set()
    assert guard.recovery_reason() is None


def test_unexplained_second_request_is_still_an_isolation_violation():
    import threading
    guard = object.__new__(cb.Guard)
    guard.response_complete = threading.Event()
    guard.responses = [200]
    guard.events = [{"type": "message_start"}]
    guard.transport_failed = False
    assert guard.recovery_reason() is None
