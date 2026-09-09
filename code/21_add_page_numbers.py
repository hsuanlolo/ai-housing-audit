"""Stamp page numbers at the bottom centre of a generated PDF.

Why post-process rather than do it in CSS or in Chrome:

  - Chrome's --print-to-pdf offers only --no-pdf-header-footer, an on/off
    switch. Turning the footer ON stamps Chrome's own template, which includes
    the source file:// URL and the print date. Not acceptable in a paper.
  - CSS Paged Media margin boxes (@page { @bottom-center { content: counter(page) } })
    are the correct standard mechanism, but Chrome does not implement them.
  - The DevTools Protocol Page.printToPDF does accept a footerTemplate, but the
    command-line flag does not expose it.

So the number is drawn directly onto each page afterwards. Geometry is derived
from the stylesheet's @page margin so the number always sits inside the margin
and can never overlap body text.
"""
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "paper" / "academic.css"

FONT = "times-roman"      # matches the body serif
SIZE = 9.5
BASELINE_FROM_BOTTOM = 36  # 0.5in


def page_margin_pt():
    m = re.search(r"@page\s*\{[^}]*?margin:\s*([0-9.]+)in", CSS.read_text())
    if not m:
        raise SystemExit(f"could not read @page margin from {CSS}")
    return float(m.group(1)) * 72


def main(path):
    d = fitz.open(path)
    margin = page_margin_pt()
    stamped = 0

    for i, pg in enumerate(d):
        # Chrome leaves a scaling transform active at the end of its content
        # stream. Appended text inherits it: the first attempt at this landed
        # every number at the top-left corner at 2.3pt instead of bottom-centre
        # at 9.5pt. wrap_contents() encloses the existing stream in q/Q so the
        # graphics state is restored before anything is added.
        pg.wrap_contents()
        W, H = pg.rect.width, pg.rect.height
        label = str(i + 1)
        y = H - BASELINE_FROM_BOTTOM

        # never encroach on the text block: the content box ends at H - margin
        if y <= H - margin:
            raise SystemExit(
                f"page number baseline {y:.1f} would sit inside the content box "
                f"(ends at {H - margin:.1f}); raise BASELINE_FROM_BOTTOM")

        w = fitz.get_text_length(label, fontname=FONT, fontsize=SIZE)
        pg.insert_text((W / 2 - w / 2, y), label, fontname=FONT,
                       fontsize=SIZE, color=(0, 0, 0))
        stamped += 1

    d.saveIncr()
    print(f"  page numbers: stamped {stamped} pages "
          f"(centred, {BASELINE_FROM_BOTTOM}pt from foot, inside a "
          f"{margin:.0f}pt margin)")


if __name__ == "__main__":
    main(sys.argv[1])
