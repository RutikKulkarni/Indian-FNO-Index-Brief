#!/usr/bin/env python3
"""
Trade calculator and Risk Manager for a trade YOU have chosen on an Indian
index option. It does arithmetic and checks your own limits; it does not pick
trades.

  calc   Lots that fit your max loss, rupee risk and reward with charges,
         reward:risk, breakeven premium, capital, theta per day, and roughly
         which index level would take the premium to your stop and target now
         (delta-gamma estimate from the live option chain).
  check  calc, then PASS / BLOCK against india-skills/config/risk_limits.json
         plus today's loss and trade count that you pass in.

Usage:
  python3 trade.py calc  --root md --index NIFTY --strike 23800 --side CE --entry 120 \
      --stop 90 [--target 170] [--max-loss 3000 | --lots 1]
  python3 trade.py check --root md --index NIFTY --strike 23800 --side CE --entry 120 \
      --stop 90 --target 170 --lots 1 --today-loss 0 --today-trades 0 [--now 10:50]

Nothing is stored: today's loss and trade count come from you each time.
Charges come from india-skills/config/charges.json; check your contract note.
"""
import argparse
import datetime as dt
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(os.path.dirname(HERE), "config")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def charges(buy_turnover, sell_turnover, c):
    brk = 2 * c["brokerage_per_order"]
    txn = (buy_turnover + sell_turnover) * c["exchange_txn_pct"] / 100
    sebi = (buy_turnover + sell_turnover) * c["sebi_pct"] / 100
    stt = sell_turnover * c["stt_sell_pct"] / 100
    stamp = buy_turnover * c["stamp_buy_pct"] / 100
    gst = (brk + txn + sebi) * c["gst_pct"] / 100
    return round(brk + txn + sebi + stt + stamp + gst, 2)


def index_move_for(dp, delta, gamma):
    """Index change dS so that delta*dS + 0.5*gamma*dS^2 = dp (nearest root)."""
    if delta is None or delta == 0:
        return None
    g = gamma or 0.0
    if abs(g) < 1e-12:
        return dp / delta
    disc = delta * delta + 2 * g * dp
    if disc < 0:
        return None
    r1, r2 = (-delta + math.sqrt(disc)) / g, (-delta - math.sqrt(disc)) / g
    return min((r1, r2), key=abs)


