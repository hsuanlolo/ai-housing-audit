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

python3 - "$OUT.pdf" <<'PY'
import fitz, sys, re
d = fitz.open(sys.argv[1]); t = "".join(p.get_text() for p in d)
lines = [l for l in d[0].get_text().split("\n") if l.strip()][:3]
print(f"  pages {d.page_count}  images {len(re.findall(r'/Subtype', open(sys.argv[1],'rb').read().decode('latin1')))//1 and len([1 for pg in d for _ in pg.get_images()])}")
print(f"  searchable: {len(t):,} chars")
print("  page-1 first lines:")
for l in lines: print("    ", l[:100])
dup = lines[0].strip() and lines[1].strip().startswith(lines[0].strip()[:40])
print(f"  DUPLICATE TITLE: {'YES -- still broken' if dup else 'no'}")
PY
