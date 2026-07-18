"""Configuration for the College Specs data pipeline: source URLs, field maps, schema."""

# ---------------------------------------------------------------------------
# Source URLs (verified live 2026-07-17)
# ---------------------------------------------------------------------------

# College Scorecard: the institution-level file is date-stamped per release, so we
# scrape the current link from the data page and fall back to a known-good URL.
SCORECARD_DATA_PAGE = "https://collegescorecard.ed.gov/data"
SCORECARD_LINK_RE = r"https://[^\s\"'<>]*Most-Recent-Cohorts-Institution_(\d+)\.zip"
SCORECARD_FALLBACK_URL = (
    "https://ed-public-download.scorecard.network/downloads/"
    "Most-Recent-Cohorts-Institution_06102026.zip"
)

# Opportunity Insights Mobility Report Cards (static release, 2017-18).
OI_TABLE1_URL = "https://opportunityinsights.org/wp-content/uploads/2018/03/mrc_table1.csv"
OI_TABLE11_URL = "https://opportunityinsights.org/wp-content/uploads/2018/04/mrc_table11.csv"
OI_VINTAGE = "2017-18 release (1980-91 birth cohorts)"

# IPEDS ADM survey (admissions yield). Probe newest-first; ADM2023 is latest as of 2026-07.
IPEDS_ADM_URL_TEMPLATE = "https://nces.ed.gov/ipeds/datacenter/data/ADM{year}.zip"
IPEDS_ADM_PROBE_START_YEAR = 2026  # probe this year downward
IPEDS_ADM_MIN_YEAR = 2021

# IPEDS SFA (Student Financial Aid) survey -> average grant aid. Concatenated academic-year
# naming: SFA{startYY}{endYY}, e.g. SFA2223 = academic year 2022-23. Probe by end-year.
IPEDS_SFA_URL_TEMPLATE = "https://nces.ed.gov/ipeds/datacenter/data/{name}.zip"
IPEDS_SFA_PROBE_START_YEAR = 2027  # end-year of the academic year; probe downward
IPEDS_SFA_MIN_YEAR = 2020

# IPEDS IC (Institutional Characteristics) survey -> undergraduate application fee.
# The newest year's provisional/directory release lacks APPLFEEU, so the pipeline probes
# newest-first and takes the newest IC file that actually contains the fee column.
IPEDS_IC_URL_TEMPLATE = "https://nces.ed.gov/ipeds/datacenter/data/IC{year}.zip"
IPEDS_IC_PROBE_START_YEAR = 2027
IPEDS_IC_MIN_YEAR = 2020

# Clery Act campus safety. Unofficial endpoints reverse-engineered from the SPA.
# NOTE: the file endpoint rejects HEAD requests (405) - always plain GET.
CLERY_FILELIST_URL = "https://ope.ed.gov/campussafety/api/dataFiles/fileList"
CLERY_FILE_URL = "https://ope.ed.gov/campussafety/api/dataFiles/file?fileName={name}"

# Some ED sites 403 the default python-requests user agent.
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 CollegeSpecsPipeline/1.0"
    )
}

# ---------------------------------------------------------------------------
# Scorecard columns to read (of ~3,300) and row filter
# ---------------------------------------------------------------------------

