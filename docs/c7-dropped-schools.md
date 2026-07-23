# CDS C7 — schools dropped by the parse-failure guards

Stage 2e of `pipeline/build_data.py` drops collegedata.fyi C7 records that show the
fingerprints of a garbled source parse (see the *Admission factors* caveat in the
[README](../README.md#caveats) for the three signatures). This file lists the schools that
were dropped, so that when a well-known school shows **N/A** for admission factors you can
confirm it was a bad parse rather than missing data.

**These schools have a Common Data Set — the aggregator just parsed its C7 table
incorrectly.** We show N/A rather than the fabricated values. A school here can reappear in a
future refresh if the aggregator re-parses it cleanly.

> [!WARNING]
> **Point-in-time snapshot.** Generated from the 2026-07-22 build (2024-25 / 2025-26
> cycles). The dropped set changes whenever the aggregator re-parses a school, so re-derive it
> after a data refresh rather than trusting this list as current — the pipeline reports the
> current *count* on every run (`dropping N garbled school-cycle records`), and
> [Regenerating](#regenerating) below reproduces the names.

## Dropped schools (52)

### Nearly all factors misread as "Very Important" (48)

The checkbox-grid bleed: every factor — or all but one — collapsed to *Very Important*,
including implausible ones like religion and state residency.

| School | IPEDS | What the parse produced |
|---|---|---|
| Albertus Magnus College | 128498 | all 17 = Very Important |
| American University | 131159 | all 17 = Very Important |
| Belmont University | 219709 | all 17 = Very Important |
| Brandeis University | 165015 | 16 of 17 = Very Important (both cycles) |
| Bryn Mawr College | 211273 | all 17 = Very Important |
| California Institute of Technology | 110404 | all 17 = Very Important |
| California State University-Sacramento | 110617 | all 17 = Very Important |
| Chapman University | 111948 | all 17 = Very Important |
| Citadel Military College of South Carolina | 217864 | all 17 = Very Important |
| Colorado College | 126678 | all 17 = Very Important |
| Denison University | 202523 | all 17 = Very Important |
| Florida Atlantic University | 133669 | all 17 = Very Important |
| Florida International University | 133951 | 16 of 17 = Very Important |
| Georgia Gwinnett College | 447689 | all 17 = Very Important |
| Gonzaga University | 235316 | all 17 = Very Important |
| Hobart William Smith Colleges | 191630 | 16 of 17 = Very Important |
| Kent State University at Kent | 203517 | all 17 = Very Important |
| Lee University | 220613 | all 17 = Very Important (both cycles) |
| Lewis-Clark State College | 142328 | all 18 = Very Important |
| Marquette University | 239105 | all 17 = Very Important |
| North Carolina Central University | 199157 | 16 of 17 = Very Important |
| Northwestern University | 147767 | all 17 = Very Important |
| Oregon Institute of Technology | 209506 | all 18 = Very Important (both cycles) |
| Ramapo College of New Jersey | 186201 | all 17 = Very Important |
| Rochester Institute of Technology | 195003 | 17 of 18 = Very Important |
| Southern Methodist University | 228246 | 16 of 17 = Very Important (both cycles) |
| Temple University | 216339 | all 17 = Very Important |
| Texas State University | 228459 | all 17 = Very Important |
| The College of Wooster | 206589 | all 16 = Very Important |
| University of Arkansas | 106397 | all 18 = Very Important |
| University of California-Santa Cruz | 110714 | all 17 = Very Important |
| University of Colorado Boulder | 126614 | all 16 = Very Important |
| University of Delaware | 130943 | all 17 = Very Important |
| University of Illinois Chicago | 145600 | all 17 = Very Important |
| University of Iowa | 153658 | all 17 = Very Important |
| University of Michigan-Ann Arbor | 170976 | all 17 = Very Important |
| University of Missouri-St Louis | 178420 | all 17 = Very Important |
| University of New Hampshire-Main Campus | 183044 | all 17 = Very Important |
| University of North Carolina Asheville | 199111 | all 17 = Very Important |
| University of North Texas | 227216 | all 18 = Very Important (both cycles) |
| University of Pikeville | 157535 | all 17 = Very Important |
| University of South Dakota | 219471 | 13 of 17 = Very Important |
| University of Utah | 230764 | 16 of 17 = Very Important |
| Virginia Commonwealth University | 234030 | 15 of 16 = Very Important |
| Washington College | 164216 | 16 of 17 = Very Important |
| Washington State University | 236939 | all 17 = Very Important |
| Wentworth Institute of Technology | 168227 | 16 of 17 = Very Important |
| West Virginia University | 238032 | 16 of 17 = Very Important |

### All factors misread as "Not Considered" (1)

Caught by the *uniform* signature; the contextual-implausibility rule alone would miss an
all-*Not Considered* bleed.

| School | IPEDS | What the parse produced |
|---|---|---|
| Missouri Western State University | 178387 | all 18 = Not Considered |

### Fragmentary / misaligned parse (3)

Spreadsheet cells bled into the C7 columns, leaving only stray non-academic fields (e.g. a
lone spurious `Religion = Very Important`) with none of the academic anchors.

| School | IPEDS | What the parse produced |
|---|---|---|
| Florida Institute of Technology | 133881 | 1 field(s) only (Interest); no academic factor |
| Purdue University-Main Campus | 243780 | 2 field(s) only (Extracurriculars, Religion); no academic factor |
| University of Missouri-Columbia | 178396 | 2 field(s) only (Recommendations, Character); no academic factor |

## Regenerating

The drop logic lives in `parse_collegedata_c7` (`pipeline/build_data.py`); the field sets it
keys on are `C7_CONTEXTUAL_FIELDS` and `C7_ANCHOR_FIELDS` in `pipeline/config.py`. To rebuild
this list from the cached raw feed after a refresh, compare C7 coverage with the guards
disabled vs. enabled — the difference is the dropped set. (A cleaner long-term option is to
have stage 2e emit the dropped names at build time; not wired up yet.)
