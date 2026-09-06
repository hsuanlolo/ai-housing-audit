"""
Persistent RentCast request ledger. Enforces the monthly quota mechanically so no
run -- or re-run -- can overspend it.

Free Developer tier = 50 requests/calendar month, overage billed at $0.20/request.
We refuse at MONTHLY_CAP, deliberately below 50, to keep a reserve.
"""
import json, datetime, pathlib
from common import RAW

LEDGER = RAW/"rentcast_ledger.json"
MONTHLY_CAP = 45          # hard refusal point; 5 requests held in reserve
HARD_LIMIT  = 50          # the actual tier limit, for reporting only

def _load():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"requests": []}

def _month_key(ts=None):
    d = datetime.datetime.fromisoformat(ts) if ts else datetime.datetime.now()
    return f"{d.year:04d}-{d.month:02d}"

def used_this_month():
    led = _load()
    mk = _month_key()
    return sum(1 for r in led["requests"] if _month_key(r["ts"]) == mk)

def remaining():
    return max(0, MONTHLY_CAP - used_this_month())

def record(endpoint, params, status, n_records):
    led = _load()
    led["requests"].append({
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "endpoint": endpoint, "params": {k: v for k, v in params.items()},
        "status": status, "n": n_records,
    })
    LEDGER.write_text(json.dumps(led, indent=2))

def check_or_die(n_wanted=1):
    rem = remaining()
    if n_wanted > rem:
        raise SystemExit(
            f"QUOTA GUARD: want {n_wanted} request(s), only {rem} left this month "
            f"(cap {MONTHLY_CAP}, tier limit {HARD_LIMIT}, used {used_this_month()}). Refusing."
        )
    return rem

def status():
    u = used_this_month()
    print(f"RentCast quota: used {u}/{MONTHLY_CAP} this month "
          f"({HARD_LIMIT - u} before real overage). Remaining under cap: {remaining()}")

if __name__ == "__main__":
    status()
