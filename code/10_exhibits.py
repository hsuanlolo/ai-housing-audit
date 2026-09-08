"""Dominance magnitude, figures, and repo-ready tables."""
import json, random, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0,"code")
from common import FINAL, INTERIM, OUT, SEED
import importlib.util as u
_a=u.spec_from_file_location("ad","code/07_audit.py"); ad=u.module_from_spec(_a); _a.loader.exec_module(ad)
_s=u.spec_from_file_location("sc","code/02_build_scenarios.py"); sc=u.module_from_spec(_s); _s.loader.exec_module(sc)
_b=u.spec_from_file_location("bm","code/04_benchmark.py"); bm=u.module_from_spec(_b); _b.loader.exec_module(bm)

TAB=OUT/"tables"; FIG=OUT/"figures"; TAB.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
def dump(df,name,idx=True):
    df.to_csv(TAB/f"{name}.csv",index=idx)
    (TAB/f"{name}.md").write_text(df.to_markdown(index=idx))

lst=pd.read_csv(FINAL/"listings.csv"); scen=pd.read_csv(INTERIM/"benchmark_scenarios.csv")
rng=random.Random(SEED); cells=sc.assign_names(sc.build_grid(rng),rng)
scen["pool_order_seed"]=scen.scenario_id.map({c["scenario_id"]:c["pool_order_seed"] for c in cells})
rs=[json.loads(l) for l in open(OUT/"audit_log.jsonl")]
df=pd.DataFrame([r for r in rs if r.get("parse_ok")])

# ---- dominance magnitude: for each dominated pick, gap to its best dominator
print("computing dominance magnitude ...")
pools={}
for _,c in scen.iterrows():
    cc=f"commute_{c.anchor}"
    try: p=ad.build_pool(lst,c,cc)
    except Exception: continue
    if p is None: continue
    p["feasible"]=((p.rent<=c.budget_usd)&(p.bedrooms>=c.bedrooms)&(p[cc]<=c.max_commute))
    pools[c.scenario_id]=(p,cc)

mag=[]
for r in df.itertuples():
    if r.scenario_id not in pools or not isinstance(r.picks,list): continue
    p,cc=pools[r.scenario_id]; f=p[p.feasible]
    if not len(f): continue
    sel=f[f.sid.isin(r.picks)]
    for s in sel.itertuples():
        d=f[(f.rent<=getattr(s,"rent"))&(f[cc]<=getattr(s,cc))&(f.bedrooms>=s.bedrooms)]
        d=d[(d.rent<getattr(s,"rent"))|(d[cc]<getattr(s,cc))|(d.bedrooms>s.bedrooms)]
        if len(d):
            best=d.nsmallest(1,"rent").iloc[0]
            mag.append(dict(model=r.model,arch=r.arch,cond=r.cond,priority=r.priority,
                            d_rent=getattr(s,"rent")-best.rent,
                            d_commute=getattr(s,cc)-best[cc]))
M=pd.DataFrame(mag)
print(f"dominated picks: {len(M):,}")
t_mag=M.groupby(["model","arch"]).agg(n=("d_rent","size"),
        rent_med=("d_rent","median"), rent_p75=("d_rent",lambda x:x.quantile(.75)),
        rent_mean=("d_rent","mean"), commute_med=("d_commute","median")).round(1)
print(t_mag.to_string()); dump(t_mag,"table7b_dominance_magnitude")

# ---- tables
L=df[df.model=="gpt-5.6-luna"]; S=df[df.model=="gpt-5.6-sol"]
t6=L.groupby("arch").agg(n=("violation","size"),violation=("violation","mean"),
    over_budget=("v_budget","mean"),under_beds=("v_beds","mean"),
    over_commute=("v_commute","mean")).round(4); dump(t6,"table6_constraint_fidelity")
t7=L.groupby("arch").agg(n=("dominance","size"),dominance=("dominance","mean"),
    rent_gap=("rent_gap","mean"),commute_gap=("commute_gap","mean"),
    pct_rent=("pct_rent","mean")).round(3); dump(t7,"table7_opportunity")
hp=L[L.arch=="S1"].groupby("priority").agg(n=("rent_gap","size"),
    rent_gap_mean=("rent_gap","mean"),rent_gap_med=("rent_gap","median"),
    commute_gap=("commute_gap","mean"),dominance=("dominance","mean")).round(1)
