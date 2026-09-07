"""Pool-density and near-miss-ratio robustness. Dominance is sensitive to the
size and composition of the set it is scored against (Sec 6.1); this arm shows
whether the headline level is an artifact of N=120 with a 2:1 infeasible ratio."""
import argparse, json, random, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd
sys.path.insert(0,"code")
from common import FINAL, INTERIM, OUT, SEED
import providers
import importlib.util as u
_a=u.spec_from_file_location("ad","code/07_audit.py"); ad=u.module_from_spec(_a); _a.loader.exec_module(ad)
_s=u.spec_from_file_location("sc","code/02_build_scenarios.py"); sc=u.module_from_spec(_s); _s.loader.exec_module(sc)
_b=u.spec_from_file_location("bm","code/04_benchmark.py"); bm=u.module_from_spec(_b); _b.loader.exec_module(bm)
LOG=OUT/"pool_density.jsonl"; _lk=threading.Lock()

# (total N, share of pool that is infeasible)
CONFIGS=[(120,0.667),(120,0.50),(120,0.25),(60,0.667),(60,0.50)]

def build(lst,c,cc,N,infeas_share):
    rng=random.Random(int(c.pool_order_seed))
    elig=lst[lst[cc].notna()]
    feas=elig[(elig.rent<=c.budget_usd)&(elig.bedrooms>=c.bedrooms)&(elig[cc]<=c.max_commute)]
    if len(feas)<10: return None
    n_inf=int(round(N*infeas_share)); n_f=N-n_inf
    fr=bm.pareto_frontier(feas.rent.values,feas[cc].values,feas.bedrooms.values)
    front=list(feas.iloc[fr].id)[:n_f]
    rest=[i for i in feas.id if i not in set(front)]; rng.shuffle(rest)
    pf=front+rest[:max(0,n_f-len(front))]
    ob=elig[(elig.rent>c.budget_usd)&(elig.rent<=c.budget_usd*1.2)&(elig.bedrooms>=c.bedrooms)&(elig[cc]<=c.max_commute)]
    ur=elig[(elig.rent<=c.budget_usd)&(elig.bedrooms==c.bedrooms-1)&(elig[cc]<=c.max_commute)]
    oc=elig[(elig.rent<=c.budget_usd)&(elig.bedrooms>=c.bedrooms)&(elig[cc]>c.max_commute)&(elig[cc]<=c.max_commute+15)]
    q=[(ob,n_inf//2),(ur,0),(oc,n_inf-n_inf//2)] if c.bedrooms==0 else \
      [(ob,n_inf//3),(ur,n_inf//3),(oc,n_inf-2*(n_inf//3))]
    inf=[]
    for src,n in q:
        if n<=0: continue
        ids=list(src.id); rng.shuffle(ids); inf+=ids[:n]
    ids=list(dict.fromkeys(pf+inf)); rng.shuffle(ids)
    pool=lst[lst.id.isin(set(ids))].copy()
    pool=pool.set_index("id").reindex([i for i in ids if i in set(pool.id)]).reset_index()
    pool=pool[pool.rent.notna()].reset_index(drop=True)
    if len(pool)<30: return None
    pool["sid"]=[f"L{i+1:03d}" for i in range(len(pool))]
    pool["feasible"]=((pool.rent<=c.budget_usd)&(pool.bedrooms>=c.bedrooms)&(pool[cc]<=c.max_commute))
    pool["budget_usd"]=c.budget_usd; pool["req_beds"]=c.bedrooms; pool["max_commute"]=c.max_commute
    return pool

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenarios",type=int,default=80); ap.add_argument("--reps",type=int,default=2)
    ap.add_argument("--model",default="gpt-5.6-luna"); ap.add_argument("--ceiling",type=float,default=19.0)
    ap.add_argument("--workers",type=int,default=8)
    a=ap.parse_args()
    lst=pd.read_csv(FINAL/"listings.csv"); scen=pd.read_csv(INTERIM/"benchmark_scenarios.csv")
    rng=random.Random(SEED); cells=sc.assign_names(sc.build_grid(rng),rng)
    scen["pool_order_seed"]=scen.scenario_id.map({c["scenario_id"]:c["pool_order_seed"] for c in cells})
    done=set()
    if LOG.exists():
        for l in open(LOG):
            try:
                r=json.loads(l); done.add((r["scenario_id"],r["N"],r["infeas_share"],r["rep"]))
            except Exception: pass
    rows=[]
    for _,c in scen.head(a.scenarios).iterrows():
        cc=f"commute_{c.anchor}"
        for N,sh in CONFIGS:
            p=build(lst,c,cc,N,sh)
            if p is None: continue
            for r in range(a.reps):
                if (c.scenario_id,N,sh,r) not in done: rows.append((c,cc,p,N,sh,r))
    print(f"tasks: {len(rows)}  est ${len(rows)*0.001:.2f}",flush=True)
    cnt={"n":0}
    def work(t):
        c,cc,pool,N,sh,rep=t
        cell=dict([x for x in cells if x["scenario_id"]==c.scenario_id][0]); cell["budget_usd"]=int(c.budget_usd)
        prompt=ad.render("S1",sc.render_request(cell,int(c.budget_usd),"C0_neutral"),pool,cc)
        try: resp=ad.call(a.model,prompt,a.ceiling)
        except providers.SpendCeilingExceeded as e: print(f"!! {e}",flush=True); return
        rec=dict(scenario_id=c.scenario_id,N=N,infeas_share=sh,rep=rep,model=a.model,
                 pool_n=len(pool),n_feasible=int(pool.feasible.sum()),priority=c.priority)
        if "error" in resp: rec.update(parse_ok=False,error=str(resp["error"])[:150])
        else:
            d=ad.parse({"content":resp["text"],"reasoning":resp["reasoning"]})
            rec.update(usd=resp["usd"])
            if d:
                picks=[str(x.get("id","")).strip().upper() for x in d["picks"]][:5]
                valid=[x for x in picks if x in set(pool.sid)]
                rec["parse_ok"]=len(valid)>0
                if valid:
                    s2=ad.score(pool,valid,cc,c.priority)
                    if s2: rec.update(s2)
            else: rec["parse_ok"]=False
        with _lk:
            with open(LOG,"a") as fh: fh.write(json.dumps(rec,default=str)+"\n")
            cnt["n"]+=1
            if cnt["n"]%150==0: print(f"  {cnt['n']}/{len(rows)}",flush=True)
    with ThreadPoolExecutor(max_workers=a.workers) as ex: list(ex.map(work,rows))
    print("done",flush=True)
if __name__=="__main__": main()
