# Indian F&O Index Brief

An AI agent skill that produces an **index-wise F&O market brief** for Indian
index derivatives. Pick the indices you care about, and the brief covers only
those, each with its own option-chain read, drivers, news, and a
**CE-side / PE-side / No clear edge** bias with levels.

Supported indices:

| Key | Index | Exchange | Lot size | Expiry (verified 24 Oct 2026) |
|---|---|---|---|---|
| `NIFTY` | Nifty 50 | NSE | 65 | Weekly, Tuesday |
| `BANKNIFTY` | Nifty Bank | NSE | 30 | Monthly, last Tuesday |
| `FINNIFTY` | Nifty Financial Services | NSE | 60 | Monthly, last Tuesday |
| `MIDCPNIFTY` | Nifty Midcap Select | NSE | 120 | Monthly, last Tuesday |
| `NIFTYNXT50` | Nifty Next 50 | NSE | 25 | Monthly, last Tuesday |
| `SENSEX` | BSE Sensex | BSE | 20 | Weekly, Thursday |
| `BANKEX` | BSE Bankex | BSE | 30 | Monthly, last Thursday |

If an expiry day is a trading holiday, expiry moves to the previous trading day
(e.g. Nifty weekly 10 Nov 2026 → Mon 9 Nov; NSE monthly 24 Nov 2026 → Mon 23 Nov).
Contract specs change by SEBI / exchange circular; the skill re-verifies them on
every run using sources dated in the last 30 days.

## What a brief contains

1. **Market context** — GIFT Nifty, India VIX, US/Asia cues, crude, USD/INR,
   FII/DII flows, top news
2. **Per index** — spot, futures basis, PCR (OI and ΔOI), max pain, top CE/PE OI
   strikes, ATM IV, and an 8-signal scorecard
3. **Bias** — 🟢 CE side / 🔴 PE side / ⚪ No clear edge, with confidence,
   confirmation level, invalidation level and expected range
4. **Event watch** and a **risk note**

The bias comes from a fixed scoring framework
([`analysis-framework.md`](fno-index-brief/references/analysis-framework.md)),
and it is forced to "No clear edge" when data is stale, signals conflict, or a
major event is due.

## Live data pipeline (Upstox)

```
GitHub Actions (every 15 min, 09:00–15:45 IST, Mon–Fri)
  ├─ regular: all indices once        → market-data: latest/<INDEX>.json
  └─ burst (≈10:28, 12:28, 14:28 IST):
       10 snapshots × 30 s, Nifty / Bank Nifty / Sensex → series/<INDEX>.json
            └─ fno-index-brief skill reads both → brief
```

- Data: spot, previous close, nearest futures + basis, India VIX, and the full
  option chain (OI, change in OI, LTP, volume, IV, delta) for the nearest expiry.
- Auth: a read-only Upstox **Analytics Token** (free, valid 1 year, cannot place
  orders) stored as the repository secret `UPSTOX_ANALYTICS_TOKEN`.
- The `market-data` branch holds only the latest snapshot (force-updated), so
  repository history stays small.
- Run it manually from **Actions → Market data snapshot → Run workflow**
  (`debug` also saves raw API responses).
- Renew the token yearly at account.upstox.com/developer/apps → Analytics, then
  update the secret.

## Repository layout

```
fno-index-brief/
├── SKILL.md                         # Entry point: workflow the agent follows
├── references/
│   ├── analysis-framework.md        # Signal scoring, bias & confidence rules
│   ├── output-template.md           # Exact brief layout + short form
│   ├── data-sources.md              # Where to fetch data, fallbacks, freshness
│   └── indices/                     # One profile per index
│       ├── nifty50.md
│       ├── banknifty.md
│       ├── finnifty.md
│       ├── midcpnifty.md
│       ├── niftynxt50.md
│       ├── sensex.md
│       └── bankex.md
└── scripts/
    ├── option_chain_metrics.py      # PCR, max pain, OI walls, ATM IV
    ├── series_momentum.py           # 30-sec burst → short-term momentum read
    ├── premium_levels.py            # Option premiums now + estimated at index levels
    └── sample_chain.json            # Illustrative test data
data_fetcher/
└── upstox_fetch.py                  # Upstox → normalized JSON snapshots
schedules/
└── scheduled-run-prompt.md          # Prompts + cron times for scheduled runs
.github/workflows/
└── market-data.yml                  # Market-hours snapshot job
```

## Usage

Install `fno-index-brief/` as a skill in your agent, then ask:

- "Nifty brief"
- "Bank Nifty and Sensex view"
- "All indices brief"

For automatic runs, use the prompts in
[`schedules/scheduled-run-prompt.md`](schedules/scheduled-run-prompt.md).

### Option-chain script

```bash
python3 fno-index-brief/scripts/option_chain_metrics.py \
  fno-index-brief/scripts/sample_chain.json --spot 25140 --step 50
```

Add `--json` for machine-readable output. Python 3.8+, no dependencies.

## Limitations

- Market data refreshes every 15 minutes, and GitHub's scheduler can start runs
  a few minutes late. This is not a tick-by-tick feed and is unsuitable for
  scalping.
- News, global cues and FII/DII flows come from public web pages; missing data
  is marked "not available".
- Low-liquidity indices (FinNifty, Midcap Nifty, Nifty Next 50, Bankex) give
  weaker option-chain signals.

## Disclaimer

This project produces market information and analysis for educational use. It
is **not investment advice** and not a recommendation to buy or sell any
security or derivative. The author is not a SEBI-registered investment adviser.
Options trading carries a high risk of loss — SEBI studies have found most
individual F&O traders lose money. Do your own research and consult a
SEBI-registered adviser before trading.

## License

MIT
