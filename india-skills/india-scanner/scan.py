#!/usr/bin/env python3
"""
Index scanner: breadth and the heavyweights driving Nifty / Bank Nifty / Sensex.

Data: market-data branch, latest/breadth_NIFTY.json and _BANKNIFTY.json
(live % change of every constituent) and india-skills/config/heavyweights.json.
Sensex uses its heavyweights' NSE quotes as a proxy.

Usage:
  python3 scan.py --root md --index NIFTY [--top 5] [--json]
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(os.path.dirname(HERE), "config", "heavyweights.json")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--index", default="NIFTY", choices=["NIFTY", "BANKNIFTY", "SENSEX"])
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    cfg = load(CONFIG)
    src = "BANKNIFTY" if a.index == "BANKNIFTY" else "NIFTY"
    b = load(os.path.join(a.root, f"latest/breadth_{src}.json"))
    by_sym = {s["symbol"]: s for s in b["stocks"]}
    if a.index == "SENSEX":
        universe = [by_sym[s] for s in cfg["SENSEX"] if s in by_sym]
    else:
        universe = b["stocks"]
    valid = [s for s in universe if s["change_pct"] is not None]
    adv = sum(1 for s in valid if s["change_pct"] > 0)
    dec = sum(1 for s in valid if s["change_pct"] < 0)
    heavy = [by_sym[s] for s in cfg.get(a.index, []) if s in by_sym]
    hv = [s for s in heavy if s["change_pct"] is not None]
    hv_up = sum(1 for s in hv if s["change_pct"] > 0)
    sectors = {}
    for s in valid:
        sectors.setdefault(s["industry"] or "Other", []).append(s["change_pct"])
    sector_avg = sorted(((k, round(sum(v) / len(v), 2), len(v)) for k, v in sectors.items()), key=lambda x: x[1])
    ranked = sorted(valid, key=lambda s: s["change_pct"])

    if len(hv) and hv_up >= 0.7 * len(hv):
        read = "heavyweights broadly green: supports the index"
    elif len(hv) and hv_up <= 0.3 * len(hv):
        read = "heavyweights broadly red: weighs on the index"
    else:
        read = "heavyweights mixed: no clear push from the largest stocks"
    out = {"index": a.index, "fetched_at": b["fetched_at"], "universe": len(valid),
           "advancers": adv, "decliners": dec,
           "heavyweights": [{"symbol": s["symbol"], "change_pct": s["change_pct"], "ltp": s["ltp"]} for s in heavy],
           "heavyweights_up": hv_up, "heavyweights_quoted": len(hv),
           "top_gainers": [(s["symbol"], s["change_pct"]) for s in ranked[::-1][:a.top]],
           "top_losers": [(s["symbol"], s["change_pct"]) for s in ranked[:a.top]],
           "sectors": sector_avg, "read": read}
    if a.json:
        print(json.dumps(out, indent=1))
        return
    note = " (Sensex: its heavyweights' NSE quotes)" if a.index == "SENSEX" else ""
    print(f"{a.index} scan{note} · data {out['fetched_at']}")
    print(f"Breadth: {adv} up / {dec} down of {len(valid)}")
    print("Heavyweights: " + ", ".join(f"{s['symbol']} {s['change_pct']:+.2f}%" for s in hv))
    print("Top gainers: " + ", ".join(f"{s} {c:+.2f}%" for s, c in out["top_gainers"]))
    print("Top losers:  " + ", ".join(f"{s} {c:+.2f}%" for s, c in out["top_losers"]))
    if a.index != "SENSEX":
        print("Weakest sectors: " + ", ".join(f"{k} {v:+.2f}% ({n})" for k, v, n in sector_avg[:3]))
        print("Strongest sectors: " + ", ".join(f"{k} {v:+.2f}% ({n})" for k, v, n in sector_avg[::-1][:3]))
    print(f"Read: {read}")


if __name__ == "__main__":
    main()
