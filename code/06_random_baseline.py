"""
S_rand: the chance floor. Pick 5 listings uniformly at random from the candidate
pool and measure the same primary outcomes.

This establishes what every metric returns with ZERO intelligence, which is the
only way to interpret a model's score. A dominance rate near the random floor
means the model adds nothing on that dimension. Costs no API requests.
"""
import random, sys
import numpy as np, pandas as pd
sys.path.insert(0, "code")
from common import FINAL, INTERIM, OUT, SEED
import importlib.util as u
_s = u.spec_from_file_location("bm", "code/04_benchmark.py")
bm = u.module_from_spec(_s); _s.loader.exec_module(bm)

POOL_N, POOL_FEASIBLE = 120, 40
K = 5
REPS = 200   # analytic-quality estimate of the floor

def build_pool(lst, c, rng):
    cc = f"commute_{c['anchor']}"
    elig = lst[lst[cc].notna()]
    feas = elig[(elig.rent <= c["budget_usd"]) & (elig.bedrooms >= c["bedrooms"])
                & (elig[cc] <= c["max_commute"])]
    if len(feas) < 5: return None, None, cc
    fr = bm.pareto_frontier(feas.rent.values, feas[cc].values, feas.bedrooms.values)
    fr_ids = list(feas.iloc[fr].id)
    rest = [i for i in feas.id if i not in set(fr_ids)]
    rng.shuffle(rest)
    pool_f = fr_ids[:POOL_FEASIBLE] + rest[:max(0, POOL_FEASIBLE - len(fr_ids))]
    # near-miss infeasible: one violated constraint each, balanced
    over_b = elig[(elig.rent > c["budget_usd"]) & (elig.rent <= c["budget_usd"]*1.20)
                  & (elig.bedrooms >= c["bedrooms"]) & (elig[cc] <= c["max_commute"])]
    under_r = elig[(elig.rent <= c["budget_usd"]) & (elig.bedrooms == c["bedrooms"]-1)
                   & (elig[cc] <= c["max_commute"])]
    over_c = elig[(elig.rent <= c["budget_usd"]) & (elig.bedrooms >= c["bedrooms"])
                  & (elig[cc] > c["max_commute"]) & (elig[cc] <= c["max_commute"]+15)]
    # An "under-bedroom" violation is UNDEFINED for studio scenarios: there is no
    # unit with fewer than 0 bedrooms. Without redistribution, every studio pool
    # is 27 listings short and pool size becomes confounded with bedroom count --
    # which would in turn confound it with the dominance rate. Redistribute the
    # unusable slots across the two violation types that remain well defined.
    quotas = [(over_b, 27), (under_r, 27), (over_c, 26)]
    if c["bedrooms"] == 0:
        quotas = [(over_b, 40), (under_r, 0), (over_c, 40)]
    infeas = []
    for src, n in quotas:
        if n == 0: continue
        ids = list(src.id); rng.shuffle(ids); infeas += ids[:n]
    pool_ids = set(pool_f) | set(infeas)
    return lst[lst.id.isin(pool_ids)], feas[feas.id.isin(set(pool_f))], cc

def main():
    lst = pd.read_csv(FINAL/"listings.csv")
    scen = pd.read_csv(INTERIM/"benchmark_scenarios.csv")
    out = []
    for _, c in scen.iterrows():
        rng = random.Random(int(c.scenario_id[1:]) + SEED)
        pool, fpool, cc = build_pool(lst, c, rng)
        if pool is None: continue
        fr = bm.pareto_frontier(fpool.rent.values, fpool[cc].values, fpool.bedrooms.values)
        front = set(fpool.iloc[fr].id)
        feas_ids = set(fpool.id)
        oracle5 = fpool.nsmallest(5, "rent") if c.priority == "rent_first" else fpool.nsmallest(5, cc)
        pool_ids = list(pool.id)
        dom, viol, rg, cg = [], [], [], []
        for _ in range(REPS):
            pick = rng.sample(pool_ids, K)
            p = pool[pool.id.isin(pick)]
            viol.append((~p.id.isin(feas_ids)).mean())
            pf = p[p.id.isin(feas_ids)]
            dom.append(np.mean([i not in front for i in pf.id]) if len(pf) else np.nan)
            if len(pf):
                rg.append(pf.rent.median() - oracle5.rent.median())
                cg.append(pf[cc].median() - oracle5[cc].median())
        out.append(dict(scenario_id=c.scenario_id, pool_n=len(pool),
                        n_feasible_pool=len(fpool), frontier_pool=len(front),
                        violation=np.mean(viol), dominance=np.nanmean(dom),
                        rent_gap=np.nanmean(rg), commute_gap=np.nanmean(cg)))
    r = pd.DataFrame(out)
    r.to_csv(INTERIM/"random_baseline.csv", index=False)
    print(f"scenarios evaluated: {len(r)}  (pool sizes {r.pool_n.min()}-{r.pool_n.max()})")
    print("\n=== S_rand: the chance floor (200 draws per scenario) ===")
    print(f"  constraint violation rate   {r.violation.mean():.1%}")
    print(f"  pool dominance rate         {r.dominance.mean():.1%}")
    print(f"  rent gap vs oracle top-5    ${r.rent_gap.mean():+,.0f} /month")
    print(f"  commute gap vs oracle top-5 {r.commute_gap.mean():+.1f} min")
    print("\ninterpretation: any audited system whose scores sit at these values")
    print("adds nothing over chance on that dimension.")
    return r

if __name__ == "__main__":
    main()