SCORECARD_COLS = [
    # identity / filtering
    "UNITID", "OPEID", "OPEID6", "INSTNM", "CITY", "STABBR", "INSTURL",
    "CONTROL", "LOCALE", "MAIN", "CURROPER", "PREDDEG", "HIGHDEG", "CCBASIC",
    # size & setting
    "UGDS", "STUFACR",
    # admissions
    "ADM_RATE", "SATVR25", "SATVR75", "SATMT25", "SATMT75", "SAT_AVG",
    "ACTCM25", "ACTCM75", "ADMCON7",
    # cost
    "TUITIONFEE_IN", "TUITIONFEE_OUT", "NPT4_PUB", "NPT4_PRIV",
    "NPT41_PUB", "NPT42_PUB", "NPT43_PUB", "NPT44_PUB", "NPT45_PUB",
    "NPT41_PRIV", "NPT42_PRIV", "NPT43_PRIV", "NPT44_PRIV", "NPT45_PRIV",
    "COSTT4_A", "PCTPELL", "PCTFLOAN", "GRAD_DEBT_MDN", "GRAD_DEBT_MDN10YR",
    # outcomes
    "C150_4", "RET_FT4", "MD_EARN_WNE_P6", "MD_EARN_WNE_P10",
    # diversity (race/ethnicity shares of undergraduate enrollment)
    "UGDS_WHITE", "UGDS_BLACK", "UGDS_HISP", "UGDS_ASIAN", "UGDS_AIAN",
    "UGDS_NHPI", "UGDS_2MOR", "UGDS_NRA", "UGDS_UNKN",
    # academics (share of degrees awarded by 2-digit CIP field)
    "PCIP01", "PCIP03", "PCIP04", "PCIP05", "PCIP09", "PCIP10", "PCIP11",
    "PCIP12", "PCIP13", "PCIP14", "PCIP15", "PCIP16", "PCIP19", "PCIP22",
    "PCIP23", "PCIP24", "PCIP25", "PCIP26", "PCIP27", "PCIP29", "PCIP30",
    "PCIP31", "PCIP38", "PCIP39", "PCIP40", "PCIP41", "PCIP42", "PCIP43",
    "PCIP44", "PCIP45", "PCIP46", "PCIP47", "PCIP48", "PCIP49", "PCIP50",
    "PCIP51", "PCIP52", "PCIP54",
]

SCORECARD_NA_VALUES = ["NULL", "PrivacySuppressed", ""]

# Keep: currently operating, predominantly bachelor's-degree-granting.
FILTER_CURROPER = 1
FILTER_PREDDEG = 3

# ---------------------------------------------------------------------------
# Code -> label maps
# ---------------------------------------------------------------------------

CONTROL_LABELS = {1: "Public", 2: "Private nonprofit", 3: "For-profit"}

LOCALE_LABELS = {
    11: "City: Large", 12: "City: Midsize", 13: "City: Small",
    21: "Suburb: Large", 22: "Suburb: Midsize", 23: "Suburb: Small",
    31: "Town: Fringe", 32: "Town: Distant", 33: "Town: Remote",
    41: "Rural: Fringe", 42: "Rural: Distant", 43: "Rural: Remote",
}

# Carnegie Basic Classification (CCBASIC) -> concise tier label. Official labels verified
# against the Scorecard data dictionary; R1/R2 and M1/M2/M3 are the standard shorthand.
# Codes -2/0 (not classified) and 1-9 (associate's, out of our 4-year scope) fall to N/A.
CARNEGIE_LABELS = {
    15: "R1: Doctoral – Very High Research",
    16: "R2: Doctoral – High Research",
    17: "Doctoral / Professional University",
    18: "M1: Master's – Larger Programs",
    19: "M2: Master's – Medium Programs",
    20: "M3: Master's – Small Programs",
    21: "Baccalaureate: Arts & Sciences (Liberal Arts)",
    22: "Baccalaureate: Diverse Fields",
    23: "Baccalaureate / Associate's: Mixed",
    14: "Baccalaureate / Associate's: Associate's-Dominant",
    24: "Special Focus: Faith-Related",
    25: "Special Focus: Medical Schools & Centers",
    26: "Special Focus: Health Professions",
    27: "Special Focus: Research Institution",
    28: "Special Focus: Engineering & Technology",
    29: "Special Focus: Business & Management",
    30: "Special Focus: Arts, Music & Design",
    31: "Special Focus: Law",
    32: "Special Focus: Other",
    33: "Tribal College",
    10: "Special Focus (2-yr): Health Professions",
    11: "Special Focus (2-yr): Technical",
    12: "Special Focus (2-yr): Arts & Design",
    13: "Special Focus (2-yr): Other",
}

