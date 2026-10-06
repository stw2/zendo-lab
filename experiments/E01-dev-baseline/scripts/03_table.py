"""03_table.py [--root DIR]   results/runs.md and results/metrics.json from every scored arm. Costs and token
counts are not published (docs/conventions.md).

Reads, per arm: results/scores/ARM.score.json and ARM.files.json (from 02_score.sh), the per-game
diagnose report and the run files in results/runs/ (local only), the run's .cmd (start, end, commit),
results/attempts.json (the Room's attempt labels) and, for a Daytona arm, its box ledger. Prices are
list prices per million tokens, as read on 2026-10-04; a provider's bill can differ (OpenRouter routes
calls to providers at other prices).
"""
import argparse
import datetime
import json
from pathlib import Path
import time

ARMS = {  # arm: (model, where, hardware, Daytona box, $/M input, $/M output)
    "qwen3.5-2b-mlx": ("Qwen/Qwen3.5-2B (bf16)", "MLX, 36 games in flight, sampler seed 0", "Apple M4 Max 128 GB", None, 0, 0),
    "qwen3.5-4b-mlx": ("Qwen/Qwen3.5-4B (bf16)", "MLX, 36 games in flight, sampler seed 0", "Apple M4 Max 128 GB", None, 0, 0),
    "qwen3.5-27b-fp8-vllm-h100": ("Qwen/Qwen3.5-27B-FP8", "vLLM 0.30.0, Daytona, --batch auto", "1x H100 80 GB", "qwen35", None, None),
    "qwen3.8-27b-fp8-vllm-h100": ("Qwen/Qwen3.8-27B-FP8", "vLLM 0.30.0, Daytona, --batch auto", "1x H100 80 GB", "qwen38", None, None),
    "deepseek-v4-flash-together": ("deepseek-ai/DeepSeek-V4-Flash-0731", "Together, 64 calls in flight", "provider", None, 0.14, 0.28),
    "gpt-oss-120b-openrouter-high": ("openai/gpt-oss-120b", "OpenRouter, 64 calls in flight", "provider", None, 0.037, 0.17),
    "gpt-6-luna-openrouter-high": ("openai/gpt-6-luna", "OpenRouter, 64 calls in flight", "provider", None, 0.10, 0.50),
}
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
    """Tokens, calls, cap hits and sampling from the arm's run files; start and end from the .cmd files."""
    files = sorted(runs.glob(f"{arm}.jsonl")) + sorted(runs.glob(f"{arm}.part*.jsonl"))
    out = dict(calls=0, prompt=0, completion=0, reasoning=0, cut=0, sampling=None, versions=None, start=None, end=None,
               commits=set())
    for f in files:
        with f.open() as fh:
            for i, line in enumerate(fh):
                r = json.loads(line)
                if i == 0:
                    out["versions"] = {k: v for k, v in (r.get("runtime_versions") or {}).items() if k.startswith("zendo")}
                if r.get("type") != "episode":
                    continue
                for c in r["calls"]:
                    b, u = c.get("backend") or {}, c.get("usage") or {}
                    out["calls"] += 1
                    out["prompt"] += u.get("prompt_tokens") or 0
                    out["completion"] += u.get("completion_tokens") or 0
                    out["reasoning"] += (u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
                    out["cut"] += (b.get("finish_reason") == "length") or c.get("finish") == "length"
                    out["sampling"] = out["sampling"] or b.get("sampling") or b.get("decoding")
        cmd = f.with_suffix(".cmd")
        if cmd.exists():
            for line in cmd.read_text().splitlines():
                key, _, value = line.partition(" ")
                if key == "started":
                    out["start"] = min(filter(None, [out["start"], value]))
                elif key == "ended":
                    out["end"] = max(filter(None, [out["end"], value.split()[0]]))
                elif key == "zendo-lab":
                    out["commits"].add(value)
    out["files"] = [f.name for f in files]
    return out


def hours(start, end):
    if not (start and end):
        return None
    t = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return (t(end) - t(start)).total_seconds() / 3600


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    a = p.parse_args()
    root = Path(a.root)
    res, scores, runs = root / "results", root / "results/scores", root / "results/runs"
    attempts = json.loads((res / "attempts.json").read_text()) if (res / "attempts.json").exists() else {}
    rows, metrics = [], {}
    for arm, (model, where, hardware, box, price_in, price_out) in ARMS.items():
        sf = scores / f"{arm}.score.json"
        if not sf.exists():
            continue
        s = json.loads(sf.read_text())
        files = json.loads((scores / f"{arm}.files.json").read_text())
        dj = runs / f"{arm}.diagnose.json"
        d = json.loads(dj.read_text())["summary"] if dj.exists() else {}
        st = run_stats(runs, arm)
        if box:
            ledger = Path.home() / ".cache/zendo-lab/e01-daytona" / box / "ledger.json"
            led = json.loads(ledger.read_text()) if ledger.exists() else {"sandboxes": []}
            cost = sum(((x.get("deleted_unix") or time.time()) - x["requested_unix"]) / 3600 * x["rate"]
                       for x in led["sandboxes"]) if led["sandboxes"] else None
        else:
            cost = st["prompt"] / 1e6 * price_in + st["completion"] / 1e6 * price_out
        h = s["headline"]
        tiers = s["tiers"]
        mal = s["malformed"]
        row = dict(
            arm=arm, attempt=(attempts.get(arm) or {}).get("label"), model=model, where=where, hardware=hardware,
            sampling=st["sampling"], versions=st["versions"], commits=sorted(st["commits"]), files=files,
            start=st["start"], end=st["end"], wall_h=hours(st["start"], st["end"]),
            headline=h["estimate"], ci=h["ci"], finished=h["finished"], items=h["items"], verified=s["verified"],
            tiers={t: tiers.get(t) for t in TIERS}, seed_only=s["context"].get("seed_only_map_win"),
            malformed_headline=(mal.get("headline") or {}).get("malformed_rate"), w0=s["w0"]["pooled"],
            calls=st["calls"], prompt=st["prompt"], completion=st["completion"], reasoning=st["reasoning"], cut=st["cut"],
            cost=cost, behaviour=d.get("all") or {},
        )
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
        m[f"{arm}.calls"], m[f"{arm}.calls_cut_at_cap"] = row["calls"], row["cut"]

    L = ["# E01 runs", "",
         "Generated by `scripts/03_table.py` from `results/scores/` and the run files (kept by the owner). "
         "ZendoBench 1.0.0, dev manifest (460 games), player `model`, `max_tokens` 65,536 a call, reasoning kept. "
         "Win rates in %, 95% CIs from `score --verify`. Behaviour measures (`diagnose`) cover all 460 games including T1; "
         "`alive at 1st sub` is a median and `p at 1st sub` a mean over games with a submission. The MLX arms' answers are "
         "grammar-constrained, so their malformed rate is not comparable with the HTTP arms'. OpenRouter arms: default routing, "
         "provider not recorded.", "",
         "## Configuration", "",
         "| Arm | Attempt | Model | Backend | Hardware | Sampling | ZendoBench | zendo-lab | Start (UTC) | End (UTC) | Run files (sha256, bytes) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        files = "<br>".join(f"`{f['file']}` `{f['sha256'][:16]}…` {f['bytes']:,}" for f in r["files"])
        sampling = json.dumps(r["sampling"], separators=(",", ":")) if r["sampling"] else "–"
        versions = ", ".join(f"{k} {v}" for k, v in (r["versions"] or {}).items())
        L.append(f"| `{r['arm']}` | {r['attempt'] or '–'} | {r['model']} | {r['where']} | {r['hardware']} | `{sampling}` | "
                 f"{versions} | {', '.join(c[:7] for c in r['commits']) or '–'} | {r['start'] or '–'} | {r['end'] or '–'} | {files} |")
    L += ["", "## Results", "",
          "| Arm | Headline T2–T6 [95% CI] | Seed-only | " + " | ".join(TIERS) +
          " | Finished / items | Unscored | Malformed (headline) | Verified |",
          "|---|---|---|" + "---|" * len(TIERS) + "---|---|---|---|"]
    for r in rows:
        ci = r["ci"] or [None, None]
        cells = []
        for t in TIERS:
            e = r["tiers"][t] or {}
            cells.append(f"{e.get('wins', '–')}/{e.get('scored', '–')}")
        unscored = sum((r["tiers"][t] or {}).get("unscored", 0) for t in TIERS)
        L.append(f"| `{r['arm']}` | **{pct(r['headline'])}** [{pct(ci[0])}, {pct(ci[1])}] | {pct(r['seed_only'])} | "
                 + " | ".join(cells) + f" | {r['finished']}/{r['items']} | {unscored} | {pct(r['malformed_headline'])} | "
                 f"{'yes' if r['verified'] else 'no'} |")
    L += ["", "## Behaviour (`diagnose`, all scored games)", "",
          "| Arm | " + " | ".join(t for _, t in BEHAVIOUR) + " |", "|---|" + "---|" * len(BEHAVIOUR)]
    for r in rows:
        cells = [str(r["behaviour"].get(k, "–")) if k in ("repeats", "certain_wrong") else num(r["behaviour"].get(k))
                 for k, _ in BEHAVIOUR]
        L.append(f"| `{r['arm']}` | " + " | ".join(cells) + " |")
    L += ["", "## Calls", "", "| Arm | Calls | Cut at `max_tokens` |", "|---|---|---|"]
    for r in rows:
        L.append(f"| `{r['arm']}` | {r['calls']:,} | {r['cut']:,} |")
    (res / "runs.md").write_text("\n".join(L) + "\n")
    (res / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    print(f"{len(rows)} arms -> {res / 'runs.md'}, {res / 'metrics.json'}")


if __name__ == "__main__":
    main()
