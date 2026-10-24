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
