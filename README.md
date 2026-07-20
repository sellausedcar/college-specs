# College Specs

Compare U.S. undergraduate colleges side-by-side, like car specs.

A fully static site — no backend, no API keys, no build step. All data is pre-merged
into `site/data.js` by a Python pipeline you can rerun anytime to refresh.

## Using the site

Open `site/index.html` directly in your browser (double-click works — the site is
`file://`-safe), or serve/deploy the `site/` folder anywhere static files are hosted.

- **Compare view** — search for 2–5 schools and see a grouped spec table with
  best-in-row highlighting and magnitude bars.
- **Browse view** — filter/sort all schools (state, public/private, size, acceptance
  rate, net price), tick rows, and jump to a comparison.
- Comparisons are shareable: the URL hash encodes the selection
  (e.g. `#compare=110635,166027`).

## Refreshing the data

```
pip install -r pipeline/requirements.txt
python pipeline/build_data.py
```

This downloads the latest source data (~65 MB, cached in `pipeline/cache/`), merges
it, validates it, and rewrites `site/data.js`. Flags:

- `--skip-download` — rebuild from cached downloads only
- `--force-download` — re-download everything even if cached

### Automation options (keeping the door open)

The underlying data only changes **~once a year**, so heavy automation isn't worth much.
Current setup and the paths still on the table:

**Current — manual (recommended).** When new Scorecard/IPEDS data drops, just:

```
python pipeline/build_data.py
git commit -am "refresh data"
git push
```

…and the site updates itself within a minute (the GitHub Pages deploy workflow runs on push).

**Also active — local weekly scheduled task.** A Windows Task Scheduler job
(`weekly-refresh.cmd`, machine-local, gitignored) runs the pipeline weekly and pushes only
if the data changed. Depends on the PC being on around the trigger.

**Deferred — cloud automation via the Scorecard API.** Fully hands-off cloud refresh (GitHub
Actions) is *not* possible today because the Scorecard bulk-download CDN **IP-blocks GitHub's
runners** (403). The fix would be to **rewrite the Scorecard fetch to use `api.data.gov`** — a
different host that isn't IP-blocked. This is a real rewrite (~50 field mappings + pagination)
and needs a **free API key stored as a GitHub secret** (the key stays server-side, never in the
published site). Heavier, but truly hands-off. Kept open for later if the manual/local options
ever stop being enough.

## Data sources

