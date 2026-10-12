"""E02's interventions on ZendoBench 1.0.0, unpatched: a pass-through engine around its MLX batch engine.

`python intervene.py ARM OUT` plays DESIGN.md's dev games (`--per-family 2`) with Qwen3.5-4B, set up as
E01's `qwen3.5-4b-mlx` (A8) was: ZendoBench's own MLX setup (`cli._mlx`) with E01's arguments, 36 games
in flight, sampler seed 0. The run's player is `agent-tools`, the arm `qwen3.5-4b-mlx-ARM`. `--first N`
(the first N items of each tier) and `--tiers` are for smoke runs.

`Intervention` changes a request after the game has rendered it, and only then (ARMS):
- force: until the player has run FORCE experiments, the observation's available_actions lists only
  experiment and the answer grammar is ZendoBench's own experiment-only variant (`interface.VARIANTS`),
  which every tier warms before its first game. The gate also opens if one more experiment would leave
  the remaining submissions unaffordable.
- show: the observation gains `consistent_rules`, {"count", "of"}: the rule classes of the game's prior
  that label every evidence scene as shown (`catalog.domain_alive`, restricted to the analysis prior, as
  `diagnose` counts them), from the evidence in the message alone, never the hidden rule.
Each intervention adds one sentence to the system prompt. Every call's backend record gains
`intervention`: the arm, the gate, the count shown, and the hashes of the messages and grammar the model
was given. The call's own `messages_sha256` and `grammar_sha256` stay the game's canonical request, the
one `score --verify` replays. With neither intervention (`PASS_THROUGH`) every request passes unchanged.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

from zendo_bench import catalog
from zendo_bench.agents import agent_for
from zendo_bench.backends.base import BackendFailure, Reply
from zendo_bench.bench import cli, runner
from zendo_bench.bench.split import TIERS
from zendo_bench.harness import grammar_digest
from zendo_bench.interface import action_grammar
from zendo_bench.protocol import get

AGENT = "e02-intervention-v1"
SOURCE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
FORCE = 16
ARMS = {"force16": {"force": FORCE, "show": False}, "show": {"force": None, "show": True},
        "force16-show": {"force": FORCE, "show": True}}
PASS_THROUGH = {"force": None, "show": False}  # no intervention: what A8 played (00_check.py)
# Each sentence follows the system prompt line it qualifies.
ECONOMY_END = "you may submit at most 2 times."
FORCE_LINE = ("In this game you may submit only after you have run {force} experiments; until then the "
              "observation's available_actions offers only experiment.")
OBSERVATION_END = "Use the budget, action costs and remaining submissions shown in the observation."
SHOW_LINE = ("The observation's consistent_rules: of the candidate rules this game's hidden rule is drawn from (of), "
             "how many label every evidence scene as shown (count). The hidden rule is always among those counted.")


class InterventionError(RuntimeError):
    pass


def protocols():
    """System prompt -> what the interventions need of its protocol: the catalog and scene size, the
    analysis prior's class indices (None: every class), and the two answer grammars. T1-T4 share one
    prompt, catalog and prior."""
    found = {}
    for tier in TIERS:
        protocol = get(tier)
        agent = agent_for(protocol)
        ids = catalog.load_domain(catalog.domain_of(protocol.tier.catalog))["class_ids"]
        prior = protocol.analysis_prior().prior_classes
        keep = None if prior is None else np.array([i for i, c in enumerate(ids) if c in prior], dtype=int)
        entry = {"catalog": protocol.tier.catalog, "pieces": protocol.tier.piece_count, "keep": keep,
                 "of": len(ids) if keep is None else len(keep),
                 "both": action_grammar(agent.max_pieces, agent.rule_limits, True, True),
                 "experiment": action_grammar(agent.max_pieces, agent.rule_limits, True, False)}
        known = found.setdefault(agent.system_prompt(), entry)
        if known is not entry and any(not np.array_equal(known[k], entry[k]) if k == "keep" else known[k] != entry[k]
                                      for k in entry):
            raise InterventionError(f"{tier} shares a system prompt with another tier but not its catalog or prior.")
    return found


def consistent(entry, view):
    """The prior's classes consistent with the view's evidence, as `diagnose` counts them at a submission."""
    alive = catalog.domain_alive(entry["catalog"], entry["pieces"], catalog.evidence_of(view))
    return int(len(alive) if entry["keep"] is None else len(np.intersect1d(alive, entry["keep"])))


def after(text, anchor, line):
    if text.count(anchor) != 1:
        raise InterventionError(f"The system prompt does not hold {anchor!r} once.")
    return text.replace(anchor, anchor + "\n" + line)


def messages_digest(messages):
    """As `harness.Game.rendered` hashes a request's messages."""
    return sha256(json.dumps([[m["role"], m["content"]] for m in messages], separators=(",", ":")).encode()).hexdigest()


