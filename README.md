# Indian F&O Index Brief

An AI agent skill that produces an **index-wise F&O market brief** for Indian
index derivatives. Pick the indices you care about, and the brief covers only
those, each with its own option-chain read, drivers, news, and a
**CE-side / PE-side / No clear edge** bias with levels.

Supported indices:

| Key | Index | Exchange | Expiry (as of Oct 2026) |
|---|---|---|---|
| `NIFTY` | Nifty 50 | NSE | Weekly, Tuesday |
| `BANKNIFTY` | Nifty Bank | NSE | Monthly, last Tuesday |
| `FINNIFTY` | Nifty Financial Services | NSE | Monthly, last Tuesday |
| `MIDCPNIFTY` | Nifty Midcap Select | NSE | Monthly, last Tuesday |
| `NIFTYNXT50` | Nifty Next 50 | NSE | Monthly, last Tuesday |
| `SENSEX` | BSE Sensex | BSE | Weekly, Thursday |
| `BANKEX` | BSE Bankex | BSE | Monthly, last Thursday |

Contract specs change by SEBI / exchange circular; the skill re-checks them at
run time.

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
    └── sample_chain.json            # Illustrative test data
schedules/
└── scheduled-run-prompt.md          # Prompts + cron times for scheduled runs
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

- Data comes from public web pages and may be delayed by several minutes. This
  is not a tick-by-tick feed and is unsuitable for scalping.
- Exchange sites sometimes block automated access; the skill falls back to other
  sources and marks missing data as "not available".
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
