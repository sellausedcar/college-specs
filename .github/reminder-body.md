👋 @sellausedcar — monthly reminder for **College Specs**.

**Rewrite Scorecard to use the API** — api.data.gov is a different host that isn't IP-blocked. This would make cloud automation work, but it's a real rewrite (~50 field mappings + pagination) and needs a free API key stored as a GitHub secret (the key stays server-side, never in the published site). Heavier, but truly hands-off.

**Keep it manual.** The underlying data only changes ~once a year, so the effort of either automation path isn't worth it. When new Scorecard/IPEDS data drops, just:

```
python pipeline/build_data.py
git commit -am "refresh data"
git push
```

…and the site updates itself within a minute.

---

**Essay-prompt links — a possible upgrade.** Right now, each school's *“see prompts”* links drop you
on the My Supplementals / CollegeVine databases where **you type the school name** into the search
box. A **“build-time ID-mapping” option** would instead pre-select the school so you don't have to
type it — **more efficient, but more fragile** (it breaks silently whenever those databases change
their internal IDs or data, which can happen every application cycle). Deferred for now; full pros &
cons in [README → Future improvement](https://github.com/sellausedcar/college-specs/blob/master/README.md#future-improvement--build-time-id-mapping-for-essay-prompt-links).

*(Automated monthly reminder — close this issue once you've refreshed, or just ignore it.)*
