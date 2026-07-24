# CDS C7 — schools dropped by the parse-failure guards

Stage 2e of `pipeline/build_data.py` drops collegedata.fyi C7 records that show the
fingerprints of a garbled source parse (see the *Admission factors* caveat in the
[README](../README.md#caveats) for the three signatures). This file lists the schools that
were dropped, so that when a well-known school shows **N/A** for admission factors you can
confirm it was a bad parse rather than missing data.

**These schools have a Common Data Set — the aggregator just parsed its C7 table
incorrectly.** We show N/A rather than the fabricated values. A school here can reappear in a
future refresh if the aggregator re-parses it cleanly.

Each school name links to the archived CDS filing the bad parse came from, so you can open the
real section C7 and read the ratings yourself.

> [!NOTE]
> The table region below is **regenerated automatically** by the pipeline on every build
> (`write_c7_dropped_doc` in `pipeline/build_data.py`), so it stays in sync with the shipped
> `site/data.js`. It is a snapshot of the latest build — the dropped set changes whenever the
> aggregator re-parses a school. Don't hand-edit between the markers; edits there are
> overwritten on the next run.

<!-- BEGIN GENERATED: c7-dropped -->
_Generated from the 2026-07-23 build (2024-25–2025-26 cycles) — do not edit this region by hand; `pipeline/build_data.py` overwrites it on every run._

## Dropped schools (52)

### Nearly all factors misread as "Very Important" (48)

The checkbox-grid bleed: every factor — or all but one — collapsed to *Very Important*, including implausible ones like religion and state residency.

| School | IPEDS | What the parse produced |
|---|---|---|
| [Albertus Magnus College](https://www.collegedata.fyi/schools/albertus-magnus-college/2024-25) | 128498 | all 17 = Very Important |
| [American University](https://www.collegedata.fyi/schools/american-university/2024-25) | 131159 | all 17 = Very Important |
| [Belmont University](https://www.collegedata.fyi/schools/belmont-university/2024-25) | 219709 | all 17 = Very Important |
| [Brandeis University](https://www.collegedata.fyi/schools/brandeis/2025-26) | 165015 | 16 of 17 = Very Important (both cycles) |
| [Bryn Mawr College](https://www.collegedata.fyi/schools/bryn-mawr-college/2024-25) | 211273 | all 17 = Very Important |
| [California Institute of Technology](https://www.collegedata.fyi/schools/california-institute-of-technology/2024-25) | 110404 | all 17 = Very Important |
| [California State University-Sacramento](https://www.collegedata.fyi/schools/california-state-university-sacramento/2024-25) | 110617 | all 17 = Very Important |
| [Chapman University](https://www.collegedata.fyi/schools/chapman-university/2024-25) | 111948 | all 17 = Very Important |
| [Citadel Military College of South Carolina](https://www.collegedata.fyi/schools/citadel-military-college-of-south-carolina/2024-25) | 217864 | all 17 = Very Important |
| [Colorado College](https://www.collegedata.fyi/schools/colorado-college/2024-25) | 126678 | all 17 = Very Important |
| [Denison University](https://www.collegedata.fyi/schools/denison-university/2024-25) | 202523 | all 17 = Very Important |
| [Florida Atlantic University](https://www.collegedata.fyi/schools/florida-atlantic-university/2024-25) | 133669 | all 17 = Very Important |
| [Florida International University](https://www.collegedata.fyi/schools/florida-international-university/2024-25) | 133951 | 16 of 17 = Very Important |
| [Georgia Gwinnett College](https://www.collegedata.fyi/schools/georgia-gwinnett-college/2024-25) | 447689 | all 17 = Very Important |
| [Gonzaga University](https://www.collegedata.fyi/schools/gonzaga-university/2024-25) | 235316 | all 17 = Very Important |
| [Hobart William Smith Colleges](https://www.collegedata.fyi/schools/hobart-william-smith-colleges/2024-25) | 191630 | 16 of 17 = Very Important |
| [Kent State University at Kent](https://www.collegedata.fyi/schools/kent-state-university-at-kent/2025-26) | 203517 | all 17 = Very Important |
| [Lee University](https://www.collegedata.fyi/schools/lee-university/2025-26) | 220613 | all 17 = Very Important (both cycles) |
| [Lewis-Clark State College](https://www.collegedata.fyi/schools/lewis-clark-state-college/2025-26) | 142328 | all 18 = Very Important |
| [Marquette University](https://www.collegedata.fyi/schools/marquette-university/2024-25) | 239105 | all 17 = Very Important |
| [North Carolina Central University](https://www.collegedata.fyi/schools/north-carolina-central-university/2024-25) | 199157 | 16 of 17 = Very Important |
| [Northwestern University](https://www.collegedata.fyi/schools/northwestern/2024-25) | 147767 | all 17 = Very Important |
| [Oregon Institute of Technology](https://www.collegedata.fyi/schools/oregon-institute-of-technology/2025-26) | 209506 | all 18 = Very Important (both cycles) |
| [Ramapo College of New Jersey](https://www.collegedata.fyi/schools/ramapo-college-of-new-jersey/2024-25) | 186201 | all 17 = Very Important |
| [Rochester Institute of Technology](https://www.collegedata.fyi/schools/rochester-institute-of-technology/2025-26) | 195003 | 17 of 18 = Very Important |
| [Southern Methodist University](https://www.collegedata.fyi/schools/southern-methodist-university/2025-26) | 228246 | 16 of 17 = Very Important (both cycles) |
| [Temple University](https://www.collegedata.fyi/schools/temple/2024-25) | 216339 | all 17 = Very Important |
| [Texas State University](https://www.collegedata.fyi/schools/texas-state-university/2024-25) | 228459 | all 17 = Very Important |
| [The College of Wooster](https://www.collegedata.fyi/schools/the-college-of-wooster/2024-25) | 206589 | all 16 = Very Important |
| [University of Arkansas](https://www.collegedata.fyi/schools/university-of-arkansas/2025-26) | 106397 | all 18 = Very Important |
| [University of California-Santa Cruz](https://www.collegedata.fyi/schools/university-of-california-santa-cruz/2024-25) | 110714 | all 17 = Very Important |
| [University of Colorado Boulder](https://www.collegedata.fyi/schools/colorado/2024-25) | 126614 | all 16 = Very Important |
| [University of Delaware](https://www.collegedata.fyi/schools/udel/2024-25) | 130943 | all 17 = Very Important |
| [University of Illinois Chicago](https://www.collegedata.fyi/schools/university-of-illinois-chicago/2024-25) | 145600 | all 17 = Very Important |
| [University of Iowa](https://www.collegedata.fyi/schools/university-of-iowa/2024-25) | 153658 | all 17 = Very Important |
| [University of Michigan-Ann Arbor](https://www.collegedata.fyi/schools/umich/2025-26) | 170976 | all 17 = Very Important |
| [University of Missouri-St Louis](https://www.collegedata.fyi/schools/university-of-missouri-st-louis/2025-26) | 178420 | all 17 = Very Important |
| [University of New Hampshire-Main Campus](https://www.collegedata.fyi/schools/university-of-new-hampshire-main-campus/2024-25) | 183044 | all 17 = Very Important |
| [University of North Carolina Asheville](https://www.collegedata.fyi/schools/university-of-north-carolina-asheville/2024-25) | 199111 | all 17 = Very Important |
| [University of North Texas](https://www.collegedata.fyi/schools/university-of-north-texas/2025-26) | 227216 | all 18 = Very Important (both cycles) |
| [University of Pikeville](https://www.collegedata.fyi/schools/university-of-pikeville/2025-26) | 157535 | all 17 = Very Important |
| [University of South Dakota](https://www.collegedata.fyi/schools/university-of-south-dakota/2024-25) | 219471 | 13 of 17 = Very Important |
| [University of Utah](https://www.collegedata.fyi/schools/university-of-utah/2024-25) | 230764 | 16 of 17 = Very Important |
| [Virginia Commonwealth University](https://www.collegedata.fyi/schools/virginia-commonwealth-university/2024-25) | 234030 | 15 of 16 = Very Important |
| [Washington College](https://www.collegedata.fyi/schools/washington-college/2024-25) | 164216 | 16 of 17 = Very Important |
| [Washington State University](https://www.collegedata.fyi/schools/washington-state-university/2024-25) | 236939 | all 17 = Very Important |
| [Wentworth Institute of Technology](https://www.collegedata.fyi/schools/wentworth-institute-of-technology/2025-26) | 168227 | 16 of 17 = Very Important |
| [West Virginia University](https://www.collegedata.fyi/schools/west-virginia-university/2024-25) | 238032 | 16 of 17 = Very Important |

### All factors misread as "Not Considered" (1)

Caught by the *uniform* signature; the contextual-implausibility rule alone would miss an all-*Not Considered* bleed.

| School | IPEDS | What the parse produced |
|---|---|---|
| [Missouri Western State University](https://www.collegedata.fyi/schools/missouri-western-state-university/2025-26) | 178387 | all 18 = Not Considered |

### Fragmentary / misaligned parse (3)

Spreadsheet cells bled into the C7 columns, leaving only stray non-academic fields (e.g. a lone spurious `Religion = Very Important`) with none of the academic anchors.

| School | IPEDS | What the parse produced |
|---|---|---|
| [Florida Institute of Technology](https://www.collegedata.fyi/schools/florida-institute-of-technology/2024-25) | 133881 | 1 field only (Level of applicant's interest); no academic factor |
| [Purdue University-Main Campus](https://www.collegedata.fyi/schools/purdue/2025-26) | 243780 | 2 fields only (Extracurricular activities, Religious affiliation / commitment); no academic factor |
| [University of Missouri-Columbia](https://www.collegedata.fyi/schools/university-of-missouri-columbia/2024-25) | 178396 | 2 fields only (Recommendation(s), Character / personal qualities); no academic factor |

<!-- END GENERATED: c7-dropped -->

## Regenerating

The list above refreshes automatically whenever you run `python pipeline/build_data.py`
(the pipeline reports the count on every run: `dropping N garbled school-cycle records`, and
`wrote c7-dropped-schools.md`). The drop logic lives in `parse_collegedata_c7`; the field
sets it keys on are `C7_CONTEXTUAL_FIELDS` and `C7_ANCHOR_FIELDS` in `pipeline/config.py`.
