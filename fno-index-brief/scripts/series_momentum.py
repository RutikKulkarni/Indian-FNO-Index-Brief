#!/usr/bin/env python3
"""
Summarise short-term momentum from a 30-second burst series
(market-data branch, series/<INDEX>.json).

Usage:
    python3 series_momentum.py series/NIFTY.json [--json]

Reports, from the first to the last snapshot of the burst:
  - spot and futures change, direction consistency (share of up-ticks)
  - India VIX change
  - total CE OI and PE OI change, and PCR change
  - near-ATM writing: OI added on CE vs PE strikes around ATM
  - ATM CE / PE premium change
and a plain-language read: "building up", "building down" or "mixed".
"""
import argparse
import json


def pct(a, b):
    return None if not a or b is None else round(100 * (b - a) / a, 3)


def analyse(series):
    pts = [p for p in series.get("points", []) if p.get("spot")]
    if len(pts) < 2:
        raise SystemExit("Need at least 2 snapshots in the series")
    first, last = pts[0], pts[-1]
    spots = [p["spot"] for p in pts]
    ups = sum(1 for a, b in zip(spots, spots[1:]) if b > a)
    downs = sum(1 for a, b in zip(spots, spots[1:]) if b < a)

    # Compare only strikes present in both the first and last snapshot, so an
    # ATM shift during the burst doesn't distort the near-ATM OI change.
    common = ({s["strike"] for s in first.get("strikes", [])} &
              {s["strike"] for s in last.get("strikes", [])})

    def near_oi(p, key):
        return sum(s.get(key) or 0 for s in p.get("strikes", []) if s["strike"] in common)

    ref_atm = first.get("atm")  # track the same strike from start to end

    def atm_ltp(p, key):
        return next((s.get(key) for s in p.get("strikes", []) if s.get("strike") == ref_atm), None)

    ce0, pe0 = first["total_ce_oi"], first["total_pe_oi"]
    ce1, pe1 = last["total_ce_oi"], last["total_pe_oi"]
    near_ce = near_oi(last, "ce_oi") - near_oi(first, "ce_oi")
    near_pe = near_oi(last, "pe_oi") - near_oi(first, "pe_oi")
    res = {
        "index": series.get("index"),
        "from": first["t"], "to": last["t"], "snapshots": len(pts),
        "spot_from": first["spot"], "spot_to": last["spot"],
        "spot_change": round(last["spot"] - first["spot"], 2),
        "spot_change_pct": pct(first["spot"], last["spot"]),
        "spot_high": max(spots), "spot_low": min(spots),
        "upticks": ups, "downticks": downs,
        "fut_change": (round(last["fut"] - first["fut"], 2) if first.get("fut") and last.get("fut") else None),
        "vix_from": first.get("vix"), "vix_to": last.get("vix"),
        "ce_oi_change": ce1 - ce0, "pe_oi_change": pe1 - pe0,
        "pcr_from": round(pe0 / ce0, 3) if ce0 else None,
        "pcr_to": round(pe1 / ce1, 3) if ce1 else None,
        "near_atm_ce_oi_added": near_ce, "near_atm_pe_oi_added": near_pe,
        "atm_from": first.get("atm"), "atm_to": last.get("atm"), "tracked_strike": ref_atm,
        "atm_ce_ltp_from": atm_ltp(first, "ce_ltp"), "atm_ce_ltp_to": atm_ltp(last, "ce_ltp"),
        "atm_pe_ltp_from": atm_ltp(first, "pe_ltp"), "atm_pe_ltp_to": atm_ltp(last, "pe_ltp"),
    }
    # Plain-language read
    price_up = res["spot_change"] > 0 and ups > downs
    price_dn = res["spot_change"] < 0 and downs > ups
    puts_writing = near_pe > max(0, near_ce)
    calls_writing = near_ce > max(0, near_pe)
    if price_up and puts_writing:
        read = "building up (price rising with fresh put writing near ATM)"
    elif price_dn and calls_writing:
        read = "building down (price falling with fresh call writing near ATM)"
    elif price_up or price_dn:
        read = ("price " + ("rising" if price_up else "falling") +
                " but option writing does not confirm — mixed")
    else:
        read = "flat / mixed — no short-term momentum"
    res["read"] = read
    return res


def fmt(x):
    if x is None:
        return "n/a"
    return f"{x:+,.0f}" if isinstance(x, (int, float)) and abs(x) >= 1000 else str(x)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("series")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = analyse(json.load(open(a.series, encoding="utf-8")))
    if a.json:
        print(json.dumps(r, indent=1))
        return
    print(f"{r['index']} burst {r['from'][11:19]}–{r['to'][11:19]} ({r['snapshots']} snapshots)")
    print(f"Spot {r['spot_from']} → {r['spot_to']} ({r['spot_change']:+}, {r['spot_change_pct']}%), "
          f"range {r['spot_low']}–{r['spot_high']}, up/down ticks {r['upticks']}/{r['downticks']}")
    print(f"Futures change: {r['fut_change']}   VIX {r['vix_from']} → {r['vix_to']}")
    print(f"Total OI change  CE {fmt(r['ce_oi_change'])}  PE {fmt(r['pe_oi_change'])}  "
          f"PCR {r['pcr_from']} → {r['pcr_to']}")
    print(f"Near-ATM OI added  CE {fmt(r['near_atm_ce_oi_added'])}  PE {fmt(r['near_atm_pe_oi_added'])}")
    print(f"ATM {r['atm_from']} → {r['atm_to']}; strike {r['tracked_strike']}  CE {r['atm_ce_ltp_from']} → {r['atm_ce_ltp_to']}   "
          f"PE {r['atm_pe_ltp_from']} → {r['atm_pe_ltp_to']}")
    print(f"Read: {r['read']}")


if __name__ == "__main__":
    main()
