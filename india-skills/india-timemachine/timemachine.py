#!/usr/bin/env python3
"""
Time Machine for Indian indices: before you act on a bias, check how often the
index actually reached one level before another from the same time of day.

Two independent checks on the index's own 5-minute history
(market-data branch, history/<INDEX>_5m.json, ~70 sessions):

  1. History replay - every past session, from the same clock time, with the
     two levels placed at the same % distance from that day's price: which was
     touched first by the end time (up first / down first / both in one bar /
     neither).
  2. Bootstrap simulation - N simulated rest-of-day paths, each 5-minute bar
     drawn at random from that same time slot on past sessions (its open-to-
     high, open-to-low and open-to-close moves, chained from the current
     price). Seeded, so a run can be repeated exactly.

Usage:
  python3 timemachine.py --history history/NIFTY_5m.json --spot 22600 \
      --up 22700 --down 22500 --at 10:45 [--until 15:25] [--sims 10000] [--seed 7] [--json]

--at defaults to the current IST time (rounded down to a 5-minute bar).
This describes how the index has behaved; it does not predict the next move.
Events that are not in the sample (results, RBI, a gap on global news) are
not reflected in it.
"""
import argparse
import datetime as dt
import json
import random
import statistics

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def hhmm(ts):
    return ts[11:16]


def load_sessions(path):
    d = json.load(open(path, encoding="utf-8"))
    sessions = {}
    for c in d.get("candles", []):
        sessions.setdefault(c["t"][:10], []).append(c)
    for v in sessions.values():
        v.sort(key=lambda c: c["t"])
    return d, sessions


def bar_slots(bars, at, until):
    """Bars whose start time is >= at and < until."""
    return [b for b in bars if at <= hhmm(b["t"]) < until]


def price_at(bars, at):
    """Close of the last bar that ended at or before `at` (bar start < at)."""
    before = [b for b in bars if hhmm(b["t"]) < at]
    return before[-1]["c"] if before else None


def race(bars, start, up, down):
    """Return ('up'|'down'|'both'|'neither', minutes from start bar index)."""
    for i, b in enumerate(bars):
        hit_up, hit_dn = b["h"] >= up, b["l"] <= down
        if hit_up and hit_dn:
            return "both", (i + 1) * 5
        if hit_up:
            return "up", (i + 1) * 5
        if hit_dn:
            return "down", (i + 1) * 5
    return "neither", None


def replay(sessions, at, until, up_pct, dn_pct, skip_day=None):
    res = {"up": 0, "down": 0, "both": 0, "neither": 0, "minutes": {"up": [], "down": []}, "days": []}
    for day in sorted(sessions):
        if day == skip_day:
            continue
        bars = sessions[day]
        p0 = price_at(bars, at)
        rest = bar_slots(bars, at, until)
        if not p0 or not rest:
            continue
        outcome, mins = race(rest, p0, p0 * (1 + up_pct), p0 * (1 - dn_pct))
        res[outcome] += 1
        if mins and outcome in ("up", "down"):
            res["minutes"][outcome].append(mins)
        res["days"].append({"day": day, "outcome": outcome})
    res["sessions"] = res["up"] + res["down"] + res["both"] + res["neither"]
    return res


def slot_moves(sessions, at, until, skip_day=None, keep_drift=False):
    """slot 'HH:MM' -> list of (high_pct, low_pct, close_pct) relative to bar open.

    By default each slot's average open-to-close move is removed (and the high
    and low shifted with it), so the simulation measures how far the index
    tends to swing at that time of day, not the direction it happened to trend
    in over the sample. The history replay keeps the real trend."""
    slots = {}
    for day, bars in sessions.items():
        if day == skip_day:
            continue
        for b in bar_slots(bars, at, until):
            if b["o"]:
                slots.setdefault(hhmm(b["t"]), []).append(
                    (b["h"] / b["o"] - 1, b["l"] / b["o"] - 1, b["c"] / b["o"] - 1))
    if not keep_drift:
        for k, moves in slots.items():
            m = sum(c for _, _, c in moves) / len(moves)
            slots[k] = [(h - m, l - m, c - m) for h, l, c in moves]
    return slots


def simulate(slots, spot, up, down, sims, seed):
    rng = random.Random(seed)
    order = sorted(slots)
    res = {"up": 0, "down": 0, "both": 0, "neither": 0, "minutes": {"up": [], "down": []}}
    closes = []
    for _ in range(sims):
        p, outcome, mins = spot, "neither", None
        for i, s in enumerate(order):
            hp, lp, cp = rng.choice(slots[s])
            hi, lo = p * (1 + hp), p * (1 + lp)
            hit_up, hit_dn = hi >= up, lo <= down
            if hit_up or hit_dn:
                outcome = "both" if hit_up and hit_dn else ("up" if hit_up else "down")
                mins = (i + 1) * 5
                break
            p *= 1 + cp
        res[outcome] += 1
        if outcome in ("up", "down"):
            res["minutes"][outcome].append(mins)
        closes.append(p)
    res["sims"] = sims
    res["seed"] = seed
    return res


