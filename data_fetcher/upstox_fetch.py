#!/usr/bin/env python3
"""
Fetch index F&O snapshots from the Upstox API and write one normalized JSON
file per index (plus a market-context file) into an output directory.

Auth: a read-only Upstox Analytics Token in the env var UPSTOX_ANALYTICS_TOKEN.
No third-party packages: standard library only.

Usage:
    UPSTOX_ANALYTICS_TOKEN=... python3 upstox_fetch.py --out data/latest [--raw data/raw]

Output (data/latest/<KEY>.json) is compatible with
fno-index-brief/scripts/option_chain_metrics.py (the "rows" list).
"""
import argparse
import datetime as dt
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.upstox.com"
INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/{exch}.json.gz"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
USER_AGENT = "Indian-FNO-Index-Brief/1.0 (+https://github.com/RutikKulkarni/Indian-FNO-Index-Brief)"

# Candidate Upstox instrument keys per index. The first one that returns a
# price is used; if none do, the instruments master file is searched by name.
INDICES = {
    "NIFTY":      {"exch": "NSE", "step": 50,  "keys": ["NSE_INDEX|Nifty 50"],          "names": ["nifty 50"]},
    "BANKNIFTY":  {"exch": "NSE", "step": 100, "keys": ["NSE_INDEX|Nifty Bank"],        "names": ["nifty bank"]},
    "FINNIFTY":   {"exch": "NSE", "step": 50,  "keys": ["NSE_INDEX|Nifty Fin Service"], "names": ["nifty fin service", "nifty financial services"]},
    "MIDCPNIFTY": {"exch": "NSE", "step": 25,  "keys": ["NSE_INDEX|NIFTY MID SELECT"],  "names": ["nifty mid select", "nifty midcap select"]},
    "NIFTYNXT50": {"exch": "NSE", "step": 100, "keys": ["NSE_INDEX|Nifty Next 50"],     "names": ["nifty next 50"]},
    "SENSEX":     {"exch": "BSE", "step": 100, "keys": ["BSE_INDEX|SENSEX"],            "names": ["sensex", "s&p bse sensex", "bse sensex"]},
    "BANKEX":     {"exch": "BSE", "step": 100, "keys": ["BSE_INDEX|BANKEX"],            "names": ["bankex", "s&p bse bankex", "bse bankex"]},
}
VIX_KEY = "NSE_INDEX|India VIX"


# ---------------------------------------------------------------- HTTP helpers
def api_get(path, params, token, retries=3):
    url = f"{API}{path}?{urllib.parse.urlencode(params, safe='|,')}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
    })
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} on {path}: {body}") from None
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise RuntimeError(f"Network error on {path}: {e}") from None


_instrument_cache = {}


