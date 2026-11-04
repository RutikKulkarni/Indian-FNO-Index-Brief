---
name: india-timemachine
description: Time Machine for Indian indices (Nifty, Bank Nifty, Sensex). Replays the index's own last ~70 sessions and 10,000 simulated rest-of-day paths to show how often it reached an upper level before a lower level from the same time of day. Use to check a CE/PE-side bias or any pair of levels before relying on them, e.g. "how often does Nifty hit 23,900 before 23,650 from here", "time machine bank nifty".
---

# india-timemachine

Adapted for NSE/BSE indices from the Time Machine in Jake Schincariol's
day-trader-skill (MIT). New code; same idea: look at how the index has
actually behaved before trusting a read.

## Data

`history/<INDEX>_5m.json` on the `market-data` branch of
`RutikKulkarni/Indian-FNO-Index-Brief` (NIFTY, BANKNIFTY, SENSEX; about 70
sessions of 5-minute candles, refreshed by the daily job). Check its
`last_day`: it should be the previous trading session or today.

```bash
git clone -q --depth 1 -b market-data https://github.com/RutikKulkarni/Indian-FNO-Index-Brief md
```

## Run

```bash
python3 "${CLAUDE_SKILL_DIR}/timemachine.py" --history md/history/NIFTY_5m.json \
  --spot 23800 --up 23900 --down 23650 --at 10:45
```

- `--spot`: current index level (from `md/latest/<INDEX>.json`).
- `--up` / `--down`: the two levels to race. For a brief, use the bias's
  confirmation level and invalidation level (one above spot, one below).
- `--at`: start time (IST); default now. `--until` defaults to 15:25.
- `--sims 10000 --seed 7`: simulation size and seed (repeatable).
- `--keep-drift`: keep the sample's trend in the simulation (default removes
  it, so the simulation measures swing size only; the history replay always
  keeps the real trend).
- `--json` for machine-readable output.

## Reading the output

| column | meaning |
|---|---|
| Up first / Down first | share of sessions (or paths) that touched that level first |
| Both in one bar | both levels inside one 5-minute bar: order unknown |
| Neither by end | neither level touched by the end time |

The `Read:` line says whether one level is reached first clearly more often
(by 10+ percentage points), whether the two checks disagree, or whether it is
close to a coin flip.

## Using it in a brief

Show the table and the read under the index's bias. If the level on the
bias side is **not** reached first more often than the other level, cap the
bias's confidence at Low and say so in one line. Never present these numbers
as a prediction or a probability of profit.

## Limits

- About 70 sessions is a small sample. It includes whatever trend those weeks
  had.
- It knows nothing about scheduled events (RBI, results, Fed, budget) or gaps.
- Index levels only; option premiums also lose time value, which this ignores.
