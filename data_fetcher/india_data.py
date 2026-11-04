#!/usr/bin/env python3
"""
Extra market data for the india-skills, fetched in GitHub Actions and written
under an output root that is published to the `market-data` branch.

Subcommands (run one or more, in order):
  constituents  NSE index lists (Nifty 50, Nifty Bank)  -> reference/constituents_<IDX>.json
  intraday      today's 1-minute candles per index       -> latest/candles_<KEY>.json
  breadth       live % change of index constituents      -> latest/breadth_<IDX>.json
  history       ~70 sessions of 5-minute index candles   -> history/<KEY>_5m.json
  news          Upstox news for heavyweights             -> latest/news.json
  smartmoney    NSE participant OI (10 days), bulk and block deals
                                                         -> smartmoney/*.json
  alerts        check india-skills/india-alerts/alerts.json against today's
                candles and open a GitHub issue for each newly hit alert
                                                         -> state/alerts_fired.json

Usage:
  UPSTOX_ANALYTICS_TOKEN=... python3 india_data.py --root out intraday breadth

Standard library only. Upstox calls use the read-only Analytics Token.
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import upstox_fetch as up  # noqa: E402

IST = up.IST
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONFIG = os.path.join(REPO, "india-skills", "config", "heavyweights.json")
ALERTS = os.path.join(REPO, "india-skills", "india-alerts", "alerts.json")
NSE_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
NSE_ARCHIVE = "https://nsearchives.nseindia.com"
INDEX_LISTS = {"NIFTY": "ind_nifty50list.csv", "BANKNIFTY": "ind_niftybanklist.csv"}
CANDLE_INDICES = ["NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY", "MIDCPNIFTY"]


# ---------------------------------------------------------------- helpers
def now_ist():
    return dt.datetime.now(IST)


def write_json(root, rel, obj):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)
    return path


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def http_get(url, headers=None, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": NSE_UA, "Accept": "*/*", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def token():
    t = os.environ.get("UPSTOX_ANALYTICS_TOKEN", "").strip()
    if not t:
        sys.exit("UPSTOX_ANALYTICS_TOKEN is not set")
    return t


def index_key(name):
    return up.INDICES[name]["keys"][0]


def parse_candles(resp):
    """Upstox candles -> ascending list of dicts."""
    out = []
    for c in (resp.get("data") or {}).get("candles") or []:
        out.append({"t": c[0], "o": c[1], "h": c[2], "l": c[3], "c": c[4],
                    "v": c[5] if len(c) > 5 else None, "oi": c[6] if len(c) > 6 else None})
    out.sort(key=lambda x: x["t"])
    return out


def enc(key):
    return urllib.parse.quote(key, safe="")


# ---------------------------------------------------------------- constituents
def cmd_constituents(root, log):
    for idx, fname in INDEX_LISTS.items():
        try:
            raw = http_get(f"{NSE_ARCHIVE}/content/indices/{fname}").decode("utf-8-sig", "replace")
            rows = list(csv.DictReader(io.StringIO(raw)))
            stocks = [{"symbol": r.get("Symbol", "").strip(), "name": r.get("Company Name", "").strip(),
                       "industry": r.get("Industry", "").strip(), "isin": r.get("ISIN Code", "").strip()}
                      for r in rows if r.get("Symbol")]
            if not stocks:
                raise ValueError("empty list")
            write_json(root, f"reference/constituents_{idx}.json",
                       {"index": idx, "fetched_at": now_ist().isoformat(timespec="seconds"),
                        "source": f"NSE {fname}", "stocks": stocks})
            log(f"constituents {idx}: {len(stocks)} stocks")
        except Exception as e:  # noqa: BLE001
            log(f"[warn] constituents {idx}: {e}")


def load_constituents(root):
    out = {}
    for idx in INDEX_LISTS:
        d = read_json(os.path.join(root, f"reference/constituents_{idx}.json"))
        if d:
            out[idx] = d["stocks"]
    return out


def symbol_isin_map(root):
    m = {}
    for stocks in load_constituents(root).values():
        for s in stocks:
            m[s["symbol"]] = s["isin"]
    return m


# ---------------------------------------------------------------- intraday candles
def cmd_intraday(root, log, tok):
    for name in CANDLE_INDICES:
        key = index_key(name)
        try:
            resp = up.api_get(f"/v3/historical-candle/intraday/{enc(key)}/minutes/1", {}, tok)
            candles = parse_candles(resp)
            write_json(root, f"latest/candles_{name}.json",
                       {"index": name, "instrument_key": key, "interval": "1minute",
                        "fetched_at": now_ist().isoformat(timespec="seconds"), "candles": candles})
            log(f"intraday {name}: {len(candles)} candles")
        except Exception as e:  # noqa: BLE001
            log(f"[warn] intraday {name}: {e}")
        time.sleep(0.25)


# ---------------------------------------------------------------- breadth
def cmd_breadth(root, log, tok):
    cons = load_constituents(root)
    if not cons:
        log("[warn] breadth: no constituents file; run 'constituents' first")
        return
    keys = sorted({f"NSE_EQ|{s['isin']}" for stocks in cons.values() for s in stocks if s["isin"]})
    quotes = {}
    for i in range(0, len(keys), 450):
        quotes.update(up.ltp(keys[i:i + 450], tok))
    t = now_ist().isoformat(timespec="seconds")
    for idx, stocks in cons.items():
        rows = []
        for s in stocks:
            q = quotes.get(f"NSE_EQ|{s['isin']}", {})
            lp, cp = up.num(q.get("last_price")), up.num(q.get("cp"))
            chg = round(100 * (lp - cp) / cp, 2) if lp and cp else None
            rows.append({"symbol": s["symbol"], "industry": s["industry"], "ltp": lp,
                         "prev_close": cp, "change_pct": chg})
        valid = [r for r in rows if r["change_pct"] is not None]
        write_json(root, f"latest/breadth_{idx}.json", {
            "index": idx, "fetched_at": t, "source": "Upstox API",
            "advancers": sum(1 for r in valid if r["change_pct"] > 0),
            "decliners": sum(1 for r in valid if r["change_pct"] < 0),
            "unchanged": sum(1 for r in valid if r["change_pct"] == 0),
            "stocks": rows})
        log(f"breadth {idx}: {len(valid)}/{len(rows)} quoted")


# ---------------------------------------------------------------- history
def cmd_history(root, log, tok, sessions=70):
    today = now_ist().date()
    for name in ["NIFTY", "BANKNIFTY", "SENSEX"]:
        key = index_key(name)
        candles, to = [], today
        try:
            # 1-15 minute candles: max one month per request; walk back in 28-day chunks
            while len({c["t"][:10] for c in candles}) < sessions + 2 and (today - to).days < 200:
                frm = to - dt.timedelta(days=27)
                resp = up.api_get(f"/v3/historical-candle/{enc(key)}/minutes/5/{to.isoformat()}/{frm.isoformat()}", {}, tok)
                candles = parse_candles(resp) + candles
                to = frm - dt.timedelta(days=1)
                time.sleep(0.4)
            uniq = {c["t"]: c for c in candles}
            candles = [uniq[k] for k in sorted(uniq)]
            days = sorted({c["t"][:10] for c in candles})[-sessions:]
            candles = [c for c in candles if c["t"][:10] in set(days)]
            write_json(root, f"history/{name}_5m.json",
                       {"index": name, "instrument_key": key, "interval": "5minute",
                        "fetched_at": now_ist().isoformat(timespec="seconds"),
                        "sessions": len(days), "first_day": days[0] if days else None,
                        "last_day": days[-1] if days else None, "candles": candles})
            log(f"history {name}: {len(days)} sessions, {len(candles)} candles")
        except Exception as e:  # noqa: BLE001
            log(f"[warn] history {name}: {e}")


# ---------------------------------------------------------------- news
def cmd_news(root, log, tok):
    cfg = read_json(CONFIG, {})
    isin = symbol_isin_map(root)
    symbols = []
    for idx in ("NIFTY", "BANKNIFTY", "SENSEX"):
        for s in cfg.get(idx, []):
            if s not in symbols:
                symbols.append(s)
    keys = [f"NSE_EQ|{isin[s]}" for s in symbols if s in isin][:30]
    if not keys:
        log("[warn] news: no instrument keys (constituents missing)")
        return
    try:
        resp = up.api_get("/v2/news", {"category": "instrument_keys", "instrument_keys": ",".join(keys),
                                       "page_number": 1, "page_size": 100}, tok)
    except Exception as e:  # noqa: BLE001
        log(f"[warn] news: {e}")
        return
    sym_by_key = {f"NSE_EQ|{isin[s]}": s for s in symbols if s in isin}
    items = []

    def add(item, key=None):
        if not isinstance(item, dict):
            return
        ts = item.get("published_at") or item.get("publishedAt") or item.get("timestamp") or item.get("published_time")
        try:
            ts_iso = dt.datetime.fromtimestamp(int(ts) / 1000, IST).isoformat(timespec="minutes")
        except (TypeError, ValueError):
            ts_iso = str(ts) if ts else None
        keys_in = item.get("instrument_keys") or item.get("instrument_key") or key
        if isinstance(keys_in, str):
            keys_in = [keys_in]
        items.append({
            "published": ts_iso,
            "headline": item.get("heading") or item.get("headline") or item.get("title"),
            "summary": item.get("summary") or item.get("description"),
            "link": item.get("article_link") or item.get("link") or item.get("url"),
            "symbols": sorted({sym_by_key.get(k, k) for k in (keys_in or [])}),
        })

    data = resp.get("data")
    if isinstance(data, dict):
        for k, v in data.items():
            for it in (v if isinstance(v, list) else [v]):
                add(it, k)
    elif isinstance(data, list):
        for it in data:
            if isinstance(it, dict) and len(it) == 1 and isinstance(next(iter(it.values())), list):
                k, v = next(iter(it.items()))
                for x in v:
                    add(x, k)
            else:
                add(it)
    merged = {}
    for i in items:
        if not i["headline"]:
            continue
        k = i["link"] or i["headline"]
        if k in merged:
            merged[k]["symbols"] = sorted(set(merged[k]["symbols"]) | set(i["symbols"]))
        else:
            merged[k] = i
    items = list(merged.values())
    items.sort(key=lambda i: i["published"] or "", reverse=True)
    write_json(root, "latest/news.json", {"fetched_at": now_ist().isoformat(timespec="seconds"),
                                          "source": "Upstox News API", "items": items[:150]})
    if not items:
        write_json(root, "latest/news_raw_sample.json", {"sample": str(resp)[:3000]})
    log(f"news: {len(items)} items")


# ---------------------------------------------------------------- smart money (NSE public files)
PART_COLS = {
    "fut_idx_long": "Future Index Long", "fut_idx_short": "Future Index Short",
    "fut_stk_long": "Future Stock Long", "fut_stk_short": "Future Stock Short",
    "opt_idx_call_long": "Option Index Call Long", "opt_idx_put_long": "Option Index Put Long",
    "opt_idx_call_short": "Option Index Call Short", "opt_idx_put_short": "Option Index Put Short",
    "total_long": "Total Long Contracts", "total_short": "Total Short Contracts",
}


def parse_participant_oi(text):
    lines = [ln for ln in text.splitlines() if ln.strip()]
    start = next((i for i, ln in enumerate(lines) if ln.lower().startswith("client type")), None)
    if start is None:
        raise ValueError("header not found")
    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    out = {}
    for r in reader:
        r = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
        who = r.get("Client Type", "").upper()
        if who not in ("CLIENT", "DII", "FII", "PRO"):
            continue
        out[who] = {k: int(float(r.get(col, "0").replace(",", "") or 0)) for k, col in PART_COLS.items()}
    if not out:
        raise ValueError("no participant rows")
    return out


def parse_deals(text):
    rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
    out = []
    for r in rows:
        r = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
        if not r.get("Symbol"):
            continue
        out.append({"date": r.get("Date"), "symbol": r.get("Symbol"), "name": r.get("Security Name"),
                    "client": r.get("Client Name"), "side": r.get("Buy/Sell"),
                    "qty": r.get("Quantity Traded"), "price": r.get("Trade Price / Wght. Avg. Price")})
    return out


def cmd_smartmoney(root, log, days=10):
    got, d = [], now_ist().date()
    for _ in range(25):
        if len(got) >= days:
            break
        if d.weekday() < 5:
            url = f"{NSE_ARCHIVE}/content/nsccl/fao_participant_oi_{d.strftime('%d%m%Y')}.csv"
            try:
                parts = parse_participant_oi(http_get(url).decode("utf-8-sig", "replace"))
                got.append({"date": d.isoformat(), "participants": parts})
            except urllib.error.HTTPError as e:
                if e.code not in (403, 404):
                    log(f"[warn] participant OI {d}: HTTP {e.code}")
            except Exception as e:  # noqa: BLE001
                log(f"[warn] participant OI {d}: {e}")
            time.sleep(0.4)
        d -= dt.timedelta(days=1)
    got.sort(key=lambda x: x["date"])
    if got:
        write_json(root, "smartmoney/participant_oi.json",
                   {"fetched_at": now_ist().isoformat(timespec="seconds"),
                    "source": "NSE participant-wise OI (nsearchives)", "days": got})
    log(f"smartmoney participant OI: {len(got)} days")

    for kind in ("bulk", "block"):
        try:
            deals = parse_deals(http_get(f"{NSE_ARCHIVE}/content/equities/{kind}.csv").decode("utf-8-sig", "replace"))
            write_json(root, f"smartmoney/{kind}_deals.json",
                       {"fetched_at": now_ist().isoformat(timespec="seconds"),
                        "source": f"NSE {kind}.csv", "deals": deals})
            log(f"smartmoney {kind} deals: {len(deals)}")
        except Exception as e:  # noqa: BLE001
            log(f"[warn] {kind} deals: {e}")


# ---------------------------------------------------------------- alerts
def gh_issue(title, body, log):
    repo, tok = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if not repo or not tok:
        log(f"[info] would open issue: {title}")
        return False
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues", method="POST",
        data=json.dumps({"title": title, "body": body, "labels": ["alert"]}).encode(),
        headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                 "User-Agent": up.USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30):
            return True
    except Exception as e:  # noqa: BLE001
        log(f"[warn] issue create failed: {e}")
        return False


def cmd_alerts(root, log):
    cfg = read_json(ALERTS, {"alerts": []})
    state_path = os.path.join(root, "state/alerts_fired.json")
    state = read_json(state_path, {"fired": {}})
    today = now_ist().date().isoformat()
    fired = 0
    for a in cfg.get("alerts", []):
        if not a.get("active", True):
            continue
        aid = a.get("id") or f"{a.get('index')}-{a.get('direction')}-{a.get('level')}"
        if state["fired"].get(aid) == today:
            continue
        name = str(a.get("index", "")).upper()
        cd = read_json(os.path.join(root, f"latest/candles_{name}.json"))
        candles = [c for c in (cd or {}).get("candles", []) if c["t"][:10] == today]
        if not candles:
            continue
        level, direction = float(a["level"]), a.get("direction", "above")
        hit = next((c for c in candles if (c["h"] >= level if direction == "above" else c["l"] <= level)), None)
        if not hit:
            continue
        last = candles[-1]["c"]
        title = f"🔔 {name} {direction} {level:g} (hit {hit['t'][11:16]} IST, now {last:g})"
        body = (f"Alert `{aid}`: **{name} {direction} {level:g}**\n\n"
                f"- First 1-minute candle that touched it: {hit['t']} (high {hit['h']}, low {hit['l']})\n"
                f"- Last price in data: {last} at {candles[-1]['t']}\n"
                f"- Note: {a.get('note') or '—'}\n\n"
                "Checked from 1-minute candles when the market-data job runs, so it can be "
                "minutes late. Use your broker's own price alerts when timing matters.")
        if gh_issue(title, body, log):
            fired += 1
        state["fired"][aid] = today
        log(f"alert fired: {title}")
    write_json(root, "state/alerts_fired.json", state)
    log(f"alerts: {fired} fired")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="out", help="Output root (published to market-data)")
    ap.add_argument("commands", nargs="+",
                    choices=["constituents", "intraday", "breadth", "history", "news", "smartmoney", "alerts"])
    a = ap.parse_args()
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    needs_token = {"intraday", "breadth", "history", "news"}
    tok = token() if needs_token & set(a.commands) else None
    for c in a.commands:
        try:
            if c == "constituents":
                cmd_constituents(a.root, log)
            elif c == "intraday":
                cmd_intraday(a.root, log, tok)
            elif c == "breadth":
                cmd_breadth(a.root, log, tok)
            elif c == "history":
                cmd_history(a.root, log, tok)
            elif c == "news":
                cmd_news(a.root, log, tok)
            elif c == "smartmoney":
                cmd_smartmoney(a.root, log)
            elif c == "alerts":
                cmd_alerts(a.root, log)
        except Exception as e:  # noqa: BLE001
            log(f"[warn] {c} failed: {e}")
    log_path = os.path.join(a.root, "state", "india_data.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"--- {now_ist().isoformat(timespec='seconds')} {' '.join(a.commands)}\n" + "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
