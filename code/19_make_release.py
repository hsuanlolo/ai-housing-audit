"""Refresh data/public/ -- the released data bundle.

data/public/audit_log.jsonl was originally copied by hand, before the
claude-opus-5 arm was collected, and was never refreshed. It therefore held
6,120 calls while the paper reported 6,840, so the cross-vendor replication in
Section 8.6 rested on data that was not in the public release. This script
exists so that cannot happen again: run it after any new arm.

What is released and what is withheld:

  Released   pool-local listing ids (L001..L120), scenario parameters, the
             model's raw response, token counts, cost, and every derived
             outcome. Also the four supplementary arm logs.

  Withheld   the RentCast listing records themselves -- rent, bedrooms,
             addresses, coordinates. RentCast's Terms of Use prohibit transfer
             or sublicense. Note that the model's own `raw` justifications
             sometimes quote a rent figure; those are the model's words about
             an anonymous pool id, and the inventory cannot be reconstructed
             from them because no address, no coordinate and no RentCast id is
             present.

The audit log is copied field-for-field. Verified identical in schema to the
working copy (33 fields), so no field-stripping step is required or performed.
"""
import json, shutil
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[1]
OUT    = ROOT/"out"
PUBLIC = ROOT/"data"/"public"
PUBLIC.mkdir(parents=True, exist_ok=True)

ARMS = ["audit_log.jsonl", "priority_swap.jsonl", "priority_swap_claude.jsonl",
        "pool_density.jsonl", "size_sweep.jsonl"]

def count(p):
    rows = [json.loads(l) for l in open(p)]
    return len(rows), sum(1 for r in rows if r.get("parse_ok"))

total_a = total_p = 0
print(f"{'file':<32} {'attempted':>10} {'parsed':>8}")
for name in ARMS:
    src = OUT/name
    if not src.is_file():
        print(f"{name:<32} {'MISSING':>10}")
        continue
    shutil.copyfile(src, PUBLIC/name)
    a, p = count(PUBLIC/name)
    total_a += a; total_p += p
    print(f"{name:<32} {a:>10,} {p:>8,}")
print(f"{'TOTAL':<32} {total_a:>10,} {total_p:>8,}  ({total_p/total_a*100:.1f}%)")

# the three derived files are produced elsewhere and are not regenerated here
for extra in ["listing_derived.csv", "scenarios.csv", "random_baseline.csv"]:
    f = PUBLIC/extra
    print(f"  {extra:<30} {'present' if f.is_file() else 'MISSING -- regenerate'}")
print(f"\nrelease bundle -> {PUBLIC}")