def calc(a):
    snap = load(os.path.join(a.root, f"latest/{a.index}.json"))
    if not snap:
        raise SystemExit(f"latest/{a.index}.json not found under {a.root}")
    lot = int(a.lot_size or snap.get("lot_size") or 0)
    if not lot:
        raise SystemExit("lot size unknown; pass --lot-size")
    side = a.side.upper()
    if a.stop >= a.entry:
        raise SystemExit("For a bought option the stop premium must be below the entry premium")
    if a.target is not None and a.target <= a.entry:
        raise SystemExit("Target premium must be above the entry premium")
    c = load(os.path.join(CFG, "charges.json"))
    row = next((r for r in snap.get("rows", []) if r["strike"] == a.strike), None)
    k = side.lower()
    delta = num(row.get(f"{k}_delta")) if row else None
    gamma = num(row.get(f"{k}_gamma")) if row else None
    theta = num(row.get(f"{k}_theta")) if row else None
    ltp = num(row.get(f"{k}_ltp")) if row else None

    def risk_for(lots):
        q = lots * lot
        gross = (a.entry - a.stop) * q
        return round(gross + charges(a.entry * q, a.stop * q, c), 2)

    per_lot_risk = risk_for(1)
    if a.lots:
        lots = a.lots
    elif a.max_loss:
        lots = 0
        while risk_for(lots + 1) <= a.max_loss:
            lots += 1
    else:
        lots = 1
    q = max(lots, 1) * lot
    out = {
        "index": a.index, "expiry": snap.get("expiry"), "option": f"{int(a.strike)} {side}",
        "data_at": snap.get("fetched_at"), "spot": snap.get("spot"), "live_ltp": ltp,
        "lot_size": lot, "entry": a.entry, "stop": a.stop, "target": a.target,
        "lots": lots, "quantity": lots * lot,
        "lots_that_fit_max_loss": (None if not a.max_loss else lots if not a.lots else None),
        "risk_per_lot": per_lot_risk, "risk_total": risk_for(lots) if lots else 0,
        "capital": round(a.entry * lots * lot, 2),
        "charges_at_stop": charges(a.entry * q, a.stop * q, c),
    }
    if a.target is not None:
        reward = round((a.target - a.entry) * q - charges(a.entry * q, a.target * q, c), 2)
        out["reward_total"] = reward if lots else 0
        out["reward_risk"] = round(reward / risk_for(max(lots, 1)), 2)
        out["charges_at_target"] = charges(a.entry * q, a.target * q, c)
    be_ch = charges(a.entry * q, a.entry * q, c)
    out["breakeven_premium"] = round(a.entry + be_ch / q, 2)
    out["theta_per_day_total"] = round(theta * lots * lot, 0) if theta is not None and lots else None
    spot = num(snap.get("spot"))
    if spot and delta is not None:
        base = ltp if ltp else a.entry
        mv_stop = index_move_for(a.stop - base, delta, gamma)
        out["index_at_stop_est"] = round(spot + mv_stop) if mv_stop is not None else None
        if a.target is not None:
            mv_t = index_move_for(a.target - base, delta, gamma)
            out["index_at_target_est"] = round(spot + mv_t) if mv_t is not None else None
    if a.max_loss and not a.lots and lots == 0:
        out["note"] = "Even 1 lot risks more than your max loss at this stop."
    return out


def check(a):
    r = calc(a)
    lim = load(os.path.join(CFG, "risk_limits.json"), {})
    now = a.now or dt.datetime.now(IST).strftime("%H:%M")
    today = dt.datetime.now(IST).date().isoformat()
    expiry_today = r.get("expiry") == today
    results = []

    def rule(name, value, ok, detail):
        if value is None:
            results.append((name, "not set", "—"))
        else:
            results.append((name, "PASS" if ok else "BLOCK", detail))

    v = lim.get("max_loss_per_trade")
    rule("Max loss per trade", v, v is None or r["risk_total"] <= v, f"₹{r['risk_total']:,.0f} vs ₹{v:,}" if v else "")
    v = lim.get("daily_loss_limit")
    left = None if v is None else v - a.today_loss
    rule("Daily loss limit", v, v is None or r["risk_total"] <= left,
         f"today lost ₹{a.today_loss:,.0f}; ₹{left:,.0f} left; this risks ₹{r['risk_total']:,.0f}" if v else "")
    v = lim.get("max_trades_per_day")
    rule("Trades per day", v, v is None or a.today_trades < v, f"{a.today_trades} done, limit {v}" if v else "")
    v = lim.get("min_reward_risk")
    rr = r.get("reward_risk")
    rule("Reward : risk", v, v is None or (rr is not None and rr >= v),
         (f"{rr} vs min {v}" if rr is not None else "no target given") if v else "")
    v = lim.get("max_lots")
    rule("Max lots", v, v is None or r["lots"] <= v, f"{r['lots']} vs {v}" if v else "")
    v = lim.get("max_capital_per_trade")
    rule("Max capital", v, v is None or r["capital"] <= v, f"₹{r['capital']:,.0f} vs ₹{v:,}" if v else "")
    v = lim.get("no_entry_before")
    rule("Not before", v, v is None or now >= v, f"now {now}, earliest {v}" if v else "")
    v = lim.get("no_entry_after")
    rule("Not after", v, v is None or now <= v, f"now {now}, latest {v}" if v else "")
    v = lim.get("expiry_day_no_entry_after") if expiry_today else None
    if expiry_today:
        rule("Expiry-day cut-off", v, v is None or now <= v, f"expiry today; now {now}, latest {v}" if v else "")
    if r["lots"] == 0:
        results.append(("Size", "BLOCK", r.get("note", "0 lots")))
    verdict = "BLOCK" if any(s == "BLOCK" for _, s, _ in results) else "PASS"
    unset = sum(1 for _, s, _ in results if s == "not set")
    return r, results, verdict, unset


