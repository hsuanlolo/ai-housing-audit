"""Figure 1 (rent-commute Pareto structure) and the exclusion-bias table."""
import json, glob, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0,"code")
from common import FINAL, RAW, OUT
from importlib import import_module
bm_mod = None

CORE = ["id","formattedAddress","city","county","latitude","longitude",
        "propertyType","bedrooms","status","price","daysOnMarket"]

def prefilter():
    rows=[]
    for f in sorted(glob.glob(str(RAW/"rentcast_*.json"))):
        if "ledger" in f: continue
        for r in json.loads(open(f).read()): rows.append({k:r.get(k) for k in CORE})
    d=pd.DataFrame(rows).drop_duplicates("id")
    d["rent"]=pd.to_numeric(d.price,errors="coerce")
    d["bedrooms"]=pd.to_numeric(d.bedrooms,errors="coerce")
    d=d[(d.status=="Active")].dropna(subset=["latitude","longitude","bedrooms","rent"])
    lo,hi=d.rent.quantile([.01,.99]); d=d[(d.rent>=lo)&(d.rent<=hi)]
    return d

lst = pd.read_csv(FINAL/"listings.csv")
pre = prefilter()
kept = set(lst.id); dropped = pre[~pre.id.isin(kept)]

print("=== TABLE 2a. Bias direction of the 800m subway-access exclusion ===")
cmp = pd.DataFrame({
    "retained (n=%d)" % len(lst): [lst.rent.median(), lst.rent.mean(), lst.bedrooms.median()],
    "dropped (n=%d)" % len(dropped): [dropped.rent.median(), dropped.rent.mean(), dropped.bedrooms.median()],
}, index=["median rent","mean rent","median bedrooms"]).round(0)
print(cmp.to_string())
print("\nborough composition (county):")
bc = pd.DataFrame({"retained": lst.county.value_counts(normalize=True),
                   "dropped":  dropped.county.value_counts(normalize=True)}).fillna(0)
print((bc*100).round(1).to_string())
delta = dropped.rent.median() - lst.rent.median()
print(f"\n>> Excluded listings are ${abs(delta):,.0f}/mo "
      f"{'CHEAPER' if delta<0 else 'MORE EXPENSIVE'} at the median.")

# ---- Figure 1 -----------------------------------------------------------
def frontier(rent, comm):
    n=len(rent); keep=np.ones(n,bool)
    for i in range(n):
        if (( (rent<=rent[i]) & (comm<=comm[i]) ) & ((rent<rent[i])|(comm<comm[i]))).any():
            keep[i]=False
    return keep

fig, axes = plt.subplots(1,3, figsize=(15,4.6), sharey=False)
for ax, b in zip(axes, [0,1,2]):
    s = lst[lst.bedrooms==b]
    x = s["commute_midtown_manhattan"].values; y = s["rent"].values
    m = ~np.isnan(x)
    x, y = x[m], y[m]
    f = frontier(y, x)
    ax.scatter(x[~f], y[~f], s=7, c="#c9ccd1", alpha=.65, label="dominated")
    ax.scatter(x[f],  y[f],  s=26, c="#c0392b", zorder=3, label="Pareto frontier")
    o = np.argsort(x[f]); ax.plot(x[f][o], y[f][o], c="#c0392b", lw=1.1, zorder=2)
    ax.set_title(f"{['Studio','1 bedroom','2 bedroom'][b]}  (n={m.sum():,})", fontsize=11)
    ax.set_xlabel("transit commute to Midtown (min)"); ax.set_xlim(0, 90)
    if b==0: ax.set_ylabel("monthly rent (USD)"); ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=.25, lw=.5)
fig.suptitle("Figure 1. Rent-commute structure of the NYC listing universe, with Pareto frontiers",
             fontsize=12.5, y=1.02)
fig.tight_layout(); fig.savefig(OUT/"figure1_pareto.png", dpi=170, bbox_inches="tight")
print(f"\nsaved: {OUT/'figure1_pareto.png'}")

print("\n=== Frontier size in the full universe, by bedroom type ===")
for b in [0,1,2]:
    s=lst[lst.bedrooms==b]; x=s["commute_midtown_manhattan"].values; y=s.rent.values
    m=~np.isnan(x); f=frontier(y[m],x[m])
    print(f"  {['studio','1BR','2BR'][b]:7s} n={m.sum():5,d}  frontier={f.sum():3d}  "
          f"({f.mean():.1%})   dominated={(~f).sum():5,d}")
