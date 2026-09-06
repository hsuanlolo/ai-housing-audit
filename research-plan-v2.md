# Research Plan v2 — Auditing the Cost of Algorithmic Omission

> **SUPERSEDED — historical document.** This is the pre-data protocol as it stood on 23 August 2026, before any model was called. It is preserved because it records what was planned in advance of seeing results, which is what makes the deviation log in the manuscript meaningful.
>
> **The study as executed differs from this plan in several respects.** Most importantly: the audited models are `gpt-5.6-luna` and `gpt-5.6-sol` rather than Claude plus an open-weight model (a budget decision); several specified arms were not run; and the paper's framing changed after the identity contrasts returned a null. For what actually happened, read **`paper/manuscript.md`** — §4.5 lists what was and was not executed, and Appendix C is a dated log of every departure from this plan.
>
> *(Originally written in Chinese; translated to English 6 September 2026 with content unchanged.)*

(Revised 2026-08-23. Supersedes v1. Changes summarized at the end.)

## Proposed title

**What It Costs to Be Overlooked: Auditing Constraint Fidelity, Forgone Opportunity, and Identity-Conditioned Disparity in AI Housing Search**

Short form: *The Price of Algorithmic Omission in High-Stakes Search*

**Framing.** Housing search as a high-stakes recommendation setting, used to measure the **verifiable cost** of what AI recommendation misses — denominated in dollars and commute minutes — and to test whether that cost varies with a user's identity cue.

**Scope.** The New York City rental market; listing-level data; synthetic user profiles; an in-context ranking audit (not a deployed-product audit); no human subjects and no platform-internal behavioral data.

---

## 1. Research gap

As of August 2026 the literature contains three mature strands:

