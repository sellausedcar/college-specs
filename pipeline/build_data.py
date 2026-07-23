"""College Specs data pipeline.

Downloads College Scorecard, IPEDS ADM, Opportunity Insights, and Clery Act data,
merges them into a single institution-level table, validates it, and emits
site/data.js for the static site.

Usage:
    python pipeline/build_data.py [--skip-download] [--force-download]
"""

import argparse
import csv
import datetime
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402

CACHE = Path(__file__).parent / "cache"
SITE = Path(__file__).parent.parent / "site"
DOCS = Path(__file__).parent.parent / "docs"


def log(msg):
    print(msg, flush=True)


def die(msg):
    log(f"FATAL: {msg}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Stage 0: downloads (with cache)
# ---------------------------------------------------------------------------

def download(url, dest, force):
    """Stream url to dest unless already cached."""
    if dest.exists() and not force:
        log(f"  cached: {dest.name} ({dest.stat().st_size:,} bytes)")
        return dest
    log(f"  GET {url}")
    with requests.get(url, headers=config.HTTP_HEADERS, stream=True, timeout=300) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        tmp.replace(dest)
    log(f"  saved: {dest.name} ({dest.stat().st_size:,} bytes)")
    return dest


def newest_cached(pattern):
    hits = sorted(CACHE.glob(pattern), key=lambda p: p.stat().st_mtime)
    return hits[-1] if hits else None


def resolve_scorecard(skip, force):
    """Find the current Scorecard institution-level zip (date-stamped filename)."""
    if skip:
        p = newest_cached("Most-Recent-Cohorts-Institution_*.zip")
        if not p:
            die("--skip-download but no cached Scorecard zip")
        return p
    url = None
    try:
        page = requests.get(config.SCORECARD_DATA_PAGE, headers=config.HTTP_HEADERS, timeout=60)
        page.raise_for_status()
        m = re.search(config.SCORECARD_LINK_RE, page.text)
        if m:
            url = m.group(0)
            log(f"  scraped current Scorecard link: {url}")
    except Exception as e:  # noqa: BLE001 - scrape failure falls back to known URL
        log(f"  scrape failed ({e}); using fallback URL")
    if not url:
        url = config.SCORECARD_FALLBACK_URL
        log(f"  using fallback Scorecard URL: {url}")
    return download(url, CACHE / url.rsplit("/", 1)[1], force)


def resolve_adm(skip, force):
    """Probe IPEDS ADM{year}.zip newest-first and download the newest that exists."""
    if skip:
        p = newest_cached("ADM*.zip")
        if not p:
            die("--skip-download but no cached ADM zip")
        return p
    for year in range(config.IPEDS_ADM_PROBE_START_YEAR, config.IPEDS_ADM_MIN_YEAR - 1, -1):
        url = config.IPEDS_ADM_URL_TEMPLATE.format(year=year)
        dest = CACHE / f"ADM{year}.zip"
        if dest.exists() and not force:
            log(f"  cached: {dest.name}")
            return dest
        r = requests.get(url, headers=config.HTTP_HEADERS, stream=True, timeout=60)
        if r.status_code == 200:
            log(f"  newest available IPEDS ADM year: {year}")
            r.close()
            return download(url, dest, force)
        r.close()
        log(f"  ADM{year}.zip -> {r.status_code}")
    die("no IPEDS ADM file found in probe range")


def resolve_sfa(skip, force):
    """Probe IPEDS SFA{startYY}{endYY}.zip newest-first and download the newest that exists."""
    if skip:
        p = newest_cached("SFA*.zip")
        if not p:
            die("--skip-download but no cached SFA zip")
        return p
    for end in range(config.IPEDS_SFA_PROBE_START_YEAR, config.IPEDS_SFA_MIN_YEAR - 1, -1):
        name = f"SFA{(end - 1) % 100:02d}{end % 100:02d}"
        url = config.IPEDS_SFA_URL_TEMPLATE.format(name=name)
        dest = CACHE / f"{name}.zip"
        if dest.exists() and not force:
            log(f"  cached: {dest.name}")
            return dest
        r = requests.get(url, headers=config.HTTP_HEADERS, stream=True, timeout=60)
        if r.status_code == 200:
            log(f"  newest available IPEDS SFA: {name} (academic year {end - 1}-{end % 100:02d})")
            r.close()
            return download(url, dest, force)
        r.close()
        log(f"  {name}.zip -> {r.status_code}")
    die("no IPEDS SFA file found in probe range")


def ic_has_fee(zip_path):
    """True if the IC zip's CSV contains the APPLFEEU column (full, not provisional, release)."""
    try:
        with zipfile.ZipFile(zip_path) as z:
            cn = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
            with z.open(cn) as f:
                hdr = next(csv.reader(io.TextIOWrapper(f, "utf-8-sig")))
        return "APPLFEEU" in {h.strip().upper() for h in hdr}
    except Exception:  # noqa: BLE001
        return False


def resolve_ic(skip, force):
    """Newest IPEDS IC file that actually contains APPLFEEU (provisional releases omit it)."""
    if skip:
        for p in sorted(CACHE.glob("IC20*.zip"), key=lambda x: x.stat().st_mtime, reverse=True):
            if "_dict" not in p.name.lower() and ic_has_fee(p):
                log(f"  cached: {p.name}")
                return p
        die("--skip-download but no cached IC zip with APPLFEEU")
    for year in range(config.IPEDS_IC_PROBE_START_YEAR, config.IPEDS_IC_MIN_YEAR - 1, -1):
        url = config.IPEDS_IC_URL_TEMPLATE.format(year=year)
        dest = CACHE / f"IC{year}.zip"
        if not dest.exists() or force:
            r = requests.get(url, headers=config.HTTP_HEADERS, stream=True, timeout=60)
            code = r.status_code
            r.close()
            if code != 200:
                log(f"  IC{year}.zip -> {code}")
                continue
            download(url, dest, force)
        if ic_has_fee(dest):
            log(f"  using IC{year} (has APPLFEEU)")
            return dest
        log(f"  IC{year} lacks APPLFEEU (provisional); trying older")
    die("no IC file with APPLFEEU found in probe range")


def resolve_clery(skip, force):
    """Pick the newest Crime*EXCEL.zip from the Clery fileList API. GET only (HEAD=405)."""
    if skip:
        p = newest_cached("Crime*.zip")
        if not p:
            die("--skip-download but no cached Clery zip")
        return p, None
    r = requests.get(config.CLERY_FILELIST_URL, headers=config.HTTP_HEADERS, timeout=60)
    r.raise_for_status()
    entries = r.json()
    best = None
    for e in entries:
        name = e.get("FileName", "")
        m = re.match(r"Crime(\d{4})EXCEL\.zip$", name, re.I)
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), name, e.get("Description") or "")
    if not best:
        log("  fileList entries seen: " + ", ".join(e.get("FileName", "?") for e in entries[:40]))
        die("no Crime*EXCEL.zip in Clery fileList")
    _, name, desc = best
    log(f"  Clery file: {name} - {desc}")
    return download(config.CLERY_FILE_URL.format(name=name), CACHE / name, force), desc


