"""
Model providers with a persistent cost ledger and a hard spend ceiling.

The ceiling is enforced mechanically before every call. It exists because a
token estimate can be wrong -- earlier in this project an Anthropic cost estimate
was off by ~3x -- and a wrong estimate must not be able to turn into a wrong bill.
"""
import json, os, re, time, datetime, pathlib, threading, fcntl
from common import OUT, load_key

LEDGER = OUT/"spend_ledger.json"
_LOCK = threading.Lock()   # serializes threads within one process
# A threading.Lock does NOT serialize separate PROCESSES. Two concurrently running
# experiment scripts corrupted this file with interleaved read-modify-write, and
# every subsequent call failed with a JSON decode error that surfaced as a bogus
# parse failure. fcntl.flock adds the cross-process guarantee.

# USD per 1M tokens: (input, cached_input, output). Verified against the
# providers' own pricing pages on 2026-08-25.
PRICES = {
    "gpt-5.6-luna":       (0.20, 0.02, 1.20),
    "gpt-5.6-terra":      (2.00, 0.20, 12.00),
    "gpt-5.6-sol":        (4.00, 0.40, 20.00),
    "openai/gpt-oss-120b":(0.00, 0.00, 0.00),   # Groq free tier
    "claude-opus-5":      (5.00, 0.50, 25.00),
    "claude-sonnet-5":    (3.00, 0.30, 15.00),
}
def _provider(m):
    if m.startswith("openai/"): return "groq"
    if m.startswith("claude-"): return "anthropic"
    return "openai"
PROVIDER_OF = {m: _provider(m) for m in PRICES}

def _load():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {"calls": [], "total_usd": 0.0}

def spent():
    return _load()["total_usd"]

def spent_on(provider):
    """Per-provider spend. Budgets are held per vendor account, so a single
    cross-provider total is the wrong guard: OpenAI spend must not consume an
    Anthropic ceiling. This was found the hard way -- a cumulative $38 ceiling
    aborted the Claude arm at $22.58 because $15.63 of unrelated OpenAI spend
    counted against it."""
    return round(sum(c["usd"] for c in _load()["calls"]
                     if PROVIDER_OF.get(c["model"]) == provider), 6)

def price(model, pt, ct, cached=0):
    pin, pcache, pout = PRICES[model]
    fresh = max(0, pt - cached)
    return (fresh*pin + cached*pcache + ct*pout) / 1e6

def record(model, pt, ct, cached, usd):
  with _LOCK:
    LEDGER.touch(exist_ok=True)
    with open(LEDGER, "r+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            try: d = json.load(fh)
            except Exception: d = {"calls": [], "total_usd": 0.0}
            d["calls"].append({
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "model": model, "in": pt, "cached": cached, "out": ct,
                "usd": round(usd, 6)})
            d["total_usd"] = round(d["total_usd"] + usd, 6)
            fh.seek(0); fh.truncate(); json.dump(d, fh, indent=1); fh.flush()
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
    return d["total_usd"]

def _record_unused(model, pt, ct, cached, usd):
    d = _load()
    d["calls"].append({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                       "model": model, "in": pt, "cached": cached, "out": ct, "usd": round(usd, 6)})
    d["total_usd"] = round(d["total_usd"] + usd, 6)
    LEDGER.write_text(json.dumps(d, indent=2))
    return d["total_usd"]

class SpendCeilingExceeded(RuntimeError): pass

def check_ceiling(ceiling, provider=None):
    """Ceiling applies to one provider's account when given, else to the total."""
    s = spent_on(provider) if provider else spent()
    if s >= ceiling:
        label = f"{provider} " if provider else ""
        raise SpendCeilingExceeded(f"{label}spend ceiling hit: ${s:.4f} >= ${ceiling:.2f}")
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

# ---------------------------------------------------------------- Anthropic
def call_anthropic(model, prompt, max_out=2200):
    """Claude 5 family. NOTE: temperature/top_p are REMOVED on these models and
    return a 400 if passed. Adaptive thinking is on by default on Opus 5; we
    leave it at the default because the audit measures shipped behavior, not a
    cost-tuned configuration."""
    import anthropic
    c = anthropic.Anthropic(api_key=load_key("anthropic"))
    r = c.messages.create(model=model, max_tokens=max_out,
                          messages=[{"role": "user", "content": prompt}])
    txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    think = "".join(getattr(b, "thinking", "") or "" for b in r.content
                    if getattr(b, "type", "") == "thinking")
    u = r.usage
    cached = getattr(u, "cache_read_input_tokens", 0) or 0
    return dict(text=txt, reasoning=think, in_tok=u.input_tokens,
                out_tok=u.output_tokens, cached=cached, finish=r.stop_reason)

def call(model, prompt, ceiling, max_out=2200):
    """Priced, ledgered, ceiling-guarded model call."""
    prov = PROVIDER_OF[model]
    check_ceiling(ceiling, provider=prov)
    fn = {"groq": call_groq, "anthropic": call_anthropic}.get(prov, call_openai)
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
