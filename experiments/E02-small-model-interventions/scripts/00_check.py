"""00_check.py: the interventions without the model, before any measurement (not reported).

A scripted engine stands in for MLX. It submits a fixed rule whenever available_actions offers submit,
and otherwise runs a seeded random scene. Through `intervene.Intervention` it plays the first item of
each tier in every arm and in a pass-through arm (no intervention, as A8 played), into
results/runs/check/. Each run file must pass `score --verify` and `diagnose`. Per arm:
- pass-through: the engine is given each game's canonical request unchanged;
- force16: no submission before 16 experiments, while one more experiment leaves both submissions
  affordable;
- show: at each submission, the count shown equals `diagnose`'s classes alive there.
"""

from pathlib import Path
import json
import random
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from zendo_bench.backends.base import Reply
from zendo_bench.bench import cli, diagnose, runner
from zendo_bench.bench import score as scores

import intervene

RULE = "(exists x0 (= (color x0) RED))"
OUT = HERE.parent / "results" / "runs" / "check"


class Scripted:
    """The stand-in engine: every request answered at the next step; what each request showed is kept."""

    batch, grammared = 36, True

    def __init__(self):
        self.pending, self.seen, self.handles = {}, [], 0

    def warm(self, grammars):
        pass

    def describe(self):
        return {"backend": "scripted", "grammared": True}

    def submit(self, request, key):
        view = json.loads(request.messages[1]["content"])
        self.handles += 1
        if "submit" in view["available_actions"]:
            text = json.dumps({"action": "submit", "rule": RULE}, separators=(",", ":"))
        else:
            c = view["constraints"]
            draw = random.Random(f"{key}:{request.decision}")
            scene = [{"color": draw.choice(c["allowed_colors"]), "shape": draw.choice(c["allowed_shapes"]),
                      "size": draw.choice(c["allowed_sizes"]), "orientation": draw.choice(c["allowed_orientations"])}
                     for _ in range(draw.randint(1, c["max_pieces"]))]
            text = json.dumps({"action": "experiment", "scene": scene}, separators=(",", ":"))
        self.seen.append({"task_id": key[0], "decision": request.decision, "view": view, "text": text,
                          "messages_sha256": intervene.messages_digest(request.messages),
                          "grammar_sha256": intervene.grammar_digest(request.grammar)})
        self.pending[self.handles] = Reply(text)
        return self.handles

    def step(self):
        out, self.pending = list(self.pending.items()), {}
        return out

    def cancel(self):
        self.pending = {}

    def stats(self):
        return {"decode_steps": None}

    def close(self):
        return self.stats()


CONFIGS = {"pass-through": intervene.PASS_THROUGH, **intervene.ARMS}


def play(arm, manifest):
    engine = Scripted()
    wrapped = intervene.Intervention(engine, arm, CONFIGS[arm])
    out = OUT / f"{arm}.jsonl"
    out.unlink(missing_ok=True)
    runner.run(manifest, lambda tier: wrapped, arm=f"check-{arm}", out=str(out), first=1, batched=True,
               player="agent-tools")
    return out, engine.seen


def calls(path):
    """(task ID, decision) -> the call record, over every episode of a run file."""
    found = {}
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record.get("type") == "episode":
            for call in record["calls"]:
                found[record["task_id"], call["decision"]] = call
    return found


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = cli.load_manifest("dev")
    for arm in CONFIGS:
        path, seen = play(arm, manifest)
        report = scores.score(manifest, [str(path)], verify=True)
        assert report["verified"], f"{arm}: not verified"
        _, games, _ = diagnose.games(manifest, [str(path)])
        recorded = calls(path)
        for s in seen:
            call = recorded[s["task_id"], s["decision"]]
            note = call["backend"]["intervention"]
            assert note["arm"] == arm, (arm, note)
            if arm == "pass-through":
                assert (s["messages_sha256"], s["grammar_sha256"]) == (call["messages_sha256"], call["grammar_sha256"])
            else:
                assert (s["messages_sha256"], s["grammar_sha256"]) == (note["messages_sha256"], note["grammar_sha256"])
        by_game = {}
        for s in seen:
            by_game.setdefault(s["task_id"], []).append(s)
        for task_id, decisions in by_game.items():
            submitted = [s for s in decisions if '"action":"submit"' in s["text"]]
            if CONFIGS[arm]["force"] is not None:  # the scripted player submits as soon as it may
                ran = decisions.index(submitted[0]) if submitted else len(decisions)
                assert ran == intervene.FORCE, (arm, task_id, ran)
            if CONFIGS[arm]["show"]:
                shown = [s["view"]["consistent_rules"]["count"] for s in submitted]
                alive = [sub["alive"] for sub in games[task_id]["submissions"]]
                assert shown == alive, (arm, task_id, shown, alive)
        print(f"{arm}: {len(by_game)} games, {len(seen)} calls, verified; wins "
              f"{sum(t['wins'] for t in report['tiers'].values())}")
    print("ok")


if __name__ == "__main__":
    main()