# Race/ethnicity shares of undergraduate enrollment: (output key, Scorecard col, label)
RACE_FIELDS = [
    ("race_white", "UGDS_WHITE", "White"),
    ("race_black", "UGDS_BLACK", "Black"),
    ("race_hisp",  "UGDS_HISP",  "Hispanic / Latino"),
    ("race_asian", "UGDS_ASIAN", "Asian"),
    ("race_aian",  "UGDS_AIAN",  "American Indian / Alaska Native"),
    ("race_nhpi",  "UGDS_NHPI",  "Native Hawaiian / Pacific Islander"),
    ("race_2mor",  "UGDS_2MOR",  "Two or more races"),
    ("race_intl",  "UGDS_NRA",   "International (non-resident)"),
    ("race_unkn",  "UGDS_UNKN",  "Race unknown"),
]

# 2-digit CIP field -> human-readable label, for "popular majors" (top 5 by degree share)
CIP_LABELS = {
    "PCIP01": "Agriculture", "PCIP03": "Natural Resources & Conservation",
    "PCIP04": "Architecture", "PCIP05": "Area, Ethnic & Gender Studies",
    "PCIP09": "Communication & Journalism", "PCIP10": "Communications Technologies",
    "PCIP11": "Computer & Information Sciences", "PCIP12": "Personal & Culinary Services",
    "PCIP13": "Education", "PCIP14": "Engineering", "PCIP15": "Engineering Technologies",
    "PCIP16": "Foreign Languages & Linguistics", "PCIP19": "Family & Consumer Sciences",
    "PCIP22": "Legal Professions", "PCIP23": "English Language & Literature",
    "PCIP24": "Liberal Arts & Humanities", "PCIP25": "Library Science",
    "PCIP26": "Biological & Biomedical Sciences", "PCIP27": "Mathematics & Statistics",
    "PCIP29": "Military Technologies", "PCIP30": "Multi / Interdisciplinary Studies",
    "PCIP31": "Parks, Recreation & Fitness", "PCIP38": "Philosophy & Religious Studies",
    "PCIP39": "Theology & Religious Vocations", "PCIP40": "Physical Sciences",
    "PCIP41": "Science Technologies", "PCIP42": "Psychology",
    "PCIP43": "Homeland Security & Law Enforcement",
    "PCIP44": "Public Administration & Social Services", "PCIP45": "Social Sciences",
    "PCIP46": "Construction Trades", "PCIP47": "Mechanic & Repair Technologies",
    "PCIP48": "Precision Production", "PCIP49": "Transportation & Materials Moving",
    "PCIP50": "Visual & Performing Arts", "PCIP51": "Health Professions",
    "PCIP52": "Business, Management & Marketing", "PCIP54": "History",
}

# IPEDS admission-consideration codes, shared by ADMCON7 (test scores) and ADMCON11
# (personal statement / essay). Verified against the ADM dictionary Frequencies sheet;
# unknown codes fall back to None.
ADMCON_LABELS = {
    1: "Required",
    2: "Recommended",
    3: "Not considered",
    4: "Required for some",
    5: "Considered if submitted",
}

# ---------------------------------------------------------------------------
# Clery offense buckets (column prefixes; each appears with a 2-digit year suffix)
# ---------------------------------------------------------------------------

CLERY_VIOLENT_PREFIXES = [
    "MURD",   # murder / non-negligent manslaughter
    "NEG_M",  # negligent manslaughter
    "RAPE", "FONDL", "INCES", "STATR",  # sex offenses
    "ROBBE", "AGG_A",
]
CLERY_PROPERTY_PREFIXES = ["BURGLA", "VEHIC", "ARSON"]

# ---------------------------------------------------------------------------
# Output schema - single source of truth for payload column order and UI rendering.
# type: str | int | usd | frac (0-1 shown as %) | pct (0-100 shown as %) | num | ratio
# better: higher | lower | neutral   (drives best-in-row highlight; neutral = no highlight)
# group: id | size | adm | cost | out | mob | safe
# ---------------------------------------------------------------------------

