LINKEDIN POST
Paste as plain text. LinkedIn strips markdown; the line breaks below are
deliberate (it collapses single newlines, so blank lines matter).
Put the link in the FIRST COMMENT, not the post body -- LinkedIn suppresses
reach on posts with outbound links.

---

I spent six weeks auditing whether AI assistants give renters good apartment
recommendations. The headline finding I started with turned out to be wrong,
and finding that out was the most useful part.

The setup: 150 synthetic NYC renters, each with a real budget, bedroom need,
and commute limit. For each one I built a pool of 120 real listings and
computed, exactly, which ones qualified — using MTA GTFS schedules to get true
transit times. So for every recommendation I could ask a question most audits
can't: was there something better sitting in the same list?

Often, yes. 39% of recommendations were strictly dominated — beaten on rent
AND commute AND bedroom count by another listing the model had just been
shown. When that happened, the better listing was typically $900/month cheaper
and 3.5 minutes closer. Simultaneously.

Here's what I got wrong. My first read was that models ignore what users tell
them to prioritize. I called it "preference infidelity" and it was the paper's
title.

Then I noticed the comparison was confounded: I was comparing across different
renters whose target was defined by their own stated priority. So I rebuilt it
as a within-renter test — same person, same listings, one sentence changed.

Models honor stated preferences just fine. Say "rent matters most" and median
recommended rent drops $646/month, in the right direction.

They just don't optimize. Even when told rent is the priority, recommendations
sat $606/month above the five cheapest qualifying listings on the same screen.
Spelling out an unambiguous rule changed nothing — I confirmed that with an
equivalence test rather than resting on a non-significant p-value.

So I retracted my own headline, renamed the paper, and reframed it:
compliance without optimization. The models follow the rules. They don't find
the best answer.

Two details that surprised me:
— On rent specifically, the models did worse than picking at random.
— It replicates across OpenAI and Anthropic models spanning a 45x price
   range, agreeing to within $3. Paying more doesn't fix it.
— I found almost no identity-based disparity: 47 of 48 tests came back null.
   That's a real result too, and narrower than it sounds — it holds for
   ranking a fixed list, not for open-ended search, where others have found
   steering.

Total API cost: $57.01. Every line of code, prompt, and per-call result is
public.

Happy to be told I'm wrong about any of this — that's rather the point.

#AI #MachineLearning #Housing #AlgorithmicFairness #LLM

---

FIRST COMMENT (post immediately after):
Paper: [OSF DOI]
Code and data: https://github.com/hsuanlolo/ai-housing-audit
