"""03_measures.py [--arms ARM=FILE ...]   E02's measures and hypothesis verdicts (DESIGN.md), from the scored arms.

Reads each arm's run files in results/runs/ (local only; `02_score.sh` has verified and scored them) and
E1's A8 run file (experiments/E01-dev-baseline/results/runs/qwen3.5-4b-mlx.jsonl, local only; verified in E1),
restricted to the 102 games of DESIGN.md. Writes results/measures.json and results/metrics.json.

- **Paired win difference** (A minus B, T2-T6): `compare`'s pairing and `breakdown` (a t interval on the
  class means, equal-weight tiers), computed here because `compare` refuses to pair the `model` player
  (A8) with this experiment's `agent-tools` runs.
- **Behaviour:** `diagnose.row` over each arm's scored games (E1's columns), and the conversion: wins
  over the summed `p_first` of the T2-T6 games with a submission.
- **Paired experiments per game:** the mean per-task difference with a Student-t 95% interval.
`--arms` replaces the arms' files (a check of this script on other run files; nothing is written).
"""

import argparse
import json
import math
from pathlib import Path
import statistics

from zendo_bench.bench import cli, diagnose, runner, stats
from zendo_bench.bench import score as scores

HERE = Path(__file__).resolve().parent
E = HERE.parent
ROOT = E.parent.parent
RUNS = E / "results" / "runs"
A8 = ROOT / "experiments/E01-dev-baseline/results/runs/qwen3.5-4b-mlx.jsonl"
ARMS = ("force16", "show", "force16-show")
WIN = {"win": 1.0, "loss": 0.0}
HEADLINE = set(scores.HEADLINE_TIERS)
CONTRADICTING = 0.10  # hypothesis 2
NARROWED = 10  # force16's median classes alive at the first submission, at most (DESIGN.md)


def files(arm):
    return [str(p) for p in [RUNS / f"qwen3.5-4b-mlx-{arm}.jsonl", *sorted(RUNS.glob(f"qwen3.5-4b-mlx-{arm}.part*.jsonl"))]
            if p.exists()]


def subset(manifest):
    """DESIGN.md's 102 games: the first 2 items of each family."""
    return {e["task_id"] for rows in runner.plan(manifest, per_family=2).values() for e in rows}


def headline(manifest, found):
    """An arm's T2-T6 win rate on its finished items (`score`'s breakdown)."""
    report = scores.breakdown(manifest, found, lambda r: WIN.get(r["outcome"]),
                              lambda items: {"method": stats.KORN_GRAUBARD, "items": items})
    return report["headline"]


def paired(manifest, found_a, found_b):
    """The paired T2-T6 win difference A - B over the items finished in both (`compare`'s)."""
    both = {}
    for task_id in found_a.keys() & found_b.keys():
        a, b = WIN.get(found_a[task_id]["outcome"]), WIN.get(found_b[task_id]["outcome"])
        both[task_id] = {"difference": None if a is None or b is None else a - b}
    report = scores.breakdown(manifest, both, lambda r: r["difference"],
                              lambda items: {"method": stats.T_INTERVAL, "bounds": (-1.0, 1.0)})
    head = report["headline"]
    return {k: head.get(k) for k in ("estimate", "se", "df", "ci", "ci_method", "finished", "missing", "withheld")}


def mean_difference(values):
    """Mean of paired differences with a Student-t 95% interval."""
    n = len(values)
    mean = statistics.mean(values)
    if n < 2:
        return {"n": n, "mean": mean, "ci": None}
    se = statistics.stdev(values) / math.sqrt(n)
    half = stats.t_critical(n - 1) * se
    return {"n": n, "mean": mean, "se": se, "ci": [mean - half, mean + half]}


def behaviour(games):
    row = diagnose.row(list(games.values()))
    subs = [s for g in games.values() for s in g["submissions"]]
    firsts = [g for g in games.values() if g["tier"] in HEADLINE and g["submissions"]]
    expected = sum(g["submissions"][0]["p_ideal"] for g in firsts)
    row.update(contradicting_share=sum(not s["consistent"] for s in subs) / len(subs) if subs else None,
               headline_wins=sum(g["outcome"] == "win" for g in firsts),
               headline_expected_wins=expected,
               conversion=sum(g["outcome"] == "win" for g in firsts) / expected if expected else None)
    return row