FIELDS = [
    # -- identity (rendered in column headers, not as table rows)
    {"key": "unitid",    "label": "UNITID",             "group": "id",   "type": "int",  "better": "neutral", "source": "scorecard"},
    {"key": "name",      "label": "Name",               "group": "id",   "type": "str",  "better": "neutral", "source": "scorecard"},
    {"key": "city",      "label": "City",               "group": "id",   "type": "str",  "better": "neutral", "source": "scorecard"},
    {"key": "state",     "label": "State",              "group": "id",   "type": "str",  "better": "neutral", "source": "scorecard"},
    {"key": "url",       "label": "Website",            "group": "id",   "type": "str",  "better": "neutral", "source": "scorecard"},
    # -- size & setting
    {"key": "control",   "label": "Type",               "group": "size", "type": "str",  "better": "neutral", "source": "scorecard"},
    {"key": "locale",    "label": "Setting",            "group": "size", "type": "str",  "better": "neutral", "source": "scorecard"},
    {"key": "carnegie",  "label": "Carnegie classification", "group": "acad", "type": "str", "better": "neutral", "source": "scorecard",
     "note": "Carnegie Basic Classification — institution type & research intensity (R1/R2 = doctoral research universities)"},
    {"key": "enrollment","label": "Undergrad enrollment","group": "size","type": "int",  "better": "neutral", "source": "scorecard"},
    {"key": "stufac",    "label": "Student-faculty ratio","group": "size","type": "ratio","better": "lower",  "source": "scorecard"},
    # -- admissions
    {"key": "adm_rate",  "label": "Acceptance rate",    "group": "adm",  "type": "frac", "better": "neutral", "source": "scorecard"},
    {"key": "app_fee",   "label": "Application fee",     "group": "adm",  "type": "usd",  "better": "lower",   "source": "ipeds_ic"},
    {"key": "sat_v25",   "label": "SAT EBRW 25th pct",  "group": "adm",  "type": "int",  "better": "higher",  "source": "scorecard"},
    {"key": "sat_v75",   "label": "SAT EBRW 75th pct",  "group": "adm",  "type": "int",  "better": "higher",  "source": "scorecard"},
    {"key": "sat_m25",   "label": "SAT Math 25th pct",  "group": "adm",  "type": "int",  "better": "higher",  "source": "scorecard"},
    {"key": "sat_m75",   "label": "SAT Math 75th pct",  "group": "adm",  "type": "int",  "better": "higher",  "source": "scorecard"},
    {"key": "sat_avg",   "label": "SAT average",        "group": "adm",  "type": "int",  "better": "higher",  "source": "scorecard"},
    {"key": "act_25",    "label": "ACT 25th pct",       "group": "adm",  "type": "int",  "better": "higher",  "source": "scorecard"},
    {"key": "act_75",    "label": "ACT 75th pct",       "group": "adm",  "type": "int",  "better": "higher",  "source": "scorecard"},
    {"key": "test_policy","label": "Test scores",       "group": "adm",  "type": "str",  "better": "neutral", "source": "scorecard"},
    {"key": "essay",     "label": "Application essay",   "group": "adm",  "type": "str",  "better": "neutral", "source": "ipeds_adm"},
    {"key": "yield",     "label": "Yield (enrolled / admitted)", "group": "adm", "type": "frac", "better": "higher", "source": "ipeds_adm"},
    # -- cost
    {"key": "tuition_in", "label": "Tuition (in-state)",   "group": "cost", "type": "usd", "better": "lower", "source": "scorecard"},
    {"key": "tuition_out","label": "Tuition (out-of-state)","group": "cost", "type": "usd", "better": "lower", "source": "scorecard"},
    {"key": "cost_attend","label": "Cost of attendance",   "group": "cost", "type": "usd", "better": "lower", "source": "scorecard"},
    {"key": "net_price", "label": "Avg net price",         "group": "cost", "type": "usd", "better": "lower", "source": "scorecard"},
    {"key": "grant_aid", "label": "Avg grant aid",         "group": "cost", "type": "usd", "better": "higher", "source": "ipeds_sfa",
     "note": "Average grant & scholarship aid awarded to full-time first-time undergraduates"},
    {"key": "np_0_30",   "label": "Net price: $0-30k income",   "group": "cost", "type": "usd", "better": "lower", "source": "scorecard"},
    {"key": "np_30_48",  "label": "Net price: $30-48k income",  "group": "cost", "type": "usd", "better": "lower", "source": "scorecard"},
    {"key": "np_48_75",  "label": "Net price: $48-75k income",  "group": "cost", "type": "usd", "better": "lower", "source": "scorecard"},
    {"key": "np_75_110", "label": "Net price: $75-110k income", "group": "cost", "type": "usd", "better": "lower", "source": "scorecard"},
    {"key": "np_110p",   "label": "Net price: $110k+ income",   "group": "cost", "type": "usd", "better": "lower", "source": "scorecard"},
    {"key": "pct_pell",  "label": "% receiving Pell grants",    "group": "cost", "type": "frac", "better": "neutral", "source": "scorecard"},
    {"key": "pct_loan",  "label": "% receiving federal loans",  "group": "cost", "type": "frac", "better": "neutral", "source": "scorecard"},
    {"key": "debt_median","label": "Median debt at graduation", "group": "cost", "type": "usd", "better": "lower", "source": "scorecard"},
    {"key": "loan_payment","label": "Median monthly loan payment", "group": "cost", "type": "usd", "better": "lower", "source": "scorecard",
     "note": "Median federal-loan debt repaid over 10 years at a fixed rate"},
    # -- outcomes
    {"key": "grad_rate", "label": "Graduation rate (6-yr)",  "group": "out", "type": "frac", "better": "higher", "source": "scorecard"},
    {"key": "retention", "label": "Freshman retention",      "group": "out", "type": "frac", "better": "higher", "source": "scorecard"},
    {"key": "earn_6",    "label": "Median earnings (6 yrs after entry)",  "group": "out", "type": "usd", "better": "higher", "source": "scorecard"},
    {"key": "earn_10",   "label": "Median earnings (10 yrs after entry)", "group": "out", "type": "usd", "better": "higher", "source": "scorecard"},
    # -- economic mobility (Opportunity Insights; values already 0-100)
    {"key": "oi_access",  "label": "Low-income access",   "group": "mob", "type": "pct", "better": "higher", "source": "oi",
     "note": "% of students from bottom-quintile-income families"},
    {"key": "oi_success", "label": "Low-income success",  "group": "mob", "type": "pct", "better": "higher", "source": "oi",
     "note": "% of bottom-quintile students who reach the top quintile"},
    {"key": "oi_mobility","label": "Mobility rate",       "group": "mob", "type": "pct", "better": "higher", "source": "oi",
     "note": "access x success: % of all students who climb from bottom to top quintile"},
    {"key": "oi_cluster", "label": "OI cluster flag",     "group": "mob", "type": "int", "better": "neutral", "source": "oi"},
    {"key": "oi_cluster_name", "label": "OI cluster",     "group": "mob", "type": "str", "better": "neutral", "source": "oi"},
    # -- campus safety (Clery; derived rates)
    {"key": "safety_violent_per1k",  "label": "Violent incidents /1k students/yr",  "group": "safe", "type": "num", "better": "lower", "source": "clery"},
    {"key": "safety_property_per1k", "label": "Property incidents /1k students/yr", "group": "safe", "type": "num", "better": "lower", "source": "clery"},
]

# Academics: popular majors (top-5 list of [label, share] pairs; rendered specially in the UI)
FIELDS.append({"key": "majors", "label": "Popular majors", "group": "acad",
               "type": "majors", "better": "neutral", "source": "scorecard"})

# Diversity: race/ethnicity shares (generated from RACE_FIELDS to stay in sync)
FIELDS += [{"key": k, "label": lbl, "group": "div", "type": "frac",
            "better": "neutral", "source": "scorecard"}
           for k, _col, lbl in RACE_FIELDS]

FIELD_KEYS = [f["key"] for f in FIELDS]

# ---------------------------------------------------------------------------
# Validation: hard assertions on well-known schools (UNITID -> field -> (lo, hi))
# ---------------------------------------------------------------------------

SPOT_CHECKS = {
    110635: {"name_contains": "Berkeley", "adm_rate": (0.05, 0.25)},
    166027: {"name_contains": "Harvard", "earn_10": (70000, 300000)},
    204796: {"name_contains": "Ohio State", "enrollment": (30000, 70000)},
}

ROW_COUNT_RANGE = (1500, 3200)          # hard failure outside this
ROW_COUNT_EXPECTED = (1900, 2400)       # warning outside this