def stage0(args):
    log("=== Stage 0: downloads ===")
    CACHE.mkdir(exist_ok=True)
    paths = {}
    paths["scorecard"] = resolve_scorecard(args.skip_download, args.force_download)
    paths["adm"] = resolve_adm(args.skip_download, args.force_download)
    paths["sfa"] = resolve_sfa(args.skip_download, args.force_download)
    paths["ic"] = resolve_ic(args.skip_download, args.force_download)
    if args.skip_download:
        for key, url in [("oi1", config.OI_TABLE1_URL), ("oi11", config.OI_TABLE11_URL)]:
            p = CACHE / url.rsplit("/", 1)[1]
            if not p.exists():
                die(f"--skip-download but no cached {p.name}")
            paths[key] = p
        paths["clery"], paths["clery_desc"] = resolve_clery(True, False)
    else:
        paths["oi1"] = download(config.OI_TABLE1_URL, CACHE / "mrc_table1.csv", args.force_download)
        paths["oi11"] = download(config.OI_TABLE11_URL, CACHE / "mrc_table11.csv", args.force_download)
        paths["clery"], paths["clery_desc"] = resolve_clery(False, args.force_download)
    return paths


# ---------------------------------------------------------------------------
# Stage 1: Scorecard base table
# ---------------------------------------------------------------------------

def to_num(s):
    return pd.to_numeric(s, errors="coerce")


def stage1_scorecard(zip_path):
    log("=== Stage 1: Scorecard base table ===")
    with zipfile.ZipFile(zip_path) as z:
        csv_names = [n for n in z.namelist()
                     if n.lower().endswith(".csv") and not n.startswith("__MACOSX")]
        if len(csv_names) != 1:
            die(f"expected 1 csv in Scorecard zip, found: {csv_names}")
        with z.open(csv_names[0]) as f:
            raw = pd.read_csv(
                f, usecols=config.SCORECARD_COLS, dtype=str,
                na_values=config.SCORECARD_NA_VALUES, keep_default_na=True,
            )
    log(f"  read {len(raw):,} institutions x {len(raw.columns)} cols")

    curroper = to_num(raw["CURROPER"])
    preddeg = to_num(raw["PREDDEG"])
    keep = (curroper == config.FILTER_CURROPER) & (preddeg == config.FILTER_PREDDEG)
    raw = raw[keep].copy()
    log(f"  after CURROPER==1 & PREDDEG==3 filter: {len(raw):,} institutions")

    df = pd.DataFrame()
    df["unitid"] = to_num(raw["UNITID"]).astype("Int64")
    df["name"] = raw["INSTNM"].str.strip()
    df["city"] = raw["CITY"].str.strip()
    df["state"] = raw["STABBR"].str.strip()
    df["url"] = raw["INSTURL"].str.strip()
    df["control"] = to_num(raw["CONTROL"]).map(config.CONTROL_LABELS)
    df["locale"] = to_num(raw["LOCALE"]).map(config.LOCALE_LABELS)
    df["carnegie"] = to_num(raw["CCBASIC"]).map(config.CARNEGIE_LABELS)
    df["enrollment"] = to_num(raw["UGDS"]).astype("Int64")
    df["stufac"] = to_num(raw["STUFACR"])
    df["adm_rate"] = to_num(raw["ADM_RATE"])
    for out_key, col in [("sat_v25", "SATVR25"), ("sat_v75", "SATVR75"),
                         ("sat_m25", "SATMT25"), ("sat_m75", "SATMT75"),
                         ("sat_avg", "SAT_AVG"), ("act_25", "ACTCM25"), ("act_75", "ACTCM75")]:
        df[out_key] = to_num(raw[col]).astype("Int64")
    admcon = to_num(raw["ADMCON7"])
    log("  ADMCON7 code distribution: "
        + str(admcon.value_counts(dropna=False).to_dict()))
    df["test_policy"] = admcon.map(config.ADMCON_LABELS)
    df["essay"] = pd.NA   # stage 2 (from IPEDS ADM ADMCON11)
    df["yield"] = pd.NA   # stage 2
    df["tuition_in"] = to_num(raw["TUITIONFEE_IN"]).astype("Int64")
    df["tuition_out"] = to_num(raw["TUITIONFEE_OUT"]).astype("Int64")
    df["cost_attend"] = to_num(raw["COSTT4_A"]).astype("Int64")
    df["net_price"] = to_num(raw["NPT4_PUB"]).fillna(to_num(raw["NPT4_PRIV"])).astype("Int64")
    for out_key, n in [("np_0_30", 1), ("np_30_48", 2), ("np_48_75", 3),
                       ("np_75_110", 4), ("np_110p", 5)]:
        df[out_key] = (to_num(raw[f"NPT4{n}_PUB"])
                       .fillna(to_num(raw[f"NPT4{n}_PRIV"])).astype("Int64"))
    df["pct_pell"] = to_num(raw["PCTPELL"])
    df["pct_loan"] = to_num(raw["PCTFLOAN"])
    df["debt_median"] = to_num(raw["GRAD_DEBT_MDN"]).astype("Int64")
    df["loan_payment"] = to_num(raw["GRAD_DEBT_MDN10YR"]).round().astype("Int64")
    df["grad_rate"] = to_num(raw["C150_4"])
    df["retention"] = to_num(raw["RET_FT4"])
    df["earn_6"] = to_num(raw["MD_EARN_WNE_P6"]).astype("Int64")
    df["earn_10"] = to_num(raw["MD_EARN_WNE_P10"]).astype("Int64")

    # diversity: race/ethnicity shares (fractions 0-1)
    for out_key, col, _lbl in config.RACE_FIELDS:
        df[out_key] = to_num(raw[col]).round(4)

    # academics: top-5 majors by share of degrees awarded
    pcip_cols = list(config.CIP_LABELS.keys())
    pcip = raw[pcip_cols].apply(to_num)

    def top_majors(row):
        pairs = [(config.CIP_LABELS[c], row[c]) for c in pcip_cols
                 if pd.notna(row[c]) and row[c] > 0]
        pairs.sort(key=lambda x: x[1], reverse=True)
        return [[lbl, round(float(v), 4)] for lbl, v in pairs[:5]] or None

    df["majors"] = [top_majors(r) for _, r in pcip.iterrows()]

    # join keys kept internally (not emitted)
    df["_opeid6"] = raw["OPEID6"].str.strip()
    df["_opeid8"] = raw["OPEID"].str.strip()

    if df["unitid"].isna().any() or df["unitid"].duplicated().any():
        die("UNITID null or duplicated in Scorecard base")
    return df