def measures(manifest, arm_files):
    keep = subset(manifest)
    arms = {"A8": [str(A8)], **arm_files}
    found, games = {}, {}
    for arm, paths in arms.items():
        _, f, _ = scores.outcomes(manifest, paths)
        _, g, _ = diagnose.games(manifest, paths)
        found[arm] = {t: r for t, r in f.items() if t in keep}
        games[arm] = {t: r for t, r in g.items() if t in keep}
    out = {"arms": {arm: {"files": [str(Path(f).resolve().relative_to(ROOT)) for f in arms[arm]], "finished": len(found[arm]), "headline": headline(manifest, found[arm]),
                          "behaviour": behaviour(games[arm])} for arm in arms}}
    pairs = [(a, "A8") for a in arm_files] + [(a, b) for a, b in (("force16-show", "force16"), ("force16-show", "show"))
                                               if a in arm_files and b in arm_files]
    out["paired_wins"] = {f"{a} - {b}": paired(manifest, found[a], found[b]) for a, b in pairs}
    out["paired_experiments"] = {}
    for a, b in pairs:
        common = sorted(games[a].keys() & games[b].keys())
        out["paired_experiments"][f"{a} - {b}"] = mean_difference(
            [len(games[a][t]["experiments"]) - len(games[b][t]["experiments"]) for t in common])
    out["hypotheses"] = verdicts(out)
    return out


def verdicts(out):
    v = {}
    force = out["arms"].get("force16")
    if force is not None:
        alive = force["behaviour"]["alive_first"]
        narrowed = alive is not None and alive <= NARROWED
        v["precondition_force16_narrowed"] = {"alive_first_median": alive, "at_most": NARROWED, "holds": narrowed}
        ci = out["paired_wins"]["force16 - A8"]["ci"]
        v["H_stopping"] = {"difference": out["paired_wins"]["force16 - A8"]["estimate"], "ci": ci,
                           "verdict": "not read" if not narrowed else "no interval" if ci is None
                           else "holds" if ci[0] > 0 else "fails"}
        share = force["behaviour"]["contradicting_share"]
        v["H_tracking"] = {"contradicting_share": share, "at_least": CONTRADICTING,
                           "verdict": "not read" if not narrowed or share is None
                           else "holds" if share >= CONTRADICTING else "fails"}
    if "show" in out["arms"]:
        d = out["paired_experiments"]["show - A8"]
        v["H_uncertainty"] = {"mean_difference": d["mean"], "ci": d["ci"],
                              "verdict": "no interval" if d["ci"] is None else "holds" if d["ci"][0] > 0 else "fails"}
    return v


def flat(out):
    m = {}
    for arm, entry in out["arms"].items():
        h, b = entry["headline"], entry["behaviour"]
        m[f"{arm}.headline"] = h["estimate"]
        m[f"{arm}.headline_ci_low"], m[f"{arm}.headline_ci_high"] = h["ci"] if h.get("ci") else (None, None)
        for key in ("games", "wins", "exp_per_game", "bits_per_exp", "eig", "zero", "repeats", "alive_first", "p_first",
                    "subs_per_game", "certain_wrong", "contradicting_share", "conversion"):
            m[f"{arm}.{key}"] = b[key]
    for name, d in out["paired_wins"].items():
        m[f"wins[{name}]"] = d["estimate"]
        m[f"wins[{name}].ci_low"], m[f"wins[{name}].ci_high"] = d["ci"] if d["ci"] else (None, None)
    for name, d in out["paired_experiments"].items():
        m[f"experiments[{name}]"] = d["mean"]
        m[f"experiments[{name}].ci_low"], m[f"experiments[{name}].ci_high"] = d["ci"] if d["ci"] else (None, None)
    return m


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--arms", nargs="+", metavar="ARM=FILE", help="check this script on other run files")
    a = parser.parse_args()
    manifest = cli.load_manifest("dev")
    if a.arms:
        arm_files = {spec.split("=", 1)[0]: [spec.split("=", 1)[1]] for spec in a.arms}
    else:
        arm_files = {arm: files(arm) for arm in ARMS if files(arm)}
    out = measures(manifest, arm_files)
    print(json.dumps(out["hypotheses"], indent=1))
    if not a.arms:
        (E / "results" / "measures.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
        (E / "results" / "metrics.json").write_text(json.dumps(flat(out), indent=1) + "\n")


if __name__ == "__main__":
    main()
