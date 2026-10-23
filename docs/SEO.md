# SEO plan

## Keyword data (Google Trends, worldwide, 2025-10-19 to 2026-10-18)

Source: two Google Trends CSV exports provided by the product owner. Trends values are **relative interest, not
search volumes**, and each export is scaled to its own peak. "audio to sheet music" appears in both exports, so the
second export was rescaled to the first by the ratio of that term's averages (×1.24).

| Keyword | Avg. interest (common scale) | First 3 months → last 3 months | Fit |
|---|---|---|---|
| audio to midi | 57 | 52 → 38 | Large but wants MIDI files; one comparison page |
| solfege | 36 | 35 → 28 | Large; mostly ear training and fixed/movable do learners; one explainer page |
| music transcription | 35 | 24 → 17 | Broad, competitive; covered by the "audio to tonic solfa" page |
| sheet music software | 19 | 15 → 13 | Wrong output (staff notation); not targeted |
| **tonic solfa** | **12** | **11 → 9** | **Exact product match, steadiest trend; primary target** |
| audio to sheet music | 11 | 13 → 5 | Close intent; covered by "audio to tonic solfa" |
| ai music transcription | 8 | 7 → 3 | Covered by "audio to tonic solfa" |
| music transcription software | 3 | 2 → 1 | Covered by "audio to tonic solfa" |
| musical notation software | 0 | 0 → 0 | No measurable interest; dropped |

## Pages and the keywords they target

| Page | Primary keyword | Also covers |
|---|---|---|
| `/` | tonic solfa | tonic solfa for keyboard, audio to solfa |
| `/how-to-read-tonic-solfa-on-keyboard` | tonic solfa | how to read tonic solfa, solfa on keyboard |
| `/audio-to-tonic-solfa` | audio to sheet music | music transcription, ai music transcription, music transcription software |
| `/audio-to-midi-or-tonic-solfa` | audio to midi | |
| `/solfege-and-tonic-solfa` | solfege | movable do, fixed do |

## What is in place

- Every public page is prerendered HTML with a unique title, meta description, canonical URL, Open Graph and Twitter
  card tags, and a 1200×630 preview image.
- Structured data: `WebApplication` and `FAQPage` on the home page (the FAQ text is the visible FAQ), `Article` on
  each guide.
- `sitemap.xml` lists the five public pages; `robots.txt` disallows `/songs`, `/results/` and `/api/`, and song
  pages also carry `noindex`.
- Fast, light pages for slow mobile data: self-hosted fonts, no tracking scripts, about 17 kB gzipped for the
  largest script chunk.

## Not done yet

- **Real domain.** `https://solfaflow.com` is a placeholder in `frontend/src/lib/site.ts` and `frontend/static/robots.txt`.
- **Regional data.** Pull Google Trends "interest by region" and "related queries" for "tonic solfa". Interest is
  expected to concentrate in Nigeria, Ghana, South Africa and Kenya, but that has not been checked.
- **Song-specific searches** ("<song> tonic solfa") are probably a large share of real demand. They conflict with the
  decision not to keep a public library of transcriptions (copyright); the guides are the safe alternative.
- **Search Console and analytics** after launch, to see which queries actually bring visitors.
- Guide copy has not been reviewed by a tonic solfa teacher.
