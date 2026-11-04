---
name: india-analyst
description: Earnings analyst for Indian index heavyweights. Finds which Nifty, Bank Nifty and Sensex heavyweights report results this week, and for a reported quarter summarises what changed (revenue, profit, margins; for banks NII, NIM, GNPA/NNPA, credit growth) versus last year and last quarter, and the stock's reaction. Use for "results this week", "HDFC Bank Q2 results", "how did Reliance's quarter look", or to flag results risk in an F&O brief.
---

# india-analyst

Adapted from the Earnings Analyst in Jake Schincariol's day-trader-skill
(MIT), for Indian companies. This one is a method, not a script: Indian
results are read from exchange filings and dated news.

## 1. Who reports this week

For the stocks in `india-skills/config/heavyweights.json`, search the NSE/BSE
board-meeting calendar and news with the current week in the query (e.g.
"board meeting results date <company> <month year>"). List date and company.
A heavyweight reporting during or right after the session is event risk for
its index (cap confidence at Low for that index that day).

## 2. A reported quarter

Use the company's results filing on NSE/BSE or its investor presentation, and
dated coverage (Economic Times, Business Standard, Mint, Moneycontrol,
CNBC-TV18). Report, each with YoY and QoQ change:

| all companies | banks and NBFCs, in addition |
|---|---|
| Revenue / total income | Net interest income (NII) |
| EBITDA and margin (non-financials) | Net interest margin (NIM) |
| Net profit (consolidated if available) | GNPA and NNPA %, provisions |
| Guidance or management commentary | Loan and deposit growth, CASA ratio |

Then: versus consensus if a dated source gives it, the stock's move on the
result (from `latest/breadth_<INDEX>.json` or a quote), and one line on the
effect on its index.

## Rules

- Every figure from a filing or a dated source, cited; "not available" otherwise.
- Never estimate numbers from memory.
- Describe the results; do not tell the reader to buy or sell the stock.
