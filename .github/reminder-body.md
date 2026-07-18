👋 @sellausedcar — monthly nudge for **College Specs**.

A reminder to consider whether the source data needs a refresh, plus the automation options on the table.

### Refresh manually (recommended)

```
python pipeline/build_data.py
git commit -am "refresh data"
git push
```

The live site redeploys itself within a minute.

### Automation options still open

- **Local weekly scheduled task** — already set up (Windows Task Scheduler → `weekly-refresh.cmd`); runs weekly when the PC is on.
- **Deferred: cloud automation via `api.data.gov`** — full hands-off cloud refresh isn't possible today because the Scorecard bulk-download CDN IP-blocks GitHub's runners (403). The fix is to rewrite the Scorecard fetch to use `api.data.gov` (a different host that isn't blocked) — a real rewrite (~50 field mappings + pagination) plus a free API key stored as a GitHub secret (server-side only, never in the published site). Heavier, but truly hands-off.

Full details: [README → Automation options](https://github.com/sellausedcar/college-specs/blob/master/README.md#automation-options-keeping-the-door-open).

*(Automated monthly reminder — close this issue once you've refreshed, or just ignore it.)*
