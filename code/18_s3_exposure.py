"""S3 -- neighborhood exposure (6.2). The measure that connects this audit to
the steering literature.

For every parsed response we take the listings the model recommended, look up
the ACS tract each sits in, and summarise the tract characteristics of the
recommended set. The identity contrast is then the WITHIN-scenario difference
in those characteristics between an identity condition and the neutral
baseline, which is the same estimand and the same inference procedure used for
every other outcome in this paper (7.2): the scenario, the pool and the
candidate ordering are fixed, and only the identity cue moves.

This is deliberately the design Liu et al. (2024) and Samad et al. (2026)
could not run, and it is also strictly weaker than theirs in one respect worth
stating plainly: our pool is fixed, so the model cannot choose WHERE to look.
It can only re-rank a set we chose. A null here therefore bounds
identity-conditioned re-ranking, and says nothing about open-ended search,
where the prior literature finds steering.

Inference: 10,000 within-scenario sign-flip permutations of the paired
difference, two-sided, Benjamini-Hochberg across the outcome family.
"""
import json, random, sys
import numpy as np, pandas as pd
import importlib.util as u
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"code"))
from common import FINAL, INTERIM, OUT, SEED

def _load(path, name):
    sp = u.spec_from_file_location(name, ROOT/"code"/path)
    m = u.module_from_spec(sp); sp.loader.exec_module(m); return m

ad = _load("07_audit.py", "ad")
sc = _load("02_build_scenarios.py", "sc")

TAB = OUT/"tables"; TAB.mkdir(parents=True, exist_ok=True)

OUTCOMES = {
    "median_hh_income":       "tract median household income ($)",
    "median_gross_rent":      "tract median gross rent ($)",
    "median_rent_pct_income": "tract rent burden (% of income)",
    "renter_share":           "tract renter share",
    "pct_nonwhite":           "tract share non-White (non-Hispanic)",
    "pct_black_nh":           "tract share Black (non-Hispanic)",
    "pct_hispanic":           "tract share Hispanic",
}

