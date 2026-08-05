# Portfolio Ops Copilot — memo viewer

A small standalone Vite + React + TypeScript static site that renders the same
`output/<company>/action_memo.json` the Python pipeline produces. It runs **alongside** the main
Streamlit app (`app/streamlit_app.py`), not instead of it:

- **Streamlit app** — the "watch it run" story: uploads files, shells out to the `claude` CLI,
  streams a live `/diagnose` run.
- **This viewer** — the "read the results" story: a fast, always-warm static site with no Python
  runtime, no cold start. It never invokes the pipeline; it only displays already-committed
  output.

## Local development

```bash
npm install
npm run dev
```

`npm run dev` (and `npm run build`) first runs `scripts/sync_data.py`, which copies
`../output/*/action_memo.json` into `public/data/` and writes `public/data/manifest.json` — the
manifest is how the app knows which companies exist. Re-run `npm run sync-data` any time the
Python pipeline produces a new company's output and you want the viewer to pick it up.

## Build

```bash
npm run build
```

Outputs a static site to `dist/` — deployable to any static host (Vercel, Netlify, GitHub Pages).
No server-side code, no environment variables required.

## Types

`src/types.ts` hand-mirrors the `ActionItem`/`ActionMemo` Pydantic models in
`../pipeline/schemas.py`. If the Python schema changes shape, this file needs a matching edit —
same "schemas are the contract" discipline the pipeline itself applies (see the root `CLAUDE.md`),
just on the TypeScript side of the fence.