def instruments(exch):
    """Upstox instruments master for an exchange (public file, no auth)."""
    if exch not in _instrument_cache:
        req = urllib.request.Request(INSTRUMENTS_URL.format(exch=exch), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as r:
            _instrument_cache[exch] = json.loads(gzip.decompress(r.read()).decode())
    return _instrument_cache[exch]


# ---------------------------------------------------------------- resolution
def ltp(keys, token):
    """Return {instrument_key(pipe form): {last_price, cp, volume}}."""
    out = {}
    if not keys:
        return out
    data = api_get("/v3/market-quote/ltp", {"instrument_key": ",".join(keys)}, token).get("data", {}) or {}
    for resp_key, v in data.items():
        k = v.get("instrument_token") or resp_key.replace(":", "|", 1)
        out[k] = v
    return out


def resolve_index_keys(token, log):
    """Map each index to a working Upstox instrument key."""
    candidates = [k for cfg in INDICES.values() for k in cfg["keys"]] + [VIX_KEY]
    prices = ltp(candidates, token)
    resolved = {}
    for name, cfg in INDICES.items():
        hit = next((k for k in cfg["keys"] if k in prices), None)
        if not hit:
            hit = search_index_key(cfg, log)
        if hit:
            resolved[name] = hit
        else:
            log(f"[warn] could not resolve instrument key for {name}")
    return resolved, prices


def search_index_key(cfg, log):
    try:
        for row in instruments(cfg["exch"]):
            seg = str(row.get("segment", ""))
            if not seg.endswith("_INDEX"):
                continue
            label = f"{row.get('name', '')} {row.get('trading_symbol', '')}".lower()
            if any(n in label for n in cfg["names"]):
                log(f"[info] resolved via instruments file: {row.get('instrument_key')}")
                return row.get("instrument_key")
    except Exception as e:  # noqa: BLE001
        log(f"[warn] instruments search failed: {e}")
    return None


# ---------------------------------------------------------------- per index
def nearest_expiry(index_key, token):
    data = api_get("/v2/option/contract", {"instrument_key": index_key}, token).get("data", []) or []
    today = dt.datetime.now(IST).date().isoformat()
    expiries = sorted({str(c.get("expiry"))[:10] for c in data if c.get("expiry")})
    upcoming = [e for e in expiries if e >= today]
    lot = next((c.get("lot_size") for c in data if c.get("lot_size")), None)
    return (upcoming[0] if upcoming else None), expiries[:6], lot


def nearest_future(cfg, index_key, token, log):
    """Find the nearest-expiry index future and its LTP (best effort)."""
    try:
        fo_exch = "NSE" if cfg["exch"] == "NSE" else "BSE"
        now_ms = int(time.time() * 1000)
        futs = [r for r in instruments(fo_exch)
                if str(r.get("instrument_type")) == "FUT"
                and r.get("underlying_key") == index_key
                and int(r.get("expiry") or 0) >= now_ms - 86_400_000]
        if not futs:
            return None
        fut = min(futs, key=lambda r: int(r["expiry"]))
        q = ltp([fut["instrument_key"]], token)
        v = next(iter(q.values()), {})
        return {
            "instrument_key": fut["instrument_key"],
            "trading_symbol": fut.get("trading_symbol"),
            "expiry": dt.datetime.fromtimestamp(int(fut["expiry"]) / 1000, IST).date().isoformat(),
            "last_price": v.get("last_price"),
        }
    except Exception as e:  # noqa: BLE001
        log(f"[warn] futures lookup failed: {e}")
        return None


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def normalize_chain(chain):
    rows = []
    spot = None
    for s in chain:
        spot = spot or num(s.get("underlying_spot_price"))
        ce = (s.get("call_options") or {})
        pe = (s.get("put_options") or {})
        cm, pm = ce.get("market_data") or {}, pe.get("market_data") or {}
        cg, pg = ce.get("option_greeks") or {}, pe.get("option_greeks") or {}
        ce_oi, pe_oi = num(cm.get("oi")) or 0, num(pm.get("oi")) or 0
        ce_prev, pe_prev = num(cm.get("prev_oi")), num(pm.get("prev_oi"))
        rows.append({
            "strike": num(s.get("strike_price")),
            "ce_oi": ce_oi, "pe_oi": pe_oi,
            "ce_chg_oi": (ce_oi - ce_prev) if ce_prev is not None else 0,
            "pe_chg_oi": (pe_oi - pe_prev) if pe_prev is not None else 0,
            "ce_ltp": num(cm.get("ltp")), "pe_ltp": num(pm.get("ltp")),
            "ce_volume": num(cm.get("volume")), "pe_volume": num(pm.get("volume")),
            "ce_iv": num(cg.get("iv")), "pe_iv": num(pg.get("iv")),
            "ce_delta": num(cg.get("delta")), "pe_delta": num(pg.get("delta")),
            "ce_gamma": num(cg.get("gamma")), "pe_gamma": num(pg.get("gamma")),
            "ce_theta": num(cg.get("theta")), "pe_theta": num(pg.get("theta")),
        })
    rows = [r for r in rows if r["strike"] is not None]
    rows.sort(key=lambda r: r["strike"])
    return rows, spot


_meta_cache = {}


def fetch_index(name, cfg, key, prices, token, raw_dir, log):
    snap = {"index": name, "instrument_key": key, "exchange": cfg["exch"], "strike_step": cfg["step"]}
    q = prices.get(key, {})
    snap["spot"] = num(q.get("last_price"))
    snap["prev_close"] = num(q.get("cp"))
    if snap["spot"] and snap["prev_close"]:
        snap["change"] = round(snap["spot"] - snap["prev_close"], 2)
        snap["change_pct"] = round(100 * snap["change"] / snap["prev_close"], 2)

    if name not in _meta_cache:
        expiry, expiries, lot = nearest_expiry(key, token)
        fut = nearest_future(cfg, key, token, log)
        _meta_cache[name] = (expiry, expiries, lot, fut)
    else:
        expiry, expiries, lot, fut = _meta_cache[name]
        if fut and fut.get("instrument_key"):  # refresh futures price only
            q = ltp([fut["instrument_key"]], token)
            fut = dict(fut, last_price=next(iter(q.values()), {}).get("last_price"))
    snap.update({"expiry": expiry, "upcoming_expiries": expiries, "lot_size": lot})
    snap["futures"] = dict(fut) if fut else None
    if snap["futures"] and snap["futures"].get("last_price") and snap["spot"]:
        snap["futures"]["basis"] = round(snap["futures"]["last_price"] - snap["spot"], 2)

    if expiry:
        resp = api_get("/v2/option/chain", {"instrument_key": key, "expiry_date": expiry}, token)
        chain = resp.get("data", []) or []
        if raw_dir:
            with open(os.path.join(raw_dir, f"{name}_chain.json"), "w") as f:
                json.dump(resp, f, indent=1)
        rows, chain_spot = normalize_chain(chain)
        snap["spot"] = snap["spot"] or chain_spot
        snap["rows"] = rows
    else:
        snap["rows"] = []
        log(f"[warn] {name}: no upcoming expiry found")
    return snap


# ---------------------------------------------------------------- burst series
def series_point(snap, vix, n_strikes=5):
    """Compact per-snapshot record for momentum analysis."""
    rows, spot, step = snap.get("rows", []), snap.get("spot"), snap.get("strike_step")
    point = {
        "t": snap["fetched_at"], "spot": spot, "vix": vix,
        "fut": (snap.get("futures") or {}).get("last_price"),
        "total_ce_oi": sum(r["ce_oi"] for r in rows),
        "total_pe_oi": sum(r["pe_oi"] for r in rows),
        "strikes": [],
    }
    if spot and step and rows:
        atm = round(spot / step) * step
        near = [r for r in rows if abs(r["strike"] - atm) <= n_strikes * step]
        point["atm"] = atm
        point["strikes"] = [{k: r[k] for k in ("strike", "ce_oi", "pe_oi", "ce_ltp", "pe_ltp")} for r in near]
    return point


# ---------------------------------------------------------------- main
def snapshot_pass(wanted, resolved, token, out_dir, raw_dir, log):
    """Fetch every wanted index once. Returns (context, snaps)."""
    fetched_at = dt.datetime.now(IST).isoformat(timespec="seconds")
    keys = list(resolved.values()) + [VIX_KEY]
    prices = ltp(keys, token)
    vix = prices.get(VIX_KEY, {})
    context = {
        "fetched_at": fetched_at,
        "source": "Upstox API (analytics token)",
        "india_vix": num(vix.get("last_price")),
        "india_vix_prev_close": num(vix.get("cp")),
        "resolved_keys": resolved,
    }
    status, snaps = {}, {}
    for name in sorted(wanted & set(INDICES)):
        if name not in resolved:
            status[name] = "unresolved"
            continue
        try:
            snap = fetch_index(name, INDICES[name], resolved[name], prices, token, raw_dir, log)
            snap["fetched_at"] = fetched_at
            snap["source"] = "Upstox API"
            with open(os.path.join(out_dir, f"{name}.json"), "w") as f:
                json.dump(snap, f, indent=1)
            snaps[name] = snap
            status[name] = f"ok ({len(snap['rows'])} strikes, expiry {snap.get('expiry')})"
        except Exception as e:  # noqa: BLE001
            status[name] = f"error: {e}"
        log(f"{fetched_at} {name}: {status[name]}")
        time.sleep(0.3)
    context["status"] = status
    return context, snaps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/latest")
    ap.add_argument("--raw", default="", help="Also save raw API responses here (debugging)")
    ap.add_argument("--only", default="", help="Comma-separated index keys (default: all)")
    ap.add_argument("--burst", type=int, default=1, help="Number of snapshots to take (default 1)")
    ap.add_argument("--interval", type=float, default=30, help="Seconds between burst snapshots")
    ap.add_argument("--series-out", default="", help="Where to write <INDEX>.json burst series")
    args = ap.parse_args()

    token = os.environ.get("UPSTOX_ANALYTICS_TOKEN", "").strip()
    if not token:
        sys.exit("UPSTOX_ANALYTICS_TOKEN is not set")
    os.makedirs(args.out, exist_ok=True)
    if args.raw:
        os.makedirs(args.raw, exist_ok=True)
    if args.series_out:
        os.makedirs(args.series_out, exist_ok=True)

    log_lines = []

    def log(msg):
        print(msg, flush=True)
        log_lines.append(msg)

    wanted = {k.strip().upper() for k in args.only.split(",") if k.strip()} or set(INDICES)
    resolved, _ = resolve_index_keys(token, log)

    series = {name: [] for name in wanted}
    context = {}
    for i in range(max(1, args.burst)):
        t0 = time.time()
        try:
            context, snaps = snapshot_pass(wanted, resolved, token, args.out,
                                           args.raw if i == 0 else "", log)
            for name, snap in snaps.items():
                series[name].append(series_point(snap, context.get("india_vix")))
        except Exception as e:  # noqa: BLE001
            log(f"[warn] burst pass {i + 1} failed: {e}")
        if args.series_out:
            for name, pts in series.items():
                if pts:
                    with open(os.path.join(args.series_out, f"{name}.json"), "w") as f:
                        json.dump({"index": name, "interval_sec": args.interval,
                                   "points": pts}, f, indent=1)
        if i < args.burst - 1:
            time.sleep(max(0.0, args.interval - (time.time() - t0)))

    if not context:
        sys.exit("No snapshot pass succeeded")
    context["burst"] = {"snapshots": args.burst, "interval_sec": args.interval} if args.burst > 1 else None
    context["log"] = log_lines
    with open(os.path.join(args.out, "_context.json"), "w") as f:
        json.dump(context, f, indent=1)

    if not any(str(s).startswith("ok") for s in context.get("status", {}).values()):
        sys.exit("No index fetched successfully")


if __name__ == "__main__":
    main()