dump(hp,"table_headline_priority")
common=set(S.scenario_id)
cm=pd.concat([L[(L.arch=="S1")&(L.scenario_id.isin(common))],S])
t_mod=cm.groupby("model").agg(n=("dominance","size"),violation=("violation","mean"),
    dominance=("dominance","mean"),rent_gap=("rent_gap","mean")).round(3)
dump(t_mod,"table_model_comparison")

# ---- Figure 2: violation vs binding constraints
L2=L.copy()
L2["n_binding"]=(L2.groupby("scenario_id")["n_feasible"].transform("first")
                 .rank(pct=True).apply(lambda q: 3 if q<.33 else (2 if q<.66 else 1)))
fig,ax=plt.subplots(figsize=(6,4))
for arch,c in zip(["S1","S2","S3"],["#c0392b","#e67e22","#2980b9"]):
    g=L2[L2.arch==arch].groupby("n_binding")["violation"].mean()
    ax.plot(g.index,g.values*100,marker="o",label=arch,color=c)
ax.axhline(66.6,ls="--",c="#7f8c8d",lw=1,label="random floor (66.6%)")
ax.set_xticks([1,2,3]); ax.set_xticklabels(["loose","medium","tight"])
ax.set_xlabel("constraint tightness (tercile of feasible-set size)")
ax.set_ylabel("violation rate (%)"); ax.set_yscale("symlog"); ax.legend(frameon=False,fontsize=8)
ax.set_title("Figure 2. Constraint violation by tightness",fontsize=11); ax.grid(alpha=.25,lw=.5)
fig.tight_layout(); fig.savefig(FIG/"figure2_violation.png",dpi=170)

# ---- Figure 3: dollars forgone
fig,axes=plt.subplots(1,2,figsize=(11,4))
ax=axes[0]
for arch,c in zip(["S1","S2","S3"],["#c0392b","#e67e22","#2980b9"]):
    v=M[(M.model=="gpt-5.6-luna")&(M.arch==arch)].d_rent
    ax.hist(v,bins=np.arange(0,3000,100),histtype="step",lw=1.6,color=c,label=arch,density=True)
ax.set_xlabel("$/month forgone vs. best dominating listing"); ax.set_ylabel("density")
ax.legend(frameon=False,fontsize=9); ax.set_title("(a) Per dominated recommendation",fontsize=10)
ax.grid(alpha=.25,lw=.5)
ax=axes[1]
# Panel (b) uses the WITHIN-scenario manipulation (12_priority_swap.py), not a
# grouping of scenarios by their own stated priority. The latter is the
# comparison retracted in 8.3: the scenarios differ and the oracle moves with
# the condition, so responsiveness and selection are not separable. Here the
# scenario, the pool, the ordering and the oracle are all held fixed and one
# sentence changes, so the between-box shift IS responsiveness and the distance
# from the zero line is the residual gap no wording closes.
_sw=[json.loads(l) for l in open(OUT/"priority_swap.jsonl") if l.strip()]
_sw=[r for r in _sw if r.get("parse_ok") and r.get("rent_gap") is not None]
order=["P_commute","P_rent","P_explicit"]
data=[[r["rent_gap"] for r in _sw if r["priority_cond"]==p] for p in order]
bp=ax.boxplot(data,labels=["commute\nfirst","rent\nfirst","rent first,\nexplicit"],
              showfliers=False,patch_artist=True)
for b in bp["boxes"]: b.set_facecolor("#d5dbdb")
ax.axhline(0,ls="-",c="#2c3e50",lw=1.1,label="oracle (5 cheapest feasible)")
for i,d in enumerate(data,start=1):
    ax.plot(i,np.median(d),marker="D",ms=5,color="#c0392b",zorder=5)
ax.set_ylabel("rent gap vs. fixed oracle ($/month)"); ax.legend(frameon=False,fontsize=8)
ax.set_title("(b) Within-scenario priority manipulation",fontsize=10)
ax.grid(alpha=.25,lw=.5,axis="y")
for _p,_d in zip(order,data):
    print(f"  fig3b {_p:12s} n={len(_d):4d} median gap ${np.median(_d):8.2f}")
fig.suptitle("Figure 3. Priced opportunity loss",fontsize=12)
fig.tight_layout(); fig.savefig(FIG/"figure3_opportunity.png",dpi=170,bbox_inches="tight")
print(f"\nfigures -> {FIG}\ntables  -> {TAB}")
