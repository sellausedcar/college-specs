👋 @sellausedcar — monthly reminder for **College Specs**.

**Rewrite Scorecard to use the API** — api.data.gov is a different host that isn't IP-blocked. This would make cloud automation work, but it's a real rewrite (~50 field mappings + pagination) and needs a free API key stored as a GitHub secret (the key stays server-side, never in the published site). Heavier, but truly hands-off.

**Keep it manual.** The underlying data only changes ~once a year, so the effort of either automation path isn't worth it. When new Scorecard/IPEDS data drops, just:

```
python pipeline/build_data.py
git commit -am "refresh data"
git push
```

…and the site updates itself within a minute.

*(Automated monthly reminder — close this issue once you've refreshed, or just ignore it.)*
