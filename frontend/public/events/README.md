# Event artwork (Wikipedia-sourced)

These files were downloaded from English Wikipedia / `upload.wikimedia.org` using:

- `scripts/fetch_event_logos_wikipedia.py`
- Wikipedia REST summaries (`/api/rest_v1/page/summary/...`)
- `Special:FilePath/...` redirects

`manifest.json` lists coverage. Regenerate TypeScript bindings after adding files:

```bash
python -c "exec(open('scripts/fetch_event_logos_wikipedia.py', encoding='utf-8').read().split('if __name__')[0]); write_ts([...])"
```

Or re-run the fetch script (cached files are skipped).

Do not invent or AI-generate official WWE marks.
