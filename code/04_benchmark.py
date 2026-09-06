"""
Calibrate scenario budgets to the observed market, build feasible sets and Pareto
frontiers, and evaluate the two pre-registered design checks from Sec. 5.5.

DESIGN CHECK A: median |F_i| >= 10. If it fails, the budget grid is mis-calibrated
                and must be redrawn BEFORE any model call.
DESIGN CHECK B: median Pareto frontier size > 2. If it fails, rent and commute are
                too tightly coupled for strict dominance to discriminate, and we
                must widen the pool or add a dominance dimension.
"""
import json, random, sys
import numpy as np, pandas as pd
sys.path.insert(0, "code")
from common import FINAL, INTERIM, OUT, SEED
import importlib.util as u
_s = u.spec_from_file_location("sc", "code/02_build_scenarios.py")
sc = u.module_from_spec(_s); _s.loader.exec_module(sc)

POOL_N, POOL_FEASIBLE, POOL_INFEASIBLE = 120, 40, 80

def pareto_frontier(rent, commute, beds):
    """Indices of rows not strictly dominated (cheaper AND faster AND >= beds)."""
    n = len(rent); keep = np.ones(n, bool)
    order = np.lexsort((commute, rent))
    for i in order:
        if not keep[i]: continue
        dom = (rent <= rent[i]) & (commute <= commute[i]) & (beds >= beds[i])
        strict = (rent < rent[i]) | (commute < commute[i]) | (beds > beds[i])
        if (dom & strict).any(): keep[i] = False
    return np.where(keep)[0]

def main():
    lst = pd.read_csv(FINAL/"listings.csv")
    rng = random.Random(SEED)
    cells = sc.assign_names(sc.build_grid(rng), rng)

    # budget calibration: percentile of rents for the SAME bedroom count
    cuts = {b: lst.loc[lst.bedrooms == b, "rent"].quantile([.25,.5,.75]) for b in [0,1,2]}
    for c in cells:
        c["budget_usd"] = int(round(cuts[c["bedrooms"]].loc[c["budget_pctl"]/100]/50)*50)

    rows = []
    for c in cells:
        cc = f"commute_{c['work_anchor']}"
        elig = lst[lst[cc].notna()]
        feas = elig[(elig.rent <= c["budget_usd"]) &
                    (elig.bedrooms >= c["bedrooms"]) &
                    (elig[cc] <= c["max_commute"])]
        # pool feasible sample: frontier is always retained, then fill to 40
        if len(feas):
            fr = pareto_frontier(feas.rent.values, feas[cc].values, feas.bedrooms.values)
            fr_ids = set(feas.iloc[fr].id)
            rest = [i for i in feas.id if i not in fr_ids]
            r2 = random.Random(c["pool_order_seed"])
            r2.shuffle(rest)
            pool_f = list(fr_ids)[:POOL_FEASIBLE] + rest[:max(0, POOL_FEASIBLE-len(fr_ids))]
            pf = feas[feas.id.isin(set(pool_f))]
            pfr = pareto_frontier(pf.rent.values, pf[cc].values, pf.bedrooms.values)
        else:
            pf, pfr, fr = feas, np.array([]), np.array([])
        rows.append(dict(
            scenario_id=c["scenario_id"], bedrooms=c["bedrooms"], anchor=c["work_anchor"],
            max_commute=c["max_commute"], budget_pctl=c["budget_pctl"],
            budget_usd=c["budget_usd"], priority=c["priority"], specificity=c["specificity"],
            n_eligible=len(elig), n_feasible_universe=len(feas),
            frontier_universe=len(fr), n_feasible_pool=len(pf), frontier_pool=len(pfr),
            min_rent_feas=feas.rent.min() if len(feas) else np.nan,
            med_rent_feas=feas.rent.median() if len(feas) else np.nan,
            min_commute_feas=feas[cc].min() if len(feas) else np.nan,
        ))
    bm = pd.DataFrame(rows)
    bm.to_csv(INTERIM/"benchmark_scenarios.csv", index=False)

    print("=== TABLE 5. Feasible-set descriptives across 150 scenarios ===")
    print(bm[["n_feasible_universe","frontier_universe","n_feasible_pool","frontier_pool",
              "budget_usd","min_rent_feas","min_commute_feas"]]
          .describe(percentiles=[.05,.25,.5,.75,.95]).round(1).to_string())

    a_med = bm.n_feasible_universe.median(); a_bad = int((bm.n_feasible_universe < 10).sum())
    b_med = bm.frontier_pool.median()
    print("\n=== PRE-REGISTERED DESIGN CHECKS (Sec. 5.5) ===")
    print(f"  CHECK A  median |F_i| = {a_med:.0f}  (require >= 10)   "
          f"{'PASS' if a_med>=10 else 'FAIL'}   [{a_bad}/150 scenarios below 10]")
    print(f"  CHECK B  median Pareto frontier in pool = {b_med:.0f}  (require > 2)   "
          f"{'PASS' if b_med>2 else 'FAIL'}")

    print("\nby budget percentile:")
    print(bm.groupby("budget_pctl")[["n_feasible_universe","frontier_pool"]].median().to_string())
    print("\nby max_commute:")
    print(bm.groupby("max_commute")[["n_feasible_universe","frontier_pool"]].median().to_string())
    print("\nby bedrooms:")
    print(bm.groupby("bedrooms")[["budget_usd","n_feasible_universe","frontier_pool"]].median().to_string())
    return bm, lst

if __name__ == "__main__":
    bm, lst = main()
    # coverage bias of the subway-unreachable exclusion
    import json as J
    log = J.load(open(FINAL/"build_log.json"))
    print("\n=== Coverage: what the 800m subway filter removed ===")
    print(f"  subway access: {log['subway_coverage']}")
