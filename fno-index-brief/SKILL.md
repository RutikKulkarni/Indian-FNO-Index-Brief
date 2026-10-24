---
name: fno-index-brief
description: Produce an index-wise F&O market brief for Indian index derivatives (Nifty 50, Bank Nifty, FinNifty, Midcap Nifty, Nifty Next 50, Sensex, Bankex). Use when asked for a market brief, F&O view, CE/PE bias, option-chain read, or pre-market/intraday update for one or more Indian indices — e.g. "nifty brief", "bank nifty view today", "sensex CE or PE?", "all indices brief".
---

# F&O Index Brief

Builds a data-backed brief for **one index or a list of indices**, chosen by the user.
Each index is analysed on its own, with its own option chain, drivers and news,
and ends with a **directional bias (CE side / PE side / no clear edge)**, the levels
that matter, and what would invalidate the view.

> This is market information and analysis, not investment advice. The brief never
> tells the reader to place a trade, never suggests position size, and always
> includes the risk note from `references/output-template.md`.

## 1. Resolve which indices to cover

Map the user's words to index keys, then load **only** those profiles from
`references/indices/`:

| User says (any case) | Key | Profile |
|---|---|---|
| nifty, nifty 50, nifty50 | `NIFTY` | `references/indices/nifty50.md` |
| bank nifty, banknifty, bnf | `BANKNIFTY` | `references/indices/banknifty.md` |
| finnifty, fin nifty, nifty financial services | `FINNIFTY` | `references/indices/finnifty.md` |
| midcap nifty, midcpnifty, nifty midcap select | `MIDCPNIFTY` | `references/indices/midcpnifty.md` |
| nifty next 50, niftynxt50, junior nifty | `NIFTYNXT50` | `references/indices/niftynxt50.md` |
| sensex | `SENSEX` | `references/indices/sensex.md` |
| bankex | `BANKEX` | `references/indices/bankex.md` |
| "all", "all indices", nothing specified | all of the above | all profiles |

If the request is from a scheduled run, the index list is in the run's prompt.

## 2. Check the clock and the calendar

1. Get the current IST date and time.
2. Classify the session:
   - **Pre-market**: before 09:15 IST on a trading day
   - **Live**: 09:15–15:30 IST
   - **Post-market**: after 15:30 IST
   - **Holiday / weekend**: market closed. Produce a short *weekly/next-session
     outlook* instead of a live brief, and say clearly the market is closed.
3. Check today against the NSE/BSE holiday list (search for it; don't assume).
4. Work out each index's **nearest expiry** using the rules in its profile, and
   flag **expiry day** and **day before expiry** — option behaviour changes sharply
   then (theta decay, gamma risk, pinning near max pain).

Contract specs (lot size, expiry weekday, weekly vs monthly) change by
SEBI/exchange circular. Each profile has an "as of" date — if it is older than
~3 months, or a search shows a newer circular, use the newer facts and say so.

## 3. Gather data (shared once, then per index)

Follow `references/data-sources.md` for where to look and fallbacks.

**Shared market context (fetch once per run):**
- GIFT Nifty (pre-market) and overnight US indices / US futures
- Asian markets (Nikkei, Hang Seng, Kospi) when pre-market or early session
- India VIX level and change
- USD/INR, Brent crude, US 10Y yield
- Latest FII / DII cash flows and FII index-futures positioning if available
- Top market-moving news of the day (RBI, government policy, global macro,
  big results, geopolitics) — headline + one-line impact

**Per index (repeat for each selected index):**
- Spot level, change %, day high/low, previous close
- Futures price and premium/discount to spot
- Option chain for the nearest expiry: total CE OI, total PE OI, OI change,
  top 3 CE strikes by OI, top 3 PE strikes by OI, ATM IV
- Index-specific drivers from its profile (heavyweight stocks, sector news)

Every number in the brief must come from something fetched **in this run**,
with its source and timestamp. If a figure cannot be found, write
"not available" — never estimate or recall it from memory.

If you have raw option-chain rows (strike, CE OI, PE OI, CE ΔOI, PE ΔOI),
compute metrics with the bundled script instead of by hand:

```bash
python3 scripts/option_chain_metrics.py chain.json --spot 25150 --step 50
```

It prints PCR (OI and ΔOI), max pain, top OI strikes, OI-based support and
resistance, and the ATM strike. See the script header for the input format.

## 4. Analyse each index

Apply `references/analysis-framework.md` to each index separately. It defines:
- how each signal is read (trend, OI/PCR, max pain, VIX, futures basis,
  heavyweights, news, global cues)
- how signals are scored and combined into a bias
- when the answer must be **"No clear edge"** (conflicting signals, event risk,
  stale data)
- the confidence level (Low / Medium / High) and what caps it

Don't let one index's view leak into another's. Bank Nifty can be bearish while
Nifty is neutral — report each as the data says.

## 5. Write the brief

Use the exact layout in `references/output-template.md`:
1. Header (date, time IST, session type, data freshness)
2. Market context (shared, short)
3. One block per index, in the order the user listed them
4. Event watch for the rest of the day / next session
5. Risk note (always)

Keep it scannable: tables for numbers, one or two lines of reasoning per signal.
For a scheduled run, keep the whole brief readable on a phone in under two minutes.

## 6. Quality checks before sending

- [ ] Every index requested has a block; no extra indices
- [ ] Each number has a source and time; nothing invented
- [ ] Expiry date and lot size per index checked against current rules
- [ ] Bias follows from the scored signals (not from a hunch)
- [ ] "No clear edge" used whenever the framework says so
- [ ] Invalidation level stated for every CE/PE-side bias
- [ ] Risk note present; no instruction to buy/sell, no position sizing