class Intervention:
    """The engine `batched.play` sees: `engine`'s, with each request changed per the arm (module docstring)."""

    def __init__(self, engine, arm, config=None):
        config = ARMS[arm] if config is None else config
        self.engine, self.arm = engine, arm
        self.force, self.show = config["force"], config["show"]
        self.protocols = protocols()
        self.notes = {}

    def __getattr__(self, name):  # batch, grammared, warm, cancel, stats, close
        return getattr(self.engine, name)

    def describe(self):
        return {**self.engine.describe(), "agent": AGENT, "agent_source_sha256": SOURCE_SHA256,
                "agent_config": {"arm": self.arm, "force_experiments": self.force, "show_consistent_rules": self.show}}

    def change(self, request):
        """(the request the model is given, its note)."""
        note = {"arm": self.arm}
        if self.force is None and not self.show:
            return request, note
        system, user = request.messages
        entry = self.protocols.get(system["content"])
        if entry is None:
            raise InterventionError("A request whose system prompt is no tier's.")
        prompt, view, grammar = system["content"], json.loads(user["content"]), request.grammar
        if self.force is not None:
            ran = sum(source["type"] == "experiment" for scene in view["evidence"] for source in scene["sources"])
            costs = view["costs"]
            closed = (ran < self.force and view["available_actions"] == ["experiment", "submit"]
                      and view["budget_remaining"] - costs["BUILD_EXPERIMENT"]
                      >= costs["SUBMIT_FOR_REVIEW"] * view["submissions_remaining"])
            if closed:
                if grammar != entry["both"]:
                    raise InterventionError(f"Decision {request.decision}: not the tier's two-action grammar.")
                view["available_actions"], grammar = ["experiment"], entry["experiment"]
            prompt = after(prompt, ECONOMY_END, FORCE_LINE.format(force=self.force))
            note.update(experiments=ran, gate="closed" if closed else "open")
        if self.show:
            count = consistent(entry, view)
            shown = {"count": count, "of": entry["of"]}
            view = {**{k: v for k, v in view.items() if k != "available_actions"}, "consistent_rules": shown,
                    "available_actions": view["available_actions"]}
            prompt = after(prompt, OBSERVATION_END, SHOW_LINE)
            note.update(consistent_rules=shown)
        messages = ({"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps(view, separators=(",", ":"))})
        note.update(messages_sha256=messages_digest(messages), grammar_sha256=grammar_digest(grammar))
        return type(request)(messages, grammar, request.decision, episode_id=request.episode_id), note

    def submit(self, request, key):
        changed, note = self.change(request)
        handle = self.engine.submit(changed, key)
        self.notes[handle] = note
        return handle

    def step(self):
        out = []
        for handle, result in self.engine.step():
            note = self.notes.pop(handle)
            if isinstance(result, BackendFailure):
                result.record["intervention"] = note
            else:
                result = Reply(result.text, result.finish, result.usage, dict(result.record, intervention=note))
            out.append((handle, result))
        return out

    def cancel(self):
        self.notes.clear()
        return self.engine.cancel()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("arm", choices=ARMS)
    parser.add_argument("out")
    parser.add_argument("--first", type=int, help="the first N items of each tier (a smoke run)")
    parser.add_argument("--tiers", nargs="+", help="only these tiers (a smoke run)")
    parser.add_argument("--exclude-finished", nargs="*", default=[])
    a = parser.parse_args(argv)
    args = cli.build_parser().parse_args(
        ["run", "--manifest", "dev", "--arm", f"qwen3.5-4b-mlx-{a.arm}", "--out", a.out, "--backend", "mlx",
         "--checkpoint", "4B", "--batch", "36", "--seed", "0", "--player", "agent-tools"]
        + (["--first", str(a.first)] if a.first else ["--per-family", "2"]) + (["--tiers", *a.tiers] if a.tiers else []))
    make, wrapped = cli._mlx(args), []

    def backends(tier):  # one engine for every tier, each tier's grammars warmed (cli._mlx_batch)
        engine = make(tier)
        if not wrapped:
            wrapped.append(Intervention(engine, a.arm))
        return wrapped[0]

    end = runner.run(cli.load_manifest(args.manifest, args.secret_dir), backends, arm=args.arm, out=args.out,
                     exclude=a.exclude_finished, tiers=args.tiers, first=args.first, per_family=args.per_family, batched=True,
                     breaker=args.breaker, player=args.player)
    if end["status"] == "stopped":
        print(f"{end['stop']['message']} Play the rest into a new file with --exclude-finished.", file=sys.stderr)
        return cli.BREAKER_EXIT
    return 0


if __name__ == "__main__":
    sys.exit(main())
