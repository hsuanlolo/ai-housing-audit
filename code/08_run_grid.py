"""
Parallel grid runner. Pools are built once per scenario and shared across the
four identity conditions -- which is also the design requirement, since the pool
and its ordering must be byte-identical across conditions for the within-scenario
contrast to be valid.
"""
import argparse, json, random, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
sys.path.insert(0, "code")
from common import FINAL, INTERIM, OUT, SEED
import providers
import importlib.util as u
_a=u.spec_from_file_location("ad","code/07_audit.py"); ad=u.module_from_spec(_a); _a.loader.exec_module(ad)
_s=u.spec_from_file_location("sc","code/02_build_scenarios.py"); sc=u.module_from_spec(_s); _s.loader.exec_module(sc)

LOG = OUT/"audit_log.jsonl"
_wlock = threading.Lock()
_stop  = threading.Event()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenarios", type=int, default=150)
    ap.add_argument("--arch", default="S1,S2,S3")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--model", default="gpt-5.6-luna")
    ap.add_argument("--ceiling", type=float, default=15.0)
    ap.add_argument("--workers", type=int, default=6)
    a=ap.parse_args()

    lst=pd.read_csv(FINAL/"listings.csv")
    scen=pd.read_csv(INTERIM/"benchmark_scenarios.csv")
    rng=random.Random(SEED); cells=sc.assign_names(sc.build_grid(rng),rng)
    seeds={c["scenario_id"]:c["pool_order_seed"] for c in cells}
    cellmap={c["scenario_id"]:c for c in cells}
    scen["pool_order_seed"]=scen.scenario_id.map(seeds)

    done=set()
    if LOG.exists():
        for line in open(LOG):
            try:
                r=json.loads(line)
                if r.get("model")==a.model:
                    done.add((r["scenario_id"],r["arch"],r["cond"],r["rep"]))
            except Exception: pass

    # Build every pool once. Same pool object serves all 4 identity conditions.
    print("building candidate pools ...", flush=True)
    pools={}
    for _,c in scen.head(a.scenarios).iterrows():
        cc=f"commute_{c.anchor}"
        try: pool=ad.build_pool(lst,c,cc)
        except Exception as e: print(f"  skip {c.scenario_id}: {e}"); continue
        if pool is None: continue
        pool["feasible"]=((pool.rent<=c.budget_usd)&(pool.bedrooms>=c.bedrooms)&(pool[cc]<=c.max_commute))
        pool["budget_usd"]=c.budget_usd; pool["req_beds"]=c.bedrooms; pool["max_commute"]=c.max_commute
        pools[c.scenario_id]=(pool,cc,c)
    print(f"pools built: {len(pools)}", flush=True)

    tasks=[]
    for sid,(pool,cc,c) in pools.items():
        for arch in a.arch.split(","):
            for cond in sc.CONDITIONS:
                for rep in range(a.reps):
                    if (sid,arch,cond,rep) not in done: tasks.append((sid,arch,cond,rep))
    est=providers.PRICES[a.model]
    print(f"tasks: {len(tasks)}   already done: {len(done)}   ceiling ${a.ceiling}", flush=True)
    providers.status()

    counter={"n":0,"ok":0}
    def work(t):
        sid,arch,cond,rep=t
        if _stop.is_set(): return
        pool,cc,c=pools[sid]
        cell=dict(cellmap[sid]); cell["budget_usd"]=int(c.budget_usd)
        request_text=sc.render_request(cell,int(c.budget_usd),cond)
        prompt=ad.render(arch,request_text,pool,cc)
        try:
            resp=ad.call(a.model,prompt,a.ceiling)
        except providers.SpendCeilingExceeded as e:
            print(f"!! {e}", flush=True); _stop.set(); return
        rec=dict(scenario_id=sid,arch=arch,cond=cond,rep=rep,model=a.model,
                 ts=time.strftime("%Y-%m-%dT%H:%M:%S"),pool_n=len(pool),
                 n_feasible=int(pool.feasible.sum()),priority=c.priority,
                 bedrooms=int(c.bedrooms),budget=int(c.budget_usd),
                 max_commute=int(c.max_commute),anchor=c.anchor)
        if "error" in resp:
            rec.update(error=str(resp["error"])[:250],parse_ok=False)
        else:
            rec.update(in_tok=resp["in_tok"],out_tok=resp["out_tok"],cached=resp["cached"],
                       usd=resp["usd"],cum_usd=resp["cum_usd"],finish=resp.get("finish"),
                       refusal=bool(ad.REFUSAL.search((resp["text"] or "")[:600])),
                       raw=(resp["text"] or "")[:400])
            d=ad.parse({"content":resp["text"],"reasoning":resp["reasoning"]})
            if d:
                picks=[str(p.get("id","")).strip().upper() for p in d["picks"]][:5]
                valid=[p for p in picks if p in set(pool.sid)]
                rec.update(picks=picks,n_valid=len(valid)); rec["parse_ok"]=len(valid)>0
                s=ad.score(pool,valid,cc,c.priority) if valid else None
                if s: rec.update(s)
            else: rec.update(parse_ok=False)
        with _wlock:
            with open(LOG,"a") as fh: fh.write(json.dumps(rec,default=str)+"\n")
            counter["n"]+=1; counter["ok"]+=1 if rec.get("parse_ok") else 0
            if counter["n"]%50==0:
                print(f"  {counter['n']}/{len(tasks)}  ok={counter['ok']}  "
                      f"${rec.get('cum_usd',0):.3f}", flush=True)

    t0=time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(work, tasks))
    print(f"\ndone in {(time.time()-t0)/60:.1f} min   {counter['ok']}/{counter['n']} parsed")
    providers.status()

if __name__=="__main__": main()
