"""03_table.py [--root DIR]   results/runs.md and results/metrics.json from every scored arm. Costs and token
counts are not published (docs/conventions.md).

Reads, per arm: results/scores/ARM.score.json and ARM.files.json (from 02_score.sh), the per-game diagnose
report and the run files in results/runs/ (local only), the parts' .cmd files (start, end, commit), and the
attempt labels in results/attempts.json.
"""
import argparse
import json
from pathlib import Path

from claude_backend import ARMS

TIERS = ["T1", "T2", "T3", "T4", "T5", "T6"]
BEHAVIOUR = [  # diagnose summary field, column title
    ("exp_per_game", "exp/game"), ("bits_per_exp", "bits/exp"), ("eig", "EIG"), ("zero", "zero-info"),
    ("repeats", "repeats"), ("alive_first", "alive at 1st sub"), ("p_first", "p at 1st sub"),
    ("subs_per_game", "subs/game"), ("nodes_ratio", "nodes/truth"), ("over_simplest", "over simplest"),
    ("contradicting", "contradicting"), ("fits_ce", "fits counterex."), ("certain_wrong", "certain wrong"),
]


def pct(x):
    return "–" if x is None else f"{100 * x:.1f}"


def num(x, digits=2):
    if x is None:
        return "–"
    return f"{x:.{digits}f}" if isinstance(x, (int, float)) and not isinstance(x, bool) else str(x)


