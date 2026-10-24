#!/usr/bin/env python3
"""
Compute option-chain metrics for one index expiry.

Input: a JSON file containing a list of strike rows (or {"rows": [...]}):

    [
      {"strike": 25000, "ce_oi": 120000, "pe_oi": 310000,
       "ce_chg_oi": 5000, "pe_chg_oi": 42000, "ce_iv": 11.2, "pe_iv": 12.8},
      ...
    ]

Only "strike", "ce_oi" and "pe_oi" are required. Change in OI and IV are optional.

Usage:
    python3 option_chain_metrics.py chain.json --spot 25150 --step 50 [--json]

Output: PCR (OI and change-in-OI), max pain, ATM strike, top-3 CE/PE OI strikes,
the strongest and nearest-significant OI support/resistance, and ATM IV when available.
"""
import argparse
import json
import sys


def load_rows(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("rows", data) if isinstance(data, dict) else data
    clean = []
    for r in rows:
        if "strike" not in r:
            continue
        clean.append({
            "strike": float(r["strike"]),
            "ce_oi": float(r.get("ce_oi") or 0),
            "pe_oi": float(r.get("pe_oi") or 0),
            "ce_chg_oi": float(r.get("ce_chg_oi") or 0),
            "pe_chg_oi": float(r.get("pe_chg_oi") or 0),
            "ce_iv": r.get("ce_iv"),
            "pe_iv": r.get("pe_iv"),
        })
    if not clean:
        sys.exit("No valid rows (need at least 'strike', 'ce_oi', 'pe_oi').")
    return sorted(clean, key=lambda r: r["strike"])


def max_pain(rows):
    """Strike at which total payout to option buyers (= writers' loss) is lowest."""
    best_strike, best_loss = None, None
    for candidate in rows:
        k = candidate["strike"]
        loss = 0.0
        for r in rows:
            loss += max(0.0, k - r["strike"]) * r["ce_oi"]   # calls ITM if expiry > strike
            loss += max(0.0, r["strike"] - k) * r["pe_oi"]   # puts ITM if expiry < strike
        if best_loss is None or loss < best_loss:
            best_strike, best_loss = k, loss
    return best_strike


def safe_ratio(num, den):
    return round(num / den, 3) if den else None


def compute(rows, spot, step):
    total_ce = sum(r["ce_oi"] for r in rows)
    total_pe = sum(r["pe_oi"] for r in rows)
    chg_ce = sum(r["ce_chg_oi"] for r in rows)
    chg_pe = sum(r["pe_chg_oi"] for r in rows)

    atm = round(spot / step) * step
    top_ce = sorted(rows, key=lambda r: r["ce_oi"], reverse=True)[:3]
    top_pe = sorted(rows, key=lambda r: r["pe_oi"], reverse=True)[:3]

    above = [r for r in rows if r["strike"] >= spot]
    below = [r for r in rows if r["strike"] <= spot]
    resistance = max(above, key=lambda r: r["ce_oi"])["strike"] if above else None
    support = max(below, key=lambda r: r["pe_oi"])["strike"] if below else None

    # Nearest "significant" wall: closest strike to spot whose OI is at least
    # half of the biggest OI on that side.
    def nearest_significant(side, key, reverse):
        if not side:
            return None
        cutoff = 0.5 * max(r[key] for r in side)
        ordered = sorted(side, key=lambda r: r["strike"], reverse=reverse)
        return next(r["strike"] for r in ordered if r[key] >= cutoff)

    near_res = nearest_significant(above, "ce_oi", reverse=False)
    near_sup = nearest_significant(below, "pe_oi", reverse=True)

    atm_row = min(rows, key=lambda r: abs(r["strike"] - atm))
    ivs = [v for v in (atm_row["ce_iv"], atm_row["pe_iv"]) if v not in (None, "")]
    atm_iv = round(sum(float(v) for v in ivs) / len(ivs), 2) if ivs else None

    return {
        "spot": spot,
        "atm_strike": atm,
        "total_ce_oi": total_ce,
        "total_pe_oi": total_pe,
        "pcr_oi": safe_ratio(total_pe, total_ce),
        "pcr_chg_oi": safe_ratio(chg_pe, chg_ce) if chg_ce > 0 else None,
        "chg_ce_oi": chg_ce,
        "chg_pe_oi": chg_pe,
        "max_pain": max_pain(rows),
        "top_ce_oi": [(r["strike"], r["ce_oi"]) for r in top_ce],
        "top_pe_oi": [(r["strike"], r["pe_oi"]) for r in top_pe],
        "strongest_resistance_above_spot": resistance,
        "strongest_support_below_spot": support,
        "nearest_significant_resistance": near_res,
        "nearest_significant_support": near_sup,
        "atm_iv": atm_iv,
    }


def fmt_num(n):
    return "n/a" if n is None else f"{n:,.0f}" if abs(n) >= 100 else f"{n}"


def print_human(m):
    print(f"Spot {fmt_num(m['spot'])}  |  ATM {fmt_num(m['atm_strike'])}  |  Max pain {fmt_num(m['max_pain'])}")
    print(f"PCR (OI): {m['pcr_oi']}   PCR (ΔOI): {m['pcr_chg_oi'] if m['pcr_chg_oi'] is not None else 'n/a'}")
    print(f"Total CE OI {fmt_num(m['total_ce_oi'])}  |  Total PE OI {fmt_num(m['total_pe_oi'])}")
    print(f"ΔOI  CE {fmt_num(m['chg_ce_oi'])}  |  PE {fmt_num(m['chg_pe_oi'])}")
    print("Top CE OI (resistance): " + ", ".join(f"{fmt_num(s)} ({fmt_num(o)})" for s, o in m["top_ce_oi"]))
    print("Top PE OI (support):    " + ", ".join(f"{fmt_num(s)} ({fmt_num(o)})" for s, o in m["top_pe_oi"]))
    print(f"Nearest significant resistance: {fmt_num(m['nearest_significant_resistance'])}   strongest above spot: {fmt_num(m['strongest_resistance_above_spot'])}")
    print(f"Nearest significant support:    {fmt_num(m['nearest_significant_support'])}   strongest below spot: {fmt_num(m['strongest_support_below_spot'])}")
    print(f"ATM IV: {m['atm_iv'] if m['atm_iv'] is not None else 'n/a'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("chain", help="Path to option-chain JSON")
    ap.add_argument("--spot", type=float, required=True, help="Current spot price of the index")
    ap.add_argument("--step", type=float, required=True, help="Strike interval (e.g. 50 for NIFTY, 100 for BANKNIFTY)")
    ap.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = ap.parse_args()

    metrics = compute(load_rows(args.chain), args.spot, args.step)
    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print_human(metrics)


if __name__ == "__main__":
    main()
