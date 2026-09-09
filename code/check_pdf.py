"""Post-build assertions on the generated PDF.

Two failure modes have already shipped in this project and are checked here so
they cannot recur silently.

1. Duplicate title. Passing --metadata title=... to pandoc makes the standalone
   HTML template emit its own <h1 class="title">, which printed above the
   manuscript's own heading. Fixed by using pagetitle; asserted here.

2. Clipped box borders. Chrome's print-to-PDF clips at the @page content box.
   With margin:1in on letter the content box ended at exactly 540pt while the
   body was also exactly 6.5in wide, so a 0.75pt border stroke on a full-width
   table or <pre> was centred at ~540.4pt and more than half of it fell outside
   the clip. The visible symptom was the right border line vanishing from most
   tables and equation blocks while the text inside them was untouched, which
   makes it easy to miss. Asserted here against the real margin.
"""
import re
import sys
from pathlib import Path

import fitz

CSS = Path(__file__).resolve().parents[1] / "paper" / "academic.css"


def page_margin_in():
    """Read the @page margin from the stylesheet that produced the PDF.

    Hardcoding this was wrong: the checker then computes a clip edge for a
    margin the build may not have used, and silently passes a file it should
    fail. Deriving it from the CSS keeps the two in step.
    """
    m = re.search(r"@page\s*\{[^}]*?margin:\s*([0-9.]+)in", CSS.read_text())
    if not m:
        raise SystemExit(f"could not read @page margin from {CSS}")
    return float(m.group(1))

def main(path):
    d = fitz.open(path)
    W = d[0].rect.width
    text = "".join(p.get_text() for p in d)
    lines = [l for l in d[0].get_text().split("\n") if l.strip()][:3]

    print(f"  pages {d.page_count}   images {sum(len(p.get_images()) for p in d)}")
    print(f"  searchable: {len(text):,} chars")
    print("  page-1 first lines:")
    for l in lines:
        print("    ", l[:96])

    dup = bool(lines) and lines[0].strip() and \
          lines[1].strip().startswith(lines[0].strip()[:40])
    print(f"  duplicate title : {'YES -- BROKEN' if dup else 'no'}")

    clip_right = W - page_margin_in() * 72
    # Check EVERY drawing, not just wide stroked rects. Collapsed table borders
    # are emitted as many thin per-cell segments, so a width filter sees only
    # the <pre> boxes and would have passed the very bug this exists to catch.
    worst, bad = 0.0, []
    for i, pg in enumerate(d):
        for dr in pg.get_drawings():
            r = dr["rect"]
            worst = max(worst, r.x1)
            if r.x1 > clip_right - 0.5:
                bad.append((round(r.x1, 2), i + 1))

    print(f"  clip edge {clip_right:.1f}pt; widest stroked border {worst:.2f}pt")
    if bad:
        print(f"  clipped borders : YES -- {len(bad)} boxes, e.g. {bad[:3]}")
    else:
        print("  clipped borders : none")

    return 1 if (dup or bad) else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
