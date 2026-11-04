---
name: india-risk
description: Trade calculator and Risk Manager for an Indian index option trade the user has already chosen. From the user's own strike, entry, stop, target and max loss it computes lots that fit, rupee risk and reward after Upstox charges, reward:risk, breakeven, capital, theta per day and the index level that roughly matches the stop and target premiums; then checks it PASS/BLOCK against the user's own limits (max loss per trade, daily loss, trades per day, reward:risk, lots, capital, time window, expiry-day cut-off). Use for "how many lots", "check my trade", "risk check", "position size for my trade".
---

# india-risk

Adapted from the Budget Manager and Risk Manager in Jake Schincariol's
day-trader-skill (MIT), for NSE/BSE index options. New code.

**The user chooses the trade.** This skill never proposes a strike, entry,
stop, target or size. It only calculates and checks what the user gives it.
If the user asks it to pick the trade, say that the trade choice is theirs and
offer the brief's levels and premium reference table as inputs.

## Run

```bash
git clone -q --depth 1 -b market-data https://github.com/RutikKulkarni/Indian-FNO-Index-Brief md
# size and numbers
python3 "${CLAUDE_SKILL_DIR}/trade.py" calc --root md --index NIFTY --strike 23800 --side CE \
  --entry 120 --stop 90 --target 170 --max-loss 3000
# limits check (pass today's realised loss and trade count from the user)
python3 "${CLAUDE_SKILL_DIR}/trade.py" check --root md --index NIFTY --strike 23800 --side CE \
  --entry 120 --stop 90 --target 170 --lots 1 --today-loss 0 --today-trades 0
```

- Lot size, live premium, delta, gamma and theta come from
  `md/latest/<INDEX>.json`. Check its `fetched_at`.
- Charges come from `india-skills/config/charges.json` (Upstox: ₹20 per
  order, STT 0.15% on sell premium, exchange and SEBI fees, stamp duty, GST;
  verified 2026-06-13). Tell the user to check their contract note.
- Limits come from `india-skills/config/risk_limits.json`. Every limit is null
  until the user sets it; unset rules show "not set". Never fill in limits for
  the user.
- Nothing is stored. Ask the user for today's realised loss and trade count.

## Output

A table of lots, risk and reward in rupees, reward:risk, capital, breakeven,
theta per day and index-level estimates, then a PASS/BLOCK table per rule.
Show it as is. A PASS means the trade fits the user's own limits; it is not a
recommendation.
