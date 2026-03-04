"""
oref_accumulate.py - GitHub Actions accumulator for oref alerts seed.
Runs every 10 minutes in CI. Merges tzevaadom + oref into alerts_seed.json.
Also maintains alerts_raw.jsonl - append-only raw log, never loses data.
Does NOT push - the workflow handles git.
"""
import urllib.request, json, sys, os
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')

# Paths are relative to repo root (GitHub Actions checks out to workspace root)
SEED_PATH = 'oref-dashboard/alerts_seed.json'
RAW_PATH  = 'oref-dashboard/alerts_raw.jsonl'   # append-only, one record per line
IL = timedelta(hours=2)

OREF_URL      = 'https://alerts-history.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx'
TZEVAADOM_URL = 'https://api.tzevaadom.co.il/alerts-history/'

# Don't keep records older than 30 days (keeps file size manageable)
NOW_TS    = int(datetime.now(tz=timezone.utc).timestamp())
CUTOFF_TS = NOW_TS - (30 * 24 * 3600)

def fetch_tzevaadom():
    req = urllib.request.Request(
        TZEVAADOM_URL,
        headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.tzevaadom.co.il/'}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        groups = json.loads(r.read())
    flat = []
    for group in groups:
        for alert in (group.get('alerts') or []):
            if alert.get('isDrill'):
                continue
            t = alert.get('time', 0)
            if t < CUTOFF_TS:
                continue
            for city in (alert.get('cities') or []):
                flat.append({
                    'city': city,
                    'time': t,
                    'threat': alert.get('threat', 1)
                })
    return flat

def fetch_oref_latest():
    today_str = (datetime.now(tz=timezone.utc) + IL).strftime('%d.%m.%Y')
    cutoff_str = datetime.fromtimestamp(CUTOFF_TS, tz=timezone.utc).strftime('%d.%m.%Y')
    url = f"{OREF_URL}?lang=he&fromDate={cutoff_str}&toDate={today_str}&mode=1"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.oref.org.il/',
        'Accept': 'application/json, text/javascript',
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        records = json.loads(r.read())
    flat = []
    for rec in records:
        city = (rec.get('data') or '').strip()
        if not city:
            continue
        alert_date = rec.get('alertDate') or ''
        try:
            dt = datetime.fromisoformat(alert_date.replace('Z', ''))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ts = int(dt.timestamp())
        except Exception:
            d = rec.get('date', '')
            t = rec.get('time', '00:00:00')
            try:
                parts = d.split('.')
                dt = datetime(int(parts[2]), int(parts[1]), int(parts[0]),
                              int(t[:2]), int(t[3:5]), tzinfo=timezone.utc)
                ts = int(dt.timestamp())
            except Exception:
                continue
        if ts < CUTOFF_TS:
            continue
        flat.append({
            'city': city,
            'time': ts,
            'threat': rec.get('category', 1),
            'rid': rec.get('rid')
        })
    return flat

def load_existing():
    if not os.path.exists(SEED_PATH):
        print(f"  WARNING: {SEED_PATH} not found - starting fresh")
        return [], set(), set()
    with open(SEED_PATH, encoding='utf-8') as f:
        data = json.load(f)
    # Prune old records (>30 days)
    before = len(data)
    data = [r for r in data if r.get('time', 0) >= CUTOFF_TS]
    if len(data) < before:
        print(f"  Pruned {before - len(data)} old records (>30 days)")
    rids = set(r['rid'] for r in data if r.get('rid'))
    ct   = set(f"{r['city']}|{r['time']}" for r in data)
    return data, rids, ct

# ── MAIN ──
now_il = datetime.now(tz=timezone.utc) + IL
print(f"[{now_il.strftime('%d/%m %H:%M')} IL] oref_accumulate starting...")

existing, seen_rids, seen_ct = load_existing()
print(f"  Existing: {len(existing):,} records")

# Fetch
tz_flat = []
try:
    tz_flat = fetch_tzevaadom()
    print(f"  tzevaadom: {len(tz_flat):,} records")
except Exception as e:
    print(f"  tzevaadom ERROR: {e}")

oref_flat = []
try:
    oref_flat = fetch_oref_latest()
    print(f"  oref: {len(oref_flat):,} records")
except Exception as e:
    print(f"  oref ERROR: {e}")

# Merge
added = 0
for r in tz_flat + oref_flat:
    rid    = r.get('rid')
    ct_key = f"{r['city']}|{r['time']}"
    if rid and rid in seen_rids:
        continue
    if ct_key in seen_ct:
        continue
    existing.append(r)
    if rid:
        seen_rids.add(rid)
    seen_ct.add(ct_key)
    added += 1

print(f"  Added: {added} new records | Total: {len(existing):,}")

if added == 0:
    print("  Up to date - no changes needed")
    sys.exit(0)

# Sort by time ascending
existing.sort(key=lambda r: r.get('time', 0))

# Save seed (rolling 30-day window)
with open(SEED_PATH, 'w', encoding='utf-8') as f:
    json.dump(existing, f, ensure_ascii=False, separators=(',', ':'))

size_kb = os.path.getsize(SEED_PATH) / 1024
print(f"  Saved: {SEED_PATH} ({size_kb:.0f} KB)")

# Append new records to raw log (append-only, never loses data)
# Load existing raw keys to avoid duplicates
raw_seen = set()
if os.path.exists(RAW_PATH):
    with open(RAW_PATH, encoding='utf-8') as f:
        for line in f:
            try:
                rec = json.loads(line.strip())
                raw_seen.add(f"{rec['city']}|{rec['time']}")
            except:
                pass

new_raw = []
for r in tz_flat + oref_flat:
    k = f"{r['city']}|{r['time']}"
    if k not in raw_seen:
        new_raw.append(r)
        raw_seen.add(k)

if new_raw:
    new_raw.sort(key=lambda r: r.get('time', 0))
    with open(RAW_PATH, 'a', encoding='utf-8') as f:
        for rec in new_raw:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    raw_kb = os.path.getsize(RAW_PATH) / 1024
    print(f"  Raw log: +{len(new_raw)} records → {RAW_PATH} ({raw_kb:.0f} KB total)")

print(f"  Done. Added {added} records.")
