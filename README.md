# Following the Preference, Missing the Optimum

**Compliance without optimization in AI housing recommendation.**

An audit of whether AI recommenders overlook objectively better options than the ones they return — measured against a verifiable ground truth, priced in dollars and minutes, and tested for equality across users who differ only by an identity cue.

**9,612 model calls · 3 models · 2 vendors · 150 scenarios · 3,885 real NYC listings · US$57.01 total cost**

---

## Headline results

| | Model (`gpt-5.6-luna`, direct) | Random-selection floor |
|---|---|---|
| Hard-constraint violation | **1.8%** | 66.6% |
| Over-budget violation | **0.08%** | — |
| Strictly dominated recommendations | **39.0%** | 55.1% |
| Rent gap vs. oracle | **+$498/mo** | +$261/mo |

**Constraint compliance is high. Preference responsiveness is high. Optimization is not.**

A within-scenario manipulation — same pool, same ordering, one fixed rent oracle, one sentence changed:

| Instruction | Median rent recommended | Rent gap vs. cheapest feasible |
|---|---|---|
| "Commute matters most" | $3,280 | +$1,251 |
| "Rent matters most" | **$2,634** | **+$606** |
| "Minimize rent first; break ties within $50" | $2,637 | **+$611** |

The models **do** honor stated preferences — one sentence moves the median recommendation **$646/month** and **12.3 minutes** in the right direction (p < 0.0001). But under "rent matters most" they still sit **$606/month above the five cheapest suitable listings on the same screen**, and an unambiguous lexicographic rule improves this by **$3.50 (p = 0.70)**. The residual gap is not a prompting problem.

**Both claims replicate on a second vendor.** Re-run on `claude-opus-5` over the same 54 scenarios: responsiveness **−$688 (p < 0.0001)**, precision effect **+$2 (p = 1.000)**, residual gap **+$593** — against luna's −$659 / +$29 / +$579.

**The gap grows with the candidate set.** Filtering removed, only feasible listings shown, explicit rule held fixed:

| Feasible listings shown | Cheapest listing selected | Rent gap |
|---|---|---|
| 10 | **93.7%** | +$111 |
| 20 | 72.4% | +$356 |
| 40 | 57.1% | +$465 |
| 80 | **53.5%** | +$419 |

The limitation binds by roughly 20–40 items. **We do not claim to have isolated the mechanism** — attention, numeric comparison, position effects and output execution are not separated by anything run here.

**It replicates across vendors.** Three models spanning a **45× range in price per token** return a rent-first gap of **+$700, +$699, +$702**; paired contrasts on that condition are indistinguishable (|Δ| ≤ $3, p ≥ 0.86). Reported as a shared failure mode, **not a ranking.**

**What travels and what doesn't.** Varying pool size and infeasible share, the dominance *rate* ranges 17.6%–51.1% and tracks feasible-set size almost mechanically — quote it only with its configuration. The *rent gap* moves only $518–$564 over the same range, and is the transportable quantity.

---

## The core idea

A recommendation is **strictly dominated** if the same candidate list contains a listing that is *cheaper* **and** *shorter-commute* **and** *no smaller*.

Dominance needs no weights, no utility function, and no claim about what the user values. It is a statement about the choice set alone — which makes it immune to the standard objection that opportunity-loss findings merely restate the analyst's preferences.

Every scenario gets a **random-selection floor** computed over 200 draws, so each number is interpretable. Without a floor, "39% dominated" means nothing.

---

## Design decisions and errors caught

*Four design faults found during construction, each of which would have invalidated part of the result. Documented because how a study fails is more informative than how it succeeds.*

**1. The walk-access radius was silently deleting cheap apartments.**
At the literature-standard 800 m subway-access radius, 11% of listings were excluded — and they were **$700/month cheaper at the median**, concentrated in Queens (39.5% of excluded vs 13.5% retained) and Staten Island (19.3% vs 1.6%). A study about *rent gaps* was about to run on a sample that systematically dropped cheap inventory. Widened to 1,200 m, retaining 94.6% while moving the median commute only 30.0 → 30.4 min.

**2. Dominance rate is partly an artifact of pool size.**
In the full universe, 99.5% of one-bedrooms are dominated. In a 120-listing pool, ~55% are. A single "dominance rate" would have conflated model behavior with our own sampling parameter. Split into pool-dominance (primary, the accountability measure) and universe-dominance (a retrieval-plus-ranking composite).

**3. Studio scenarios had structurally undersized pools.**
An "under-bedroom" violation is undefined for a studio — there is no unit with fewer than zero bedrooms. All 50 studio scenarios were silently carrying 93-listing pools instead of 120, making pool size a deterministic function of bedroom count and confounding it with dominance. Slots redistributed 40/0/40.

