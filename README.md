# NVIDIA CEO Price Forecaster

Forecasts the Yes price of every market of Polymarket's "Next CEO of NVIDIA?" event, minute by minute, 4 hours ahead, as five quantiles (5%, 25%, 50%, 75%, 95%) per minute.

Method: persistence median (no drift — prices are near-martingales) with a per-market spread from realized 1-minute volatility over the last 120 minutes, shrunk by 0.45 and floored/capped (0.0005–0.008 per sqrt-minute), widening like sqrt(h). Practice pinball loss 0.275 vs the house baseline's 0.364 (6 cases p00–p05). Deterministic, offline, Python 3.13 stdlib only.

Run: `python3 main.py` reads `$MAKEFUN_INPUT_DIR` (else `/input/`) and writes one `<case>.out` per case to `$MAKEFUN_OUTPUT_DIR` (else `/output/`).
