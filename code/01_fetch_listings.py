"""
Fetch the NYC long-term rental listing universe from RentCast.

QUOTA DISCIPLINE. The free Developer tier allows 50 requests/calendar month and
bills $0.20 per request beyond that. Every request passes through api_ledger,
which refuses at 45. Pages are cached to data/raw/ so re-running this script
costs ZERO requests. Do not delete the cache unless you intend to spend quota.

SAMPLING CAVEAT (reported in the paper). `city="New York"` returns New York
County (Manhattan) only, so boroughs are queried separately. We take a fixed
number of pages per borough under the API's default ordering rather than
paginating to exhaustion. That ordering is undocumented, so the realized sample
is NOT a random draw from each borough's active inventory. Section 5.4 benchmarks
the realized rent and borough distribution against ACS and NYCHVS and reports the
divergence. Because every scenario, architecture, and identity condition draws
from the same universe, this affects external validity (the absolute level of
cost gaps) but not the internal validity of within-scenario contrasts.
"""
import json, time
import requests
from common import RAW, require_key
import api_ledger as L

BASE  = "https://api.rentcast.io/v1/listings/rental/long-term"
LIMIT = 500

# (city, pages) -- allocation proportional to borough rental stock
PLAN = [("New York", 3), ("Brooklyn", 3), ("Queens", 2), ("Bronx", 1), ("Staten Island", 1)]

def cache_path(city, offset):
    return RAW/f"rentcast_{city.replace(' ','_').lower()}_{offset:05d}.json"

def fetch(dry_run=False):
    key = require_key("rentcast")
    hdr = {"X-Api-Key": key, "Accept": "application/json"}

    need = sum(1 for city, pages in PLAN for p in range(pages)
               if not cache_path(city, p*LIMIT).exists())
    print(f"pages needed (uncached): {need}")
    L.status()
    if dry_run:
        print("DRY RUN -- no requests issued"); return
    L.check_or_die(need)

    manifest = []
    for city, pages in PLAN:
        for p in range(pages):
            off = p * LIMIT
            cp = cache_path(city, off)
            if cp.exists():
                page = json.loads(cp.read_text())
                print(f"  cached  {city:14s} off={off:5d}  n={len(page)}")
            else:
                params = {"city": city, "state": "NY", "status": "Active",
                          "limit": LIMIT, "offset": off}
                r = requests.get(BASE, headers=hdr, params=params, timeout=90)
                if r.status_code == 429:
                    print("  429 rate limited; sleeping 20s"); time.sleep(20)
                    r = requests.get(BASE, headers=hdr, params=params, timeout=90)
                page = r.json() if r.status_code == 200 else []
                page = page if isinstance(page, list) else (page.get("listings") or page.get("data") or [])
                L.record("listings/rental/long-term", params, r.status_code, len(page))
                if r.status_code != 200:
                    print(f"  !! {city} off={off} HTTP {r.status_code}: {r.text[:160]}")
                    continue
                cp.write_text(json.dumps(page))
                print(f"  fetched {city:14s} off={off:5d}  n={len(page)}  "
                      f"[quota {L.used_this_month()}/{L.MONTHLY_CAP}]")
            manifest.append({"city": city, "offset": off, "n": len(page), "file": cp.name})
            if len(page) < LIMIT:
                print(f"     ({city} exhausted at {len(page)} < {LIMIT}; skipping later pages)")
                break
    (RAW/"manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest

if __name__ == "__main__":
    import sys
    m = fetch(dry_run="--dry-run" in sys.argv)
    if m:
        print(f"\ntotal raw records: {sum(x['n'] for x in m)} across {len(m)} pages")
        L.status()
