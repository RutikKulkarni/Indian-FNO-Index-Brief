# Analysis Framework

Apply this to **each index separately**. Score each signal from **-2 (strongly
bearish)** to **+2 (strongly bullish)**, 0 when neutral or unavailable. Write the
reason next to every score.

## Signals

### 1. Price trend & structure (weight ×2)
- Spot vs previous close, day high/low, and position within the day's range.
- Higher highs / higher lows on the intraday chart → bullish; the reverse → bearish.
- Spot above/below key moving levels if published by the source (e.g. 20-DMA, VWAP).
- Gap up/down at open and whether the gap is filling.

| Reading | Score |
|---|---|
| Strong up-move, holding near day high, above VWAP | +2 |
| Mild up, mid-to-upper range | +1 |
| Flat / range-bound | 0 |
| Mild down, mid-to-lower range | -1 |
| Strong down-move, near day low, below VWAP | -2 |

### 2. Option-chain positioning (weight ×2)
- **PCR (OI)** = total PE OI ÷ total CE OI.
  - > 1.3 → heavy put writing (support below) → bullish lean, but > 1.6 can mean
    over-bought / crowded → cap at +1
  - 0.9–1.3 → balanced
  - < 0.7 → heavy call writing (resistance above) → bearish lean; < 0.5 can mean
    over-sold → cap at -1
- **ΔOI PCR** (today's change) shows *fresh* positioning and outweighs the
  absolute PCR intraday.
- **Highest PE OI strike** = likely support; **highest CE OI strike** = likely
  resistance. Note if writers are shifting strikes (PE OI building at higher
  strikes → bullish; CE OI building at lower strikes → bearish).
- Spot squeezed between two big OI walls → range, score 0.

### 3. Max pain & expiry dynamics (weight ×1, ×2 on expiry day)
- Distance of spot from max pain. Near expiry, spot often drifts toward max pain.
- Spot well above max pain on expiry day → mild bearish pull (-1); well below → +1.
- More than 2 sessions from expiry → weight this at ×0.5.

### 4. Volatility — India VIX & ATM IV (weight ×1)
- VIX rising sharply with index falling → fear, bearish (-1 / -2).
- VIX falling with index rising → calm uptrend (+1).
- VIX spike with flat index → event risk; push the overall verdict toward
  "No clear edge" and note that option premiums are expensive.

### 5. Futures basis & FII positioning (weight ×1)
- Futures premium widening with rising OI → long build-up (+1).
- Premium shrinking / discount with rising OI → short build-up (-1).
- FII net long/short ratio in index futures, when published, as context.

### 6. Heavyweights & sector drivers (weight ×1)
- Use the stocks/sectors listed in the index profile.
- Majority of heavyweights green with volume → +1; red → -1.
- One stock dragging the index on stock-specific news is a weaker signal than a
  broad sector move — say which it is.

### 7. News & events (weight ×1)
- Index-relevant news from the profile's triggers (RBI for banks, crude for
  OMCs/Reliance, US tech for IT, etc.).
- Positive surprise +1 / negative -1. A scheduled high-impact event later today
  (RBI policy, US CPI/Fed, budget, election result) → cap confidence at Low.

### 8. Global cues (weight ×1, ×0.5 after 11:00 IST)
- GIFT Nifty, US futures, Asian markets, crude, USD/INR.
- Matters most pre-market; fades as the Indian session develops its own trend.

## Combining

```
total = Σ (score × weight)
max_possible = Σ (2 × weight)  for the signals that had data
normalised = total / max_possible          # range -1.0 … +1.0
```

| Normalised | Bias |
|---|---|
| ≥ +0.35 | **Bullish → CE side favoured** |
| +0.15 to +0.35 | Mildly bullish → CE side, low conviction |
| -0.15 to +0.15 | **No clear edge** (range / wait) |
| -0.35 to -0.15 | Mildly bearish → PE side, low conviction |
| ≤ -0.35 | **Bearish → PE side favoured** |

## Forced "No clear edge"

Output **No clear edge** regardless of score when any of these hold:
- Fewer than 4 of the 8 signals have fresh data
- Option-chain data is older than 30 minutes during live market
- Price trend (1) and option chain (2) point in opposite directions with
  |score| ≥ 1 each
- A high-impact scheduled event is due within the next 60 minutes
- The market is closed (give an outlook for the next session instead)

## Confidence

| Confidence | Conditions |
|---|---|
| High | |normalised| ≥ 0.5, signals 1 and 2 agree, no event risk, data < 15 min old |
| Medium | |normalised| ≥ 0.35, no forced-neutral conditions |
| Low | Anything else, or any event within the session, or expiry-day gamma risk |

## Levels to state for every CE/PE-side bias

- **Trigger zone**: the level that confirms the view (e.g. sustained move above
  highest-CE-OI strike for CE side).
- **Invalidation**: the level where the view is wrong (usually the opposite OI wall
  or the day's low/high). Always state it.
- **Support / resistance**: the nearest significant OI walls (closest strike
  with ≥ 50% of the side's biggest OI) and the strongest walls, both printed by
  `option_chain_metrics.py`. Use the nearest walls for the session's levels.
- **Expected range** for the session if VIX is available:
  `spot × (VIX / 100) / √252` ≈ one-standard-deviation daily move.

Never give a premium target, strike recommendation with quantity, or position
size. The levels describe the index, not a trade.
