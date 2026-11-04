#!/usr/bin/env python3
"""
Score logged briefs: after each brief's time, did the index touch the bias's
confirmation level or its invalidation level first, by the 15:25 bar?

Input:  a folder of brief documents saved by ArtifactData (`out_dir`), or a
        JSON file holding a list of them. Each brief has: date (YYYY-MM-DD),
        time (HH:MM IST), index, bias (CE | PE | NONE), confirm, invalidate,
        outcome (pending | confirm | invalidate | neither).
History: market-data branch history/<INDEX>_5m.json.

Usage:
  python3 score.py --briefs saved/briefs --history md/history [--json]

Prints the updates for pending CE/PE briefs whose day is in the history file.
Both levels inside one 5-minute bar is scored "invalidate" (conservative:
the order inside the bar is unknown). NONE briefs are never scored.
"""
import argparse
import glob
import json
import os


def load_briefs(path):
    if os.path.isdir(path):
        out = []
        for f in sorted(glob.glob(os.path.join(path, "**", "*.json"), recursive=True)):
            d = json.load(open(f, encoding="utf-8"))
            doc = d.get("data", d) if isinstance(d, dict) else d
            doc_id = d.get("doc_id") or d.get("id") or os.path.splitext(os.path.basename(f))[0]
            ver = d.get("version")
            out.append(dict(doc, _id=doc_id, _version=ver))
        return out
    data = json.load(open(path, encoding="utf-8"))
    return [dict(x.get("data", x), _id=x.get("doc_id") or x.get("id"), _version=x.get("version")) for x in data]


def bars_for(history_dir, index, day, cache={}):
    if index not in cache:
        p = os.path.join(history_dir, f"{index}_5m.json")
        cache[index] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"candles": []}
    return [c for c in cache[index]["candles"] if c["t"][:10] == day]


def floor5(hhmm):
    h, m = int(hhmm[:2]), int(hhmm[3:5])
    t = max(h * 60 + m, 9 * 60 + 15)
    t = 9 * 60 + 15 + ((t - (9 * 60 + 15)) // 5) * 5
    return f"{t // 60:02d}:{t % 60:02d}"


def score(b, history_dir):
    bias = b.get("bias")
    if bias not in ("CE", "PE") or b.get("outcome") not in (None, "", "pending"):
        return None
    try:
        conf, inv = float(b["confirm"]), float(b["invalidate"])
    except (KeyError, TypeError, ValueError):
        return None
    bars = bars_for(history_dir, b["index"], b["date"])
    if not bars:
        return None
    start = floor5(b.get("time", "09:15"))
    # the brief's own bar may already be part-way; start at the next full bar
    rest = [c for c in bars if c["t"][11:16] >= start and c["t"][11:16] <= "15:25"]
    if b.get("time", "09:15") > "09:15":
        rest = [c for c in rest if c["t"][11:16] > b["time"][:5]] or rest
    up_level, down_level = (conf, inv) if bias == "CE" else (inv, conf)
    for c in rest:
        hu, hd = c["h"] >= up_level, c["l"] <= down_level
        if hu or hd:
            if hu and hd:
                return {"outcome": "invalidate", "outcome_at": c["t"][11:16], "scored_by": "auto",
                        "score_note": "both levels inside one 5-min bar; scored conservatively"}
            hit_up = hu
            confirm_first = (hit_up and bias == "CE") or (not hit_up and bias == "PE")
            return {"outcome": "confirm" if confirm_first else "invalidate",
                    "outcome_at": c["t"][11:16], "scored_by": "auto"}
    if rest and rest[-1]["t"][11:16] >= "15:25":
        return {"outcome": "neither", "outcome_at": "15:30", "scored_by": "auto"}
    return None  # session not complete in the history file yet


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--briefs", required=True)
    ap.add_argument("--history", required=True, help="Folder with <INDEX>_5m.json files")
    ap.add_argument("--json", action="store_true", help="Print an ArtifactData batch 'writes' list")
    a = ap.parse_args()
    updates = []
    for b in load_briefs(a.briefs):
        u = score(b, a.history)
        if u:
            updates.append({"op": "update", "collection": "briefs", "doc_id": b["_id"],
                            "if_version": b["_version"], "data": u})
    if a.json:
        print(json.dumps([{k: v for k, v in x.items() if v is not None} for x in updates], indent=1))
        return
    if not updates:
        print("Nothing to score.")
    for x in updates:
        print(f"{x['doc_id']}: {x['data']['outcome']} at {x['data']['outcome_at']}")


if __name__ == "__main__":
    main()
