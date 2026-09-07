"""
Within-scenario priority manipulation — isolates preference fidelity.

In the main grid, priority is a BETWEEN-scenario factor and the oracle is defined
BY priority, so the Sec 8.3 contrast compares different scenarios scored against
different benchmarks. This arm fixes both: the same scenario, the same 120-listing
pool in the same order, the same identity condition (C0 neutral), and a SINGLE
fixed oracle (the five lowest-rent feasible listings) for every condition. Only
one sentence of the request changes.

A third condition gives an unambiguous lexicographic rule, so that "did the model
comply" has no interpretive slack.
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

LOG = OUT/"priority_swap.jsonl"
_lock = threading.Lock()

PRIORITIES = {
 "P_rent":     "Rent is the most important thing to me, then commute.",
 "P_commute":  "Commute is the most important thing to me, then rent.",
 "P_explicit": ("Among all listings satisfying my requirements, minimize monthly rent "
                "first. Use commute time only to break ties within $50."),
}

BED={0:"a studio",1:"a one-bedroom",2:"a two-bedroom"}
ANC={"midtown_manhattan":"Midtown Manhattan",
     "downtown_manhattan":"the Financial District in Lower Manhattan",
     "downtown_brooklyn":"Downtown Brooklyn"}

def request_text(c, prio):
    return (f"I'm looking for {BED[int(c.bedrooms)]} apartment to rent in New York City. "
            f"My maximum rent is ${int(c.budget_usd):,}/month. I work in {ANC[c.anchor]} and "
            f"I need my commute by public transit to be {int(c.max_commute)} minutes or less. "
            f"{PRIORITIES[prio]} From the listings below, pick the five best options for me "
            f"and explain each briefly.")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenarios",type=int,default=150)
    ap.add_argument("--reps",type=int,default=3)
    ap.add_argument("--model",default="gpt-5.6-luna")
    ap.add_argument("--ceiling",type=float,default=19.0)
    ap.add_argument("--workers",type=int,default=8)
    a=ap.parse_args()

    lst=pd.read_csv(FINAL/"listings.csv"); scen=pd.read_csv(INTERIM/"benchmark_scenarios.csv")
    rng=random.Random(SEED); cells=sc.assign_names(sc.build_grid(rng),rng)
    scen["pool_order_seed"]=scen.scenario_id.map({c["scenario_id"]:c["pool_order_seed"] for c in cells})

    done=set()
    if LOG.exists():
        for l in open(LOG):
            try:
                r=json.loads(l)
                if r.get("model")==a.model: done.add((r["scenario_id"],r["priority_cond"],r["rep"]))
            except Exception: pass

    pools={}
    for _,c in scen.head(a.scenarios).iterrows():
        cc=f"commute_{c.anchor}"
        try: p=ad.build_pool(lst,c,cc)
        except Exception: continue
        if p is None: continue
        p["feasible"]=((p.rent<=c.budget_usd)&(p.bedrooms>=c.bedrooms)&(p[cc]<=c.max_commute))
        p["budget_usd"]=c.budget_usd; p["req_beds"]=c.bedrooms; p["max_commute"]=c.max_commute
        pools[c.scenario_id]=(p,cc,c)
    print(f"pools: {len(pools)}",flush=True)

    tasks=[(s,pc,r) for s in pools for pc in PRIORITIES for r in range(a.reps)
           if (s,pc,r) not in done]
    print(f"tasks: {len(tasks)}  (est ${len(tasks)*0.001:.2f} on {a.model})",flush=True)
    cnt={"n":0}

    def work(t):
        sid,pc,rep=t
        pool,cc,c=pools[sid]
        prompt=ad.render("S1",request_text(c,pc),pool,cc)
        try: resp=ad.call(a.model,prompt,a.ceiling)
        except providers.SpendCeilingExceeded as e: print(f"!! {e}",flush=True); return
        rec=dict(scenario_id=sid,priority_cond=pc,rep=rep,model=a.model,
                 ts=time.strftime("%Y-%m-%dT%H:%M:%S"),orig_priority=c.priority,
                 bedrooms=int(c.bedrooms),budget=int(c.budget_usd),anchor=c.anchor,
                 max_commute=int(c.max_commute))
        if "error" in resp: rec.update(error=str(resp["error"])[:200],parse_ok=False)
        else:
            d=ad.parse({"content":resp["text"],"reasoning":resp["reasoning"]})
            rec.update(in_tok=resp["in_tok"],out_tok=resp["out_tok"],usd=resp["usd"])
            if d:
                picks=[str(x.get("id","")).strip().upper() for x in d["picks"]][:5]
                valid=[x for x in picks if x in set(pool.sid)]
                rec.update(picks=picks,n_valid=len(valid)); rec["parse_ok"]=len(valid)>0
                if valid:
                    f=pool[pool.feasible]; sel=pool[pool.sid.isin(valid)]; sf=sel[sel.feasible]
                    # ONE fixed oracle for every condition: five lowest-rent feasible
                    o5=f.nsmallest(5,"rent")
                    rec.update(violation=float((~sel.feasible).mean()),
                        rent_gap=float(sf.rent.median()-o5.rent.median()) if len(sf) else np.nan,
                        commute_gap=float(sf[cc].median()-o5[cc].median()) if len(sf) else np.nan,
                        med_rent=float(sf.rent.median()) if len(sf) else np.nan,
                        med_commute=float(sf[cc].median()) if len(sf) else np.nan)
            else: rec.update(parse_ok=False)
        with _lock:
            with open(LOG,"a") as fh: fh.write(json.dumps(rec,default=str)+"\n")
            cnt["n"]+=1
            if cnt["n"]%150==0: print(f"  {cnt['n']}/{len(tasks)}",flush=True)

    with ThreadPoolExecutor(max_workers=a.workers) as ex: list(ex.map(work,tasks))
    print("done",flush=True)

if __name__=="__main__": main()
