# Third-party skills

## day-trader-skill

| | |
|---|---|
| Source | https://github.com/Jakeschincariol/day-trader-skill |
| Version | 2.0.0, commit `3d0f4ef` (20 Oct 2026) |
| Author | Jake Schincariol |
| License | MIT. See [`day-trader-skill/LICENSE`](day-trader-skill/LICENSE) |
| Changes | None. Copied as published. |

Eleven skills for **US stock day trading**: chart scanner, news monitor,
entry timer, exit planner, Time Machine (10,000-session replay), risk manager,
budget manager, order executor (Alpaca / Interactive Brokers, paper trading by
default), price alerts, earnings analyst and a congressional-trades tracker.

### Scope: US stocks, not Indian F&O

These tools read US data sources (Yahoo Finance US charts, Nasdaq Trader
symbol lists, SEC EDGAR, the US House Clerk) and use New York market hours.
The order executor connects to US brokers (Alpaca, Interactive Brokers), not
Upstox or Dhan. They do not cover NSE/BSE index options, and the
`fno-index-brief` skill in this repo does not use them.

### Install

As a Claude Code plugin:

```
/plugin marketplace add Jakeschincariol/day-trader-skill
/plugin install day-trader-skill@day-trader-skill
```

Or copy the folders from this repo:

```bash
cp -r third_party/day-trader-skill/trader-* ~/.claude/skills/
```

Python 3.8+, no packages to install. The SEC tools need
`SEC_USER_AGENT="Your Name you@example.com"`.

### Tests

```bash
cd third_party/day-trader-skill && python3 -m unittest discover -s tests
```

315 tests, all passing at the copied commit.

### Updating

Re-copy the upstream repo over `day-trader-skill/` and update the commit
above. Keep the upstream `LICENSE` file; MIT requires its notice to stay
with the code.