# ---------------------------------------------------------------------------
# Stage 2: IPEDS ADM yield
# ---------------------------------------------------------------------------

def stage2_yield(df, adm_zip):
    log("=== Stage 2: IPEDS ADM yield ===")
    with zipfile.ZipFile(adm_zip) as z:
        csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
        # prefer revised (_rv) file when present
        rv = [n for n in csvs if "_rv" in n.lower()]
        pick = rv[0] if rv else csvs[0]
        log(f"  using {pick} (of {csvs})")
        with z.open(pick) as f:
            adm = pd.read_csv(f, dtype=str, na_values=[".", "", " "])
    adm.columns = [c.strip().upper() for c in adm.columns]
    for col in ("UNITID", "ADMSSN", "ENRLT"):
        if col not in adm.columns:
            die(f"ADM file missing column {col}; has: {list(adm.columns)[:20]}")
    # ADMCON11 (personal statement / essay) may be absent in older ADM files.
    admcon11 = (to_num(adm["ADMCON11"]) if "ADMCON11" in adm.columns
                else pd.Series(pd.NA, index=adm.index))
    adm_small = pd.DataFrame({
        "unitid": to_num(adm["UNITID"]).astype("Int64"),
        "_admssn": to_num(adm["ADMSSN"]),
        "_enrlt": to_num(adm["ENRLT"]),
        "_admcon11": admcon11,
    }).dropna(subset=["unitid"]).drop_duplicates("unitid")
    df = df.merge(adm_small, on="unitid", how="left")
    ok = (df["_admssn"] > 0) & df["_enrlt"].notna()
    df.loc[ok, "yield"] = (df.loc[ok, "_enrlt"] / df.loc[ok, "_admssn"]).clip(upper=1.0)
    df["yield"] = to_num(df["yield"])
    df["essay"] = df["_admcon11"].map(config.ADMCON_LABELS)
    log(f"  yield coverage: {df['yield'].notna().sum():,}/{len(df):,}; "
        f"essay coverage: {df['essay'].notna().sum():,}/{len(df):,}")
    return df.drop(columns=["_admssn", "_enrlt", "_admcon11"])


# ---------------------------------------------------------------------------
# Stage 2b: IPEDS SFA average grant aid
# ---------------------------------------------------------------------------