**4. Response truncation was about to correlate missing data with the treatment.**
An early pilot showed 26% parse failure from verbose justifications overflowing `max_tokens` mid-JSON. Because verbosity may covary with the identity cue, the resulting missingness would have been **correlated with treatment** — quietly confounding the identity contrast, which is the paper's central claim. Capped justifications at 12 words and discarded the affected pilot data rather than merging it. Final parse rate: 96.7%, zero hallucinated listing ids.

---

## Honest limitations

- **This audits in-context ranking, not deployed products.** We hand the model its candidate pool, removing the retrieval stage entirely. Nothing here describes ChatGPT, Perplexity, or any shipped pipeline.
- **The stress-test pool is not a market.** 80 of 120 listings violate a constraint by design, so violation is measurable at all. These are **not prevalence estimates** for real housing search.
- **The identity null is bounded by the design.** Fixing the pool removes the freedom through which steering operated in prior open-ended studies. We explicitly decline the inference that constraining retrieval *eliminates* steering — that requires a comparison arm we did not run.
- **Not pre-registered.** The protocol was written and version-controlled before execution, but never filed with a registry. Stated plainly rather than implied.
- **Three models, two vendors — but not a benchmark.** Enough to foreclose the single-lab explanation, not enough to establish universality. No model ranking should be extracted from it.
- **Name cues are unvalidated.** Gaddis (2017) perception scores were not obtained, so the two name conditions rest on an unvalidated instrument. The voucher condition and all non-identity results are unaffected.

---

## Reproducing

```bash
pip install pandas numpy geopandas shapely matplotlib scipy statsmodels openai
```

Credentials are read from `keys/*.txt` (gitignored) — a RentCast key and an OpenAI key. Then run in order:

| Step | Script | Output |
|---|---|---|
| 1 | `01_fetch_listings.py` | RentCast listings (quota-ledgered, hard-capped) |
| 2 | `03_build_dataset.py` | Cleaning, census-tract join |
| 3 | `transit.py` | GTFS router — backward RAPTOR over the MTA feed |
| 4 | `02_build_scenarios.py` | 150 scenarios × 4 identity conditions |
| 5 | `04_benchmark.py` | Feasible sets, Pareto frontiers, design checks |
| 6 | `06_random_baseline.py` | Chance floor |
| 7 | `08_run_grid.py` | The audit (parallel, spend-ceilinged) |
| 8 | `09_analyze.py` | Randomization inference, variance decomposition |
| 9 | `10_exhibits.py` | Tables and figures |

Master seed `20260823`. Two safety mechanisms are built in: a **quota ledger** that refuses RentCast requests past a monthly cap, and a **spend ledger** that hard-aborts the audit at a dollar ceiling.

### The transit router

No Java, no OpenTripPlanner, no `r5py`. `transit.py` implements a backward RAPTOR over the MTA GTFS feed, solving the arrive-by problem (`tau = T_arrive − t`) rather than depart-at, because commuting is an arrive-by problem. Validated against nine known routes:

| Route (to Midtown) | Router | Published |
|---|---|---|
| Grand Central | 10.2 min | ~8–12 |
| Wall St | 21.9 | ~20–25 |
| Bedford Av | 21.9 | ~20–25 |
| Flushing–Main St | 34.5 | ~30–35 |
| Coney Island | 61.0 | ~60–70 |
| Far Rockaway | 86.5 | ~85–95 |
| Tottenville (via ferry) | 106.5 | ~100–110 |

The Staten Island Railway has no track connection to the subway, so a subway-only network silently deletes a borough; the ferry is added as an explicit fixed-cost link.

---

## Data

`data/public/` contains everything releasable:

| File | Contents |
|---|---|
| `audit_log.jsonl` | All 6,120 calls — pool-local ids, scores, tokens, cost |
| `listing_derived.csv` | Listing ids, census tract, borough, and our GTFS-computed commute times |
| `scenarios.csv` | 150 scenario definitions with feasible-set statistics |
| `random_baseline.csv` | Chance floor per scenario |

**Raw listing records are not redistributed.** RentCast's Terms of Use prohibit transfer or sublicense of their data, so rent, bedrooms, addresses and coordinates are withheld. Released fields are limited to identifiers and values *we* derived from public sources (MTA GTFS, Census TIGER). Re-run `01_fetch_listings.py` with your own RentCast key to reconstruct the full dataset.

---

## Citation

```
Lo, H. (2026). Obeying the Rules, Missing the Point: Preference Infidelity and
Priced Opportunity Loss in AI Housing Recommendation. Working paper.
```

## License

Code: MIT. Derived data and text: CC BY 4.0. Provider data: not redistributed.
