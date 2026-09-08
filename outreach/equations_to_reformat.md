# Equations to reformat in Google Docs

Nine display equations, all plain text in the source (no LaTeX anywhere).
Line numbers refer to `paper/manuscript.md` at commit 02bd823.

## How to format these in Google Docs

Do NOT use Insert -> Equation. It is clumsy for this kind of notation and the
output does not reflow with the text. Two better options:

**Option A (fastest, recommended).** Paste the "READY TO PASTE" line below.
It already carries real Unicode subscripts, so it needs no formatting at all
beyond italicising the variable names if you want. Survives copy-paste,
export to PDF, and Word round-trips.

**Option B (for the two regression equations).** Unicode has no subscript
"g" or "s", so Eq. 8 and Eq. 9 cannot be done with characters alone. Type
them normally, select each subscript, and press Ctrl+, (Cmd+, on Mac).

For all nine: set the paragraph to Normal text, centre it, and add 6 pt space
above and below. Keep them in a monospaced or serif font consistently -- do
not mix.

## !! Do not break this one !!

Eq. 2 (strict dominance) is followed in the prose by the phrase
**"with at least one inequality strict."** That qualifier is part of the
definition. If you reformat the three inequalities into a display block and
the sentence gets orphaned or deleted, the definition becomes WEAK dominance,
which is a different measure and would contradict the paper's results.
Keep that phrase immediately after the block.

---

## Section 6 — Notation (line 367, prose)

Runs inline in a sentence, not a display block. Reformat the three symbols
as subscripts in place:

    P_i   ->  Pᵢ     the candidate pool for scenario i
    F_i   ->  Fᵢ     the feasible set, Fᵢ ⊆ Pᵢ
    R_i   ->  Rᵢ     the set of five recommended listings

---

## Eq. 1 — Feasible set  (§6, lines 371-375)

AS IT STANDS
    F_i = { j ∈ P_i : Rent_j ≤ Budget_i
                    AND Bedrooms_j ≥ Bedrooms_i
                    AND Commute_ij ≤ MaxCommute_i }

READY TO PASTE
    Fᵢ = { j ∈ Pᵢ : Rentⱼ ≤ Budgetᵢ ∧ Bedroomsⱼ ≥ Bedroomsᵢ ∧ Commuteᵢⱼ ≤ MaxCommuteᵢ }

If you prefer to keep it on three lines, align the ∧ operators under each
other rather than the AND keywords.

---

## Eq. 2 — Strict dominance  (§6, lines 379-383)

AS IT STANDS
    Rent_j′     ≤ Rent_j
    Commute_ij′ ≤ Commute_ij
    Bedrooms_j′ ≥ Bedrooms_j

READY TO PASTE
    Rentⱼ′ ≤ Rentⱼ ,    Commuteᵢⱼ′ ≤ Commuteᵢⱼ ,    Bedroomsⱼ′ ≥ Bedroomsⱼ

FOLLOWED IMMEDIATELY BY (do not orphan -- see warning above)
    with at least one inequality strict.

---

## Eq. 3 — P1, confirmed violation rate  (§6.1, lines 391-393)

AS IT STANDS
    ViolationRate_i = |{ j ∈ R_i : j violates a verified constraint }| / |R_i|

READY TO PASTE
    ViolationRateᵢ = |{ j ∈ Rᵢ : j violates a verified constraint }| ⁄ |Rᵢ|

---

## Eq. 4 — P2a, pool dominance  (§6.1, lines 401-403)

AS IT STANDS
    PoolDominance_i = |{ j ∈ R_i : ∃ j′ ∈ F_i ⊆ P_i, j′ strictly dominates j }| / |R_i|

READY TO PASTE
    PoolDominanceᵢ = |{ j ∈ Rᵢ : ∃ j′ ∈ Fᵢ ⊆ Pᵢ , j′ strictly dominates j }| ⁄ |Rᵢ|

---

## Eq. 5 — P3, cost gaps  (§6.1, lines 413-416)

AS IT STANDS
    RentGap_i    = median{ Rent_j : j ∈ R_i ∩ F_i }     − median{ Rent_j : j ∈ OracleTop5_i }
    CommuteGap_i = median{ Commute_ij : j ∈ R_i ∩ F_i } − median{ Commute_ij : j ∈ OracleTop5_i }

