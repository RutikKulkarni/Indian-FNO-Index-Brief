#!/usr/bin/env python3
"""
Smart Money Tracker: how FIIs, DIIs, Pros and Clients are positioned in index
derivatives, how that changed, and bulk/block deals in index stocks.

Data: market-data branch, smartmoney/participant_oi.json (NSE participant-wise
OI, last ~10 trading days), smartmoney/bulk_deals.json, block_deals.json, and
reference/constituents_NIFTY.json / _BANKNIFTY.json.

Usage:
  python3 smartmoney.py --root md            # positioning table + deals in index stocks
  python3 smartmoney.py --root md --days 5 --json
"""
import argparse
import json
import os


def load(root, rel, default=None):
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def positions(p):
    fut_net = p["fut_idx_long"] - p["fut_idx_short"]
    fut_tot = p["fut_idx_long"] + p["fut_idx_short"]
    return {
        "fut_idx_net": fut_net,
        "fut_idx_long_pct": round(100 * p["fut_idx_long"] / fut_tot, 1) if fut_tot else None,
        "call_net": p["opt_idx_call_long"] - p["opt_idx_call_short"],
        "put_net": p["opt_idx_put_long"] - p["opt_idx_put_short"],
    }


def read_fii(series):
    """Plain-language read of FII index-futures positioning over the window."""
    if not series:
        return "not available"
    last = series[-1]
    lp = last["fut_idx_long_pct"]
    trend = series[-1]["fut_idx_net"] - series[0]["fut_idx_net"]
    side = "net long" if last["fut_idx_net"] > 0 else "net short"
    tilt = ("heavily " if lp is not None and (lp < 25 or lp > 75) else "")
    move = "adding to longs / covering shorts" if trend > 0 else ("adding shorts / cutting longs" if trend < 0 else "unchanged")
    return (f"FIIs are {tilt}{side} in index futures ({lp}% of their index-futures OI is long); "
            f"over {len(series)} sessions they have been {move} (net {trend:+,} contracts)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="Path to a checkout of the market-data branch")
    ap.add_argument("--days", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    po = load(a.root, "smartmoney/participant_oi.json")
    if not po or not po.get("days"):
        raise SystemExit("smartmoney/participant_oi.json missing or empty")
    days = po["days"][-a.days:]
    table = {}
    for who in ("FII", "DII", "PRO", "CLIENT"):
        table[who] = [dict(date=d["date"], **positions(d["participants"][who]))
                      for d in days if who in d["participants"]]

    index_syms = set()
    for idx in ("NIFTY", "BANKNIFTY"):
        c = load(a.root, f"reference/constituents_{idx}.json")
        if c:
            index_syms |= {s["symbol"] for s in c["stocks"]}
    deals = []
    for kind in ("bulk", "block"):
        d = load(a.root, f"smartmoney/{kind}_deals.json", {"deals": []})
        for x in d["deals"]:
            if x["symbol"] in index_syms:
                deals.append(dict(kind=kind, **x))

    out = {"participant_oi_fetched_at": po.get("fetched_at"), "dates": [d["date"] for d in days],
           "positioning": table, "fii_read": read_fii(table["FII"]), "index_stock_deals": deals}
    if a.json:
        print(json.dumps(out, indent=1))
        return

    print(f"Participant positioning in index derivatives (NSE, {out['dates'][0]} to {out['dates'][-1]})")
    print("| Date | FII fut net | FII long % | FII call net | FII put net | Client fut net | Pro fut net | DII fut net |")
    print("|---|---|---|---|---|---|---|---|")
    for i, d in enumerate(out["dates"]):
        f = table["FII"][i]
        c, p_, di = table["CLIENT"][i], table["PRO"][i], table["DII"][i]
        print(f"| {d} | {f['fut_idx_net']:+,} | {f['fut_idx_long_pct']}% | {f['call_net']:+,} | {f['put_net']:+,} | "
              f"{c['fut_idx_net']:+,} | {p_['fut_idx_net']:+,} | {di['fut_idx_net']:+,} |")
    print(f"\nRead: {out['fii_read']}.")
    print("Net = long minus short contracts. Calls/puts: long minus short index option contracts.")
    if deals:
        print(f"\nBulk/block deals in Nifty / Bank Nifty stocks (latest NSE file): {len(deals)}")
        print("| Kind | Date | Symbol | Client | Side | Qty | Price |")
        print("|---|---|---|---|---|---|---|")
        for x in deals[:15]:
            print(f"| {x['kind']} | {x['date']} | {x['symbol']} | {x['client']} | {x['side']} | {x['qty']} | {x['price']} |")
    else:
        print("\nNo bulk or block deals in Nifty / Bank Nifty stocks in the latest NSE file.")


if __name__ == "__main__":
    main()
