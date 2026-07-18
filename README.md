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

## Data sources

| Source | What it provides | Vintage |
|---|---|---|
| [College Scorecard](https://collegescorecard.ed.gov/data) (U.S. Dept. of Education) | Admissions, cost, debt, outcomes, earnings, size & setting, majors, diversity, Carnegie classification | Updated ~annually; pipeline scrapes the latest institution-level file |
| [IPEDS ADM survey](https://nces.ed.gov/ipeds/use-the-data) (NCES) | Admissions yield (enrolled ÷ admitted) | Pipeline probes for the newest `ADM*.zip` |
| [IPEDS SFA survey](https://nces.ed.gov/ipeds/use-the-data) (NCES) | Average grant & scholarship aid to first-time undergraduates | Pipeline probes for the newest `SFA*.zip` |
| [IPEDS ADM survey](https://nces.ed.gov/ipeds/use-the-data) (NCES) | Application-essay policy (`ADMCON11`) | Same file as yield |
| [IPEDS IC survey](https://nces.ed.gov/ipeds/use-the-data) (NCES) | Undergraduate application fee | Newest `IC*.zip` that contains the fee column |
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
