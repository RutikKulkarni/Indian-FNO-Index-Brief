---
name: india-orb
description: Opening-range read for Nifty, Bank Nifty, Sensex, FinNifty and Midcap Nifty from today's 1-minute candles. Reports the first-15-minute range, whether the index has broken above or below it on a 5-minute close, whether the breakout is holding, and any failed breakouts. Use for "opening range", "ORB", "has Nifty broken out", or as part of an intraday F&O brief's price-trend signal.
---

# india-orb

Adapted from the opening-range-breakout setup in Jake Schincariol's
day-trader-skill (MIT), applied to the index itself. New code. It describes
what the index has done; it does not say when to enter a trade.

## Data

`latest/candles_<INDEX>.json` on the `market-data` branch: today's 1-minute
candles, refreshed with every market-data run. Check `fetched_at` (≤ 30
minutes old during market hours).

```bash
python3 "${CLAUDE_SKILL_DIR}/orb.py" --candles md/latest/candles_NIFTY.json
```

`--minutes 15` sets the opening-range length (09:15–09:30). `--json` for
machine-readable output.

## Output

- Opening range high / low / width, last price and where it sits (above,
  inside, below), day high / low.
- Breakout: first completed 5-minute close beyond the range, its time, whether
  price is still beyond it, and the furthest move beyond.
- Failed breakouts: a 5-minute close back inside the range after a breakout.

## Using it in a brief

Add one line under the index's price-trend signal, e.g. "ORB: broke above
23,628 at 10:10 and holding (+183 pts)". A breakout that is holding supports
a price-trend score in its direction (+1 / −1); a failed breakout or price
back inside the range argues for "range" (0). Before 09:30 say "opening range
still forming".