1. **Housing steering audits.** Whether LLMs recommend different locations depending on a user's ethnicity. Liu et al. (EAAMO '24) tested GPT-4 with 168,000 prompts and found racial steering, default whiteness, and the routing of minority users toward lower-opportunity-index neighborhoods. arXiv:2606.06694 (AIES '26) extended this to seven models across four cities and argued that steering is interpretive behavior rather than a fixed model property.
2. **Industry ranking evaluation.** arXiv:2607.14835 (QuintoAndar) evaluated an LLM re-ranker on 960k query-item pairs; production A/B testing showed +5.3% CTR and +4.8% scheduled visits.
3. **Omission / coverage audits.** arXiv:2608.07069 (*Invisible to the Machine*, August 2026) used a **complete market census** as its benchmark, enumerating all 4,776 venues across two locations in Bali and testing 2,208 responses. It found 85.6% of venues were never recommended, and identified staleness rather than hallucination as the dominant failure mode.

**A point that must be faced honestly:** the gap v1 claimed — "what does AI miss?" — was closed for the restaurant domain three weeks ago. A plain omission audit is no longer a novel contribution.

What remains genuinely unaddressed is the **intersection** of these three strands:

> Existing omission audits have no protected class and no user-verifiable hard constraints. Existing steering audits have no oracle and never convert harm into a cost. As a result, **no study can currently state the following sentence**:
>
> *Holding the request and the candidate inventory constant and changing only an identity cue, the listings a user is shown are on average $X/month more expensive and Y minutes further from work, and Z% of what is recommended is strictly dominated by something the system also saw.*

The contribution is therefore positioned as:

> **Not "AI misses things" (already known), and not "AI steers" (already known), but: the forgone opportunity is measurable in dollars and minutes against a verifiable ground truth, it is unequally distributed across identity cues, and a specific architectural change reduces it.**

Housing is one of very few domains satisfying all three of the following conditions simultaneously. This is the reason for the site selection, not convenience:

* Hard constraints are **objectively verifiable** (rent, bedroom count, commute time) without relying on an LLM judge.
* A **statutory fairness regime** applies (the Fair Housing Act; in New York City, the Human Rights Law additionally protects source of income).
* The cost of omission is directly expressible in **money and time**, requiring no utility assumption.

---

## 2. Research questions and hypotheses

| Research question | Hypotheses |
| --- | --- |
| **RQ1. Constraint fidelity:** Do AI recommenders respect explicitly stated hard constraints? | **H1a:** When both conforming and non-conforming listings are present in the candidate set, LLM recommendations will include confirmed violations (over budget, too few bedrooms, over the commute ceiling). **H1b:** Violation rate rises with the number of simultaneously binding constraints. *(Note: H1b is already established in the general instruction-following literature — compositional constraint satisfaction, e.g. arXiv:2608.12426, SEQUOR arXiv:2605.06353. The contribution here is domain-specific magnitude and distribution, not discovery of the phenomenon.)* |
| **RQ2. Forgone opportunity:** When recommendations look reasonable, do they still omit objectively better listings? | **H2a:** A substantial share of recommended listings will be **strictly dominated** by another listing in the same candidate set (cheaper **and** shorter commute **and** no fewer bedrooms). **H2b:** Dominance rate rises with candidate-set density and with preference ambiguity. |
| **RQ3. Identity-conditioned disparity:** Are these failures unevenly distributed across identity cues? | **H3a:** Holding the profile, candidate set and ordering fixed and changing only the identity cue changes rent gap, commute gap, dominance rate, or neighborhood exposure. **H3b:** The effect of an explicitly protected attribute (housing voucher) exceeds that of name cues. |
| **RQ4. Mitigation and its side effects:** Can architecture reduce these failures, and at what cost? | **H4a:** Constraint-first architecture eliminates verifiable violations **by definition, not as an empirical finding**; the open question is its effect on opportunity loss and identity gaps. **H4b:** Prompts carrying identity cues raise refusal and information-withholding rates, potentially reducing steering while also reducing usefulness. |

**Core discipline:** study only these four things. No extension to real-user preference change, actual leasing, long-run welfare, or the national market.

---

## 3. Data sources

### Core (load-bearing; none can be dropped)

| Source | Variables | Purpose |
| --- | --- | --- |
| **RentCast API** `/listings/rental/long-term` | Rent, address, coordinates, property type, bed/bath, floor area, status, days on market, listing history | Listing universe |
| **ACS 5-year (tract)** | Median income, rent burden, demographic composition, renter share | Neighborhood exposure outcome only |
| **GTFS static (MTA)** | Stops, routes, timetables | Transit commute matrix |

### Cut from v1 (explicitly removed, with reasons)

| Dropped | Reason |
| --- | --- |
| **LEHD/LODES** | Serves no research question. Commute is computed from GTFS; job accessibility is not an outcome. |
| **Opportunity Insights** | Appears only in the neighborhood-exposure narrative, where ACS suffices. Retaining it adds a week of work with no corresponding hypothesis. |
| **NYC Housing Connect** | Eligibility rules cannot be fully reconstructed (v1 conceded this). Using incomplete eligibility as a robustness check manufactures a new validity problem rather than solving one. |

### Volume and coverage

* Target: **3,000–5,000** active NYC long-term rental listings.
* **API quota arithmetic:** free tier = 50 requests/month × 500 records/request = 25,000 record-slots. Paginating by city is feasible; **do not** fetch ZIP by ZIP (New York has ~180 ZIPs, exhausting the quota in a single pass). Budget one month of the Foundation tier ($74) as insurance.
* **Mandatory coverage benchmark (absent from v1):** New York's rental market runs largely through StreetEasy and REBNY channels, so MLS syndication coverage may systematically under-represent no-fee and small-landlord units. The listing sample's rent and borough distributions must be compared against ACS rent distributions and NYC Housing and Vacancy Survey quantiles, with the direction of bias presented in a table. Housing-journal reviewers will ask.
* **Data release:** after checking RentCast's Terms of Use, default to releasing code, derived aggregates and listing IDs only — **not raw listings**. Confirm this in week 1, not week 12.

---

## 4. Study design

### Step 1. Build the listing universe

Inclusion: active; rent between the 1st and 99th percentile; geocodable address; identifiable bedroom count; assignable to a census tract.

Cleaning: deduplicate on an address + bedrooms + rent fingerprint; retain the most recent record for repeat listings; remove implausible rent or floor area; remove ungeocodable addresses.

**Any missing field is coded `unknown` and must never be presumed compliant or non-compliant.** This corresponds directly to the "unverifiable" category in the outcome measures.

### Step 2. Commute matrix

* Tooling: `r5py` or OpenTripPlanner. **Fix a single departure time (08:00 on a weekday);** do not vary time of day.
* Destinations: **three** (Midtown Manhattan, Downtown Manhattan/FiDi, Downtown Brooklyn). The 5–10 destinations contemplated in v1 correspond to no hypothesis and only add compute.
* Scale: roughly 4,000 listings × 3 destinations ≈ 12,000 routings.
* **This is the single largest schedule risk in the project.** If OTP has never been stood up before, run a week-1 spike; on failure, fall back to a tract-to-tract travel-time matrix (an acceptable and documentable loss of precision).

### Step 3. Synthetic user profiles

**150 base scenarios** (v1 specified 250; the reduction buys replicates per cell — see Step 7).

Variation dimensions:

* Budget (as a percentile of the real rent distribution, not an arbitrary dollar figure)
* Unit type: studio / 1BR / 2BR
* Work location: one of three
* Maximum commute: 30 / 45 / 60 min
* Priority ordering: rent-first / commute-first / location-first
* Request specificity: explicit constraints vs. lifestyle-phrased (addresses H2b)

**Identity conditions (four; v1 had three):**

1. **Neutral** — no identity cue
2. **Name cue A** — name pool A
3. **Name cue B** — name pool B
4. **Housing voucher disclosure** — "I have a CityFHEPS / Section 8 voucher"

Three disciplines govern the identity cues (unaddressed in v1):

* Names must **not be invented**. They must come from published name-perception datasets, with each name's perceived-race and perceived-SES scores reported, directly confronting Gaddis's critique of the race/SES confound.
* Each profile draws names by **random rotation** from a pool; name identity is a random effect, not two fixed exemplars.
* The voucher condition is included because source of income is legally protected in New York City, is the most policy-relevant attribute available, and is a **legitimate material constraint** — it genuinely changes which listings are appropriate. This permits a distinction a name-only design cannot make: lawful adaptation to a stated circumstance versus unlawful degradation of service. This is the substantive advance over existing name-only steering audits.

### Step 4. Candidate pool construction (the critical step entirely absent from v1)

This step determines what the study measures. It must be specified in advance.

For each profile *i*, draw **N = 120** candidate listings from the universe:

* **40 feasible** (satisfying every hard constraint), **necessarily including the oracle top 10**. If the oracle top-*k* is not in the pool, what is measured is retrieval failure rather than ranking failure.
* **80 near-miss infeasible**: over budget by 5–20%, one bedroom short, or over the commute ceiling by 5–15 minutes. Exactly one constraint is violated per listing, and the three violation types are balanced.

**Why infeasible listings must be present:** if the entire pool is feasible, the violation rate is zero by definition and H1 is untestable. This was an unnoticed logical hole in the v1 design.

Other controls:

* **Randomize candidate order** on every call (position effects).
* All systems see the **identical** candidate pool.
* Token budget: 120 listings × ~50 tokens ≈ 6,000 tokens, comfortably within context.

**Commute-visibility arms (new):**

* **Arm 1 (primary):** candidate records include the precomputed commute in minutes. This tests pure constraint following.
* **Arm 2 (robustness, 50-profile subsample):** only the address is given, no commute. This tests the model's performance when it must infer geography itself.

Without this separation, a "commute violation" conflates constraint-following failure with New York geographic knowledge, and the resulting rate is uninterpretable. v1 took no position on this at all.

### Step 5. Objective benchmark

**(a) Feasible set (weight-free, primary)**

```
F_i = { j : Rent_j <= Budget_i
          AND Bedrooms_j >= Bedrooms_i
          AND Commute_ij <= MaxCommute_i }
```

**(b) Dominance frontier (weight-free, primary)**

Listing *j* is **strictly dominated** by listing *j'* iff:

```
Rent_j'     <  Rent_j
Commute_ij' <  Commute_ij
Bedrooms_j' >= Bedrooms_j
```

(with at least one strict inequality and no dimension worse). The Pareto frontier is the set of undominated members of F_i.

**This is the most important methodological change in v2.** Dominance requires no weights, no utility function, and no argument about preferences, and it is immune to the most likely rejection reason — "your utility function is assumed."

**(c) Weighted score (demoted to secondary/robustness only)**

```
Score_ij = -w1*Rent_j - w2*Commute_ij + w3*UnitMatch_ij + w4*TransitAccess_j
```

Weights derive from the profile's stated priority ordering. **Robustness exhibit only**, with a sensitivity grid of at least three weight vectors.

> **Explicit disclaimer:** this is a scenario-based relevance benchmark, not an empirically validated utility function, and it is not equivalent to consumer welfare. v1 carried this disclaimer and v2 retains it — but more importantly, v2's primary outcomes do not depend on it at all.

### Step 6. Four recommendation systems

| System | Design | Research purpose |
| --- | --- | --- |
| **S0. Non-LLM IR baseline** | BM25 or embedding retrieval plus a simple linear ranker, identity-blind | **Missing from v1.** Without it, a reviewer cannot judge whether the LLM performs poorly or the task is simply hard. Deterministic; one run per profile. |
| **S1. Direct LLM** | The model reads the request and the candidate pool and returns a top five | Violations and omissions from an unengineered model |
| **S2. Retrieval-grounded LLM** | Structured listing records plus source attribution, with a requirement to check each constraint explicitly | Whether grounding improves quality |
| **S3. Constraint-first** | Code filters hard constraints; the LLM ranks and explains only within F_i | The cost and benefit of a safer architecture |

**An honest framing of S3 (a logical problem in v1):** S3's violation rate is zero by construction. That is not an empirical finding, it is a definition. The real question is whether **opportunity loss and identity gaps persist in the soft ranking stage** once the hard constraints are guaranteed. The paper must say this outright, or a reviewer will write "you have proved that a filter filters."

### Step 7. Execution grid

**Main grid:**

```
150 profiles x 4 identity conditions x 3 LLM systems x 3 replicates x 2 models
= 10,800 LLM calls
```

(S0 is deterministic; 150 additional runs serve as a reference point and do not enter the identity contrast.)

**Replicates and temperature (entirely unaddressed in v1 — a substantive hole):**

* Temperature at the model default (≈1.0), with **three replicates per cell**, to capture the stochasticity present in real deployment.
* Temperature = 0 yields a single draw per cell and cannot distinguish model bias from sampling noise.
* Replicate-level variance must be reported separately: if within-cell variance exceeds the identity effect, that effect cannot be claimed.

**Robustness arms (subsamples):**

* Commute-hidden arm: 50 profiles × 4 identity × S1 × 3 replicates
* Prompt-wording variants: 3 phrasings × 50 profiles
* Top-*k* sensitivity: k = 3, 5, 10
* Candidate-pool density: N = 60 vs. 120

**Cost estimate (absent from v1):** the main table is roughly 10,800 calls × ~8k input tokens ≈ 86M input tokens; with robustness arms, real API cost is approximately **US$500–900**. This is a genuine budget line requiring confirmation in advance.

**Model versioning:** pin specific model snapshots and record call dates. API models drift, and an audit without recorded versions cannot be reproduced.

---

## 5. Main outcome measures

### Pre-registered PRIMARY outcomes (three, all weight-free)

**P1 — Confirmed hard-constraint violation rate**

```
ViolationRate_i = (# recommended listings violating a VERIFIED constraint) / (# recommended listings)
```

Missing fields are reported separately as **unverifiable** and excluded from confirmed violations. Report the decomposition: over-budget / under-bedroom / over-commute.

**P2 — Strict-dominance rate**

```
DominanceRate_i = (# recommended listings strictly dominated by some listing in F_i) / (# recommended listings)
```

Also report the **magnitude** of dominance: the rent difference (USD) and commute difference (minutes) between each dominated listing and the listing that dominates it.

**P3 — Identity-conditioned cost gaps**

```
RentGap_i    = median(Rent of R_i ∩ F_i)     - median(Rent of oracle top-5)     [USD/month]
CommuteGap_i = median(Commute of R_i ∩ F_i)  - median(Commute of oracle top-5)  [minutes]
```

Medians rather than minima (v1 used minima, which are unstable under ties and sensitive to a single outlier). The identity contrast is the within-profile difference in these gaps.

> **Note a definitional error in v1:** v1 defined `OpportunityLoss = max_{j in F} Score − max_{j in R} Score`, where R may contain infeasible listings scoring highly — causing the measure to *understate* loss in precisely the cases it exists to detect. v2 always intersects with F_i first.

### SECONDARY outcomes

**S1 — Mean percentile rank within the feasible set.** The mean percentile of recommended listings within F_i, computed on rent and on commute.

> **Why this replaces v1's Capture@k:** when |F_i| runs to hundreds of near-equivalent listings, Capture@5 approaches zero for **any** system including a perfect one — it measures set size, not quality. If Capture@k is retained, it needs a tolerance band (within $50 and 5 minutes counts as a hit).

**S2 — Refusal / information-withholding rate.** The share of responses that decline, evade neighborhood characteristics, or substitute safety language for substance.

> **v1 placed this under "potential unexpected finding." v2 promotes it to a formally measured outcome.** "Fair-housing guardrails simultaneously reduce steering and withhold information users need" is plausibly the most publishable finding available, and cannot be left to chance.

**S3 — Neighborhood exposure.** ACS tract characteristics of recommended listings — the point of comparability with the existing steering literature.

**S4 — Tolerance-band Capture@k, NDCG@5, Precision@5.** All relevance labels must derive from **pre-specified** constraints and a transparent benchmark, never from post-hoc judgment or model self-scoring.

### TERTIARY / robustness only

**T1 — Weighted opportunity loss**

```
OpportunityLoss_i = max_{j in F_i} Score_ij - max_{j in R_i ∩ F_i} Score_ij
```

With a three-weight sensitivity grid. **Not a headline number.**

### Fairness gap (for any outcome Y)

```
FairnessGap = E[Y_i | Identity = A] - E[Y_i | Identity = B]
```

The critical comparison: **same profile, same candidate pool, same ordering, only the identity cue changes** — a within-profile matched contrast.

---

## 6. Statistical methodology

### Correct description of the design

This is a **within-profile matched design**: the four identity conditions for a given profile face an identical candidate pool. Identity effects are matched contrasts, not between-group comparisons. v1 obtained the same estimator via profile fixed effects but never said so, and consequently chose the wrong inferential method.

### Primary inference: randomization inference

Identity conditions are randomly assigned within profile, so a **permutation test** is the method matched to the design:

* Permute identity labels within profile, 10,000 draws, to build the null distribution.
* Report the permutation *p*-value and the point estimate of the paired difference.
* Rationale: the primary outcomes are zero-inflated proportions (most profiles have a violation rate of 0), and with n = 150 clusters the asymptotic properties of clustered OLS are unreliable.

### Secondary: fixed-effects regression (v1's model, retained as support)

**Model 1 — identity disparities**

```
Y_igmr = alpha_i + beta * IdentityCue_g + lambda_m + delta_r + eps_igmr
```

*i* = profile; *g* = identity cue; *m* = model; *r* = replicate. Standard errors clustered at the profile level.

**Model 2 — mitigation and interaction**

```
Y_igsmr = alpha_i
        + b1 * Grounded_s
        + b2 * ConstraintFirst_s
        + b3 * IdentityCue_g
        + b4 * (ConstraintFirst_s x IdentityCue_g)
        + lambda_m + delta_r + eps_igsmr
```

b2 = the architecture's effect on overall quality; **b4 = whether it narrows identity gaps** (the core coefficient for RQ4).

**Variance decomposition (new).** Use a mixed model to partition between-profile, between-identity, and within-cell (replicate) variance. If replicate variance exceeds the identity effect, that effect must not be claimed as systematic bias.

### Power / MDE

* 150 profiles, within-profile pairing, three replicates per cell.
* Rough estimate: MDE ≈ 0.2–0.25 SD of the paired difference for continuous outcomes; ≈ 8–10 percentage points for binary outcomes.
* **Required:** run a **simulation-based power analysis** on the week-4 pilot (20 profiles) before finalizing the profile count. Do not substitute rules of thumb for simulation.

### Statistical safeguards

* **Pre-registration (absent from v1; mandatory in v2):** register primary outcomes, sample size, exclusion rules and analysis models on OSF or AsPredicted before running the main grid. Adjacent omission and hotel audits both pre-registered; for audit papers this materially raises acceptance odds.
* Multiple testing: Benjamini–Hochberg within each outcome family, with families defined at registration.
* Randomized candidate ordering (Step 4).
* Prompt-wording and name-pool rotation (robustness arms).
* Full logging of model snapshots and call dates.
* State explicitly that **thousands of model outputs are not thousands of independent users** — the effective sample size is the number of profiles (150), not the number of calls.

---

## 7. Expected outcomes

**E1 — High apparent relevance, high dominated-recommendation rate.** Recommendations look reasonable and conventional ranking metrics are acceptable, yet a substantial share are strictly dominated by cheaper, shorter-commute listings in the same pool. The strength of this finding is that it **requires no utility assumption whatsoever**.

**E2 — Constraint interaction penalty.** Requests combining budget + bedrooms + commute show higher violation rates than single-constraint requests. This is a quantification of the existing compositional-constraint literature in a new domain, not a claim of novelty.

**E3 — Identity effects appear in cost, not in accuracy.** Identity cues may produce no difference in mean ranking accuracy while significantly changing rent gap, commute gap, neighborhood exposure and dominance rate. **"Equal accuracy, unequal cost" is itself the most important possible result**, and is the substantive advance over the existing steering literature.

**E4 — Voucher effect exceeds name effect.** An explicitly protected attribute should produce a larger effect than a name cue. If so, the policy implication is more direct than any name-based audit can support.

**E5 — Constraint-first eliminates violations by construction, but soft-ranking disparity persists.** If b4 is not significant, architectural safeguards **do not solve inequality at the ranking layer** — an implication far more important to industry than "just filter it."

**E6 — The guardrail trade-off.** Fair-housing or safety constraints may simultaneously reduce obvious bias **and** raise refusal/withholding rates, reduce diversity, and suppress genuinely useful neighborhood information. This trade-off is directly relevant to both AI companies and regulators, and in v2 it is measured rather than merely anticipated.

---

## 8. Limitations

**This study can identify:** how identity cues in a prompt and recommendation architecture change model ranking output over a fixed candidate set, and the verifiable cost of those changes.

**It cannot identify:**

* Whether real preferences change, whether users actually lease, market transaction effects, or long-run housing welfare.
* Deployed product behavior. **This is an in-context ranking audit, not a deployed-product audit.** We control the candidate pool and thereby exclude the retrieval stage; retrieval failures in real systems (Zillow's or Redfin's assistants, ChatGPT with browsing) are outside the measurement. This boundary must be stated in the abstract.
* Full Housing Connect eligibility (that data source has been removed).

**Other limitations:**

* Synthetic profiles do not represent all renters; request phrasing is researcher-authored.
* RentCast's NYC coverage skews toward MLS syndication and may under-represent no-fee and small-landlord units (§3's coverage benchmark quantifies the direction but cannot remove it).
* New York does not generalize to the United States; arXiv:2606.06694 shows steering is city-heterogeneous — "the city is not a neutral testing unit."
* Name cues carry race and SES signals simultaneously; even validated name datasets cannot fully separate them.
* The weighted opportunity score is not equivalent to any user's actual welfare (the primary outcomes avoid depending on it).
* Legal implications require care: **evidence of steering is not a finding of FHA liability.** The paper should describe behavior and its cost, and confine legal argument to "these behaviors fall within the class of conduct the FHA and NYCHRL address."

