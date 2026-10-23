# SolfaFlow website

SvelteKit app for the public site and the song player. The Python server (`../server.py`) does the work: uploads,
transcription progress and results. This app only talks to it over `/api` and `/results`.

## Pages

| Route | Rendering | What it is |
|---|---|---|
| `/` | Prerendered | Home: upload, live demo, how it works, FAQ |
| `/how-to-read-tonic-solfa-on-keyboard`, `/audio-to-tonic-solfa`, `/audio-to-midi-or-tonic-solfa`, `/solfege-and-tonic-solfa` | Prerendered | Guides, one per search-keyword group (see `docs/SEO.md`) |
| `/songs`, `/songs/[id]` | Browser only, `noindex` | A user's songs and the player. Served from the `200.html` shell |
| `/sitemap.xml`, `/robots.txt` | Prerendered / static | Public pages only; song pages and results are disallowed |

## Develop

```bash
# terminal 1, in prototype/: the API on :8765
.venv/Scripts/python.exe -m uvicorn server:app --port 8765
# terminal 2, in prototype/frontend/: the site on :5173, forwarding /api and /results to :8765
npm run dev
```

## Build, check, test

```bash
npm run build   # writes build/, which server.py serves at /
npm run check   # svelte-check (types)
npm test        # vitest
```

`src/lib/solfa.ts` mirrors the slide cleanup in `../keyboard.py`, because the player re-cleans when the user changes
do. `slides.test.ts` replays Python's answers for two real songs in all 12 keys. If `keyboard.py` changes, run
`python export_slide_fixture.py` in `prototype/` and then `npm test`. `tests/test_slide_fixture.py` fails if the
fixture is stale.

## Things to change when the site goes live

- `SITE_URL` in `src/lib/site.ts` and the `Sitemap:` line in `static/robots.txt` use the placeholder
  `https://solfaflow.com`.
- `static/og-image.png` (link previews) is drawn by `python make_og_image.py` in `prototype/`.

Fonts are self-hosted (Bricolage Grotesque and Atkinson Hyperlegible Next, both SIL Open Font License), so the site
makes no requests to Google.
