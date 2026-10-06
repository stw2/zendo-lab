"""04_rank_agreement.py   rank agreement across E1's arms between the T2-T6 headline and each behaviour measure.

Descriptive: Spearman's rho over the seven systems (ties get average ranks), no p-value. The systems are
not a random sample and both measures come from the same games (DESIGN.md amendment, 2026-10-06).
Reads results/metrics.json; writes results/rank_agreement.json.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS = ["qwen3.5-2b-mlx", "qwen3.5-4b-mlx", "qwen3.5-27b-fp8-vllm-h100", "qwen3.8-27b-fp8-vllm-h100",
        "deepseek-v4-flash-together", "gpt-oss-120b-openrouter-high", "gpt-6-luna-openrouter-high"]
MEASURES = ["exp_per_game", "alive_first", "p_first", "eig"]


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return cov / (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5


def main():
    m = json.loads((ROOT / "results/metrics.json").read_text())
    headline = [m[f"{a}.headline"] for a in ARMS]
    out = {"systems": ARMS, "n_systems": len(ARMS), "y": "headline (T2-T6 equal-weight win rate)",
           "values": {a: {"headline": m[f"{a}.headline"], **{k: m[f"{a}.{k}"] for k in MEASURES}} for a in ARMS},
           "spearman_rho": {k: round(spearman([m[f"{a}.{k}"] for a in ARMS], headline), 4) for k in MEASURES},
           "note": "Descriptive rank agreement among these seven systems; not a causal or population claim; no p-value."}
    (ROOT / "results/rank_agreement.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["spearman_rho"]))


if __name__ == "__main__":
    main()
