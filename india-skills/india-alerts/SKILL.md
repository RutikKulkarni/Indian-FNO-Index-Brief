---
name: india-alerts
description: Index level alerts for Nifty, Bank Nifty, Sensex, FinNifty and Midcap Nifty. Add, list or remove alerts like "Nifty above 23,900" or "Bank Nifty below 56,800"; each market-data run checks today's 1-minute candles and opens a GitHub issue in the repo when an alert is hit (GitHub notifies by email and app). Use for "alert me when", "set an alert", "my alerts", "remove alert".
---

# india-alerts

Adapted from Price Alerts in Jake Schincariol's day-trader-skill (MIT). New
code.

## How it works

- Alerts live in `india-skills/india-alerts/alerts.json` on `main` of
  `RutikKulkarni/Indian-FNO-Index-Brief`.
- Every market-data run (`data_fetcher/india_data.py alerts`) checks each
  active alert against today's 1-minute candles, so a touch between runs is
  still caught.
- A hit opens a GitHub issue labelled `alert` ("🔔 NIFTY above 23900 (hit
  10:42 IST, now 23915)"). GitHub sends the repo owner an email and an app
  notification. Each alert fires at most once per day
  (`state/alerts_fired.json` on `market-data`).

## Adding, listing, removing

Edit `alerts.json` on `main` and commit (as the repo owner). Format:

```json
{"alerts": [
  {"id": "nifty-above-23900", "index": "NIFTY", "direction": "above", "level": 23900,
   "note": "invalidation of PE-side view", "active": true}
]}
```

`index`: NIFTY, BANKNIFTY, SENSEX, FINNIFTY or MIDCPNIFTY. `direction`:
above | below. Set `active` to false to pause, or delete the entry.

## Limits

Alerts are checked when the market-data job runs (each brief starts one, plus
GitHub's best-effort schedule), so a notification can be minutes late. For
alerts where timing matters, also set them in the Upstox app, which notifies
on the live price.