| Source | What it provides | Vintage |
|---|---|---|
| [College Scorecard](https://collegescorecard.ed.gov/data) (U.S. Dept. of Education) | Admissions, cost, debt, outcomes, earnings, size & setting, majors, diversity, Carnegie classification | Updated ~annually; pipeline scrapes the latest institution-level file |
| [IPEDS ADM survey](https://nces.ed.gov/ipeds/use-the-data) (NCES) | Admissions yield (enrolled ÷ admitted) | Pipeline probes for the newest `ADM*.zip` |
| [IPEDS SFA survey](https://nces.ed.gov/ipeds/use-the-data) (NCES) | Average grant & scholarship aid to first-time undergraduates | Pipeline probes for the newest `SFA*.zip` |
| [IPEDS ADM survey](https://nces.ed.gov/ipeds/use-the-data) (NCES) | Application-essay policy (`ADMCON11`) | Same file as yield |
| [IPEDS IC survey](https://nces.ed.gov/ipeds/use-the-data) (NCES) | Undergraduate application fee | Newest `IC*.zip` that contains the fee column |
| [collegedata.fyi](https://www.collegedata.fyi) (community Common Data Set aggregator) | Average high-school GPA of enrolled first-years (CDS item C12) | Parses schools' published CDS filings; ~200 schools, 2024-25/2025-26 cycles |
| [Opportunity Insights](https://opportunityinsights.org/data/) Mobility Report Cards | Economic mobility: low-income access, success rate, mobility rate | Static (2017–18 release, 1980–91 birth cohorts) |
| [Campus Safety & Security](https://ope.ed.gov/campussafety/) (Clery Act) | On-campus violent/property incident rates per 1,000 students (3-yr avg) | Latest 3-calendar-year release |

Scope: currently operating, predominantly bachelor's-degree-granting U.S. Title IV
institutions (~2,000). Missing values render as "N/A" — small schools suppress many
statistics for privacy.

### Caveats

- Opportunity Insights groups some multi-campus systems (e.g. CUNY) under one
  estimate; those values carry a footnote in the UI.
- Clery counts are *reported on-campus incidents* — reporting practices vary, and
  rates are not a complete measure of safety.
- SAT/ACT ranges are sparse post-test-optional; see each school's test policy row.
- **Average high-school GPA** comes from schools' self-reported Common Data Sets (via the
  community aggregator collegedata.fyi), so it covers only the ~200 schools that publish a CDS
  *and* fill in that item — many holistic/test-optional schools (e.g. Duke, MIT) leave it blank,
  which correctly renders as N/A rather than a value. Reporting **scales vary** (weighted vs.
  unweighted), so figures above 4.0 occur and aren't directly comparable between schools — the
  row is shown without best-in-row highlighting for that reason. This source is optional
  enrichment: if its API is unavailable at build time, the pipeline leaves GPA blank and
  continues, so a refresh never fails on it.
- Essay *prompts* aren't a bundled dataset (they're copyrighted and rewritten yearly, and no
  site supports opening one school's prompts by name). The Application-essay row links to the
  My Supplementals and CollegeVine prompt databases; clicking a link **copies that school's name**
  so you paste it with **Ctrl+V (⌘V on Mac)** into the database's search box. A panel lists the
  shared Common App personal-statement prompts (attributed).

## Deploying

The `site/` folder is the entire site (no build step).

**Live site:** https://sellausedcar.github.io/college-specs/

**GitHub Pages (this repo's setup):** a GitHub Actions workflow
(`.github/workflows/deploy.yml`) publishes the `site/` folder on every push to `master`.
Pages branch-deployment can only serve from `/` or `/docs`, so the workflow uploads
`site/` as a Pages artifact instead — no restructuring, no Jekyll. To refresh the live
site after regenerating data, just commit and push:

```
python pipeline/build_data.py
git commit -am "refresh data"
git push
```

The workflow redeploys automatically.

**Other hosts:** the `site/` folder is a plain static site — e.g. drag-and-drop it onto
Netlify, or set the publish directory to `site`.

## Project layout

```
site/       index.html, styles.css, app.js, data.js (generated, committed)
pipeline/   build_data.py (stages 0–5), config.py (URLs/fields), requirements.txt
```

## Future improvements

### Admission-factor importance (CDS section C7)

**What it is.** The Common Data Set's section **C7** is each school's own rating of how much it
weighs ~18 admission factors — the "what does this school actually focus on?" data (one school
leans on rigor + essays + character; a big state school leans on GPA + test scores). Every factor
is rated on a 4-level scale: **Very Important / Important / Considered / Not Considered**, split
into academic and nonacademic groups.

**Source — verified present.** collegedata.fyi carries the whole C7 table as fields
`C.701`–`C.718` (confirmed live: e.g. Davidson reads rigor/essay/character = *Very Important*,
class rank/GPA = *Considered*, interview/alumni/residency = *Not Considered*). Expected
field → factor mapping (confirm against the CDS C7 template when building — the level *values*
were verified empirically, the field-number-to-label mapping was not):

| Field | Factor (academic) | Field | Factor (nonacademic) |
|---|---|---|---|
| `C.701` | Rigor of secondary school record | `C.710` | Character / personal qualities |
| `C.702` | Class rank | `C.711` | First generation |
| `C.703` | Academic GPA | `C.712` | Alumni/ae relation |
| `C.704` | Recommendation(s) | `C.713` | Geographical residence |
| `C.705` | Standardized test scores | `C.714` | State residency |
| `C.706` | Application essay | `C.715` | Religious affiliation / commitment |
| `C.707` | Interview | `C.716` | Volunteer work |
| `C.708` | Extracurricular activities | `C.717` | Work experience |
| `C.709` | Talent / ability | `C.718` | Level of applicant's interest |

**Build approach — same as the shipped GPA feature.** Add a best-effort pipeline stage (mirror
`stage2d_gpa` / `fetch_collegedata_gpa` in `build_data.py`) that pulls these fields from
collegedata.fyi, joins by IPEDS `UNITID`, dedupes to the newest cycle, and degrades to N/A on any
failure so a refresh never breaks on this third-party source. **Filter parse noise:** keep only the
four canonical labels — stray values like `X`, `VI`, `✔` appear in the raw data and must be dropped.
Coverage is bounded by the same aggregator universe as GPA (~200 schools; N/A for the rest).

**Presentation (decided).** Add all 18 factors as individual rows in the compare view, inside a
**collapsible group** (collapsed by default so it doesn't overwhelm the table, expandable to reveal
the full academic/nonacademic breakdown). This will be the first collapsible row-group in the
compare view, so it also introduces that UI affordance.

### Build-time ID-mapping for essay-prompt links

**Today's behaviour.** Each school's Application-essay cell links to the *search pages* of the
My Supplementals and CollegeVine databases. No prompt site supports opening one school's prompts
by name (My Supplementals deep-links only by internal numeric IDs like `?s=130`; CollegeVine is a
single top-100 page), so the link drops you on the database and **you type the school name** into
its search box. Simple and robust, but one extra step per school.

**The alternative: build-time ID-mapping.** At pipeline build time, fetch My Supplementals'
internal school-ID list, match our ~2,000 schools (by `UNITID` / name) to their IDs, and store each
ID in `data.js`. The "see prompts" link could then be a **true per-school deep-link**
(`https://my-supplementals.pages.dev/?s=<id>`) that pre-selects the school — no typing.

**Pros**
- One click pre-selects the school on My Supplementals — no searching/typing.
- Best experience for the schools that database covers (1,159, verified for the current cycle).

**Cons**
- **Fragile.** Their internal IDs and schools list can change every application cycle; when they do,
  the embedded links silently point to the wrong school or break — with no error to warn us.
- **Ongoing maintenance.** The ID map must be re-fetched and re-validated each cycle (another moving
  part in the pipeline, and one more source that can go stale between refreshes).
- **Coverage gaps + dependency.** Schools they don't list get no link (need a fallback anyway), and
  the approach leans on scraping their compiled ID data — a gray area under their terms, and it
  breaks outright if they change their URL scheme.
- **Still not a clean prompts page.** Even when it works, `?s=<id>` opens their list-*builder* with
  the school pre-selected, not a dedicated "here are the prompts" view — the user still clicks through.

**Verdict:** deferred. The current search-page links are copyright-safe, zero-maintenance, and never
silently wrong; the ID-mapping option trades that robustness for saving one search box. Revisit only
if My Supplementals publishes a stable per-school URL or an official lookup.

### "See rankings" links to external ranking sites

Analogous to the essay **"see prompts"** links, add **"see rankings"** links that open the major
college-ranking sites. Rankings are proprietary/copyrighted, so these would link **out** to the
sites (like the prompt-database links) rather than embedding any ranking data. Planned targets:

- **U.S. News — Best Colleges (National Universities):** <https://www.usnews.com/best-colleges/rankings/national-universities>
- **Forbes — America's Top Colleges:** <https://www.forbes.com/top-colleges/>
- **Niche — grades & rankings:** <https://www.niche.com/colleges/search/best-colleges/>
- **CollegeSimply — The Best Colleges:** <https://www.collegesimply.com/guides/the-best-colleges/>

Notes: these are general "best colleges" **list pages**, not per-school, so — like the prompt
databases — they can't be deep-linked to a specific school by name (and U.S. News gates its full
rankings behind sign-in). Decide the final set/placement when implementing (you mentioned "three
links" but listed four sites).
