X / TWITTER THREAD
9 posts. Character counts verified below (limit 280).
Attach out/figures/figure3_opportunity.png to post 4.
Attach out/figures/figure4_mechanism.png to post 6.

---

[1/9]
I audited whether AI assistants recommend good apartments to renters.

39% of their picks were beaten by a listing on the same screen — $900/month
cheaper AND 3.5 min closer.

Then I found my own headline result was confounded and had to retract it.

Thread.

[2/9]
Setup: 150 synthetic NYC renters. Each gets a pool of 120 real listings.

I computed exactly which ones qualify — real transit times from MTA GTFS
schedules.

So I can ask what most AI audits can't: was something better right there in
the list?

[3/9]
First, the good news, and it's genuinely good.

Constraint compliance is near-perfect. Models broke a stated hard limit on
1.8% of picks.

Random selection from the same pool would break one 66.6% of the time.

They are listening.

[4/9]
Now the bad news.

39% of recommendations were strictly dominated: cheaper AND faster AND no
fewer bedrooms, available in the same pool.

On rent specifically, the models did WORSE than picking at random.
(+$498/mo vs +$261 off the optimum.)

[5/9]
Here's where I was wrong.

I concluded models ignore stated priorities. Titled the paper
"preference infidelity."

But I was comparing different renters whose target moved with their own
priority. Confounded.

So I rebuilt it: same renter, same listings, one sentence changed.

[6/9]
Models honor preferences fine.

"Rent matters most" → median recommended rent drops $646/mo, correct
direction, p<0.0001.

They just don't optimize. Still $606/mo above the 5 cheapest qualifying
listings on the same screen.

Compliance without optimization.

[7/9]
I tried spelling it out: "minimize rent first, use commute only to break ties
within $50."

No improvement. Confirmed by equivalence test against a pre-specified $50
bound, not a non-significant p-value.

It isn't a prompting problem.

[8/9]
It gets worse with more options.

Show 10 listings: the cheapest appears in 93.7% of answers.
Show 80: 53.5%.

The ceiling arrives early. And it replicates across OpenAI and Anthropic
models over a 45x price range, agreeing within $3.

Paying more doesn't fix it.

[9/9]
Also: I found almost no identity-based disparity. 47 of 48 tests null.
Real result, and narrower than it sounds — it's ranking a fixed list, not
open-ended search.

Total cost: $57.01. Code + every call public.

Paper: [OSF DOI]
Code: github.com/hsuanlolo/ai-housing-audit
