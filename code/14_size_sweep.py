"""
Mechanism diagnostic: does the optimization gap scale with candidate-set size?

Sec 8.8 shows the model responds correctly to a stated priority yet still leaves
~$600/month on the table, and that an unambiguous lexicographic instruction does
not help. That is consistent with several mechanisms -- attention dilution over a
long list, unstable numeric comparison, position effects, or a default preference
surviving into the output stage -- and this arm cannot separate all of them. What
it CAN do is test the scale hypothesis: hold the instruction fixed at the explicit
lexicographic rule and vary only the number of feasible candidates.

If the gap falls monotonically as the set shrinks, scale is implicated. If it is
flat, scale is not the binding constraint and no attention/search explanation is
licensed by this evidence.
"""
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
LOG=OUT/"size_sweep.jsonl"; _lk=threading.Lock()
SIZES=[10,20,40,80]            # number of FEASIBLE candidates shown
EXPLICIT=("Among all listings satisfying my requirements, minimize monthly rent "
          "first. Use commute time only to break ties within $50.")
BED={0:"a studio",1:"a one-bedroom",2:"a two-bedroom"}
ANC={"midtown_manhattan":"Midtown Manhattan","downtown_manhattan":"the Financial District in Lower Manhattan",
     "downtown_brooklyn":"Downtown Brooklyn"}

def build(lst,c,cc,n_feas):
    """Feasible listings ONLY, so the optimization task is isolated from filtering."""
    rng=random.Random(int(c.pool_order_seed))
    elig=lst[lst[cc].notna()]
    feas=elig[(elig.rent<=c.budget_usd)&(elig.bedrooms>=c.bedrooms)&(elig[cc]<=c.max_commute)]
    if len(feas)<n_feas: return None
    fr=bm.pareto_frontier(feas.rent.values,feas[cc].values,feas.bedrooms.values)
    front=list(feas.iloc[fr].id)
    cheapest=list(feas.nsmallest(5,"rent").id)          # the answer must be present
    must=list(dict.fromkeys(cheapest+front))[:n_feas]
    rest=[i for i in feas.id if i not in set(must)]; rng.shuffle(rest)
    ids=(must+rest)[:n_feas]; rng.shuffle(ids)
    pool=lst[lst.id.isin(set(ids))].copy()
    pool=pool.set_index("id").reindex([i for i in ids if i in set(pool.id)]).reset_index()
    pool=pool[pool.rent.notna()].reset_index(drop=True)
    if len(pool)<n_feas*0.8: return None
    pool["sid"]=[f"L{i+1:03d}" for i in range(len(pool))]
    pool["feasible"]=True
    pool["budget_usd"]=c.budget_usd; pool["req_beds"]=c.bedrooms; pool["max_commute"]=c.max_commute
    return pool

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenarios",type=int,default=100); ap.add_argument("--reps",type=int,default=2)
    ap.add_argument("--model",default="gpt-5.6-luna"); ap.add_argument("--ceiling",type=float,default=19.0)
    ap.add_argument("--workers",type=int,default=8)
    a=ap.parse_args()
    lst=pd.read_csv(FINAL/"listings.csv"); scen=pd.read_csv(INTERIM/"benchmark_scenarios.csv")
    rng=random.Random(SEED); cells=sc.assign_names(sc.build_grid(rng),rng)
    scen["pool_order_seed"]=scen.scenario_id.map({c["scenario_id"]:c["pool_order_seed"] for c in cells})
    done=set()
    if LOG.exists():
        for l in open(LOG):
            try: r=json.loads(l); done.add((r["scenario_id"],r["n_feas"],r["rep"]))
            except Exception: pass
    tasks=[]
    for _,c in scen.head(a.scenarios).iterrows():
        cc=f"commute_{c.anchor}"
        for nf in SIZES:
            p=build(lst,c,cc,nf)
            if p is None: continue
            for r in range(a.reps):
                if (c.scenario_id,nf,r) not in done: tasks.append((c,cc,p,nf,r))
    print(f"tasks: {len(tasks)}  est ${len(tasks)*0.0008:.2f}",flush=True)
    cnt={"n":0}
    def work(t):
        c,cc,pool,nf,rep=t
        req=(f"I'm looking for {BED[int(c.bedrooms)]} apartment to rent in New York City. "
             f"My maximum rent is ${int(c.budget_usd):,}/month. I work in {ANC[c.anchor]} and I "
             f"need my commute by public transit to be {int(c.max_commute)} minutes or less. "
             f"{EXPLICIT} From the listings below, pick the five best options for me.")
        prompt=ad.render("S3",req,pool,cc)   # all-feasible pool, filtering already done
        try: resp=ad.call(a.model,prompt,a.ceiling)
        except providers.SpendCeilingExceeded as e: print(f"!! {e}",flush=True); return
        rec=dict(scenario_id=c.scenario_id,n_feas=nf,rep=rep,model=a.model,pool_n=len(pool))
        if "error" in resp: rec.update(parse_ok=False)
        else:
            d=ad.parse({"content":resp["text"],"reasoning":resp["reasoning"]})
            rec.update(usd=resp["usd"])
            if d:
                picks=[str(x.get("id","")).strip().upper() for x in d["picks"]][:5]
                valid=[x for x in picks if x in set(pool.sid)]
                rec["parse_ok"]=len(valid)>0
                if valid:
                    sel=pool[pool.sid.isin(valid)]; o5=pool.nsmallest(5,"rent")
                    rec.update(rent_gap=float(sel.rent.median()-o5.rent.median()),
                               med_rent=float(sel.rent.median()),
                               opt_rent=float(o5.rent.median()),
                               got_cheapest=bool(pool.nsmallest(1,"rent").iloc[0].sid in set(valid)))
            else: rec["parse_ok"]=False
        with _lk:
            with open(LOG,"a") as fh: fh.write(json.dumps(rec,default=str)+"\n")
            cnt["n"]+=1
            if cnt["n"]%150==0: print(f"  {cnt['n']}/{len(tasks)}",flush=True)
    with ThreadPoolExecutor(max_workers=a.workers) as ex: list(ex.map(work,tasks))
    print("done",flush=True)
if __name__=="__main__": main()