READY TO PASTE
    RentGapᵢ    = median{ Rentⱼ : j ∈ Rᵢ ∩ Fᵢ } − median{ Rentⱼ : j ∈ OracleTop5ᵢ }
    CommuteGapᵢ = median{ Commuteᵢⱼ : j ∈ Rᵢ ∩ Fᵢ } − median{ Commuteᵢⱼ : j ∈ OracleTop5ᵢ }

Keep these two on separate lines and align the = signs.
Note the minus signs are U+2212 (true minus), not hyphens. Preserve them.

---

## Eq. 6 — Weighted score and opportunity loss  (§6.3, lines 436-440)

Tertiary / robustness only -- no headline claim depends on it.

AS IT STANDS
    Score_ij = −w1·Rent_j − w2·Commute_ij + w3·UnitMatch_ij + w4·TransitAccess_j

    OpportunityLoss_i = max_{j ∈ F_i} Score_ij − max_{j ∈ R_i ∩ F_i} Score_ij

READY TO PASTE
    Scoreᵢⱼ = −w₁·Rentⱼ − w₂·Commuteᵢⱼ + w₃·UnitMatchᵢⱼ + w₄·TransitAccessⱼ

    OpportunityLossᵢ = max  Scoreᵢⱼ − max  Scoreᵢⱼ
                     j ∈ Fᵢ          j ∈ Rᵢ ∩ Fᵢ

The two max operators take subscripts UNDER the operator. Unicode cannot do
that; either set the range as a small line beneath (as above) or write it
inline as max{ Scoreᵢⱼ : j ∈ Fᵢ }, which is unambiguous and much easier to
typeset. I would use the inline form.

---

## Eq. 7 — Fairness gap  (§6.4, lines 448-450)

AS IT STANDS
    FairnessGap(A, B) = E[ Y_i | Identity = A ] − E[ Y_i | Identity = B ]

READY TO PASTE
    FairnessGap(A, B) = E[ Yᵢ | Identity = A ] − E[ Yᵢ | Identity = B ]

The vertical bars here mean "conditional on", not absolute value. If your
formatting makes them ambiguous next to Eq. 3 and 4, which use |·| for
cardinality, consider E[ Yᵢ ; Identity = A ] or add a note.

---

## Eq. 8 — Primary fixed-effects model  (§7.3, lines 474-476)

Specified but NOT estimated in this version. Section 7.3 says so; keep that
sentence attached.

AS IT STANDS
    Y_igmr = α_i + β·IdentityCue_g + λ_m + δ_r + ε_igmr

NEEDS MANUAL SUBSCRIPTS (no Unicode subscript g or s exists)
    Y[igmr] = α[i] + β·IdentityCue[g] + λ[m] + δ[r] + ε[igmr]

    -> type as: Yigmr = αi + β·IdentityCueg + λm + δr + εigmr
       then select each of  igmr, i, g, m, r, igmr  and press Ctrl+,

---

## Eq. 9 — Architecture-interaction model  (§7.3, lines 480-483)

Also specified but not estimated.

AS IT STANDS
    Y_igsmr = α_i + β1·Grounded_s + β2·ConstraintFirst_s + β3·IdentityCue_g
              + β4·(ConstraintFirst_s × IdentityCue_g) + λ_m + δ_r + ε_igsmr

NEEDS MANUAL SUBSCRIPTS
    Yigsmr = αi + β₁·Groundeds + β₂·ConstraintFirsts + β₃·IdentityCueg
             + β₄·(ConstraintFirsts × IdentityCueg) + λm + δr + εigsmr

    The β coefficient numbers CAN use Unicode: β₁ β₂ β₃ β₄  (paste directly).
    Only the trailing letter subscripts need Ctrl+,.
    Indent the continuation line so the + aligns under the first term's +.

---

## Also worth a subscript pass (prose, not display)

These appear in running text and currently read as underscores:

    F_i      15 occurrences   lines 173, 196, 342, 344, 354, 357, 359, 367 ...
    P_i       4 occurrences   lines 194, 367, 377
    R_i       2 occurrences   lines 367, 418
    S_rand    7 occurrences   lines 163, 165, 216, 542, 561, 662

S_rand is a label for the random-selection chance floor, not a variable. Set
it as S_rand with "rand" subscripted, and keep it consistent everywhere --
it appears in three tables as a row label too.

Note lines 354 and 359 write the cardinality as |F_i| and one of them escapes
the pipes as \|F_i\|. In Docs both should read |Fᵢ|.