def run_stats(runs, arm):
    """Calls, calls without an answer, calls retried and the Claude version from the arm's run files; start, end and
    commits from the parts' .cmd files."""
    files = sorted(runs.glob(f"{arm}.jsonl")) + sorted(runs.glob(f"{arm}.part*.jsonl"),
                                                       key=lambda f: int(f.stem.split(".part")[-1]))
    out = dict(calls=0, unanswered=0, retried=0, truncated=0, continuations_blocked=0,
               recoveries_blocked=0,
               claude=None, versions=None, start=None, end=None, commits=set())
    for f in files:
        with f.open() as fh:
            for i, line in enumerate(fh):
                r = json.loads(line)
                if i == 0:
                    out["versions"] = {k: v for k, v in (r.get("runtime_versions") or {}).items() if k.startswith("zendo")}
                    out["claude"] = ((r.get("backend") or {}).get("agent_config") or {}).get("claude_cli")
                if r.get("type") != "episode":
                    continue
                for c in r["calls"]:
                    out["calls"] += 1
                    out["unanswered"] += c.get("finish") not in (None, "action")
                    out["retried"] += bool((c.get("backend") or {}).get("retries"))
                    out["truncated"] += (c.get("backend") or {}).get("stop_reason") == "max_tokens"
                    out["continuations_blocked"] += (c.get("backend") or {}).get("continuations_blocked", 0)
                    backend = c.get("backend") or {}
                    out["recoveries_blocked"] += sum(record.get("recoveries_blocked", 0)
                                                     for record in [backend, *backend.get("retries", [])])
        cmd = f.with_suffix(".cmd")
        if cmd.exists():
            for line in cmd.read_text().splitlines():
                key, _, value = line.partition(" ")
                if key == "started":
                    out["start"] = min(filter(None, [out["start"], value]))
                elif key == "ended":
                    out["end"] = max(filter(None, [out["end"], value.split()[0]]))
                elif key == "zendo-lab":
                    out["commits"].add(value.split()[0])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    a = p.parse_args()
    root = Path(a.root)
    res, scores, runs = root / "results", root / "results/scores", root / "results/runs"
    attempts = json.loads((res / "attempts.json").read_text()) if (res / "attempts.json").exists() else {}
    rows, metrics = [], {}
    for arm, model in ARMS.items():
        sf = scores / f"{arm}.score.json"
        if not sf.exists():
            continue
        s = json.loads(sf.read_text())
        files = json.loads((scores / f"{arm}.files.json").read_text())
        dj = runs / f"{arm}.diagnose.json"
        d = json.loads(dj.read_text())["summary"] if dj.exists() else {}
        st = run_stats(runs, arm)
        h, tiers, mal = s["headline"], s["tiers"], s["malformed"]
        row = dict(arm=arm, attempt=(attempts.get(arm) or {}).get("label"), model=model, claude=st["claude"],
                   versions=st["versions"], commits=sorted(st["commits"]), files=files, start=st["start"], end=st["end"],
                   headline=h["estimate"], ci=h["ci"], finished=h["finished"], items=h["items"], verified=s["verified"],
                   tiers={t: tiers.get(t) for t in TIERS}, seed_only=s["context"].get("seed_only_map_win"),
                   malformed_headline=(mal.get("headline") or {}).get("malformed_rate"), calls=st["calls"],
                   unanswered=st["unanswered"], retried=st["retried"], truncated=st["truncated"],
                   continuations_blocked=st["continuations_blocked"], behaviour=d.get("all") or {})
        rows.append(row)
        m = metrics
        m[f"{arm}.headline"] = row["headline"]
        m[f"{arm}.headline_ci_low"], m[f"{arm}.headline_ci_high"] = (row["ci"] or [None, None])
        m[f"{arm}.seed_only_map_win"] = row["seed_only"]
        m[f"{arm}.malformed_rate_headline"] = row["malformed_headline"]
        for t in TIERS:
            e = row["tiers"][t] or {}
            m[f"{arm}.{t}.wins"], m[f"{arm}.{t}.scored"] = e.get("wins"), e.get("scored")
        for key, _ in BEHAVIOUR:
            v = row["behaviour"].get(key)
            if isinstance(v, (int, float)):
                m[f"{arm}.{key}"] = v
        m[f"{arm}.calls"], m[f"{arm}.calls_without_answer"] = row["calls"], row["unanswered"]
        m[f"{arm}.truncated_calls"] = row["truncated"]
        m[f"{arm}.blocked_cli_continuations"] = row["continuations_blocked"]
        m[f"{arm}.blocked_cli_recoveries"] = st["recoveries_blocked"]
        m[f"{arm}.unfinished_games"] = sum((tiers.get(t) or {}).get("unfinished", 0) for t in TIERS)
        m[f"{arm}.unscored_games"] = sum((tiers.get(t) or {}).get("unscored", 0) for t in TIERS)

    L = ["# E04 runs", "",
         "Generated by `scripts/03_table.py` from `results/scores/` and the run files (kept by the owner). "
         "ZendoBench 1.0.0, dev manifest (460 games), player `model`, through the Claude CLI with no tools "
         "(`claude -p`, first API response per stateless decision), reasoning effort high, summarized thinking kept. "
         "Benchmark messages are unchanged; Claude additionally receives the fixed SDK identity sentence in DESIGN.md. "
         "Claude uses adaptive thinking, max_tokens 128000 and provider-default sampling. "
         "Hosted Anthropic inference; provider hardware unknown. Local orchestrator: Apple M4 Max, 128 GB. Episode seeds from the dev manifest; models unseeded. Win rates in %, 95% CIs from `score --verify`. Behaviour measures (`diagnose`) cover all 460 games including T1; "
         "`alive at 1st sub` is a median and `p at 1st sub` a mean over games with a submission.", "",
         "## Configuration", "",
         "| Arm | Attempt | Model (Claude slug) | Claude CLI | ZendoBench | zendo-lab | Start (UTC) | End (UTC) | Run files (sha256, bytes) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        files = "<br>".join(f"`{f['file']}` `{f['sha256'][:16]}…` {f['bytes']:,}" for f in r["files"])
        versions = ", ".join(f"{k} {v}" for k, v in (r["versions"] or {}).items())
        L.append(f"| `{r['arm']}` | {r['attempt'] or '–'} | `{r['model']}` | {r['claude'] or '–'} | {versions} | "
                 f"{', '.join(c[:7] for c in r['commits']) or '–'} | {r['start'] or '–'} | {r['end'] or '–'} | {files} |")
    L += ["", "## Results", "",
          "| Arm | Headline T2–T6 [95% CI] | Seed-only | " + " | ".join(TIERS) +
          " | Finished / items (T2–T6) | Unscored (all) | Unfinished (all) | Malformed (headline) | Verified |",
          "|---|---|---|" + "---|" * len(TIERS) + "---|---|---|---|---|"]
    for r in rows:
        ci = r["ci"] or [None, None]
        cells = [f"{(r['tiers'][t] or {}).get('wins', '–')}/{(r['tiers'][t] or {}).get('scored', '–')}" for t in TIERS]
        unscored = sum((r["tiers"][t] or {}).get("unscored", 0) for t in TIERS)
        unfinished = sum((r["tiers"][t] or {}).get("unfinished", 0) for t in TIERS)
        L.append(f"| `{r['arm']}` | **{pct(r['headline'])}** [{pct(ci[0])}, {pct(ci[1])}] | {pct(r['seed_only'])} | "
                 + " | ".join(cells) + f" | {r['finished']}/{r['items']} | {unscored} | {unfinished} | {pct(r['malformed_headline'])} | "
                 f"{'yes' if r['verified'] else 'no'} |")
    L += ["", "## Behaviour (`diagnose`, all scored games)", "",
          "| Arm | " + " | ".join(t for _, t in BEHAVIOUR) + " |", "|---|" + "---|" * len(BEHAVIOUR)]
    for r in rows:
        cells = [str(r["behaviour"].get(k, "–")) if k in ("repeats", "certain_wrong") else num(r["behaviour"].get(k))
                 for k, _ in BEHAVIOUR]
        L.append(f"| `{r['arm']}` | " + " | ".join(cells) + " |")
    L += ["", "## Calls", "", "| Arm | Calls | Without an answer | Retried | Truncated | CLI continuations blocked |", "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| `{r['arm']}` | {r['calls']:,} | {r['unanswered']:,} | {r['retried']:,} | {r['truncated']:,} | {r['continuations_blocked']:,} |")
    (res / "runs.md").write_text("\n".join(L) + "\n")
    (res / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    print(f"{len(rows)} arms -> {res / 'runs.md'}, {res / 'metrics.json'}")


if __name__ == "__main__":
    main()
