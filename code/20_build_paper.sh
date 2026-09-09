#!/usr/bin/env bash
# Build the paper's distributable formats from paper/manuscript.md.
#
# Run this instead of invoking pandoc by hand. The hand-run commands carried a
# bug for several builds: passing --metadata title=... makes pandoc's standalone
# HTML template emit its own <h1 class="title"> title block, which appeared ON
# TOP of the manuscript's own "# " heading, so page 1 showed the title twice --
# once truncated, once in full. The HTML <title> element is set with pagetitle,
# which does not render a visible block.
set -euo pipefail
cd "$(dirname "$0")/.."

MD=paper/manuscript.md
OUT=${1:-paper/Lo_2026_Following_the_Preference_v2}
TITLE="Following the Preference, Missing the Optimum: Compliance Without Optimization in AI Housing Recommendation"

PANDOC_ARGS=(
  --from=markdown+pipe_tables+tex_math_dollars
  --resource-path="paper:.:out/figures"
  --metadata pagetitle="$TITLE"     # <title> only; no rendered title block
)

echo "building html ..."
pandoc "$MD" "${PANDOC_ARGS[@]}" --to=html5 --standalone --self-contained \
  --css=paper/academic.css -o paper/manuscript.html

echo "building docx ..."
pandoc "$MD" "${PANDOC_ARGS[@]}" --to=docx --toc --toc-depth=2 -o "$OUT.docx"

echo "building pdf ..."
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --no-pdf-header-footer --no-sandbox \
  --print-to-pdf="$OUT.pdf" --virtual-time-budget=20000 \
  "file://$PWD/paper/manuscript.html" 2>/dev/null | grep -i "bytes written" || true

python3 code/check_pdf.py "$OUT.pdf"
