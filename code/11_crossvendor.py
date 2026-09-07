"""Cross-vendor analysis: three models, S1 direct, common scenarios."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0,"code")
from common import OUT
rng=np.random.default_rng(20260823)
TAB=OUT/"tables"; TAB.mkdir(exist_ok=True)
FLOOR={"violation":.666,"dominance":.551,"rent_gap":261.,"commute_gap":10.2}

rs=[json.loads(l) for l in open(OUT/"audit_log.jsonl")]
df=pd.DataFrame([r for r in rs if r.get("parse_ok")])
C=df[df.model=="claude-opus-5"]; S=df[df.model=="gpt-5.6-sol"]
L=df[(df.model=="gpt-5.6-luna")&(df.arch=="S1")]
common=set(C.scenario_id)&set(S.scenario_id)&set(L.scenario_id)
print(f"common scenarios across all three models: {len(common)}")
cmp=pd.concat([L[L.scenario_id.isin(common)],S[S.scenario_id.isin(common)],
               C[C.scenario_id.isin(common)]])
ORDER=["gpt-5.6-luna","gpt-5.6-sol","claude-opus-5"]

print("\n"+"="*76)
print("TABLE 13. Cross-vendor comparison, S1 direct, common scenarios")
print("="*76)
t13=cmp.groupby("model").agg(n=("dominance","size"),violation=("violation","mean"),
    dominance=("dominance","mean"),rent_gap=("rent_gap","mean"),
    commute_gap=("commute_gap","mean"),refusal=("refusal","mean")).reindex(ORDER).round(3)
print(t13.to_string())
print(f"\n  chance floor: violation {FLOOR['violation']:.1%}  dominance {FLOOR['dominance']:.1%}  "
      f"rent_gap ${FLOOR['rent_gap']:.0f}  commute_gap {FLOOR['commute_gap']:.1f}min")
t13.to_csv(TAB/"table13_crossvendor.csv"); (TAB/"table13_crossvendor.md").write_text(t13.to_markdown())

print("\n"+"="*76)
print("TABLE 14. Preference infidelity by stated priority — does it replicate?")
print("="*76)
t14=cmp.pivot_table(index="priority",columns="model",values="rent_gap",aggfunc="mean")[ORDER].round(0)
t14.loc["_n per cell"]=cmp.pivot_table(index="priority",columns="model",
    values="rent_gap",aggfunc="size")[ORDER].iloc[0]
print(t14.to_string())
t14.to_csv(TAB/"table14_priority_crossvendor.csv")
(TAB/"table14_priority_crossvendor.md").write_text(t14.to_markdown())

def perm(d,metric,a,b,n=10000):
    piv=d[d.cond.isin([a,b])].groupby(["scenario_id","cond"])[metric].mean().unstack().dropna()
    if len(piv)<5: return None
    diffs=(piv[a]-piv[b]).values; obs=diffs.mean()
    null=(rng.choice([-1,1],size=(n,len(diffs)))*diffs).mean(axis=1)
    lo,hi=np.percentile(diffs,[2.5,97.5])
    return dict(n=len(piv),obs=obs,p=(np.abs(null)>=abs(obs)).mean(),ci_lo=lo,ci_hi=hi)

print("\n"+"="*76)
print("TABLE 15. Identity contrasts on claude-opus-5 (randomization inference)")
print("="*76)
rows=[]
for m in ["dominance","rent_gap","commute_gap","violation"]:
    for c in ["C1_name_a","C2_name_b","C3_voucher"]:
        r=perm(C,m,c,"C0_neutral")
        if r: rows.append(dict(metric=m,contrast=f"{c} - C0",**r))
t15=pd.DataFrame(rows)
for m in t15.metric.unique():
    i=t15.index[t15.metric==m]; p=t15.loc[i,"p"].values
    o=np.argsort(p); rk=np.empty_like(o); rk[o]=np.arange(1,len(p)+1)
    t15.loc[i,"p_adj"]=np.minimum(1,p*len(p)/rk)
print(t15.round(4).to_string(index=False))
print(f"\n  significant after BH: {int((t15.p_adj<0.05).sum())} of {len(t15)}")
t15.to_csv(TAB/"table15_identity_claude.csv",index=False)
(TAB/"table15_identity_claude.md").write_text(t15.round(4).to_markdown(index=False))

print("\n"+"="*76)
print("Variance decomposition, claude-opus-5")
print("="*76)
for m in ["dominance","rent_gap"]:
    v_s=C.groupby("scenario_id")[m].mean().var(); v_c=C.groupby("cond")[m].mean().var()
    v_r=C.groupby(["scenario_id","cond"])[m].var().mean()
    print(f"  {m:11s} scenario {v_s:10.2f}  condition {v_c:9.4f}  replicate {v_r:10.2f}"
          f"  -> condition {'>' if v_c>v_r else '<'} replicate noise")

print("\n"+"="*76)
print("Token / cost profile by model")
print("="*76)
print(df.groupby("model").agg(n=("in_tok","size"),in_tok=("in_tok","mean"),
    out_tok=("out_tok","mean"),usd_per_call=("usd","mean"),
    total_usd=("usd","sum")).reindex(["gpt-5.6-luna","gpt-5.6-sol","claude-opus-5"]).round(4).to_string())
