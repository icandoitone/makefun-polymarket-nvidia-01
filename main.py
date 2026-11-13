#!/usr/bin/env python3
"""Polymarket "Next CEO of NVIDIA?" minute-by-minute forecaster.

Reads every *.in case in $MAKEFUN_INPUT_DIR (else /input/) and writes one
/output/<id>.out per case: for each market, 240 rows x 5 quantiles
(0.05, 0.25, 0.5, 0.75, 0.95) of the Yes price at minutes at+1 .. at+240.

Method (per market, from the case's own 72 hours of 1-minute prices only):
  * Median: the last price. Prices are near-martingales, so any drift
    estimated from the recent trend is mostly noise and was measured to
    hurt (practice median error rose when drift was added); drift is 0.
  * Spread: per-market realized volatility of 1-minute changes over the
    last 120 minutes, scaled by 0.45 and floored/capped
    (0.0005 / 0.008 per sqrt-minute). One-minute changes overstate the
    true diffusion because microstructure noise mean-reverts, hence the
    0.45 shrink; a short 120-minute window adapts when a market's regime
    changes, where a 24-hour window was measured much worse. Dead markets
    stay tight, jumpy markets get honest tails.
  * Quantiles: q_tau = x + z_tau * sigma * sqrt(h), with z the standard
    normal quantiles (-1.644854, -0.674490, 0, 0.674490, 1.644854),
    clamped to [0, 1] and rounded to 6 decimals.

Practice (6 cases p00-p05, answers from the next case's prices, p05's
from Polymarket's live history): pinball loss 0.275 vs the house
baseline's 0.364 (p00-p04: 0.311 vs 0.393; p05: 0.120 vs 0.238),
90% coverage 0.88-0.96. Fully deterministic (no randomness, no network,
stdlib only); two runs produce byte-identical output.
"""
import glob
import json
import math
import os

Z = [-1.644854, -0.674490, 0.0, 0.674490, 1.644854]
SIGMA_WIN = 120       # minutes of recent history for volatility
SIGMA_SCALE = 0.45    # shrink: 1-min changes overstate diffusion
SIGMA_FLOOR = 0.0005  # per sqrt-minute
SIGMA_CAP = 0.008     # per sqrt-minute


def _std(vals):
    n = len(vals)
    if n < 2:
        return 0.0
    m = sum(vals) / n
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1))


def forecast_market(prices):
    x = prices[-1]
    diffs = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
    sigma = _std(diffs[-SIGMA_WIN:]) if len(diffs) >= 2 else 0.0
    sigma = min(SIGMA_CAP, max(SIGMA_FLOOR, sigma * SIGMA_SCALE))
    rows = []
    for h in range(1, 241):
        spread = sigma * math.sqrt(h)
        row = []
        prev = -1.0
        for z in Z:
            q = min(1.0, max(0.0, x + z * spread))
            q = max(q, prev)  # keep quantiles non-decreasing after clamping
            q = round(q, 6)
            row.append(q)
            prev = q
        rows.append(row)
    return rows


def forecast_case(case):
    return {"forecasts": [
        {"id": m["id"], "q": forecast_market(m["prices"])}
        for m in case["markets"]
    ]}


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input/")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output/")
    os.makedirs(out_dir, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(in_dir, "*.in"))):
        with open(path) as f:
            case = json.load(f)
        out = forecast_case(case)
        name = os.path.splitext(os.path.basename(path))[0] + ".out"
        with open(os.path.join(out_dir, name), "w") as f:
            json.dump(out, f, separators=(",", ":"))


if __name__ == "__main__":
    main()