def print_calc(r):
    print(f"{r['index']} {r['option']} · expiry {r['expiry']} · lot {r['lot_size']} · data {r['data_at']}")
    print(f"Spot {r['spot']} · live premium {r['live_ltp']} · your entry {r['entry']} / stop {r['stop']}"
          + (f" / target {r['target']}" if r['target'] is not None else ""))
    print("| | |")
    print("|---|---|")
    print(f"| Lots / quantity | {r['lots']} / {r['quantity']} |")
    print(f"| Risk per lot at stop (incl. charges) | ₹{r['risk_per_lot']:,.0f} |")
    print(f"| Risk total at stop | ₹{r['risk_total']:,.0f} |")
    if "reward_total" in r:
        print(f"| Reward total at target (after charges) | ₹{r['reward_total']:,.0f} |")
        print(f"| Reward : risk | {r['reward_risk']} |")
    print(f"| Capital (premium paid) | ₹{r['capital']:,.0f} |")
    print(f"| Breakeven premium (after charges) | {r['breakeven_premium']} |")
    if r.get("theta_per_day_total") is not None:
        print(f"| Time decay per day (theta, total) | ₹{r['theta_per_day_total']:,.0f} |")
    if r.get("index_at_stop_est") is not None:
        print(f"| Index level ≈ at your stop premium, if it moved now | {r['index_at_stop_est']:,} |")
    if r.get("index_at_target_est") is not None:
        print(f"| Index level ≈ at your target premium, if it moved now | {r['index_at_target_est']:,} |")
    if r.get("note"):
        print(f"\nNote: {r['note']}")
    print("\nIndex-level estimates use delta and gamma from the chain and ignore time decay and IV "
          "changes. A stop can fill worse than its price in a fast market.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["calc", "check"])
    ap.add_argument("--root", required=True, help="Checkout of the market-data branch")
    ap.add_argument("--index", required=True, choices=["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50", "SENSEX", "BANKEX"])
    ap.add_argument("--strike", type=float, required=True)
    ap.add_argument("--side", required=True, choices=["CE", "PE", "ce", "pe"])
    ap.add_argument("--entry", type=float, required=True, help="Your entry premium")
    ap.add_argument("--stop", type=float, required=True, help="Your stop premium")
    ap.add_argument("--target", type=float, help="Your target premium")
    ap.add_argument("--max-loss", type=float, help="Size to this rupee loss at the stop")
    ap.add_argument("--lots", type=int, help="Use this many lots instead of sizing")
    ap.add_argument("--lot-size", type=int, help="Override the lot size")
    ap.add_argument("--today-loss", type=float, default=0, help="Realised loss so far today (₹, positive number)")
    ap.add_argument("--today-trades", type=int, default=0)
    ap.add_argument("--now", help="HH:MM IST (default: now)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    a.side = a.side.upper()
    if a.cmd == "calc":
        r = calc(a)
        print(json.dumps(r, indent=1)) if a.json else print_calc(r)
        return
    r, results, verdict, unset = check(a)
    if a.json:
        print(json.dumps({"calc": r, "rules": results, "verdict": verdict}, indent=1))
        return
    print_calc(r)
    print(f"\nRisk check against your limits: **{verdict}**")
    print("| Rule | Result | Detail |")
    print("|---|---|---|")
    for name, s, d in results:
        print(f"| {name} | {s} | {d} |")
    if unset:
        print(f"\n{unset} rule(s) not set. Set your own limits in india-skills/config/risk_limits.json.")


if __name__ == "__main__":
    main()
