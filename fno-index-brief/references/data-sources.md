# Data Sources

Use web search / page fetch. Prefer official sources; fall back in order. Always
record the source name and the timestamp shown on the page.

Exchange sites (NSE especially) often block automated requests. If a fetch
fails, move to the next source rather than retrying the same URL.

## Spot, futures, day range
1. NSE — https://www.nseindia.com (market data → indices)
2. BSE — https://www.bseindia.com (for SENSEX, BANKEX)
3. Moneycontrol, Economic Times Markets, Business Standard markets pages
4. Investing.com / Google Finance index pages

## Option chain (OI, ΔOI, IV)
1. NSE option chain — https://www.nseindia.com/option-chain
2. BSE derivatives — https://www.bseindia.com (SENSEX / BANKEX options)
3. Sensibull, Opstra, Moneycontrol option chain, NiftyTrader, Groww / Upstox
   public option-chain pages
4. If only a summary is available (PCR, max pain, top OI strikes), use it and say
   "summary source, raw chain not available".

When raw rows are available, save them as JSON and run
`scripts/option_chain_metrics.py` (input format in the script header).

## India VIX
NSE India VIX page; fallback: Moneycontrol / Investing.com India VIX.

## Global cues
- GIFT Nifty: NSE IX, Moneycontrol "GIFT Nifty" page, Investing.com
- US / Asia indices and futures: Investing.com, CNBC, Reuters markets, Google Finance
- Brent crude, USD/INR, US 10Y: Investing.com, Reuters, RBI reference rate

## FII / DII flows
NSE "FII/DII trading activity" (published after market close); Moneycontrol
FII/DII page. FII derivatives positioning: NSE participant-wise OI report.

## News
Search "<index> news today", "stock market news India today", "RBI", "Sensex
Nifty today". Prefer Reuters, Economic Times, Business Standard, Mint,
Moneycontrol, CNBC-TV18. Note the publish time; ignore articles older than
24 hours for "today's news".

## Contract specs & calendar
- Lot sizes, expiry days: NSE/BSE circulars, or broker explainer pages that cite
  the circular. Verify when the profile's "as of" is stale.
- Trading holidays: NSE "Holidays" page for the current year.

## Source dating

Every source must show a publish or update date. Reject:
- contract-spec / calendar pages older than 30 days (unless an official circular
  still in force)
- news older than 24 hours (72 hours after a weekend or holiday)
- any undated page, unless a second dated source confirms the same fact

Verified 24 Oct 2026 against: Quantsapp expiry calendar (Oct–Nov 2026),
StockMojo F&O lot sizes (updated 22 Oct 2026), StockeZee lot sizes (Oct 2026),
OneTradeJournal 2026 lot sizes and expiry rules.

## Freshness rules
| Session | Max age for price / OI data |
|---|---|
| Live | 30 min (else force "No clear edge") |
| Pre-market | previous close + latest GIFT Nifty |
| Post-market / closed | today's close |
