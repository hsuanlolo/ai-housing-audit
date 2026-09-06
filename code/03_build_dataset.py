"""
Clean the raw RentCast pages into the analysis listing universe, join census
tracts, and attach transit commute times to the three workplace anchors.

Missing-field policy: absent attributes are coded `unknown` and are NEVER imputed
as compliant or non-compliant (manuscript Sec. 5.1). Only rent, bedrooms, and
commute -- all fully observed after cleaning -- are treated as verifiable
constraints, which is why the violation rate is a floor rather than an estimate.
"""
import json, glob
import numpy as np, pandas as pd, geopandas as gpd
from common import RAW, INTERIM, FINAL

CORE = ["id","formattedAddress","city","county","zipCode","latitude","longitude",
        "propertyType","bedrooms","bathrooms","squareFootage","status","price",
        "listedDate","daysOnMarket"]

def load_raw():
    rows, prov = [], []
    files = [f for f in sorted(glob.glob(str(RAW/"rentcast_*.json")))
             if "ledger" not in f]
    for f in files:
        d = json.loads(open(f).read())
        for r in d:
            rows.append({k: r.get(k) for k in CORE})
        prov.append((f.split("/")[-1], len(d)))
    return pd.DataFrame(rows), prov

def main():
    log = []
    df, prov = load_raw()
    log.append(("raw records loaded", len(df)))

    df = df.drop_duplicates("id")
    log.append(("after dedupe on listing id", len(df)))

    df["rent"] = pd.to_numeric(df["price"], errors="coerce")
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    df = df[df.status == "Active"];                      log.append(("status Active", len(df)))
    df = df.dropna(subset=["latitude","longitude"]);      log.append(("has coordinates", len(df)))
    df = df.dropna(subset=["bedrooms"]);                  log.append(("has bedrooms", len(df)))
    df = df.dropna(subset=["rent"]);                      log.append(("has rent", len(df)))

    lo, hi = df.rent.quantile([.01, .99])
    df = df[(df.rent >= lo) & (df.rent <= hi)]
    log.append((f"rent within p1-p99 (${lo:,.0f}-${hi:,.0f})", len(df)))

    df["fingerprint"] = (df.formattedAddress.astype(str).str.upper().str.strip()
                         + "|" + df.bedrooms.astype(int).astype(str)
                         + "|" + df.rent.astype(int).astype(str))
    df = df.sort_values("daysOnMarket").drop_duplicates("fingerprint", keep="first")
    log.append(("after dedupe on address|beds|rent", len(df)))

    # ---- census tract join -------------------------------------------------
    tr = gpd.read_file(INTERIM/"nyc_tracts.gpkg")
    g = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=4326)
    g = gpd.sjoin(g, tr[["GEOID","borough","geometry"]], how="left", predicate="within")
    g = g.drop_duplicates("id")
    n_no_tract = g.GEOID.isna().sum()
    g = g[g.GEOID.notna()]
    log.append((f"assigned to a NYC census tract (dropped {n_no_tract} outside)", len(g)))
    df = pd.DataFrame(g.drop(columns=["geometry","index_right"]))

    # ---- transit commute ---------------------------------------------------
    import sys; sys.path.insert(0, "code")
    from transit import Network
    print("\nbuilding transit network ...")
    net = Network()
    cov = net.report_coverage(df.latitude.values, df.longitude.values)
    print(f"\nsubway access coverage: {cov}")
    stt = net.station_times_to_anchors()
    print("\nrouting listings -> anchors ...")
    cm = net.listing_commutes(df.latitude.values, df.longitude.values, stt)
    for k, v in cm.items():
        df[f"commute_{k}"] = v
    ccols = [f"commute_{k}" for k in cm]
    unreach = df[ccols].isna().all(axis=1).sum()
    log.append((f"reachable by subway within {__import__('transit').ACCESS_M}m walk (dropped {unreach})",
                int((~df[ccols].isna().all(axis=1)).sum())))
    df = df[~df[ccols].isna().all(axis=1)]

    df.to_csv(FINAL/"listings.csv", index=False)
    json.dump({"provenance": prov, "cleaning_log": log, "subway_coverage": cov},
              open(FINAL/"build_log.json","w"), indent=2, default=str)

    print("\n=== TABLE 3a. Cleaning cascade ===")
    for step, n in log: print(f"  {n:6,d}   {step}")
    print(f"\nsaved: {FINAL/'listings.csv'}")
    return df

if __name__ == "__main__":
    df = main()
    print("\n=== TABLE 3b. Rent by bedrooms x borough (median) ===")
    p = df.pivot_table(index="bedrooms", columns="borough", values="rent",
                       aggfunc="median")
    print(p.round(0).to_string())
    print("\n=== TABLE 3c. Counts by bedrooms x borough ===")
    print(df.pivot_table(index="bedrooms", columns="borough", values="rent",
                         aggfunc="size").fillna(0).astype(int).to_string())
    print("\n=== TABLE 4. Commute minutes to anchors ===")
    cc=[c for c in df.columns if c.startswith("commute_")]
    print(df[cc].describe(percentiles=[.1,.25,.5,.75,.9]).round(1).to_string())
    for c in cc:
        print(f"  {c}: within 30min {(df[c]<=30).mean():.1%}  45min {(df[c]<=45).mean():.1%}  "
              f"60min {(df[c]<=60).mean():.1%}")
    print("\nrent-commute correlation (key check for Pareto degeneracy):")
    for c in cc:
        print(f"  {c}: overall r={df.rent.corr(df[c]):+.3f}")
