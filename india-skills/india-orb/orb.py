#!/usr/bin/env python3
"""
Opening-range read for an Indian index from today's 1-minute candles
(market-data branch, latest/candles_<INDEX>.json).

The opening range is the high and low of the first N minutes (default 15:
09:15-09:30). A breakout is the first 5-minute close beyond the range.
Reports: range, current price vs range, breakout time and direction, whether
it has held, the furthest move beyond the range, and any failed breakout.

Usage:
  python3 orb.py --candles latest/candles_NIFTY.json [--minutes 15] [--json]

This describes what the index has done today; it is not a signal to trade.
"""
import argparse
import json


def hhmm(t):
    return t[11:16]


def resample5(c1):
    """1-minute candles -> 5-minute bars aligned to :15, :20, ..."""
    bars = {}
    for c in c1:
        h, m = int(c["t"][11:13]), int(c["t"][14:16])
        mins = h * 60 + m - (9 * 60 + 15)
        if mins < 0:
            continue
        slot = 9 * 60 + 15 + (mins // 5) * 5
        key = f"{slot // 60:02d}:{slot % 60:02d}"
        b = bars.get(key)
        if not b:
            bars[key] = {"t": key, "o": c["o"], "h": c["h"], "l": c["l"], "c": c["c"], "n": 1}
        else:
            b["h"], b["l"], b["c"], b["n"] = max(b["h"], c["h"]), min(b["l"], c["l"]), c["c"], b["n"] + 1
    return [bars[k] for k in sorted(bars)]


def analyse(c1, minutes=15):
    if not c1:
        return {"status": "no candles yet"}
    day = c1[-1]["t"][:10]
    c1 = [c for c in c1 if c["t"][:10] == day]
    end = 9 * 60 + 15 + minutes
    end_s = f"{end // 60:02d}:{end % 60:02d}"
    rng = [c for c in c1 if hhmm(c["t"]) < end_s]
    out = {"date": day, "range_window": f"09:15-{end_s}", "last_time": hhmm(c1[-1]["t"]), "last": c1[-1]["c"]}
    if hhmm(c1[-1]["t"]) < end_s or len(rng) < max(1, minutes - 2):
        out["status"] = "opening range still forming"
        return out
    hi, lo = max(c["h"] for c in rng), min(c["l"] for c in rng)
    out.update({"or_high": hi, "or_low": lo, "or_width": round(hi - lo, 2),
                "or_width_pct": round(100 * (hi - lo) / lo, 2)})
    bars = [b for b in resample5(c1) if b["t"] >= end_s and b["n"] >= 5]  # completed 5-min bars only
    side = when = None
    failed = []
    for b in bars:
        if side is None:
            if b["c"] > hi:
                side, when = "above", b["t"]
            elif b["c"] < lo:
                side, when = "below", b["t"]
        else:
            back_inside = lo <= b["c"] <= hi
            flipped = (side == "above" and b["c"] < lo) or (side == "below" and b["c"] > hi)
            if back_inside or flipped:
                failed.append({"side": side, "at": when, "back_inside": b["t"]})
                side, when = ("below", b["t"]) if flipped and b["c"] < lo else (("above", b["t"]) if flipped else (None, None))
    last = c1[-1]["c"]
    after = [c for c in c1 if hhmm(c["t"]) >= end_s]
    out["day_high"], out["day_low"] = max(c["h"] for c in c1), min(c["l"] for c in c1)
    out["position"] = "above range" if last > hi else ("below range" if last < lo else "inside range")
    if side:
        ext = (max(c["h"] for c in after) - hi) if side == "above" else (lo - min(c["l"] for c in after))
        out.update({"breakout": side, "breakout_at": when, "max_extension": round(ext, 2),
                    "held": out["position"] == f"{side} range"})
        out["status"] = (f"broke {side} the opening range at {when} (5-min close) and "
                         f"{'is holding' if out['held'] else 'has slipped back'}; furthest {ext:.0f} pts beyond")
    else:
        out["status"] = ("no 5-minute close beyond the opening range yet"
                         if not failed else "breakout attempt failed; back inside the range")
    out["failed_breakouts"] = failed
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candles", required=True)
    ap.add_argument("--minutes", type=int, default=15)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    d = json.load(open(a.candles, encoding="utf-8"))
    r = analyse(d.get("candles", []), a.minutes)
    r["index"], r["fetched_at"] = d.get("index"), d.get("fetched_at")
    if a.json:
        print(json.dumps(r, indent=1))
        return
    print(f"{r['index']} opening range ({r.get('range_window', '')}) · data {r['fetched_at']}")
    if "or_high" in r:
        print(f"Range {r['or_low']:g}–{r['or_high']:g} ({r['or_width']:g} pts, {r['or_width_pct']}%) · "
              f"last {r['last']:g} at {r['last_time']} ({r['position']}) · day {r['day_low']:g}–{r['day_high']:g}")
    print(f"Read: {r['status']}")
    for f in r.get("failed_breakouts", []):
        print(f"  failed: broke {f['side']} at {f['at']}, back at {f['back_inside']}")


if __name__ == "__main__":
    main()