def main():
    lst  = pd.read_csv(FINAL/"listings.csv")
    acs  = pd.read_csv(INTERIM/"acs_tract_covariates.csv", dtype={"GEOID": str})
    scen = pd.read_csv(INTERIM/"benchmark_scenarios.csv")

    lst["GEOID"] = lst.GEOID.astype(str).str.zfill(11)
    acs["GEOID"] = acs.GEOID.astype(str).str.zfill(11)
    lst = lst.merge(acs[["GEOID"] + list(OUTCOMES)], on="GEOID", how="left")
    cov = lst[["id"] + list(OUTCOMES)].set_index("id")
    print(f"listings joined to ACS: "
          f"{lst.median_hh_income.notna().mean()*100:.1f}% have tract income")

    rng = random.Random(SEED)
    cells = sc.assign_names(sc.build_grid(rng), rng)
    scen["pool_order_seed"] = scen.scenario_id.map(
        {c["scenario_id"]: c["pool_order_seed"] for c in cells})

    # rebuild each scenario's pool so pool-local sids resolve to listing ids
    pools = {}
    for _, c in scen.iterrows():
        cc = f"commute_{c.anchor}"
        try:
            p = ad.build_pool(lst, c, cc)
        except Exception:
            continue
        if p is not None:
            pools[c.scenario_id] = dict(zip(p.sid, p.id))

    rows = []
    for line in open(OUT/"audit_log.jsonl"):
        r = json.loads(line)
        if not r.get("parse_ok") or not isinstance(r.get("picks"), list):
            continue
        m = pools.get(r["scenario_id"])
        if not m:
            continue
        ids = [m[s] for s in r["picks"] if s in m]
        if not ids:
            continue
        sub = cov.reindex(ids)
        rec = {"scenario_id": r["scenario_id"], "cond": r["cond"],
               "model": r["model"], "arch": r["arch"], "rep": r["rep"]}
        for k in OUTCOMES:
            rec[k] = sub[k].median(skipna=True)
        rows.append(rec)

    d = pd.DataFrame(rows)
    d.to_csv(TAB/"s3_exposure_raw.csv", index=False)
    print(f"{len(d):,} responses scored for neighborhood exposure")

    # ---- descriptive: exposure by condition, luna S1
    base = d[(d.model == "gpt-5.6-luna") & (d.arch == "S1")]
    desc = base.groupby("cond")[list(OUTCOMES)].median().round(3)
    desc.to_csv(TAB/"table22_s3_exposure_by_condition.csv")
    print("\nMedian tract characteristics of recommended listings "
          "(gpt-5.6-luna, S1):")
    print(desc.to_string())

    # ---- within-scenario paired contrasts vs the neutral baseline
    res = []
    nperm = 10_000
    for model in d.model.unique():
        for arch in sorted(d[d.model == model].arch.unique()):
            g = d[(d.model == model) & (d.arch == arch)]
            piv = g.groupby(["scenario_id", "cond"])[list(OUTCOMES)].mean()
            for cond in ["C1_name_a", "C2_name_b", "C3_voucher"]:
                for k in OUTCOMES:
                    try:
                        a = piv.xs("C0_neutral", level="cond")[k]
                        b = piv.xs(cond, level="cond")[k]
                    except KeyError:
                        continue
                    j = pd.concat([a, b], axis=1, keys=["c0", "c1"]).dropna()
                    if len(j) < 20:
                        continue
                    diff = (j.c1 - j.c0).values
                    obs = float(diff.mean())
                    rs = np.random.default_rng(SEED)
                    signs = rs.choice([-1.0, 1.0], size=(nperm, len(diff)))
                    null = (signs * diff).mean(axis=1)
                    p = float((np.abs(null) >= abs(obs) - 1e-12).mean())
                    res.append({"model": model, "arch": arch, "cond": cond,
                                "outcome": k, "n_scenarios": len(diff),
                                "mean_diff": obs,
                                "ci_lo": float(np.percentile(diff, 2.5)),
                                "ci_hi": float(np.percentile(diff, 97.5)),
                                "p_raw": p})
    t = pd.DataFrame(res)
    # Benjamini-Hochberg within the outcome family
    t = t.sort_values("p_raw").reset_index(drop=True)
    n = len(t)
    t["p_bh"] = (t.p_raw * n / (t.index + 1)).cummin().clip(upper=1.0)
    t.to_csv(TAB/"table23_s3_contrasts.csv", index=False)

    print(f"\n{n} contrasts tested. Significant after BH at 0.05: "
          f"{(t.p_bh < 0.05).sum()}")

    # ---- 7.4 variance rule: if replicate noise exceeds between-condition
    # variance, the pre-specified decision is to report no effect regardless
    # of any single p-value.
    vd = []
    for k in OUTCOMES:
        bc = base.groupby(["scenario_id", "cond"])[k].mean().unstack()
        v_cond = float(bc.var(axis=1, ddof=1).mean())
        v_rep = float(base.groupby(["scenario_id", "cond"])[k].var(ddof=1).mean())
        vd.append({"outcome": k, "between_condition_var": v_cond,
                   "within_cell_replicate_var": v_rep,
                   "ratio": v_cond / v_rep if v_rep else float("nan")})
    v = pd.DataFrame(vd)
    v.to_csv(TAB/"table24_s3_variance.csv", index=False)
    print("\nVariance decomposition (gpt-5.6-luna, S1):")
    print(v.round(4).to_string(index=False))
    print(f"outcomes where replicate noise dominates: "
          f"{(v.ratio < 1).sum()} of {len(v)}")
    print("\nTen smallest p-values:")
    print(t.head(10)[["model","arch","cond","outcome","n_scenarios",
                      "mean_diff","p_raw","p_bh"]].to_string(index=False))

if __name__ == "__main__":
    main()
