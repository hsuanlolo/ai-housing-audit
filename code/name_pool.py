"""
Name pool for identity conditions C1 / C2.

PROVENANCE. First names are the lists from Bertrand & Mullainathan (2004),
"Are Emily and Greg More Employable than Lakisha and Jamal?", AER 94(4),
Appendix Table A1. Surnames are drawn independently so the first-name signal
is not reinforced by an unvalidated surname signal.

WHAT THE LITERATURE ACTUALLY PROVIDES, AND WHAT IT DOES NOT.

  Gaddis (2017), Sociological Science 4:469-489, measures perceived RACE. Its
  Table 1 additionally marks each name's quartile of mother's education within
  race -- bold for lowest, italic for highest -- which is an OBJECTIVE SES
  correlate, not a perceived-SES score. That marking is recoverable exactly
  from the PDF and is recorded in MOTHERS_EDUCATION_QUARTILE below.

  Per-name perceived race appears in Gaddis Figures 1-2 as raster bar charts.
  Per-name perceived SOCIAL CLASS is not in Gaddis (2017) at all; it is in
  Crabtree, Gaddis, Holbein & Larsen (2022), Sociological Science 9:454-472,
  Figure 4 -- also a raster figure. Neither yields a numeric per-name column
  without reading values off a chart, so neither is transcribed here.

TWO DEFECTS, FOUND AFTER DATA COLLECTION. Documented in Appendix B.

  1. FLAGGED_PENDING_VALIDATION was recorded as "names Gaddis specifically
     flags as SES-atypical". Against Gaddis Table 1 that holds for Lakisha and
     Latonya (both lowest quartile) but NOT for Kenya or Tremayne (both middle
     quartile). Two names were therefore excluded without basis.

  2. Latoya and Tamika are lowest-quartile and were RETAINED, which the stated
     rule would have excluded.

  The exclusion is applied identically across every scenario and condition, so
  it cannot manufacture an identity contrast. It is preserved unchanged because
  the data were collected under it; changing it now would silently desynchronise
  the code from out/audit_log.jsonl. It is corrected in the write-up, not here.

CONSEQUENCE FOR INTERPRETATION. The pools are unbalanced on the SES correlate:
Pool A is 11/18 highest-quartile with no lowest-quartile name; Pool B has no
highest-quartile name and two lowest-quartile names. C1/C2 is therefore a JOINT
race-and-class cue. The confound is single-directional and so biases toward
detecting a difference; none is detected, which makes the null stronger rather
than weaker, but it forbids attributing the absent effect to race or class
separately.
"""

# Pool A and Pool B are labelled by the signal B&M constructed them to carry.
# Surnames are paired separately so that the first-name signal is not reinforced
# by a surname signal we have not validated.
POOL_A = [  # B&M "white-sounding" first names
    ("Allison","F"),("Anne","F"),("Carrie","F"),("Emily","F"),("Jill","F"),
    ("Laurie","F"),("Kristen","F"),("Meredith","F"),("Sarah","F"),
    ("Brad","M"),("Brendan","M"),("Geoffrey","M"),("Greg","M"),("Brett","M"),
    ("Jay","M"),("Matthew","M"),("Neil","M"),("Todd","M"),
]
POOL_B = [  # B&M "Black-sounding" first names
    ("Aisha","F"),("Ebony","F"),("Keisha","F"),("Kenya","F"),("Latonya","F"),
    ("Lakisha","F"),("Latoya","F"),("Tamika","F"),("Tanisha","F"),
    ("Darnell","M"),("Hakim","M"),("Jamal","M"),("Jermaine","M"),("Kareem","M"),
    ("Leroy","M"),("Rasheed","M"),("Tremayne","M"),("Tyrone","M"),
]

SURNAMES = ["Baker","Carter","Ellis","Hayes","Jenkins","Morgan","Palmer",
            "Reynolds","Sutton","Warren"]

# Excluded before the main grid. Recorded at the time as "flagged by Gaddis";
# that attribution holds for Lakisha and Latonya only (see module docstring).
# Frozen: the collected data depend on it.
FLAGGED_PENDING_VALIDATION = {"Lakisha", "Tremayne", "Latonya", "Kenya"}

# Quartile of mother's education within race, read from the bold/italic
# encoding of Gaddis (2017) Table 1. This IS sourced and exact.
MOTHERS_EDUCATION_QUARTILE = {
    # Pool A
    "Allison": "highest", "Anne": "highest", "Carrie": "middle",
    "Emily": "highest", "Jill": "highest", "Kristen": "middle",
    "Laurie": "middle", "Meredith": "highest", "Sarah": "highest",
    "Brad": "middle", "Brendan": "highest", "Brett": "highest",
    "Geoffrey": "highest", "Greg": "middle", "Jay": "middle",
    "Matthew": "highest", "Neil": "highest", "Todd": "middle",
    # Pool B
    "Aisha": "middle", "Ebony": "middle", "Keisha": "middle",
    "Kenya": "middle", "Lakisha": "lowest", "Latonya": "lowest",
    "Latoya": "lowest", "Tamika": "lowest", "Tanisha": "middle",
    "Darnell": "middle", "Hakim": "middle", "Jamal": "middle",
    "Jermaine": "middle", "Kareem": "middle", "Leroy": "middle",
    "Rasheed": "middle", "Tremayne": "middle", "Tyrone": "middle",
}

# Per-name perceived race and perceived social class are deliberately absent.
# They exist in the literature only as figures (see module docstring) and are
# NOT estimated, guessed, or read off a chart here.
PERCEPTION_SCORES = {}   # name -> {"perceived_race": None, "perceived_ses": None}

def usable_pool(pool):
    return [(n, g) for (n, g) in pool if n not in FLAGGED_PENDING_VALIDATION]

def validation_complete():
    names = [n for n, _ in usable_pool(POOL_A) + usable_pool(POOL_B)]
    return all(
        PERCEPTION_SCORES.get(n, {}).get("perceived_ses") is not None
        for n in names
    )
