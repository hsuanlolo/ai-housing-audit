# Posting to SocArXiv (on OSF) — step by step

Verified against OSF and SocArXiv documentation on 8 September 2026. Where a
label may have changed in their current interface, it is marked [VERIFY].
OSF has restructured its help site recently and two of its own articles on
this flow now return 404, so treat exact wording as approximate and the
sequence as reliable.

Total time: about 25 minutes of your effort, then under 2 days of waiting.
Cost: nothing.

--------------------------------------------------------------------------
WHY SocArXiv AND NOT PLAIN "OSF PREPRINTS"
--------------------------------------------------------------------------
Both live on the same OSF platform and use the same submission form. The
difference is the moderation queue and the disciplinary home:

  SocArXiv          social sciences     screening expected under 2 days
  OSF Preprints     no discipline       allow 4-5 business days

Your paper is housing plus algorithmic fairness, which is squarely social
science, so SocArXiv is both the faster queue and the better-matched archive.
You pick the server during submission, so this is not a separate signup.

--------------------------------------------------------------------------
STEP 1 - CREATE THE ACCOUNT (5 min)
--------------------------------------------------------------------------
1. Go to  https://osf.io
2. Click  "Sign Up"  (top right).
3. Register with  hsuanlo@alumni.harvard.edu.
   Use the alumni address, not Gmail: OSF displays your email domain on the
   profile, and it is the same address on the paper's byline.
4. Confirm the verification email. Check spam if it does not arrive; Harvard
   forwarding sometimes delays it.
5. Optional but worth two minutes - on your OSF profile, add:
      Employment / Affiliation:  Independent Researcher
      Education:                 Harvard University, DDes
      ORCID:                     link it if you have one; if not, get one free
                                 at https://orcid.org/register - it takes about
                                 three minutes and permanently disambiguates
                                 your name on every future paper. Recommended.

--------------------------------------------------------------------------
STEP 2 - START THE SUBMISSION (2 min)
--------------------------------------------------------------------------
6. Go to  https://osf.io/preprints
7. Click  "Add a Preprint"  (a tab near the top of the page).
8. You are asked to choose a preprint service. Select  SocArXiv.
9. Click the button at the bottom to continue - labelled "Create preprint"
   or "Next" depending on version. [VERIFY]

--------------------------------------------------------------------------
STEP 3 - UPLOAD THE FILE (2 min)
--------------------------------------------------------------------------
10. Choose  "Upload from your computer"  (the alternative is pulling from an
    existing OSF Project, which you do not have).
11. Click  "Upload file"  and select:

       paper/Lo_2026_Following_the_Preference.pdf

    Upload the PDF, not the .docx. Both are accepted, but the PDF is what you
    want people to cite and it renders identically everywhere. It is 58 pages,
    1.8 MB, and text-searchable (131,182 extractable characters), which is a
    SocArXiv moderation requirement - I checked this.

--------------------------------------------------------------------------
STEP 4 - TITLE AND ABSTRACT (5 min)
--------------------------------------------------------------------------
12. Title - paste exactly:

Following the Preference, Missing the Optimum: Compliance Without Optimization in AI Housing Recommendation

13. Abstract - paste the 325-word version from  outreach/osf_abstract.txt
    (the section marked ABSTRACT). Do NOT paste the manuscript's own abstract:
    it is roughly 900 words and reads badly in a submission box.

    Minimum is 20 characters, so there is no upper problem here.

--------------------------------------------------------------------------
STEP 5 - METADATA (8 min)
--------------------------------------------------------------------------
14. Contributors. You are added automatically as the sole author and
    administrator. Add nobody else. Leave yourself as bibliographic.

15. Subjects / disciplines. At least one top-level selection is required.
    Choose:
       Social and Behavioral Sciences  >  Sociology       [or Urban Studies
                                                           and Planning if
                                                           offered]
    Add as secondary if available:
       Social and Behavioral Sciences  >  Urban Studies and Planning
       Physical Sciences and Mathematics  >  Computer Sciences
    Pick the closest available labels; the taxonomy is fixed and yours may not
    contain every branch above. [VERIFY]

16. License. Choose  CC-By Attribution 4.0 International (CC-BY 4.0).
    Reason: it permits reuse with credit, satisfies every funder and journal
    preprint policy you are likely to meet, and does not waive attribution
    the way CC-0 does. Do not choose "No license" - it makes reuse legally
    unclear and some indexers skip it.

17. Conflict of interest. State that you have none. You funded the API costs
    personally; that is not a conflict, but if there is a free-text box, the
    honest one-liner is:
       "No competing interests. API costs were paid by the author."

18. Original publication date / DOI of published version. LEAVE BLANK.
    This paper has not been published anywhere and has no prior DOI. Do not
    put the GitHub URL here.

19. Supplemental materials, if the form offers a field. Put:
       https://github.com/hsuanlolo/ai-housing-audit
    If there is no such field, the repository is already cited in the
    abstract's last line, so nothing is lost.

--------------------------------------------------------------------------
STEP 6 - SUBMIT (1 min)
--------------------------------------------------------------------------
20. Review the preview. Check three things specifically:
       - the byline reads  Hsuan Lo, DDes (Harvard University)
       - the abstract is the 325-word one, not the long one
       - the file opens and the four figures are visible
21. Submit for moderation. The button is "Submit" or "Create preprint". [VERIFY]

22. The preprint is now PRIVATE and PENDING. It is not public, has no DOI, and
    is not indexed until a SocArXiv moderator accepts it. Expect under two
    days. You get an email on acceptance.

--------------------------------------------------------------------------
STEP 7 - AFTER ACCEPTANCE
--------------------------------------------------------------------------
23. You receive a DOI of the form  10.31235/osf.io/XXXXX  and a permanent URL.

24. Fill the DOI into the two placeholders:
       outreach/linkedin_post.md   - the FIRST COMMENT block
       outreach/x_thread.md        - post 9

25. Add the DOI to the repository README so the code and paper point at each
    other. Tell me the DOI and I will do this.

26. Only then post to LinkedIn and X. Posting before the DOI exists wastes the
    launch, because the link is the whole point.

--------------------------------------------------------------------------
IF MODERATION REJECTS IT
--------------------------------------------------------------------------
The SocArXiv checklist asks whether the work is scholarly, correctly
categorised, authentic, correctly attributed, in a supported language, and in
a searchable format. Your paper satisfies all six. The realistic failure modes
are a wrong subject category or a file that is not text-searchable, both of
which are fixable in minutes and both of which are already handled above.
Rejection is not a judgement on the research - there is no peer review here.