---

## 9. Execution plan (12 weeks, replacing v1's 6)

v1's six-week schedule is infeasible if the transit network has never been built before. The schedule below is realistic; if compression is required, cut the number of models (2 → 1) and the robustness arms, never the pilot or the pre-registration.

| Week | Work | Deliverable |
| --- | --- | --- |
| **1** | RentCast fetch strategy and ToS confirmation; listing universe v0; **r5py/OTP spike (go/no-go decision point)** | Listing dataset + routing go/no-go |
| **2** | Listing cleaning, deduplication, geocoding, tract join; coverage benchmark vs. ACS/NYCHVS | Cleaned dataset + coverage bias table |
| **3** | Commute matrix (4,000 × 3); ACS tract variables merged | Enriched property dataset |
| **4** | 150 profiles + name pool (from published datasets); feasible sets and dominance frontiers; **20-profile pilot** | Benchmark scenarios + pilot results |
| **5** | Pilot analysis → simulation-based power analysis → final sample size; **submit pre-registration** | OSF pre-registration (timestamped) |
| **6** | Build S0 baseline and candidate-pool sampler; finalize prompt templates | Evaluation harness |
| **7** | Build S1 / S2 / S3 architectures; small-scale smoke test | Recommendation pipeline |
| **8** | Run the main grid (10,800 calls, 2 models) | Raw response corpus |
| **9** | Run robustness arms (commute-hidden, wording, top-*k*, pool density) | Robustness corpus |
| **10** | Primary analysis: permutation tests, FE models, variance decomposition | Main results |
| **11** | Visualization; neighborhood exposure; refusal analysis; limitations | Figures + full results |
| **12** | Working paper; GitHub repo (code + aggregates + listing IDs) | Paper draft + reproducible portfolio |

