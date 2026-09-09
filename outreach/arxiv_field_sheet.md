# arXiv submission — metadata field sheet

File to upload:  paper/Lo_2026_Following_the_Preference_v2.pdf   (58 pages)
  sha256 f2a317b397746442697beb8c899809258f755f522c649793558a4f1b0559cf35
NOT the SocArXiv v1 (also 58 pages, sha256 fbc5ca30...). Confirm the file you pick
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
ABSTRACT
------------------------------------------------------------------
Copy the whole of  outreach/arxiv_abstract.txt  -- it holds the abstract
and nothing else. 1,877 characters of the 1,920 allowed, pure ASCII,
single block, no leading "Abstract".

TWO TRAPS ALREADY HIT, BOTH NOW DESIGNED OUT:

  Length. Selecting the abstract out of this sheet caught the dash
  separator line and came to 1,949, over the cap. Hence the separate file.

  Dollar signs. arXiv runs MathJax over the abstract, so a bare $ opens
  math mode and the next $ closes it. With five amounts in the text,
  everything between "$900" and "$646" was rendered as a formula: spaces
  collapsed and the words ran together as
  "900/monthcheaperand3.5minutescloser". Every amount is now written as
  "900 USD/month", so the file contains no $, backslash, underscore,
  caret, brace or tilde at all. Escaping as \$ would also work where
  MathJax runs, but arXiv abstracts also go out in listing emails, RSS
  and API responses where the backslash can show through, so the symbol
  is avoided rather than escaped.

  Percent signs are kept: % is only special inside math mode and is
  routine in arXiv abstracts.

------------------------------------------------------------------
COMMENTS
------------------------------------------------------------------
58 pages, 4 figures, 31 tables. Code, prompts, and per-call results: https://github.com/hsuanlolo/ai-housing-audit

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
