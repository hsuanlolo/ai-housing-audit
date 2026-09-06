"""
Name pool for identity conditions C1 / C2.

PROVENANCE. These names are the first-name lists from Bertrand & Mullainathan
(2004), "Are Emily and Greg More Employable than Lakisha and Jamal?", AER 94(4),
Appendix Table A1 -- the most widely replicated correspondence-audit name set.

MANDATORY VALIDATION STEP BEFORE THE MAIN GRID.
Gaddis (2017, Sociological Science 4:469-489) showed that several B&M names carry
unusually low perceived-SES signals, so a raw B&M contrast confounds race with
class. Before any main-grid call we must:
  (1) obtain Gaddis's published perception scores,
  (2) fill perceived_race and perceived_ses below,
  (3) DROP names whose perceived-SES deviates from the cross-pool median by more
      than a pre-registered threshold,
  (4) report the surviving names and their scores in Appendix B.

perceived_race / perceived_ses are deliberately None. They are NOT estimated,
guessed, or imputed here. Any script that needs them must fail loudly.
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

# Names Gaddis (2017) specifically flags as SES-atypical. Excluded pending
# validated scores; listed explicitly so the exclusion is auditable.
FLAGGED_PENDING_VALIDATION = {"Lakisha", "Tremayne", "Latonya", "Kenya"}

PERCEPTION_SCORES = {}   # name -> {"perceived_race": None, "perceived_ses": None}

def usable_pool(pool):
    return [(n, g) for (n, g) in pool if n not in FLAGGED_PENDING_VALIDATION]

def validation_complete():
    names = [n for n, _ in usable_pool(POOL_A) + usable_pool(POOL_B)]
    return all(
        PERCEPTION_SCORES.get(n, {}).get("perceived_ses") is not None
        for n in names
    )
