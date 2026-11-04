---
name: india-smartmoney
description: Smart Money Tracker for Indian index derivatives, the India alternative to a congressional-trades tracker. Shows how FIIs, DIIs, Pros and retail Clients are positioned in index futures and options (NSE participant-wise OI, last 5-10 sessions), how FII positioning is shifting, bulk/block deals in Nifty and Bank Nifty stocks, and insider/promoter trades in index heavyweights. Use for "FII positioning", "smart money", "what are FIIs doing", "bulk deals", "insider trades", or as the futures/FII input of an F&O brief.
---

# india-smartmoney

India's public disclosures that matter for index F&O, adapted from the idea
of the Pelosi Tracker in Jake Schincariol's day-trader-skill (MIT). New code.

## Data (market-data branch, daily job ~19:15 IST)

| file | source |
|---|---|
| `smartmoney/participant_oi.json` | NSE participant-wise OI, last ~10 trading days (published after each session) |
| `smartmoney/bulk_deals.json`, `block_deals.json` | NSE's latest bulk and block deal files |
| `reference/constituents_NIFTY.json`, `_BANKNIFTY.json` | NSE index lists, to filter deals to index stocks |

```bash
git clone -q --depth 1 -b market-data https://github.com/RutikKulkarni/Indian-FNO-Index-Brief md
python3 "${CLAUDE_SKILL_DIR}/smartmoney.py" --root md --days 5
```

Check `participant_oi_fetched_at` and the last date in the table: it should be
the previous trading day (NSE publishes it in the evening).

## What it prints

- Per session: FII index-futures net (long − short), share of FII index-futures
  OI that is long, FII net index calls and net index puts, and the index-futures
  net of Clients, Pros and DIIs.
- A one-line read of FII positioning and its direction over the window.
- Bulk and block deals in Nifty / Bank Nifty stocks.

## Insider and promoter trades

NSE's insider-trading (SEBI PIT) and SAST disclosure pages block automated
downloads, so look these up with a web search dated to the last 7 days, for the
index heavyweights in `india-skills/config/heavyweights.json` only
(e.g. "HDFC Bank promoter shares sold <month year>", "insider trading
disclosure <company> <month year>"). Report only dated, sourced items.

## Reading it

- FIIs heavily net short (long share under ~25%) and still adding shorts:
  a headwind signal for index futures (framework signal 5, −1).
- FIIs covering shorts over several sessions: easing headwind (signal 5 toward 0 / +1).
- Clients usually sit on the opposite side of FIIs; Client positioning alone is
  not a directional signal.
- FII index puts: long puts can be hedges for cash holdings, not just bearish bets.
- Bulk/block deals and insider trades are stock-level news: mention them only
  for heavyweights that move the index.

This is public positioning data, not a prediction.
