# Scheduled Run Prompt

Copy one of these into a scheduled task. Each run starts fresh, so the prompt
must say which indices to cover and where the skill lives.

Cron times are IST (`CRON_TZ=Asia/Kolkata`). Runs on non-trading days produce a
short "market closed — outlook" note.

## Pre-market (08:45 IST, Mon–Fri)

```
Run the fno-index-brief skill for: NIFTY, BANKNIFTY, SENSEX.
Session: pre-market. Focus on GIFT Nifty, global cues, overnight news,
previous-day FII/DII flows, and each index's option-chain levels from the last
close. Start with the one-line-per-index summary, then the full brief.
If today is an NSE/BSE trading holiday, send only a one-line note saying so.
```

## Intraday check (e.g. 11:00, 13:30, 14:45 IST, Mon–Fri)

```
Run the fno-index-brief skill for: NIFTY, BANKNIFTY.
Session: live. Use option-chain data no older than 30 minutes; if fresher data
isn't available, mark the bias "No clear edge" for that index.
Start with the one-line-per-index summary, then the full brief.
```

## Choosing indices

Replace the index list with any of:
`NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, NIFTYNXT50, SENSEX, BANKEX` or `all`.

Example cron expressions:

| Run | Cron |
|---|---|
| Pre-market 08:45 | `CRON_TZ=Asia/Kolkata 45 8 * * 1-5` |
| 11:00 | `CRON_TZ=Asia/Kolkata 0 11 * * 1-5` |
| 13:30 | `CRON_TZ=Asia/Kolkata 30 13 * * 1-5` |
| 14:45 (expiry-hour check) | `CRON_TZ=Asia/Kolkata 45 14 * * 1-5` |
