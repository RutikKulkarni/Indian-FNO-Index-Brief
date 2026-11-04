#!/usr/bin/env python3
"""
Recent news for index heavyweights from the Upstox News API
(market-data branch, latest/news.json).

Usage:
  python3 news.py --root md [--hours 24] [--symbols HDFCBANK,RELIANCE] [--limit 20] [--json]
"""
import argparse
import datetime as dt
import json
import os

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
TAGS = {
    "results": ["result", "q1", "q2", "q3", "q4", "quarter", "profit", "earnings", "revenue", "nii", "margin"],
    "rbi/rates": ["rbi", "repo", "rate cut", "rate hike", "monetary policy", "inflation"],
    "deal": ["acquire", "acquisition", "merger", "stake", "deal", "buyback", "ipo"],
    "regulatory": ["sebi", "penalty", "probe", "ban", "regulator", "tax", "gst"],
    "rating/target": ["target price", "upgrade", "downgrade", "rating", "brokerage"],
    "crude/fx": ["crude", "oil", "rupee", "dollar"],
}


def tags(text):
    t = (text or "").lower()
    return [k for k, words in TAGS.items() if any(w in t for w in words)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--hours", type=float, default=24)
    ap.add_argument("--symbols", default="")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    d = json.load(open(os.path.join(a.root, "latest/news.json"), encoding="utf-8"))
    cutoff = dt.datetime.now(IST) - dt.timedelta(hours=a.hours)
    want = {s.strip().upper() for s in a.symbols.split(",") if s.strip()}
    items = []
    for it in d.get("items", []):
        try:
            ts = dt.datetime.fromisoformat(it["published"])
        except (TypeError, ValueError):
            continue
        if ts < cutoff:
            continue
        if want and not (want & set(it.get("symbols", []))):
            continue
        items.append(dict(it, tags=tags(f"{it.get('headline')} {it.get('summary')}")))
    items = items[:a.limit]
    if a.json:
        print(json.dumps({"fetched_at": d.get("fetched_at"), "items": items}, indent=1))
        return
    print(f"Heavyweight news, last {a.hours:g} h · Upstox News API · fetched {d.get('fetched_at')}")
    if not items:
        print("No items in the window.")
    for it in items:
        tg = f" [{', '.join(it['tags'])}]" if it["tags"] else ""
        print(f"- {it['published'][5:16].replace('T', ' ')} {','.join(it['symbols'])}: {it['headline']}{tg}")
        if it.get("link"):
            print(f"  {it['link']}")


if __name__ == "__main__":
    main()
