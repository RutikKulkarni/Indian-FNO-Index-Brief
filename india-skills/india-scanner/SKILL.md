---
name: india-scanner
description: Breadth and heavyweight scan for Nifty, Bank Nifty and Sensex. Shows advancers vs decliners, each heavyweight's live % move, top gainers and losers, and strongest and weakest sectors, so you can see which stocks are driving the index. Use for "who is dragging Nifty", "market breadth", "bank nifty heavyweights", or as the heavyweights signal of an F&O brief.
---

# india-scanner

Adapted from the Chart Scanner in Jake Schincariol's day-trader-skill (MIT),
narrowed to the stocks that move Indian indices. New code.

## Data

- `latest/breadth_NIFTY.json`, `latest/breadth_BANKNIFTY.json` on the
  `market-data` branch: live LTP and % change of every constituent (Upstox).
- `india-skills/config/heavyweights.json`: the heavyweights per index. Update
  it when NSE/BSE rebalance the index.
- Sensex has no constituent file; its heavyweights' NSE quotes stand in.

```bash
python3 "${CLAUDE_SKILL_DIR}/scan.py" --root md --index NIFTY
python3 "${CLAUDE_SKILL_DIR}/scan.py" --root md --index BANKNIFTY --top 3
```

## Output

Breadth (up / down), each heavyweight's move, top gainers and losers, the
three weakest and strongest sectors (Nifty, Bank Nifty), and a one-line read:
heavyweights broadly green (≥ 70% up), broadly red (≤ 30% up) or mixed.

## Using it in a brief

Use the read for framework signal 6 (heavyweights): broadly green +1, broadly
red −1, mixed 0. Name the one or two stocks doing most of the work. A single
stock moving on its own news is weaker evidence than a whole sector moving.
