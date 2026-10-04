"""The ZendoBench pin is installed and plays a game end to end."""

import importlib.metadata
import json

import pytest


@pytest.mark.parametrize("package", ["zendo-engine", "zendo-bench"])
def test_zendobench_is_the_pinned_release(package):
    assert importlib.metadata.version(package) == "1.0.0"


def submit_true(messages):
    return '{"action":"submit","rule":"true"}'


def test_a_game_plays_and_its_run_file_records_the_release(tmp_path):
    from zendo_bench import play

    out = tmp_path / "run.jsonl"
    result = play(submit_true, player="model", tiers=["T2"], first=1, out=str(out))
    assert result.counts["finished"] == 1
    header = json.loads(out.read_text().splitlines()[0])
    assert {k: v for k, v in header["runtime_versions"].items() if k.startswith("zendo")} == {
        "zendo-bench": "1.0.0", "zendo-engine": "1.0.0"}