def stage2b_grant_aid(df, sfa_zip):
    log("=== Stage 2b: IPEDS SFA average grant aid ===")
    with zipfile.ZipFile(sfa_zip) as z:
        csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
        rv = [n for n in csvs if "_rv" in n.lower()]
        pick = rv[0] if rv else csvs[0]
        log(f"  using {pick} (of {csvs})")
        with z.open(pick) as f:
            sfa = pd.read_csv(f, dtype=str, na_values=[".", "", " "], encoding="latin-1")
    sfa.columns = [c.strip().upper() for c in sfa.columns]
    for col in ("UNITID", "GRNTA2", "GISTA2"):
        if col not in sfa.columns:
            die(f"SFA file missing column {col}; has: {list(sfa.columns)[:20]}")
    # GRNTA2 (academic-year reporters) and GISTA2 (program/other reporters) are mutually
    # exclusive per school - coalesce to cover both.
    grant = to_num(sfa["GRNTA2"]).fillna(to_num(sfa["GISTA2"]))
    small = pd.DataFrame({
        "unitid": to_num(sfa["UNITID"]).astype("Int64"),
        "grant_aid": grant,
    }).dropna(subset=["unitid"]).drop_duplicates("unitid")
    df = df.merge(small, on="unitid", how="left")
    df["grant_aid"] = df["grant_aid"].round().astype("Int64")
    log(f"  grant aid coverage: {df['grant_aid'].notna().sum():,}/{len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Stage 2c: IPEDS IC undergraduate application fee
# ---------------------------------------------------------------------------

def stage2c_app_fee(df, ic_zip):
    log("=== Stage 2c: IPEDS IC application fee ===")
    with zipfile.ZipFile(ic_zip) as z:
        cn = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        log(f"  using {cn}")
        with z.open(cn) as f:
            ic = pd.read_csv(
                f, dtype=str, encoding="utf-8-sig", na_values=[".", "", " "],
                usecols=lambda c: c.strip().upper() in ("UNITID", "APPLFEEU"),
            )
    ic.columns = [c.strip().upper() for c in ic.columns]
    small = pd.DataFrame({
        "unitid": to_num(ic["UNITID"]).astype("Int64"),
        "app_fee": to_num(ic["APPLFEEU"]),
    }).dropna(subset=["unitid"]).drop_duplicates("unitid")
    df = df.merge(small, on="unitid", how="left")
    df["app_fee"] = df["app_fee"].round().astype("Int64")
    log(f"  application fee coverage: {df['app_fee'].notna().sum():,}/{len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Stage 2d: CollegeData.FYI average high-school GPA (Common Data Set item C12)
#
# Optional, best-effort enrichment. Unlike the federal sources this must NEVER fail the
# build: a fetch error, an offline --skip-download, or an empty/renamed API all degrade
# gracefully to an all-N/A gpa column so the rest of the pipeline is unaffected.
# ---------------------------------------------------------------------------

def fetch_collegedata_gpa(skip, force):
    """Return raw GPA rows (list of dicts) from collegedata.fyi, or None. Never raises."""
    dest = CACHE / "collegedata_gpa.json"
    if dest.exists() and not force:
        log(f"  cached: {dest.name}")
        try:
            return json.loads(dest.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 - unreadable cache falls through to refetch
            log(f"  cached GPA file unreadable ({e}); refetching")
    if skip:
        log("  --skip-download and no usable GPA cache; leaving GPA blank")
        return None
    params = {
        "select": ("ipeds_id,school_name,canonical_year,year_start,value_num,"
                   "value_status,sub_institutional,data_quality_flag"),
        "field_id": "eq." + config.COLLEGEDATA_GPA_FIELD_ID,
        "value_num": "not.is.null",
        "data_quality_flag": "is.null",   # drop blank-template / mis-parsed rows at the source
        "limit": "10000",
    }
    headers = dict(config.HTTP_HEADERS)
    headers["apikey"] = config.COLLEGEDATA_ANON_KEY
    headers["Authorization"] = "Bearer " + config.COLLEGEDATA_ANON_KEY
    try:
        log(f"  GET {config.COLLEGEDATA_API_URL} (field {config.COLLEGEDATA_GPA_FIELD_ID})")
        r = requests.get(config.COLLEGEDATA_API_URL, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        rows = r.json()
        dest.write_text(json.dumps(rows), encoding="utf-8")
        log(f"  saved: {dest.name} ({len(rows):,} rows)")
        return rows
    except Exception as e:  # noqa: BLE001 - optional source; a failure is never fatal
        log(f"  WARNING: GPA fetch failed ({e}); continuing without GPA")
        return None


def parse_collegedata_gpa(rows):
    """Clean raw GPA rows -> (DataFrame[unitid, gpa], cycle-span string) or (None, None)."""
    if not rows:
        return None, None
    g = pd.DataFrame(rows)
    if "value_num" not in g.columns or "ipeds_id" not in g.columns:
        log("  WARNING: unexpected GPA payload shape; skipping GPA")
        return None, None
    g = g[g["value_num"].notna()].copy()
    if "data_quality_flag" in g.columns:              # belt-and-suspenders vs the server filter
        g = g[g["data_quality_flag"].isna()]
    if "value_status" in g.columns:
        g = g[g["value_status"].fillna("reported") == "reported"]
    if "sub_institutional" in g.columns:              # keep the main institution, not sub-campuses
        g = g[g["sub_institutional"].isna()]
    g["unitid"] = to_num(g["ipeds_id"]).astype("Int64")
    g["gpa"] = to_num(g["value_num"])
    g = g.dropna(subset=["unitid", "gpa"])
    # Guard against non-reports and parse noise. Schools that leave CDS C12 blank (many
    # test-optional/holistic ones — Duke, Georgetown, Williams…) surface as 0.0; no real
    # average enrolled-first-year GPA is below 2.0. Weighted scales legitimately exceed 4.0
    # (UNC 4.47, Georgia Tech 4.14), so the upper bound allows up to a 5.0 weighted scale.
    g = g[(g["gpa"] >= 2.0) & (g["gpa"] <= 5.0)]
    yr = to_num(g["year_start"]) if "year_start" in g.columns else pd.Series(0, index=g.index)
    g = g.assign(_yr=yr).sort_values("_yr", ascending=False).drop_duplicates("unitid")
    if g.empty:
        return None, None
    years = sorted(str(y) for y in g.get("canonical_year", pd.Series(dtype=str)).dropna().unique())
    span = f"{years[0]}–{years[-1]}" if len(years) > 1 else (years[0] if years else "recent cycles")
    return g[["unitid", "gpa"]].reset_index(drop=True), span


def stage2d_gpa(df, skip, force):
    log("=== Stage 2d: CollegeData.FYI average HS GPA ===")
    gpa, span = parse_collegedata_gpa(fetch_collegedata_gpa(skip, force))
    if gpa is None:
        df["gpa"] = pd.NA
        log(f"  GPA unavailable; column N/A for all {len(df):,} schools")
        return df, None
    df = df.merge(gpa, on="unitid", how="left")
    df["gpa"] = to_num(df["gpa"]).round(2)
    log(f"  GPA coverage: {df['gpa'].notna().sum():,}/{len(df):,} (CDS cycles {span})")
    return df, span


# ---------------------------------------------------------------------------
# Stage 2e: CollegeData.FYI admission-factor importance (Common Data Set section C7)
#
# Optional, best-effort enrichment like stage 2d: any failure degrades to all-N/A
# c7_* columns, never a failed build. Unlike the single-shot GPA fetch this one must
# paginate — the server caps every response at 1,000 rows regardless of `limit`
# (and `Prefer: count=exact` times out server-side, so total size is unknowable upfront).
# ---------------------------------------------------------------------------

C7_MAX_PAGES = 40  # 40k rows, >5x current volume; growth past this means revisit the design


def fetch_collegedata_c7(skip, force):
    """Return raw C7 rows (list of dicts) from collegedata.fyi, or None. Never raises."""
    dest = CACHE / "collegedata_c7.json"
    if dest.exists() and not force:
        log(f"  cached: {dest.name}")
        try:
            return json.loads(dest.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 - unreadable cache falls through to refetch
            log(f"  cached C7 file unreadable ({e}); refetching")
    if skip:
        log("  --skip-download and no usable C7 cache; leaving C7 blank")
        return None
    params = {
        "select": ("ipeds_id,school_name,field_id,canonical_year,year_start,value_text,"
                   "value_status,sub_institutional,data_quality_flag"),
        "field_id": "in.(" + ",".join(fid for fid, _k, _l in config.COLLEGEDATA_C7_FIELDS) + ")",
        "value_text": "not.is.null",
        "data_quality_flag": "is.null",   # drop blank-template / mis-parsed rows at the source
        "order": "ipeds_id.asc,field_id.asc,year_start.asc",  # stable order for offset paging
        "limit": "1000",
    }
    headers = dict(config.HTTP_HEADERS)
    headers["apikey"] = config.COLLEGEDATA_ANON_KEY
    headers["Authorization"] = "Bearer " + config.COLLEGEDATA_ANON_KEY
    rows = []
    try:
        log(f"  GET {config.COLLEGEDATA_API_URL} (fields C.701-C.718, paginated)")
        for page_no in range(C7_MAX_PAGES):
            r = requests.get(config.COLLEGEDATA_API_URL,
                             params=params | {"offset": str(len(rows))},
                             headers=headers, timeout=60)
            r.raise_for_status()
            page = r.json()
            if not page:
                break
            rows.extend(page)
            log(f"  page {page_no + 1}: {len(page):,} rows (total {len(rows):,})")
        else:
            log(f"  WARNING: C7 pagination hit the {C7_MAX_PAGES}-page cap; using what we have")
        dest.write_text(json.dumps(rows), encoding="utf-8")
        log(f"  saved: {dest.name} ({len(rows):,} rows)")
        return rows
    except Exception as e:  # noqa: BLE001 - optional source; a failure is never fatal
        log(f"  WARNING: C7 fetch failed ({e}); continuing without C7")
        return None


def _c7_dropped_summary(g, bad, kept_unitids):
    """Summarize the schools *removed* by the guards (had data pre-guard, none survived).
    Returns a list of {unitid, category, pattern} dicts for the transparency doc."""
    label = {fid: lbl for fid, _k, lbl in config.COLLEGEDATA_C7_FIELDS}
    removed = set(g["unitid"].dropna().unique()) - set(kept_unitids)
    bad_rows = g[bad & g["unitid"].isin(removed)]
    out = []
    for uid, grp in bad_rows.groupby("unitid"):
        cycles = sorted(grp["_yr"].dropna().unique(), reverse=True)
        newest = grp[grp["_yr"] == cycles[0]] if cycles else grp
        vc = newest["level"].value_counts()
        n, distinct, top = int(vc.sum()), len(vc), (int(vc.iloc[0]) if len(vc) else 0)
        ctx = int((newest["field_id"].isin(config.C7_CONTEXTUAL_FIELDS)
                   & newest["level"].eq("Very Important")).sum())
        both = " (both cycles)" if len(cycles) > 1 else ""
        if n >= 10 and distinct == 1:
            val = vc.index[0]
            cat = "vi" if val == "Very Important" else "nc"
            pattern = f"all {n} = {val}{both}"
        elif ctx >= 3:
            cat, pattern = "vi", f"{top} of {n} = Very Important{both}"
        else:
            fields = ", ".join(label[f] for f in sorted(newest["field_id"].unique()))
            cat, pattern = "frag", f"{n} field{'s' if n != 1 else ''} only ({fields}); no academic factor"
        out.append({"unitid": int(uid), "category": cat, "pattern": pattern})
    return out


def parse_collegedata_c7(rows):
    """Clean raw C7 rows -> (wide DataFrame[unitid, c7_*...], cycle-span, dropped-summary list).
    On no usable data returns (None, None, [])."""
    if not rows:
        return None, None, []
    g = pd.DataFrame(rows)
    if not {"value_text", "ipeds_id", "field_id"} <= set(g.columns):
        log("  WARNING: unexpected C7 payload shape; skipping C7")
        return None, None, []
    g = g[g["value_text"].notna()].copy()
    if "data_quality_flag" in g.columns:              # belt-and-suspenders vs the server filter
        g = g[g["data_quality_flag"].isna()]
    if "value_status" in g.columns:
        g = g[g["value_status"].fillna("reported") == "reported"]
    if "sub_institutional" in g.columns:              # keep the main institution, not sub-campuses
        g = g[g["sub_institutional"].isna()]
    g["unitid"] = to_num(g["ipeds_id"]).astype("Int64")
    # Guard against parse noise: the raw data holds stray values ("x", "Text", "0.024",
    # "NotConsidered"…). Normalizing to lowercase letters and mapping onto the four
    # canonical labels keeps mis-spaced variants and drops everything else.
    norm = g["value_text"].astype(str).str.lower().str.replace(r"[^a-z]", "", regex=True)
    g["level"] = norm.map(config.C7_LEVELS)
    g["key"] = g["field_id"].map({fid: k for fid, k, _l in config.COLLEGEDATA_C7_FIELDS})
    g["_yr"] = to_num(g["year_start"]) if "year_start" in g.columns else pd.Series(0, index=g.index)
    g = g.dropna(subset=["unitid", "level", "key"])
    if g.empty:
        return None, None, []
    # Guard against source parse failures -- garbled checkbox-grid reads that bleed one
    # column across every factor. Confirmed on real records (e.g. University of Michigan
    # 2025-26, source_format "pdf_flat" / producer "tier4_docling", which reads all 18
    # factors as the identical "Very Important"). These slip past both the server's own
    # data_quality_flag and the noise filter above because the values are well-formed
    # canonical labels. Three signatures, all evaluated per (school, cycle) so a school's
    # clean cycle still survives when another cycle is bad:
    cycle = ["unitid", "_yr"]
    lvl = g.groupby(cycle)["level"]
    #   (a) every parsed factor reads the identical rating (>=10 present, all equal) -- also
    #       catches all-"Not Considered" bleeds, which signature (b) would miss;
    uniform = (lvl.transform("size") >= 10) & (lvl.transform("nunique") == 1)
    #   (b) >=3 contextual factors (alumni, geography, state residency, religion) rated
    #       "Very Important" at once -- implausible for any real school, and the tell for an
    #       all-"Very Important" bleed that (a) misses when a stray field parses differently.
    ctx_vi = g["field_id"].isin(config.C7_CONTEXTUAL_FIELDS) & g["level"].eq("Very Important")
    implausible = ctx_vi.groupby([g["unitid"], g["_yr"]]).transform("sum") >= 3
    #   (c) none of the core academic anchor factors present -- a genuine C7 table always
    #       rates rigor/GPA/test scores/essay, so a record with only scattered non-academic
    #       fragments is a misaligned parse (e.g. Purdue, whose sole surviving cell is a
    #       spurious religion="Very Important").
    has_anchor = g["field_id"].isin(config.C7_ANCHOR_FIELDS)
    anchorless = ~has_anchor.groupby([g["unitid"], g["_yr"]]).transform("any")
    bad = uniform | implausible | anchorless
    if bad.any():
        n = g.loc[bad, cycle].drop_duplicates().shape[0]
        log(f"  dropping {n:,} garbled school-cycle record(s) (parse failure: uniform, "
            f"implausible contextual factors, or no academic anchor)")
    kept = g[~bad]
    if kept.empty:
        return None, None, []
    kept = kept.sort_values("_yr", ascending=False).drop_duplicates(["unitid", "key"])  # newest cycle wins
    years = sorted(str(y) for y in kept.get("canonical_year", pd.Series(dtype=str)).dropna().unique())
    span = f"{years[0]}–{years[-1]}" if len(years) > 1 else (years[0] if years else "recent cycles")
    wide = (kept.pivot(index="unitid", columns="key", values="level")
                .reindex(columns=[k for _f, k, _l in config.COLLEGEDATA_C7_FIELDS])
                .reset_index())                     # reindex guarantees all 18 columns exist
    dropped = _c7_dropped_summary(g, bad, wide["unitid"])
    return wide, span, dropped


C7_DROPPED_BEGIN = "<!-- BEGIN GENERATED: c7-dropped -->"
C7_DROPPED_END = "<!-- END GENERATED: c7-dropped -->"


def write_c7_dropped_doc(df, dropped, span):
    """Regenerate the table region of docs/c7-dropped-schools.md from this build's dropped
    set, so the human-readable list never goes stale. Best-effort: never raises, and does
    nothing if the doc or its markers are absent (the surrounding prose is hand-authored)."""
    try:
        doc = DOCS / "c7-dropped-schools.md"
        if not doc.exists():
            return
        text = doc.read_text(encoding="utf-8")
        i, j = text.find(C7_DROPPED_BEGIN), text.find(C7_DROPPED_END)
        if i == -1 or j == -1:
            log("  note: C7 dropped-schools doc has no generated-region markers; skipping")
            return
        # Restrict to schools that actually appear on the site (in df). A garbled record for
        # an out-of-scope institution never shows N/A anywhere a reader would see, so listing
        # it is just noise (and has no display name to show).
        name_by_uid = dict(zip(df["unitid"].tolist(), df["name"].tolist()))
        rows = sorted(({"name": name_by_uid[d["unitid"]], **d}
                       for d in dropped if d["unitid"] in name_by_uid),
                      key=lambda r: r["name"].lower())
        groups = [
            ("vi", 'Nearly all factors misread as "Very Important"',
             "The checkbox-grid bleed: every factor — or all but one — collapsed to "
             "*Very Important*, including implausible ones like religion and state residency."),
            ("nc", 'All factors misread as "Not Considered"',
             "Caught by the *uniform* signature; the contextual-implausibility rule alone "
             "would miss an all-*Not Considered* bleed."),
            ("frag", "Fragmentary / misaligned parse",
             "Spreadsheet cells bled into the C7 columns, leaving only stray non-academic "
             "fields (e.g. a lone spurious `Religion = Very Important`) with none of the "
             "academic anchors."),
        ]
        today = datetime.date.today().isoformat()
        out = [C7_DROPPED_BEGIN,
               f"_Generated from the {today} build ({span} cycles) — do not edit this region "
               f"by hand; `pipeline/build_data.py` overwrites it on every run._", "",
               f"## Dropped schools ({len(rows)})"]
        if not rows:
            out += ["", "_No records were dropped in this build._"]
        for cat, title, blurb in groups:
            g = [r for r in rows if r["category"] == cat]
            if not g:
                continue
            out += ["", f"### {title} ({len(g)})", "", blurb, "",
                    "| School | IPEDS | What the parse produced |", "|---|---|---|"]
            out += [f"| {r['name']} | {r['unitid']} | {r['pattern']} |" for r in g]
        out.append("")
        new = text[:i] + "\n".join(out) + "\n" + text[j:]
        if new != text:
            doc.write_text(new, encoding="utf-8")
            log(f"  wrote {doc.name} ({len(rows)} dropped schools)")
    except Exception as e:  # noqa: BLE001 - a transparency doc must never fail the build
        log(f"  WARNING: could not update C7 dropped-schools doc ({e})")


def stage2e_c7(df, skip, force):
    log("=== Stage 2e: CollegeData.FYI CDS C7 admission factors ===")
    keys = [k for _f, k, _l in config.COLLEGEDATA_C7_FIELDS]
    try:
        c7, span, dropped = parse_collegedata_c7(fetch_collegedata_c7(skip, force))
    except Exception as e:  # noqa: BLE001 - optional source must never fail the build
        log(f"  WARNING: C7 parse failed ({e}); continuing without C7")
        c7, span, dropped = None, None, []
    if c7 is None:
        for k in keys:
            df[k] = pd.NA
        log(f"  C7 unavailable; columns N/A for all {len(df):,} schools")
        return df, None
    df = df.merge(c7, on="unitid", how="left")
    covered = df[keys].notna().any(axis=1).sum()
    log(f"  C7 coverage: {covered:,}/{len(df):,} schools with >=1 factor (CDS cycles {span})")
    write_c7_dropped_doc(df, dropped, span)
    return df, span


# ---------------------------------------------------------------------------
# Stage 3: Opportunity Insights mobility
# ---------------------------------------------------------------------------

def stage3_oi(df, oi1_path, oi11_path):
    log("=== Stage 3: Opportunity Insights ===")
    t1 = pd.read_csv(oi1_path)
    t11 = pd.read_csv(oi11_path)
    t11 = t11[t11["super_opeid"] != -1].copy()
    t11["opeid_int"] = to_num(t11["opeid"]).astype("Int64")

    # OI's opeid format isn't formally documented - test candidate joins against
    # both Scorecard OPEID forms and use whichever matches the most institutions.
    cand = {
        "opeid6": to_num(df["_opeid6"]).astype("Int64"),
        "opeid8": to_num(df["_opeid8"]).astype("Int64"),
        "opeid8//100": (to_num(df["_opeid8"]) // 100).astype("Int64"),
    }
    oi_keys = set(t11["opeid_int"].dropna().tolist())
    matches = {name: s.isin(oi_keys).sum() for name, s in cand.items()}
    log(f"  join candidate match counts: {matches}")
    best = max(matches, key=matches.get)
    log(f"  joining OI on {best}")
    df["_oi_key"] = cand[best]

    cluster_size = t11.groupby("super_opeid")["opeid_int"].nunique()
    t11["_cluster"] = t11["super_opeid"].map(cluster_size).gt(1).astype(int)
    xwalk = t11.drop_duplicates("opeid_int")[["opeid_int", "super_opeid", "superopeid_name", "_cluster"]]
    df = df.merge(xwalk, left_on="_oi_key", right_on="opeid_int", how="left")

    vals = t1[["super_opeid", "par_q1", "kq5_cond_parq1", "mr_kq5_pq1"]]
    df = df.merge(vals, on="super_opeid", how="left")
    df["oi_access"] = to_num(df["par_q1"]).round(2)
    df["oi_success"] = to_num(df["kq5_cond_parq1"]).round(2)
    df["oi_mobility"] = to_num(df["mr_kq5_pq1"]).round(2)
    df["oi_cluster"] = df["_cluster"].where(df["oi_access"].notna()).astype("Int64")
    df["oi_cluster_name"] = df["superopeid_name"].where(df["oi_cluster"] == 1)
    log(f"  OI coverage: {df['oi_access'].notna().sum():,}/{len(df):,} "
        f"(clustered: {(df['oi_cluster'] == 1).sum():,})")
    return df.drop(columns=["_oi_key", "opeid_int", "super_opeid", "superopeid_name",
                            "_cluster", "par_q1", "kq5_cond_parq1", "mr_kq5_pq1"])


# ---------------------------------------------------------------------------
# Stage 4: Clery campus safety
# ---------------------------------------------------------------------------

def read_clery_workbook(clery_zip):
    """Find and read the on-campus criminal offenses workbook from the Clery zip."""
    with zipfile.ZipFile(clery_zip) as z:
        names = z.namelist()
        # anchor to path start so "Noncampuscrime..." (a different file) can't match
        crime = [n for n in names if re.search(r"(?:^|/)oncampuscrime[^/]*\.xlsx?$", n, re.I)]
        if not crime:
            log("  zip contents:")
            for n in names:
                log(f"    {n}")
            die("no oncampuscrime*.xls[x] workbook found in Clery zip - inspect listing above")
        pick = crime[0]
        log(f"  reading {pick}")
        data = z.read(pick)
    engine = "openpyxl" if pick.lower().endswith(".xlsx") else "xlrd"
    try:
        wb = pd.read_excel(io.BytesIO(data), sheet_name=0, dtype=str, engine=engine)
    except ImportError:
        die(f"workbook {pick} needs the '{engine}' package: pip install {engine}")
    m = re.search(r"(\d{6})", pick)
    year_suffixes = [m.group(1)[i:i + 2] for i in (0, 2, 4)] if m else []
    return wb, year_suffixes, pick


def stage4_clery(df, clery_zip):
    log("=== Stage 4: Clery campus safety ===")
    wb, years, pick = read_clery_workbook(clery_zip)
    wb.columns = [c.strip() for c in wb.columns]
    log(f"  {len(wb):,} campus rows; year suffixes {years}; "
        f"columns: {list(wb.columns)[:24]}...")

    opeid_col = next((c for c in wb.columns if c.upper() == "OPEID"), None)
    total_col = next((c for c in wb.columns if c.strip().lower() == "total"), None)
    if not opeid_col:
        die(f"no OPEID column in {pick}; columns: {list(wb.columns)}")

    def cols_for(prefixes):
        found, missing = [], []
        for p in prefixes:
            for y in years:
                c = next((c for c in wb.columns if c.upper() == f"{p}{y}".upper()), None)
                (found if c else missing).append(c or f"{p}{y}")
        return found, missing

    vcols, vmiss = cols_for(config.CLERY_VIOLENT_PREFIXES)
    pcols, pmiss = cols_for(config.CLERY_PROPERTY_PREFIXES)
    if vmiss or pmiss:
        log(f"  WARNING: expected offense columns not found: {vmiss + pmiss}")
    if not vcols or not pcols:
        die(f"offense columns missing entirely; columns are: {list(wb.columns)}")

    camp = pd.DataFrame()
    # OPE IDs may parse as numbers and lose leading zeros - normalize to 8 digits
    camp["ope6"] = (to_num(wb[opeid_col]).astype("Int64").astype(str)
                    .str.replace("<NA>", "", regex=False).str.zfill(8).str[:6])
    camp["violent"] = wb[vcols].apply(to_num).fillna(0).sum(axis=1)
    camp["property"] = wb[pcols].apply(to_num).fillna(0).sum(axis=1)
    camp["cl_enroll"] = to_num(wb[total_col]) if total_col else pd.NA
    camp = camp[camp["ope6"].str.len() == 6]

    agg = camp.groupby("ope6").agg(
        violent=("violent", "sum"), property=("property", "sum"),
        cl_enroll=("cl_enroll", "sum"),
    ).reset_index()

    # denominator fallback: Scorecard UGDS summed across the OPE6 group
    df["_ope6norm"] = (to_num(df["_opeid6"]).astype("Int64").astype(str)
                       .str.replace("<NA>", "", regex=False).str.zfill(6))
    ugds_by_ope6 = df.groupby("_ope6norm")["enrollment"].sum(min_count=1)
    agg["sc_enroll"] = agg["ope6"].map(ugds_by_ope6)
    agg["denom"] = agg["cl_enroll"].where(agg["cl_enroll"] > 0, agg["sc_enroll"])
    ok = agg["denom"] > 0
    nyears = len(years) if years else 3
    agg.loc[ok, "safety_violent_per1k"] = (agg.loc[ok, "violent"] / nyears
                                           / agg.loc[ok, "denom"] * 1000).round(2)
    agg.loc[ok, "safety_property_per1k"] = (agg.loc[ok, "property"] / nyears
                                            / agg.loc[ok, "denom"] * 1000).round(2)

    df = df.merge(
        agg[["ope6", "safety_violent_per1k", "safety_property_per1k"]],
        left_on="_ope6norm", right_on="ope6", how="left",
    ).drop(columns=["ope6"])
    log(f"  safety coverage: {df['safety_violent_per1k'].notna().sum():,}/{len(df):,}")
    return df, years


# ---------------------------------------------------------------------------
# Stage 5: emit + validate
# ---------------------------------------------------------------------------

def cast_value(v, ftype):
    if ftype == "majors":
        return v if isinstance(v, list) and v else None
    if v is None or (isinstance(v, float) and pd.isna(v)) or pd.isna(v):
        return None
    if ftype == "int" or ftype == "usd":
        return int(v)
    if ftype == "frac":
        return round(float(v), 4)
    if ftype in ("pct", "num"):
        return round(float(v), 2)
    if ftype == "ratio":
        return round(float(v), 1)
    return str(v)


def stage5_emit(df, vintages):
    log("=== Stage 5: emit + validate ===")
    failures = []

    n = len(df)
    lo, hi = config.ROW_COUNT_RANGE
    if not (lo <= n <= hi):
        failures.append(f"row count {n} outside hard range {config.ROW_COUNT_RANGE}")
    elo, ehi = config.ROW_COUNT_EXPECTED
    if not (elo <= n <= ehi):
        log(f"  WARNING: row count {n} outside expected range {config.ROW_COUNT_EXPECTED}")

    log(f"  field coverage over {n:,} institutions:")
    for f in config.FIELDS:
        cov = df[f["key"]].notna().sum()
        log(f"    {f['key']:<24} {cov / n * 100:5.1f}%")

    for col in ("name", "state", "control"):
        if df[col].isna().any():
            failures.append(f"{col} has nulls")

    by_id = df.set_index(df["unitid"].astype(int))
    for unitid, checks in config.SPOT_CHECKS.items():
        if unitid not in by_id.index:
            failures.append(f"spot-check school {unitid} missing from output")
            continue
        row = by_id.loc[unitid]
        for key, expect in checks.items():
            if key == "name_contains":
                if expect.lower() not in str(row["name"]).lower():
                    failures.append(f"{unitid}: name {row['name']!r} lacks {expect!r}")
            else:
                v = row[key]
                if pd.isna(v) or not (expect[0] <= float(v) <= expect[1]):
                    failures.append(f"{unitid}: {key}={v} outside {expect}")

    if failures:
        for f in failures:
            log(f"  ASSERTION FAILED: {f}")
        die("validation failed - data.js NOT written")

    fields = [{k: v for k, v in f.items() if k != "source"} | {"source": f["source"]}
              for f in config.FIELDS]
    schools = []
    types = {f["key"]: f["type"] for f in config.FIELDS}
    records = df[config.FIELD_KEYS].to_dict("records")
    for rec in records:
        schools.append([cast_value(rec[k], types[k]) for k in config.FIELD_KEYS])

    payload = {
        "generated": datetime.date.today().isoformat(),
        "vintages": vintages,
        "fields": fields,
        "schools": schools,
    }
    out = SITE / "data.js"
    text = "window.COLLEGE_DATA=" + json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + ";"
    out.write_text(text, encoding="utf-8")
    log(f"  wrote {out} ({out.stat().st_size:,} bytes, {n:,} schools)")


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-download", action="store_true",
                    help="rebuild from cached downloads only")
    ap.add_argument("--force-download", action="store_true",
                    help="re-download all sources even if cached")
    args = ap.parse_args()

    paths = stage0(args)

    scorecard_date = "unknown"
    m = re.search(r"_(\d{2})(\d{2})(\d{4})\.zip$", paths["scorecard"].name)
    if m:
        scorecard_date = f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
    adm_year = re.search(r"ADM(\d{4})", paths["adm"].name).group(1)
    sfa_m = re.search(r"SFA(\d{2})(\d{2})", paths["sfa"].name)
    sfa_span = f"20{sfa_m.group(1)}-{sfa_m.group(2)}" if sfa_m else paths["sfa"].name
    ic_m = re.search(r"IC(\d{4})", paths["ic"].name)
    ic_year = ic_m.group(1) if ic_m else paths["ic"].name

    df = stage1_scorecard(paths["scorecard"])
    df = stage2_yield(df, paths["adm"])
    df = stage2b_grant_aid(df, paths["sfa"])
    df = stage2c_app_fee(df, paths["ic"])
    df, gpa_span = stage2d_gpa(df, args.skip_download, args.force_download)
    df, c7_span = stage2e_c7(df, args.skip_download, args.force_download)
    df = stage3_oi(df, paths["oi1"], paths["oi11"])
    df, clery_years = stage4_clery(df, paths["clery"])

    clery_span = (f"calendar years 20{clery_years[0]}-20{clery_years[-1]}"
                  if clery_years else paths["clery"].name)
    vintages = {
        "scorecard": f"College Scorecard, {scorecard_date} release",
        "ipeds_adm": f"IPEDS ADM {adm_year}",
        "ipeds_sfa": f"IPEDS SFA (grant aid) {sfa_span}",
        "ipeds_ic": f"IPEDS IC (application fee) {ic_year}",
        "collegedata": ("Common Data Set (avg HS GPA, admission factors) via collegedata.fyi"
                        + (f", {' / '.join(s for s in dict.fromkeys([gpa_span, c7_span]) if s)} cycles"
                           if gpa_span or c7_span else "")),
        "oi": f"Opportunity Insights, {config.OI_VINTAGE}",
        "clery": f"Campus Safety and Security, {clery_span}",
    }
    stage5_emit(df, vintages)
    log("DONE")


if __name__ == "__main__":
    main()
