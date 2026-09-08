"""Fetch ACS 2023 5-year tract covariates for the five NYC counties.

Fills two things that were previously outstanding:
  - the ACS borough column of Table 2b (county-level tenure, B25003)
  - the tract covariates that the S3 neighborhood-exposure measure needs (6.2)

Requires a Census API key in keys/census.txt. The key is never printed and the
request URL is never logged, because the key travels in the query string.

Note on failure modes: an unauthenticated request returns HTTP 200 and
redirects to an HTML page titled "Missing Key"; an unactivated key returns
HTTP 200 with "Invalid Key". Neither raises. We therefore check the response
BODY, not the status code.
"""
import sys, json, time, urllib.request, urllib.parse
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_key

ROOT   = Path(__file__).resolve().parents[1]
INTER  = ROOT/"data"/"interim"
COUNTIES = {"005": "Bronx", "047": "Brooklyn", "061": "Manhattan",
            "081": "Queens", "085": "Staten Island"}
BASE = "https://api.census.gov/data/2023/acs/acs5"

VARS = {
    "B19013_001E": "median_hh_income",
    "B25064_001E": "median_gross_rent",
    "B25071_001E": "median_rent_pct_income",   # rent burden
    "B25003_001E": "occupied_units",
    "B25003_003E": "renter_occupied",
    "B03002_001E": "pop_total",
    "B03002_003E": "pop_white_nh",
    "B03002_004E": "pop_black_nh",
    "B03002_006E": "pop_asian_nh",
    "B03002_012E": "pop_hispanic",
}

def get(params, key, tries=4):
    """GET with body-based error detection, retry, and key-safe errors.

    Two hazards handled here:

    1. Query values contain spaces (`in=state:36 county:005`). urllib will not
       encode them and raises InvalidURL, so params are encoded explicitly.

    2. urllib puts the full URL into the exception message, and the Census key
       travels in the query string -- an unguarded traceback therefore prints
       the credential. Every exception is caught and re-raised with the key
       redacted, so the key can never reach a log or a traceback.
    """
    url = f"{BASE}?{params}&key={key}"

    def scrub(msg):
        return str(msg).replace(key, "<REDACTED>")

    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                body = r.read().decode()
            if body.lstrip().startswith("<"):
                import re
                t = re.search(r"<title>(.*?)</title>", body)
                raise RuntimeError(f"Census returned an HTML error page: "
                                   f"{t.group(1) if t else 'unknown'}")
            return json.loads(body)
        except RuntimeError:
            raise
        except Exception as e:
            if i == tries - 1:
                raise RuntimeError(
                    f"request failed after {tries} tries: "
                    f"{type(e).__name__}: {scrub(e)}") from None
            print(f"    retry {i+1} after {type(e).__name__}")
            time.sleep(5 * (i + 1))


def q(**kw):
    """Build an encoded query string; Census wants ':' and ',' literal."""
    return urllib.parse.urlencode(kw, safe=":,*")


def main():
    key = load_key("census")
    if not key:
        sys.exit("no Census key found; put it in keys/census.txt")

    # ---- county tenure, for Table 2b
    cols = "NAME,B25003_001E,B25003_002E,B25003_003E"
    d = get(q(**{"get": cols, "for": f"county:{','.join(COUNTIES)}",
                 "in": "state:36"}), key)
    cty = pd.DataFrame(d[1:], columns=d[0])
    cty["borough"] = cty.county.map(COUNTIES)
    for c in ["B25003_001E", "B25003_002E", "B25003_003E"]:
        cty[c] = cty[c].astype(int)
    cty = cty.rename(columns={"B25003_001E": "occupied_units",
                              "B25003_002E": "owner_occupied",
                              "B25003_003E": "renter_occupied"})
    cty["renter_share_of_nyc"] = cty.renter_occupied / cty.renter_occupied.sum()
    cty[["borough","occupied_units","owner_occupied","renter_occupied",
         "renter_share_of_nyc"]].to_csv(INTER/"acs_county_tenure.csv", index=False)
    print(f"county tenure -> {INTER/'acs_county_tenure.csv'}")

    # ---- tract covariates, for S3
    frames = []
    varlist = ",".join(VARS)
    for fips, name in COUNTIES.items():
        d = get(q(**{"get": f"NAME,{varlist}", "for": "tract:*",
                     "in": f"state:36 county:{fips}"}), key)
        t = pd.DataFrame(d[1:], columns=d[0])
        t["borough"] = name
        frames.append(t)
        print(f"  {name:<14} {len(t):>5} tracts")
    tr = pd.concat(frames, ignore_index=True)
    tr["GEOID"] = tr.state + tr.county + tr.tract
    tr = tr.rename(columns=VARS)

    num = list(VARS.values())
    for c in num:
        tr[c] = pd.to_numeric(tr[c], errors="coerce")
        # ACS uses large negative sentinels for suppressed estimates
        tr.loc[tr[c] < -1e6, c] = pd.NA

    tr["renter_share"] = tr.renter_occupied / tr.occupied_units
    for c, lbl in [("pop_white_nh","pct_white_nh"), ("pop_black_nh","pct_black_nh"),
                   ("pop_asian_nh","pct_asian_nh"), ("pop_hispanic","pct_hispanic")]:
        tr[lbl] = tr[c] / tr.pop_total
    tr["pct_nonwhite"] = 1 - tr.pct_white_nh

    keep = (["GEOID","borough","median_hh_income","median_gross_rent",
             "median_rent_pct_income","renter_share","pct_white_nh",
             "pct_black_nh","pct_asian_nh","pct_hispanic","pct_nonwhite",
             "pop_total","occupied_units"])
    tr[keep].to_csv(INTER/"acs_tract_covariates.csv", index=False)
    print(f"\n{len(tr):,} tracts -> {INTER/'acs_tract_covariates.csv'}")
    print(tr[["median_hh_income","median_gross_rent","median_rent_pct_income",
              "renter_share","pct_nonwhite"]].describe().round(2).to_string())

if __name__ == "__main__":
    main()
