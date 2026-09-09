# SocArXiv submission — complete field sheet

Every value, in form order. Paste from here rather than retyping.
File to upload:  paper/Lo_2026_Following_the_Preference.pdf
  58 pages, 1,841,445 bytes
  sha256 fbc5ca306ae6444e9e1b7c610eac1049a163c023aa867b888d3412b2fb814dde
  (verify the hash if you ever re-download it:  shasum -a 256 <file>)

------------------------------------------------------------------
1. SERVICE
------------------------------------------------------------------
SocArXiv

------------------------------------------------------------------
2. FILE
------------------------------------------------------------------
Upload from your computer -> Lo_2026_Following_the_Preference.pdf

------------------------------------------------------------------
3. TITLE
------------------------------------------------------------------
Following the Preference, Missing the Optimum: Compliance Without Optimization in AI Housing Recommendation

------------------------------------------------------------------
4. ABSTRACT  (2,789 chars of the 3,000 allowed)
------------------------------------------------------------------
Large language models are becoming the first point of contact for consumer search in domains where the stakes are material and the law is explicit. Existing audits of AI housing search show that models steer users toward different neighborhoods depending on perceived racial identity. None can say what a user loses when a recommender simply overlooks a suitable option, because none has an enumerated inventory to score omissions against.

We audit AI housing recommendation against a verifiable ground truth. For each of 150 synthetic renter scenarios in New York City we build a pool of 120 real listings with known rent, bedrooms, and GTFS-computed transit commute, compute the exact set satisfying the renter's stated constraints, and derive its Pareto frontier. The primary outcome assumes no utility function: a recommendation is strictly dominated if the same pool holds a listing that is cheaper, faster to commute from, and no smaller in bedrooms. We report 9,945 model calls (96.5% parsed) across three models and two vendors, for US$57.01 in API cost.

Constraint compliance is near-perfect: models violate a stated hard constraint on 1.8% of recommendations against a 66.6% random-selection floor. Optimization is poor and priced. 39.0% of recommendations are strictly dominated, and where one is dominated the dominating listing is a median $900/month cheaper and 3.5 minutes closer. On rent the models underperform random selection (+$498/month versus +$261 against the oracle).

A within-scenario manipulation separates two capabilities usually conflated. Models do honor stated preferences: changing one sentence moves median recommended rent by $646/month in the correct direction. Yet recommendations still sit +$606/month above the five cheapest qualifying listings on the same screen, and an unambiguous lexicographic instruction yields no improvement, established by equivalence testing against a pre-specified $50 bound. The gap widens with candidate-set size: the cheapest listing appears in 93.7% of answers at ten candidates, 53.5% at eighty. This replicates across OpenAI and Anthropic models spanning a 45x price range, agreeing within $3. We characterize the failure as compliance without optimization.

We detect almost no identity-conditioned disparity. Of 48 pre-specified contrasts, 47 return null after Benjamini-Hochberg correction, and a further 105 contrasts on the census-tract characteristics of recommended listings return none, with replicate noise exceeding between-condition variance. This null holds for re-ranking a fixed candidate set and does not license claims about open-ended search, where prior work finds steering.

We propose dominance-rate instrumentation as a deployable diagnostic and release all code, prompts, and per-call results.

------------------------------------------------------------------
5. CONTRIBUTORS
------------------------------------------------------------------
Name                     Hsuan Lo
Permissions              Administrator     <- do NOT change this
Bibliographic            Yes / checked
Employment history       Independent Researcher
Education history        Harvard University, DDes
Add no other contributors.

------------------------------------------------------------------
6. LICENSE   <- this is the field that was blank last time
------------------------------------------------------------------
Creative Commons Attribution 4.0 International   (CC-BY 4.0)
  If it asks:  Copyright Holders = Hsuan Lo      Year = 2026
Confirm the review page SHOWS a license before submitting.

------------------------------------------------------------------
7. SUBJECTS  (required)
------------------------------------------------------------------
Social and Behavioral Sciences > Sociology > Inequality, Poverty, and Mobility
Social and Behavioral Sciences > Science and Technology Studies
Social and Behavioral Sciences > Urban Studies and Planning
(parent terms Sociology and Social and Behavioral Sciences are added
 automatically; SocArXiv has no Computer Sciences branch)

------------------------------------------------------------------
8. TAGS  (12, enter or comma after each)
------------------------------------------------------------------
algorithm auditing
algorithmic fairness
constrained optimization
fair housing
housing search
large language models
LLM evaluation
New York City
opportunity cost
Pareto dominance
recommender systems
source of income discrimination

------------------------------------------------------------------
9. PUBLICATION FIELDS  (all three: nothing / Not Applicable)
------------------------------------------------------------------
Publication DOI          leave blank
Publication Date         Not Applicable
Publication Citation     Not Applicable
Never put the GitHub URL in Publication DOI. Nothing here was published
anywhere; asserting otherwise would be false.

------------------------------------------------------------------
10. AUTHOR ASSERTIONS
------------------------------------------------------------------
Conflict of Interest ....... No
  If a comment box appears:
  No competing interests. The research was unfunded; all API costs
  (US$57.01) were paid by the author. The author has no employment,
  consulting, financial, or contractual relationship with OpenAI,
  Anthropic, Groq, or RentCast.

Public Data ................ Available
  Link:  https://github.com/hsuanlolo/ai-housing-audit

Public Preregistration ..... Unavailable
  Description:
  No preregistration was filed. The hypotheses, primary outcomes, inference
  procedure, multiple-comparison correction, and the variance-decomposition
  decision rule are all specified in advance within the manuscript (Sections
  3, 6 and 7) and are described throughout as "pre-specified," never as
  "pre-registered." Section 7.6 states this explicitly. An earlier draft of
  that section incorrectly implied a registration had been lodged; the claim
  was removed. Any additional data collection will be registered before it
  begins.

------------------------------------------------------------------
11. SUPPLEMENTS
------------------------------------------------------------------
Skip. Do not create an empty OSF project.

------------------------------------------------------------------
AVOIDING ANOTHER LOSS
------------------------------------------------------------------
- Do not use the browser Back button or the form's "go back" control once
  past the metadata step. Navigate with the form's own step links.
- The abstract is the only long paste; everything else is short. Filling from
  this sheet takes about five minutes.
- Check "My Preprints" under your OSF profile before redoing anything: OSF
  keeps unsubmitted submissions as drafts and yours may still be there.
