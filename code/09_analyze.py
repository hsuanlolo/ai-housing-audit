"""Primary analysis. Randomization inference for identity contrasts."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0,"code")
from common import OUT, INTERIM

rng = np.random.default_rng(20260823)
FLOOR = {"violation":0.666,"dominance":0.551,"rent_gap":261.0,"commute_gap":10.2}

rs=[json.loads(l) for l in open(OUT/"audit_log.jsonl")]
df=pd.DataFrame(rs)
df=df[df.parse_ok==True].copy()
print(f"usable calls: {len(df)}   models: {dict(df.model.value_counts())}")
print(f"scenarios: {df.scenario_id.nunique()}   parse failures excluded: {len(rs)-len(df)}\n")

L=df[df.model=="gpt-5.6-luna"]; S=df[df.model=="gpt-5.6-sol"]

print("="*78)
print("TABLE 6. Constraint fidelity by architecture (gpt-5.6-luna, full grid)")
print("="*78)
t6=L.groupby("arch").agg(n=("violation","size"), violation=("violation","mean"),
    over_budget=("v_budget","mean"), under_beds=("v_beds","mean"),
    over_commute=("v_commute","mean")).round(4)
print(t6.to_string())
print(f"\n  random chance floor: {FLOOR['violation']:.1%}")

print("\n"+"="*78)
print("TABLE 7. Forgone opportunity by architecture (gpt-5.6-luna)")
print("="*78)
t7=L.groupby("arch").agg(n=("dominance","size"), dominance=("dominance","mean"),
    rent_gap=("rent_gap","mean"), commute_gap=("commute_gap","mean"),
    pct_rent=("pct_rent","mean")).round(3)
print(t7.to_string())
print(f"\n  floors: dominance {FLOOR['dominance']:.1%}  rent_gap ${FLOOR['rent_gap']:.0f}  commute_gap {FLOOR['commute_gap']:.1f}min")

print("\n"+"="*78)
print("HEADLINE. Rent gap by STATED priority (S1 direct, luna)")
print("="*78)
s1=L[L.arch=="S1"]
h=s1.groupby("priority").agg(n=("rent_gap","size"), rent_gap=("rent_gap","mean"),
    rent_gap_med=("rent_gap","median"), commute_gap=("commute_gap","mean"),
    dominance=("dominance","mean")).round(1)
print(h.to_string())

print("\n"+"="*78)
print("MODEL COMPARISON. luna vs sol, S1 only, common 60 scenarios")
print("="*78)
common=set(S.scenario_id)
cmp=pd.concat([L[(L.arch=="S1")&(L.scenario_id.isin(common))].assign(m="gpt-5.6-luna"),
               S.assign(m="gpt-5.6-sol")])
print(cmp.groupby("m").agg(n=("dominance","size"), violation=("violation","mean"),
    dominance=("dominance","mean"), rent_gap=("rent_gap","mean"),
    commute_gap=("commute_gap","mean")).round(3).to_string())
print("\n  by stated priority:")
print(cmp.groupby(["m","priority"])["rent_gap"].agg(["mean","size"]).round(0).to_string())

# ---------------- randomization inference ----------------
def perm_test(d, metric, a, b, nperm=10000):
    """Within-scenario paired contrast, identity labels permuted within scenario."""
    piv=(d[d.cond.isin([a,b])].groupby(["scenario_id","cond"])[metric].mean().unstack())
    piv=piv.dropna()
    if len(piv)<5: return None
    obs=(piv[a]-piv[b]).mean()
    diffs=(piv[a]-piv[b]).values
    signs=rng.choice([-1,1],size=(nperm,len(diffs)))
    null=(signs*diffs).mean(axis=1)
    p=(np.abs(null)>=abs(obs)).mean()
    lo,hi=np.percentile(diffs,[2.5,97.5])
    return dict(n=len(piv), obs=obs, p=p, ci_lo=lo, ci_hi=hi)

print("\n"+"="*78)
print("TABLE 8. Identity contrasts — within-scenario, randomization inference")
print("="*78)
CONDS=["C0_neutral","C1_name_a","C2_name_b","C3_voucher"]
rows=[]
for arch in ["S1","S2","S3"]:
    d=L[L.arch==arch]
    for metric in ["dominance","rent_gap","commute_gap","violation"]:
        for b in CONDS[1:]:
            r=perm_test(d,metric,b,"C0_neutral")
            if r: rows.append(dict(arch=arch,metric=metric,contrast=f"{b} - C0",**r))
t8=pd.DataFrame(rows)
# Benjamini-Hochberg within metric family
t8["p_adj"]=np.nan
for m in t8.metric.unique():
    idx=t8.index[t8.metric==m]
    p=t8.loc[idx,"p"].values; o=np.argsort(p); r=np.empty_like(o); r[o]=np.arange(1,len(p)+1)
    t8.loc[idx,"p_adj"]=np.minimum(1, p*len(p)/r)
print(t8.round(4).to_string(index=False))
sig=t8[t8.p_adj<0.05]
print(f"\n  significant after BH correction: {len(sig)} of {len(t8)}")
if len(sig): print(sig.round(4).to_string(index=False))

print("\n"+"="*78)
print("TABLE 9. Variance decomposition (S1, luna)")
print("="*78)
for metric in ["dominance","rent_gap"]:
    d=L[L.arch=="S1"]
    v_scen=d.groupby("scenario_id")[metric].mean().var()
    v_cond=d.groupby("cond")[metric].mean().var()
    v_rep=d.groupby(["scenario_id","cond"])[metric].var().mean()
    print(f"  {metric:12s} between-scenario {v_scen:10.2f}   between-condition {v_cond:8.4f}   "
          f"within-cell(replicate) {v_rep:10.2f}")
    print(f"               -> condition effect {'EXCEEDS' if v_cond>v_rep else 'IS SMALLER THAN'} replicate noise")

print("\n"+"="*78)
print("TABLE 11. Refusal / withholding")
print("="*78)
print(L.groupby("cond").agg(refusal=("refusal","mean"), n=("refusal","size")).round(4).to_string())

t6.to_csv(OUT/"table6_violation.csv"); t7.to_csv(OUT/"table7_opportunity.csv")
h.to_csv(OUT/"table_headline_priority.csv"); t8.to_csv(OUT/"table8_identity.csv",index=False)
print(f"\ntables written to {OUT}")
