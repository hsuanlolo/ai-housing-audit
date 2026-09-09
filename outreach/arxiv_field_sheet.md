# arXiv submission — metadata field sheet

File to upload:  paper/Lo_2026_Following_the_Preference_v2.pdf   (59 pages)
  sha256 27ab8a554970af11c94f2b303258c42e38f1d93b2371b32e852505d8a9baa9be
NOT the SocArXiv v1 (58 pages, sha256 fbc5ca30...). Confirm the file you pick
contains the phrase "Summary of findings" -- that is only in v2.

Rebuild with ./code/20_build_paper.sh, never by invoking pandoc directly. The
hand-run command passed --metadata title= with a shortened title, which made
pandoc emit its own title block on top of the manuscript's own heading, so
page 1 printed the title twice. Fixed by using pagetitle, which sets the HTML
<title> element without rendering a visible block.

------------------------------------------------------------------
TITLE
------------------------------------------------------------------
Following the Preference, Missing the Optimum: Compliance Without Optimization in AI Housing Recommendation

------------------------------------------------------------------
AUTHOR(S)
------------------------------------------------------------------
Hsuan Lo

Plain name, nothing else. arXiv allows an affiliation in parentheses but
"(Harvard University)" would assert a current affiliation you do not hold --
the same reason the paper's byline says DDes (Harvard University) as a degree
and Independent Researcher as the affiliation. No honorifics; arXiv forbids
them. Do not add "DDes" here: arXiv's author field is names only.

------------------------------------------------------------------
ABSTRACT   (1,884 of the 1,920 characters arXiv allows)
------------------------------------------------------------------
Paste as ONE block, no blank lines. arXiv wraps at 80 characters itself and
treats stray carriage returns oddly. Do not begin with the word "Abstract".

Large language models are becoming the first point of contact for consumer search in domains where the stakes are material and the law is explicit. Existing audits show that models steer housing seekers by perceived identity, but none can say what a user loses when a recommender overlooks a suitable option, because none has an enumerated inventory to score omissions against. We audit AI housing recommendation against a verifiable ground truth. For each of 150 synthetic renter scenarios in New York City we build a pool of 120 real listings with known rent, bedrooms, and GTFS-computed transit commute, compute the exact set satisfying the renter's stated constraints, and derive its Pareto frontier. The primary outcome assumes no utility function: a recommendation is strictly dominated if the same pool holds a listing that is cheaper, faster to commute from, and no smaller in bedrooms. Across 9,945 calls to three models from two vendors, constraint compliance is near-perfect (1.8% violation against a 66.6% random floor), but 39.0% of recommendations are strictly dominated, and the dominating listing is a median $900/month cheaper and 3.5 minutes closer. A within-scenario manipulation separates two capabilities usually conflated: changing one sentence moves median recommended rent by $646/month in the correct direction, so preferences are honored, yet recommendations still sit $606/month above the five cheapest qualifying listings on the same screen, and an unambiguous lexicographic instruction yields no improvement under equivalence testing against a pre-specified $50 bound. The gap widens with candidate-set size and replicates across OpenAI and Anthropic models to within $3. We characterize the failure as compliance without optimization, propose dominance-rate instrumentation as a deployable diagnostic, and release all code, prompts, and per-call results.

------------------------------------------------------------------
COMMENTS
------------------------------------------------------------------
59 pages, 4 figures, 31 tables. Code, prompts, and per-call results: https://github.com/hsuanlolo/ai-housing-audit

Note the space after the URL is deliberate -- arXiv warns that a period
directly after a URL gets absorbed into the link. End the field with the URL
or put a space before any following punctuation.

------------------------------------------------------------------
REPORT NUMBER
------------------------------------------------------------------
leave blank   (for institutional report series; you have none)

------------------------------------------------------------------
JOURNAL REFERENCE
------------------------------------------------------------------
leave blank   (only for work already published in a journal)

------------------------------------------------------------------
EXTERNAL DOI
------------------------------------------------------------------
leave blank

Do NOT put the SocArXiv DOI here. This field is for the DOI of a *journal
version* of the article. A preprint DOI is not that, and entering it asserts
a journal publication that does not exist. Once SocArXiv issues the DOI, the
place to mention it is the Comments field, e.g. appended as
"Also available at SocArXiv, doi:10.31235/osf.io/frbcq".

------------------------------------------------------------------
ACM CLASS   (optional)
------------------------------------------------------------------
H.3.3; K.4.1

  H.3.3  Information Search and Retrieval  -- the ranking/recommendation core
  K.4.1  Computers and Society: Public Policy Issues -- the fair-housing frame

------------------------------------------------------------------
MSC CLASS   (optional)
------------------------------------------------------------------
leave blank   (Mathematics Subject Classification; this is not a math paper)

------------------------------------------------------------------
EARLIER FIELDS, FOR REFERENCE
------------------------------------------------------------------
Submission agreement  accept
Authorship            I am submitting as an author of this article
License               CC BY  (irrevocable; matches the CC-BY 4.0 already
                      chosen on SocArXiv and stated in the README)
Archive               cs
Primary class         cs.CY   -- unless the endorsement was issued for a
                      different category, in which case use that one
Cross-list            cs.IR, econ.GN