def pct(n, d):
    return round(100 * n / d, 1) if d else None


def summary(r, total_key):
    total = r[total_key]
    return {k: {"count": r[k], "pct": pct(r[k], total)} for k in ("up", "down", "both", "neither")} | {
        "median_minutes_up": statistics.median(r["minutes"]["up"]) if r["minutes"]["up"] else None,
        "median_minutes_down": statistics.median(r["minutes"]["down"]) if r["minutes"]["down"] else None,
        total_key: total}


def verdict(h, s):
    """Plain-language read from the two checks."""
    def edge(x):
        u, d = x["up"]["pct"] or 0, x["down"]["pct"] or 0
        return u - d
    eh, es = edge(h), edge(s)
    if abs(eh) < 10 and abs(es) < 10:
        return "close to a coin flip: neither level is reached first clearly more often"
    side_h = "up" if eh > 0 else "down"
    side_s = "up" if es > 0 else "down"
    if side_h != side_s and abs(eh) >= 10 and abs(es) >= 10:
        return "the two checks disagree: treat as no edge"
    side = side_h if abs(eh) >= abs(es) else side_s
    src = "history replay" if abs(eh) >= abs(es) else "simulation"
    return (f"the {side} level is reached first more often "
            f"({src}: {max(abs(eh), abs(es)):.0f} percentage points more often than the other level)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--history", required=True)
    ap.add_argument("--spot", type=float, required=True)
    ap.add_argument("--up", type=float, required=True, help="Upper level (index points)")
    ap.add_argument("--down", type=float, required=True, help="Lower level (index points)")
    ap.add_argument("--at", default=None, help="Start time HH:MM IST (default: now, 5-min floor)")
    ap.add_argument("--until", default="15:25", help="Stop at this bar start time (default 15:25)")
    ap.add_argument("--sims", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--keep-drift", action="store_true",
                    help="Keep each slot's average move in the simulation (default: removed)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not (a.down < a.spot < a.up):
        raise SystemExit("Need --down < --spot < --up")
    if a.at is None:
        n = dt.datetime.now(IST)
        a.at = f"{n.hour:02d}:{(n.minute // 5) * 5:02d}"
    if a.at < "09:15":
        a.at = "09:15"

    meta, sessions = load_sessions(a.history)
    today = dt.datetime.now(IST).date().isoformat()
    up_pct, dn_pct = a.up / a.spot - 1, 1 - a.down / a.spot
    h = replay(sessions, a.at, a.until, up_pct, dn_pct, skip_day=today)
    slots = slot_moves(sessions, a.at, a.until, skip_day=today, keep_drift=a.keep_drift)
    if not slots:
        raise SystemExit(f"No history bars between {a.at} and {a.until}")
    s = simulate(slots, a.spot, a.up, a.down, a.sims, a.seed)
    hs, ss = summary(h, "sessions"), summary(s, "sims")
    out = {
        "index": meta.get("index"), "history_file_fetched_at": meta.get("fetched_at"),
        "history_range": f"{meta.get('first_day')} to {meta.get('last_day')}",
        "spot": a.spot, "up": a.up, "down": a.down,
        "up_distance_pct": round(100 * up_pct, 2), "down_distance_pct": round(100 * dn_pct, 2),
        "from": a.at, "until": a.until, "simulation_drift": "kept" if a.keep_drift else "removed",
        "history": hs, "simulation": ss, "verdict": verdict(hs, ss),
    }
    if a.json:
        print(json.dumps(out, indent=1))
        return
    print(f"{out['index']} Time Machine · from {a.at} to {a.until} IST · history {out['history_range']}")
    print(f"Spot {a.spot:g} · up {a.up:g} (+{out['up_distance_pct']}%) · down {a.down:g} (−{out['down_distance_pct']}%)")
    print("| Check | Up first | Down first | Both in one bar | Neither by end |")
    print("|---|---|---|---|---|")
    for label, r, n in (("History replay", hs, f"{hs['sessions']} sessions"), ("Simulation", ss, f"{ss['sims']:,} paths, seed {a.seed}, drift {'kept' if a.keep_drift else 'removed'}")):
        print(f"| {label} ({n}) | {r['up']['pct']}% ({r['up']['count']}) | {r['down']['pct']}% ({r['down']['count']}) | "
              f"{r['both']['pct']}% | {r['neither']['pct']}% |")
    mu, md = hs["median_minutes_up"], hs["median_minutes_down"]
    print(f"Median time to touch in history: up {mu if mu is not None else '—'} min, down {md if md is not None else '—'} min")
    print(f"Read: {out['verdict']}")
    print("Based on the index's own recent 5-minute bars; it does not know about scheduled events.")


if __name__ == "__main__":
    main()