---

## 10. Suggested paper structure

1. **Introduction** — AI as an intermediary in high-stakes search; the cost of what is overlooked; why housing is the only setting with both a verifiable ground truth and a statutory fairness regime.
2. **Related work** — (a) housing steering audits (Liu et al. EAAMO '24; arXiv:2606.06694); (b) omission/coverage audits (arXiv:2608.07069); (c) industry ranking evaluation (arXiv:2607.14835); (d) constraint following (arXiv:2608.12426; SEQUOR). **State clearly that this work sits at the intersection of the four, rather than claiming a void.**
3. **Data** — listings, commute matrix, tract variables, coverage benchmark and its bias.
4. **Benchmark construction** — feasible sets, dominance frontier, and why the primary outcomes are deliberately weight-free.
5. **Audit design** — candidate pool construction, identity conditions (including voucher), four architectures, two commute-visibility arms, replicates.
6. **Results I: constraint fidelity and forgone opportunity** — violations, dominance, cost gaps.
7. **Results II: identity-conditioned disparity** — permutation-based matched contrasts; exposure.
8. **Results III: mitigation and the guardrail trade-off** — b2, b4, refusal rate.
9. **Discussion** — transferability to hiring, lending, healthcare and other high-stakes recommendation; implications for platform design and regulation.
10. **Limitations and conclusion.**

**Final positioning:** this is a paper about **AI fairness, recommendation evaluation and high-stakes search**, situated in the housing market — not a housing policy paper.

### Venue strategy

| Stage | Target | Rationale |
| --- | --- | --- |
| **Primary** | **ACM FAccT** | Where this literature actually lives; identity-conditioned harm + verifiable cost + mitigation is squarely its core. |
| **Alt / parallel** | **AIES** (where 2606.06694 went), **EAAMO** (where Liu et al. went) | Same community, friendlier to a solo author. |
| **Journal (method-forward)** | **Computers, Environment and Urban Systems**; **EPB: Urban Analytics and City Science** | Computational method + urban data + audit. |
| **Journal (policy-forward)** | **Housing Policy Debate**; **Cityscape (HUD)** | Strongest fit for the FHA/NYCHRL framing; Cityscape is fast with broad policy reach. |
| **Journal (metric-forward)** | **ACM TORS**; **Information Processing & Management** | Will require the S0 non-LLM baseline from Step 6 — another reason to include it. |
| **Not recommended** | *Journal of Housing Economics*, *Real Estate Economics* | Will reject on "synthetic profiles are not behavior and there is no market outcome," and would be right by their own standards. |

Recommended path: **FAccT / AIES first → extended version to Housing Policy Debate or CEUS.** Given that three adjacent papers appeared in the preceding ten weeks, timeliness is a substantive consideration.

---

# Appendix — What changed from v1 to v2

## A. Fatal-level corrections (would have caused rejection)

| # | v1 | v2 | Why |
| --- | --- | --- | --- |
| 1 | Claimed nobody had measured what AI omits | Acknowledges arXiv:2608.07069 (Aug 2026) did exactly this for restaurants using a complete market census; repositions to the **intersection** of four literatures | v1's gap no longer exists. A reviewer would find that paper in thirty seconds. |
| 2 | Did not cite Liu et al. (EAAMO '24) | Listed as the canonical prior for RQ3 | The 168k-prompt GPT-4 steering audit is foundational here; its absence is conspicuous. |
| 3 | Headline metric depended on hand-set weights | **Strict-dominance rate promoted to primary**; weighted score demoted to tertiary robustness | Dominance needs no weights and no utility assumption. This change alone removes the most likely rejection reason. |
| 4 | Candidate pool undefined | N=120: 40 feasible (**including the oracle top-10**) + 80 near-miss infeasible | With an all-feasible pool the violation rate is zero by definition and H1 is untestable; without the oracle in the pool, what is measured is retrieval failure, not ranking failure. A logical hole in v1. |
| 5 | No position on whether commute is shown to the model | Added **commute-visible / commute-hidden arms** | Without the distinction, violation rate conflates constraint-following with NYC geographic knowledge and cannot be interpreted. |
| 6 | Temperature and replicates unmentioned | Temperature ≈1.0, **3 replicates per cell**, within-cell variance reported | v1 could not separate model bias from sampling noise. |
| 7 | No pre-registration | OSF/AsPredicted registration in week 5 | Adjacent omission and hotel audits both registered; for audit papers this materially affects acceptance. |

## B. Metric definition corrections

| # | v1 | v2 |
| --- | --- | --- |
| 8 | `OpportunityLoss = max_F Score − max_R Score` | Changed to `max_F Score − max_{R∩F} Score`. v1's R may contain high-scoring infeasible listings, causing it to **understate** loss precisely where detection matters most. |
| 9 | `Capture@k` with denominator `min(k,|F_i|)` | Replaced by **mean percentile rank within F_i**; Capture@k retained with a ±$50 / ±5min tolerance band. With |F| in the hundreds, Capture@5 approaches zero even for a perfect system — it measures set size. |
| 10 | `RentGap` / `CommuteGap` used minima | Changed to **medians**, robust to ties and single outliers. |
| 11 | Refusal/withholding appeared only under "potential unexpected finding" | Promoted to formal secondary outcome **S2**. "Guardrails reduce steering while withholding useful information" is plausibly the most publishable finding and cannot be left to chance. |

## C. Design and feasibility

| # | v1 | v2 |
| --- | --- | --- |
| 12 | Three systems, no non-LLM control | Added **S0: BM25/embedding + linear ranker**. Without it a reviewer cannot tell whether the model is bad or the task is hard; TORS/IPM would demand it. |
| 13 | S3 constraint-first treated as a testable hypothesis | States plainly that **a zero violation rate is a definition, not a finding**; relocates the real question to opportunity loss and identity gaps in soft ranking |
| 14 | Six data sources | **Cut LODES, Opportunity Insights, Housing Connect**, retaining RentCast + ACS + GTFS. None served any RQ; together they added about a week of work. |
| 15 | Commute: 5–10 destinations, no tooling or time specified | **Three destinations, fixed 08:00 weekday, r5py or OTP**, with a week-1 go/no-go spike and a tract-to-tract fallback |
| 16 | RentCast quota arithmetic and coverage bias unexamined | Computed: free tier = 50 req × 500 rec = 25,000 slots/month; **must fetch by city with pagination, never ZIP by ZIP**; added a **coverage benchmark table** against ACS/NYCHVS (NYC rentals run through StreetEasy/REBNY, so MLS syndication under-represents no-fee and small-landlord units — a question housing reviewers always ask) |
| 17 | Promised a GitHub data release | Changed to code + derived aggregates + listing IDs; ToS confirmed in week 1 |
| 18 | No API cost estimate | Estimated **US$500–900** as a real budget line; requires pinned model snapshots and dates |
| 19 | Six-week schedule | **Twelve weeks**; compression cuts models and robustness arms, never the pilot or the registration |

## D. Identity cues and statistical inference

| # | v1 | v2 |
| --- | --- | --- |
| 20 | "Identity cue A / B" undefined; names self-authored | Names drawn from **published name-perception datasets** with race × SES perception scores reported, directly answering Gaddis's SES confound critique |
| 21 | Name cues only | Added a fourth condition: **housing voucher (CityFHEPS / Section 8) disclosure**. Source of income is legally protected in NYC and the most policy-relevant attribute available; it is also a **legitimate material constraint**, permitting a distinction between lawful adaptation and unlawful degradation. This is the substantive advance over name-only audits and the justification for choosing New York. |
| 22 | Clustered OLS as primary inference | **Permutation / randomization inference primary**, FE OLS secondary. The design is a within-profile matched contrast; with zero-inflated proportions and n=150 clusters, clustered OLS asymptotics are unreliable. |
| 23 | 250 profiles × 3 conditions, no power analysis | **150 profiles × 4 conditions × 3 replicates**; week-4 pilot → **simulation-based power analysis** before finalizing; added variance decomposition (if replicate variance > identity effect, the effect is not claimed) |
| 24 | No distinction between in-context ranking and deployed products | Limitations and abstract state explicitly that **this is an in-context ranking audit that excludes the retrieval stage**, and claim nothing about Zillow, Redfin or ChatGPT deployment behavior |
| 25 | Legal overreach unaddressed | States plainly that **evidence of steering is not FHA liability**; legal argument confined to "conduct of a type the FHA / NYCHRL addresses" |

## E. Framing and new questions

| # | Change |
| --- | --- |
| 26 | Title and positioning shift from "what AI omits" to "**the cost of omission, in dollars and minutes, unequally distributed**" — the only position not already occupied by existing literature. |
| 27 | H1b explicitly labeled as a phenomenon already established in the compositional-constraint literature; the contribution is domain-specific magnitude, not discovery. |
| 28 | Added **RQ4** (mitigation and its side effects), merging v1's mitigation question with the guardrail trade-off previously buried under "unexpected finding" into a single question with formal hypotheses. |
| 29 | Added an explicit expectation for **E3**: "equal accuracy, unequal cost" is itself a core result, not a null finding. |
| 30 | Added a **venue strategy table**: FAccT / AIES / EAAMO first; journals split into method-forward (CEUS, EPB), policy-forward (Housing Policy Debate, Cityscape) and metric-forward (TORS, IPM); real estate economics journals listed as not recommended, with reasons. |
