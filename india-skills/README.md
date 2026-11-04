# India skills

Seven skills for Indian index F&O analysis, adapted from the ideas in
[day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill) by
Jake Schincariol (MIT; original copied unchanged in
[`../third_party/day-trader-skill`](../third_party/day-trader-skill)).
The code here is new and written for NSE/BSE indices and Upstox data.

| Skill | What it does | Based on |
|---|---|---|
| [`india-timemachine`](india-timemachine/SKILL.md) | How often the index reached one level before another from the same time of day: 70-session replay + 10,000 simulated paths | Time Machine |
| [`india-smartmoney`](india-smartmoney/SKILL.md) | FII / DII / Pro / Client positioning in index futures and options, bulk and block deals, insider trades | Pelosi Tracker (India alternative) |
| [`india-orb`](india-orb/SKILL.md) | Opening-range breakout read on the index | Entry Timer / ORB setup |
| [`india-scanner`](india-scanner/SKILL.md) | Breadth, heavyweights, sectors driving the index | Chart Scanner |
| [`india-news`](india-news/SKILL.md) | Heavyweight news (Upstox News API) + dated macro news | News Monitor |
| [`india-analyst`](india-analyst/SKILL.md) | Results calendar and quarterly results of index heavyweights | Earnings Analyst |
| [`india-alerts`](india-alerts/SKILL.md) | Index level alerts delivered as GitHub issues | Price Alerts |
| [`india-risk`](india-risk/SKILL.md) | Calculator + Risk Manager for a trade you have chosen: lots, ₹ risk/reward with charges, PASS/BLOCK against your limits | Budget Manager + Risk Manager |

Not adapted: the Exit Planner (it generates stops and targets), the Order
Executor (order placement), and the Pelosi Tracker itself (US Congress only;
`india-smartmoney` replaces it).

## Data

All market data comes from the `market-data` branch, filled by
[`.github/workflows/market-data.yml`](../.github/workflows/market-data.yml):

| Mode | When | Writes |
|---|---|---|
| snapshot | each brief starts one; GitHub schedule as fallback | `latest/` option chains, 1-min candles, breadth, news; checks alerts |
| burst | before intraday briefs | `series/` 10 × 30 s snapshots |
| daily | evening (and before the pre-market brief) | `history/` 5-min candles, `smartmoney/`, `reference/` |

Config: [`config/heavyweights.json`](config/heavyweights.json),
[`config/charges.json`](config/charges.json),
[`config/risk_limits.json`](config/risk_limits.json) (your own limits).

## Install as skills

```bash
cp -r india-skills/india-* ~/.claude/skills/
cp -r india-skills/config ~/.claude/skills/config
```

The scripts are standard-library Python 3.8+.

All of this describes what the market has done and how reliable past reads
were. It is not investment advice.
