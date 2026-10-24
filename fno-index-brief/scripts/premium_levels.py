#!/usr/bin/env python3
"""
Show option premiums for strikes near spot and estimate where each premium
would be if the index moved to given levels.

Input: an index snapshot JSON (market-data branch, latest/<INDEX>.json) whose
"rows" include strike, ce_ltp/pe_ltp, ce_iv/pe_iv, ce_delta/pe_delta and,
when available, ce_gamma/pe_gamma and ce_theta/pe_theta.

Usage:
    python3 premium_levels.py latest/NIFTY.json --levels 22400,22700 [--side PE] [--strikes 3]

Estimate (per strike):  P(L) ≈ P + Δ·(L − S) + ½·Γ·(L − S)²
floored at intrinsic value (and at 0.05). It assumes the move happens now:
it ignores time decay (theta, shown per day) and IV changes, so treat it as a
rough reference, not a price forecast. Large moves and expiry day make the
estimate less reliable.
"""
import argparse
import json


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def estimate(p, delta, gamma, spot, level, strike, side):
    if p is None or delta is None:
        return None
    d = level - spot
    est = p + delta * d + 0.5 * (gamma or 0.0) * d * d
    intrinsic = max(0.0, level - strike) if side == "CE" else max(0.0, strike - level)
    return round(max(est, intrinsic, 0.05), 2)


def build(snap, levels, sides, n):
    spot, step = num(snap.get("spot")), num(snap.get("strike_step"))
    rows = {r["strike"]: r for r in snap.get("rows", [])}
    if not spot or not step or not rows:
        raise SystemExit("Snapshot is missing spot, strike_step or rows")
    atm = round(spot / step) * step
    out = []
    for side in sides:
        k = side.lower()
        # ATM plus n strikes in-the-money and n out-of-the-money for that side
        strikes = [atm + i * step for i in range(-n, n + 1)]
        for s in strikes:
            r = rows.get(s)
            if not r or r.get(f"{k}_ltp") in (None, 0):
                continue
            p, dl, gm = num(r.get(f"{k}_ltp")), num(r.get(f"{k}_delta")), num(r.get(f"{k}_gamma"))
            moneyness = "ATM" if s == atm else (
                ("ITM" if s < spot else "OTM") if side == "CE" else ("ITM" if s > spot else "OTM"))
            out.append({
                "side": side, "strike": s, "moneyness": moneyness, "ltp": p,
                "iv": num(r.get(f"{k}_iv")), "delta": dl, "gamma": gm,
                "theta_per_day": num(r.get(f"{k}_theta")),
                "oi": num(r.get(f"{k}_oi")), "volume": num(r.get(f"{k}_volume")),
                "at_levels": {str(int(L)) if float(L).is_integer() else str(L):
                              estimate(p, dl, gm, spot, L, s, side) for L in levels},
            })
    return {"index": snap.get("index"), "spot": spot, "atm": atm, "expiry": snap.get("expiry"),
            "lot_size": snap.get("lot_size"), "fetched_at": snap.get("fetched_at"),
            "levels": levels, "options": out}


def fmt(x, d=2):
    return "—" if x is None else (f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.{d}f}")


def print_table(res):
    lv = [str(int(L)) if float(L).is_integer() else str(L) for L in res["levels"]]
    print(f"{res['index']}  spot {fmt(res['spot'])}  ATM {fmt(res['atm'])}  expiry {res['expiry']}  "
          f"lot {res['lot_size']}  data {res['fetched_at']}")
    head = ["Option", "LTP", "IV", "Delta", "Theta/day"] + [f"@{l}" for l in lv]
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for o in res["options"]:
        name = f"{int(o['strike'])} {o['side']} ({o['moneyness']})"
        cells = [name, fmt(o["ltp"]), fmt(o["iv"], 1), fmt(o["delta"], 2), fmt(o["theta_per_day"], 1)]
        cells += [fmt(o["at_levels"][l]) for l in lv]
        print("| " + " | ".join(cells) + " |")
    print("\nEstimates assume an immediate move; they ignore time decay and IV changes.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("snapshot")
    ap.add_argument("--levels", required=True, help="Comma-separated index levels, e.g. 22400,22700")
    ap.add_argument("--side", default="both", choices=["CE", "PE", "both"])
    ap.add_argument("--strikes", type=int, default=2, help="Strikes either side of ATM (default 2)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    snap = json.load(open(a.snapshot, encoding="utf-8"))
    levels = [float(x) for x in a.levels.split(",") if x.strip()]
    sides = ["CE", "PE"] if a.side == "both" else [a.side]
    res = build(snap, levels, sides, a.strikes)
    if a.json:
        print(json.dumps(res, indent=1))
    else:
        print_table(res)


if __name__ == "__main__":
    main()
