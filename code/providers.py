"""
Model providers with a persistent cost ledger and a hard spend ceiling.

The ceiling is enforced mechanically before every call. It exists because a
token estimate can be wrong -- earlier in this project an Anthropic cost estimate
was off by ~3x -- and a wrong estimate must not be able to turn into a wrong bill.
"""
import json, os, re, time, datetime, pathlib, threading
from common import OUT, load_key

LEDGER = OUT/"spend_ledger.json"
_LOCK = threading.Lock()   # ledger is read-modify-write; threads must serialize

# USD per 1M tokens: (input, cached_input, output). Verified against the
# providers' own pricing pages on 2026-08-25.
PRICES = {
    "gpt-5.6-luna":       (0.20, 0.02, 1.20),
    "gpt-5.6-terra":      (2.00, 0.20, 12.00),
    "gpt-5.6-sol":        (4.00, 0.40, 20.00),
    "openai/gpt-oss-120b":(0.00, 0.00, 0.00),   # Groq free tier
}
PROVIDER_OF = {m: ("groq" if m.startswith("openai/") else "openai") for m in PRICES}

def _load():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {"calls": [], "total_usd": 0.0}

def spent():
    return _load()["total_usd"]

def price(model, pt, ct, cached=0):
    pin, pcache, pout = PRICES[model]
    fresh = max(0, pt - cached)
    return (fresh*pin + cached*pcache + ct*pout) / 1e6

def record(model, pt, ct, cached, usd):
  with _LOCK:
    d = _load()
    d["calls"].append({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                       "model": model, "in": pt, "cached": cached, "out": ct, "usd": round(usd, 6)})
    d["total_usd"] = round(d["total_usd"] + usd, 6)
    LEDGER.write_text(json.dumps(d, indent=2))
    return d["total_usd"]

class SpendCeilingExceeded(RuntimeError): pass

def check_ceiling(ceiling):
    s = spent()
    if s >= ceiling:
        raise SpendCeilingExceeded(f"spend ceiling hit: ${s:.4f} >= ${ceiling:.2f}")
    return s

# ---------------------------------------------------------------- OpenAI
def call_openai(model, prompt, max_out=2200):
    import openai
    c = openai.OpenAI(api_key=load_key("openai"))
    r = c.chat.completions.create(model=model,
            messages=[{"role":"user","content":prompt}],
            max_completion_tokens=max_out)
    u = r.usage
    cached = 0
    try: cached = u.prompt_tokens_details.cached_tokens or 0
    except Exception: pass
    txt = r.choices[0].message.content or ""
    return dict(text=txt, reasoning="", in_tok=u.prompt_tokens, out_tok=u.completion_tokens,
                cached=cached, finish=r.choices[0].finish_reason)

# ---------------------------------------------------------------- Groq
def call_groq(model, prompt, max_out=2200):
    import requests
    H={"Authorization":f"Bearer {load_key('groq')}","Content-Type":"application/json"}
    r=requests.post("https://api.groq.com/openai/v1/chat/completions",headers=H,
        json={"model":model,"messages":[{"role":"user","content":prompt}],
              "temperature":1.0,"max_tokens":max_out,"reasoning_effort":"low"},timeout=240)
    if r.status_code!=200:
        return dict(error=r.text[:300], status=r.status_code,
                    retry_after=r.headers.get("retry-after"))
    d=r.json(); m=d["choices"][0]["message"]; u=d["usage"]
    return dict(text=m.get("content") or "", reasoning=m.get("reasoning") or "",
                in_tok=u["prompt_tokens"], out_tok=u["completion_tokens"], cached=0,
                finish=d["choices"][0]["finish_reason"])

def call(model, prompt, ceiling, max_out=2200):
    """Priced, ledgered, ceiling-guarded model call."""
    check_ceiling(ceiling)
    fn = call_groq if PROVIDER_OF[model]=="groq" else call_openai
    res = fn(model, prompt, max_out)
    if "error" in res: return res
    usd = price(model, res["in_tok"], res["out_tok"], res["cached"])
    res["usd"] = usd
    res["cum_usd"] = record(model, res["in_tok"], res["out_tok"], res["cached"], usd)
    return res

def status():
    d=_load()
    print(f"spend ledger: ${d['total_usd']:.4f} across {len(d['calls'])} calls")
    by={}
    for c in d["calls"]:
        b=by.setdefault(c["model"],[0,0.0]); b[0]+=1; b[1]+=c["usd"]
    for m,(n,u) in by.items(): print(f"   {m:22s} {n:5d} calls  ${u:.4f}")

if __name__=="__main__": status()
