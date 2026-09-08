"""Table 2b: benchmark the listing sample's rent distribution against NYCHVS 2023.

NYCHVS is the NYC Housing and Vacancy Survey public-use microdata: a free
direct download from nyc.gov, no API key. This fills the NYCHVS half of
Table 2b. The ACS half (borough shares vs renter-occupied units) still needs a
Census API key and is not computed here.

Three decisions worth stating, because each could bias the comparison:

1. TENURE coding is verified, not assumed. TENURE==1 has positive GRENT and
   zero MOWNERCOST; TENURE==2 the reverse. The implied weighted renter share,
   67.7%, matches the published NYC figure.

2. GRENT is gross rent (contract rent plus tenant-paid utilities). Negative
   values are reserved codes (-2 not applicable, -3 no cash rent) and are
   excluded, so the benchmark is the distribution of CASH gross rent.

3. The comparison is stock vs flow and must be bounded on both sides. Our
   sample is ASKING rent on units currently available. NYCHVS gross rent over
   ALL renters is rent currently PAID, which includes rent-stabilised,
   rent-controlled and subsidised tenancies of long duration that no listings
   sample can contain. Comparing against all renters therefore overstates
   coverage bias by attributing a structural difference to sampling. We report
   nested populations and treat recent unsubsidised movers as the fair
   comparison, since that population is the market-rate flow a renter using a
   listings site actually faces.

Estimates are weighted by FW, the final household weight. Replicate weights
FW1..FW80 exist for variance estimation and are not used: we report point
estimates, and the distributional gap is far larger than sampling error on the
NYCHVS side.
"""
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NY   = ROOT/"data"/"raw"/"nychvs"/"occupied_puf_23.csv"
OUT  = ROOT/"out"/"tables"; OUT.mkdir(parents=True, exist_ok=True)

DECILES = np.arange(0.1, 1.0, 0.1)

def wq(v, w, qs):
    """Weighted quantiles via the cumulative-weight step function."""
    o = np.argsort(v)
    v, w = np.asarray(v)[o], np.asarray(w)[o]
    cw = np.cumsum(w) / w.sum()
    return [float(v[np.searchsorted(cw, q, side="left")]) for q in qs]

def wpct_at(g, x):
    """Weighted share of population g at or below rent x."""
    return float((g.FW.values * (g.GRENT.values <= x)).sum() / g.FW.values.sum())

h = pd.read_csv(NY, usecols=["TENURE","GRENT","FW","HHFIRSTMOVEIN","RENTASSIST",
                             "MOWNERCOST"], low_memory=False)

assert h.loc[h.TENURE == 1, "GRENT"].gt(0).sum() > 0
assert h.loc[h.TENURE == 2, "GRENT"].gt(0).sum() == 0
assert h.loc[h.TENURE == 1, "MOWNERCOST"].gt(0).sum() == 0

renters = h[(h.TENURE == 1) & (h.GRENT > 0)]
share   = h.loc[h.TENURE == 1, "FW"].sum() / h.FW.sum()

POPS = {
    "All renter households, cash rent":       renters,
    "Moved in 2021-2023":                     renters[renters.HHFIRSTMOVEIN >= 2021],
    "Moved in 2021-2023, no rent assistance": renters[(renters.HHFIRSTMOVEIN >= 2021)
                                                      & (renters.RENTASSIST == 2)],
}

lst = pd.read_csv(ROOT/"data"/"final"/"listings.csv")
sample = [float(lst.rent.quantile(q)) for q in DECILES]
smed   = sample[4]

print(f"NYCHVS 2023: {len(renters):,} renter records with cash rent; "
      f"weighted renter share {share*100:.1f}%\n")

rows = [{"decile": f"p{int(round(q*100))}", "sample_asking_rent": s}
        for q, s in zip(DECILES, sample)]
for name, g in POPS.items():
    for row, v in zip(rows, wq(g.GRENT.values, g.FW.values, DECILES)):
        row[name] = v
t = pd.DataFrame(rows)
t.to_csv(OUT/"table2b_nychvs_benchmark.csv", index=False)
(OUT/"table2b_nychvs_benchmark.md").write_text(t.to_markdown(index=False))

hdr = f"{'decile':>7} {'sample':>9}" + "".join(f"{n.split(',')[0][:22]:>24}" for n in POPS)
print(hdr); print("-"*len(hdr))
for _, x in t.iterrows():
    line = f"{x.decile:>7} {x.sample_asking_rent:>9,.0f}"
    for n in POPS:
        line += f"{x[n]:>24,.0f}"
    print(line)

print("\nWhere the sample median sits in each NYCHVS population:")
for name, g in POPS.items():
    med = wq(g.GRENT.values, g.FW.values, [0.5])[0]
    print(f"  ${smed:,.0f} = {wpct_at(g, smed)*100:>5.1f}th pct of {name:<42}"
          f" ratio {smed/med:.2f}x")
print(f"\nwrote {OUT/'table2b_nychvs_benchmark.csv'}")
