# Output Template

Use this layout exactly. Replace `<…>`. Drop a row only if the data was
unavailable, and then write "not available" rather than removing the row.

````markdown
# 📊 F&O Index Brief — <DD Mon YYYY>, <HH:MM> IST
**Session:** <Pre-market | Live | Post-market | Market closed — outlook>
**Indices:** <NIFTY, BANKNIFTY, …>  ·  **Data as of:** <HH:MM IST, oldest key figure>

## 🌍 Market context
| | Level | Change |
|---|---|---|
| GIFT Nifty | <…> | <…> |
| India VIX | <…> | <…> |
| US (S&P 500 / Nasdaq fut.) | <…> | <…> |
| Asia (Nikkei / Hang Seng) | <…> | <…> |
| Brent crude | <…> | <…> |
| USD/INR | <…> | <…> |
| FII / DII cash (prev. day) | <₹… cr / ₹… cr> | |

**Top news**
- <Headline> — <one-line likely impact, and on which indices>
- <…>

---

## <INDEX NAME> · Expiry <DD Mon (weekly/monthly)> <⚠️ EXPIRY DAY if today>
| Spot | Change | Day range | Futures (basis) |
|---|---|---|---|
| <…> | <+/-…%> | <low – high> | <… (+/-…)> |

| Option chain (<expiry>) | |
|---|---|
| PCR (OI) / PCR (ΔOI) | <…> / <…> |
| Max pain | <…> |
| Resistance (top CE OI) | <strike (OI)>, <…>, <…> |
| Support (top PE OI) | <strike (OI)>, <…>, <…> |
| ATM IV | <…> |

**Momentum (30-sec burst <HH:MM–HH:MM>):** <spot change, up/down ticks,
near-ATM OI added CE vs PE, ATM premium change> → <building up | building down |
mixed | not available>

**Signal read**
| Signal | Score | Why |
|---|---|---|
| Price trend | <-2…+2> | <…> |
| Option chain | <…> | <…> |
| Max pain / expiry | <…> | <…> |
| VIX / IV | <…> | <…> |
| Futures basis | <…> | <…> |
| Heavyweights | <…> | <…> |
| News | <…> | <…> |
| Global cues | <…> | <…> |

### ➡️ Bias: <🟢 Bullish — CE side | 🔴 Bearish — PE side | ⚪ No clear edge>
**Confidence:** <High | Medium | Low>  ·  **Score:** <normalised, e.g. +0.42>
- **Confirms above/below:** <level>
- **Invalidated if:** <level>
- **Expected range today:** <low – high>
- **Watch:** <the one thing most likely to change this view>

**Premium reference (<CE|PE> side, data <HH:MM>)** — only for CE/PE-side bias
| Option | LTP | IV | Delta | Theta/day | @<invalidation> | @<confirmation> | @<range edge> |
|---|---|---|---|---|---|---|---|
| <strike side (ITM/ATM/OTM)> | <…> | <…> | <…> | <…> | <…> | <…> | <…> |
_Estimated premiums if the index reached each level now; they ignore time decay
and IV changes. Reference data only — not an entry, stop-loss or target._

<repeat the index block for each selected index>

---

## 🗓️ Event watch
- <time IST> — <event> — <indices affected>

## ⚠️ Risk note
This brief is market information and analysis for education, not investment
advice or a recommendation to buy or sell. Data may be delayed. Options carry a
high risk of loss — SEBI studies have found most individual F&O traders lose
money. Do your own analysis, use stop-losses, and consult a SEBI-registered
adviser before trading.
````

## Short form (scheduled runs, push notifications)

When the output goes to a notification, send a one-line-per-index summary first,
then the full brief:

```
NIFTY 25,150 (+0.4%) · 🟢 CE side · Med · inv. 25,000
BANKNIFTY 56,300 (-0.6%) · 🔴 PE side · Low · inv. 56,700
SENSEX 82,400 (+0.3%) · ⚪ No clear edge
```
