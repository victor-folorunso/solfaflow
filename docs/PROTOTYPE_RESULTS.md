# Prototype results — 2026-10-23

First end-to-end run of `prototype/` (song → separated vocal → notes → keyboard solfa → synced player).
**This is a smoke test on three public recordings, not a benchmark.** There are no human-verified note annotations yet,
so no precision/recall numbers are claimed. "Correct" below means checked by ear-knowledge of a well-known tune.

## Setup

| Item | Value |
|---|---|
| Machine | Intel Core i7-8565U (4 cores, 2018 laptop CPU), 16 GB RAM, **no GPU**, Windows 11 |
| Python / torch | 3.12.10 / torch 2.11.0+cpu |
| Vocal separation | audio-separator 0.30.2, `vocals_mel_band_roformer.ckpt` (Kimberley Jensen Mel-Band RoFormer; listed vocal SDR 12.6) |
| Transcription | openvpi GAME 1.0 medium (`GAME-1.0-medium.zip`, sha256 `8c5b3e53…a60c`), default settings (D3PM 8 steps, thresholds 0.2) |
| Post-processing | `prototype/keyboard.py` (deterministic) |

## Research summary (why these engines)

Web research on 2026-10-22, with sources:
- **Vocal separation:** BS-RoFormer / Mel-Band RoFormer variants top current vocal-separation leaderboards
  ([MVSEP](https://mvsep.com/en), [Mel-Band RoFormer paper](https://arxiv.org/pdf/2310.01809)). audio-separator exposes the
  community checkpoints; the one used has the highest vocal SDR in its list.
- **Singing → notes:** [openvpi/GAME](https://github.com/openvpi/GAME) (successor of SOME; MIT code; release v1.0.3 March 2026,
  ONNX builds available) is singing-specific, outputs onset/offset seconds + float pitch, and claims robustness to
  noise/reverb/leftover accompaniment. [VocalParse](https://arxiv.org/abs/2605.04613) (May 2026, Qwen3-ASR-1.7B fine-tune,
  Apache-2.0 code) claims SOTA but needs a GPU-class model and emits note values + BPM rather than seconds — worse fit for
  synced playback and free-tier cost; worth a later benchmark. [ROSVOT](https://arxiv.org/abs/2405.09940) (ACL 2024) is another
  candidate. [RMVPE](https://arxiv.org/abs/2306.15412) is a frame-level pitch tracker, not a note transcriber.
- **Weight licences are not stated** for GAME or the RoFormer checkpoint. Must be resolved before any public release.

## Results

| Recording (Wikimedia Commons) | Length | Separation | Result |
|---|---|---|---|
| `Breves_dies_hominis.ogg` — solo unaccompanied voice, public domain | 212 s | skipped | 212 notes. Singer drifts **+1.15 semitones** over the piece; a single global tuning gave mostly chromatic garbage (key score 0.59). With drift tracking: do = D, almost all diatonic (*re la la so so la la la do' ti la so fa mi…*), plausible Dorian chant. Not verified note-by-note. |
| `La_Cucaracha.ogg` — voice + guitar, CC BY-SA 3.0 | 43.5 s | **none** | 82 notes, many stray chromatics (ri, li, si) from guitar leakage; repeated same-pitch syllables merged. |
| same | 43.5 s | Mel-Band RoFormer | 98 notes. Pitches match the known chorus: E E E A C# = **s s s d m**, then *t, t, d d t, t, l, l, s,*. Key initially wrong (do = E, 0.846 vs A 0.812) because the tune dwells on so; fixed by a final-note tie-break → do = A. Remaining errors: a few short scoop notes become chromatic syllables (*si* between two *so*). |
| `Love_In_Vain_Blues_-_Colin_Ross_Band,_2004.ogg` — full band, CC BY-SA 3.0 | first 60 s | Mel-Band RoFormer | 92 notes, do = C with the tune centred on la (A minor, typical for blues in A). Many chromatic syllables (*ri, li, fi, di*), which may be genuine blue notes and bends, or errors; not verifiable without a reference. Separation 698 s + transcription 421 s for 60 s of audio (run alongside another job). |
| `La_Cucaracha.ogg`, first 15 s only, via the web UI | 15 s | Mel-Band RoFormer | 14 notes; **key wrong (do = E)**. The clip stops before the tune comes home to A, so the final-note tie-break can't help. Short clips need the user to set do. |

## Speed (CPU only, this laptop)

| Stage | La Cucaracha (43.5 s audio) | Real-time factor |
|---|---|---|
| Mel-Band RoFormer separation | 500 s | ~11.5× slower than real time |
| GAME medium transcription | 290 s | ~6.7× |
| Solo voice, GAME only (212 s audio) | 334 s | ~1.6× |

GAME's speed varied a lot between runs (1.6×–7.5× real time); the separation download was running concurrently during
some runs, so treat these as rough. **A 4-minute song would take roughly an hour end-to-end on this laptop.** That is
fine for a prototype but not for a free product. Options: GAME small model / fewer D3PM steps / ONNX runtime;
a lighter separator; a cheap GPU server; or browser/on-device inference. None measured yet.

## Progressive (chunked) processing — 2026-10-23

Same machine, `La_Cucaracha.ogg` (43.5 s), uploaded through the web UI. Chunks: 0–10.95 s, 10.95–33.4 s,
33.4–43.5 s, each padded 3 s. The first cut landed 0.26 s before the singer's first note (quietest-point search).

| | Whole song (earlier run) | Progressive |
|---|---|---|
| Player usable (song plays) | after 790 s | **~15 s** |
| First solfa visible | after 790 s | 168 s for chunk 1, but it was all guitar intro with no notes; first notes at **~480 s** |
| Everything done | 790 s | **653 s** (models loaded once, which outweighs the padding overhead) |
| Key | do = A | do = E while partial, **corrected to A** when the ending arrived |

Quality check (onset ±50 ms + same key, `compare_notes.py`):

| Comparison | Matched | F1 |
|---|---|---|
| Whole song vs the same whole-song vocal re-run through GAME | 90 / 98 | 0.928 |
| Whole song vs progressive | 92 / 98 | 0.953 |

**Chunking changed the result less than GAME's own run-to-run randomness did**, and the differing notes are spread
through the song, not clustered at the cuts. One song is not proof, but no quality loss from chunking was observed.
GAME's randomness (D3PM boundary sampling uses `torch.rand`) is now fixed with a seed, so a song gives the same
solfa every time.

Still slow on this laptop: ~11× real time per chunk. An instrumental intro delays the first visible solfa because
it is transcribed (as nothing) first. Fixes: a GPU, and transcribing the intro's instrument melody (open question).

## Slide cleanup, piano sound and chords — 2026-10-23

### Slide cleanup (`keyboard.clean_slides`)

Singers slide into and between notes; GAME then reports pitches between two keys that snap to a sharp/flat
("do **ri** mi" for a sung "do re mi"). An out-of-key note now moves to the nearer in-key note, unless it is held
(≥ 0.6 s) and sung squarely on the chromatic key (± 0.25 semitone). If the nearer note would just repeat a neighbour
while the other in-key note lies between them (a third apart at most), it is a passing step ("mi ri do" → "mi re do").
The exact, uncleaned notes are kept and the player has an **Exact (as sung)** view.

| Recording | Before | After |
|---|---|---|
| Mary Had a Little Lamb (user upload), first 36 s, do = C, vs the standard tune (3 verses, 78 notes, edit distance) | syllable accuracy **0.756** (6 × *ri*, 2 × *si*) | **0.833**, no *ri* left |
| La Cucaracha (separated) | 4 chromatic syllables from scoops, e.g. *so so **si** so do* | **0** chromatics; chorus reads *so, so, so, so, do do mi* |
| Love in Vain (blues) | — | 21 notes changed. Some are probably real blue notes, not slides: the in-key prior is wrong for blues, hence the Exact view |

What is left on Mary is mostly the singer's own repeated/merged syllables and pickup or breath notes, not pitch errors.
The rule is mirrored in the player's JavaScript so changing do re-cleans instantly; the two implementations were
compared on both fixture songs for all 12 possible keys: **2,748 notes, 0 mismatches**.

### Piano-like playback

"Detected notes" now plays a synthetic piano-like tone (8 slightly inharmonic overtones decaying faster the higher they
are, two strings detuned ±0.7 cents, damper release at note end), with detected chords softly underneath. Rendering
131 notes takes ~1.7 s on this laptop; repeated notes are cached because the track is re-rendered after every chunk.

### Chords (`chords.py`)

Method: chroma (CQT, ~93 ms frames) of the separator's accompaniment stem, matched against the 24 major/minor triads,
Viterbi-smoothed with a chord-change penalty; quiet frames are "no chord", pauses ≤ 0.5 s are bridged, chords
< 0.6 s are folded into the previous one. Deterministic, no extra model or download. The separator already computed
the accompaniment; it is now saved instead of discarded.

**Bug found and fixed on the first real run:** the separator names this model's stems in lowercase ("(vocals)"),
so the vocal stem was filed as accompaniment and transcription had no input. Matching is now case-insensitive and
fails loudly if no vocal stem is found.

**Second fix:** on Mary the quiet moments between accompaniment hits (0.28 s gaps) split chords into fragments
(median chord 0.47 s, 33 chords in 30 s). Bridging short pauses gave a median of 1.12 s, 26 chords.

| Recording | Chords detected (start s: chord) | Plausible? |
|---|---|---|
| La Cucaracha (43.5 s) | 0.3 A · 4.4 E · 10.2 A · 16.0 E · 21.8 A · 27.6 E · 33.5 A · 35.0 E · 36.4 A · 37.8 E · 42.2 A (E 23.3 s, A 19.7 s) | **Yes**: I and V in A, the usual harmony for this song; even the guitar intro (0–11 s) gets chords |
| Mary Had a Little Lamb, first 30 s | 0.1 C · 0.7 Gm · 1.3 C · 1.9 G · 2.6 C · 4.5 G · 6.3 C · 7.6 G · 8.8 C · 10.0 Am · 12.5 Dm · 13.3 G · 13.9 C · 17.1 Em · 17.7 G · 19.0 C · 20.1 Am · 21.5 A · 22.6 G · 24.0 C · … | **Mostly**: C and G (I and V) dominate, as expected; the Gm, A, Dm are probably errors |

Neither has been checked against a reference chord chart, so chord accuracy is still **unmeasured**. Limits: major/minor
triads only (sevenths, sus and slash chords map to the nearest triad), no bass-note or beat awareness.

**Chords as key evidence: tried, measured, switched off** (`USE_CHORDS_FOR_KEY = False`). Adding chord tones to
the key estimate (melody and harmony weighted equally) fixed neither song and broke one:

| Recording | Melody only | Melody + chord tones |
|---|---|---|
| La Cucaracha (true do = A) | **do = A** (0.869 vs E 0.844) | do = E (0.922 vs A 0.783), wrong |
| Mary (true do = C) | do = G (0.621 vs C 0.482), wrong | do = G (0.788 vs C 0.691), wrong |

The cause is systematic: an I–V accompaniment (A and E) contains exactly the notes of IV–I a fifth higher (E major),
so chord tones pull do up a fifth; Mary's C and G pull toward G the same way. Ideas for a better use of chords, not
yet tried: the first/last chord as tonic (right for La Cucaracha's A; Mary's first chord C is right, its last chord in
a 30 s excerpt is not), or the bass note under each chord.

In the browser (Mary, do set to C): chords show as **C I · G V · C I…** above the notes, the intro shows chord chips,
three chord-tone keys light on the mini keyboard during playback, Show/Hide works, no console errors.

## Findings that changed the code

1. **Vocal separation is necessary** — without it, accompaniment leaks in as wrong notes.
2. **Tuning drift is real** for unaccompanied singing → `estimate_tuning_curve` (per-note, ±10 s circular mean, unwrapped).
   Abrupt key changes still land on whole semitones and are preserved (tested).
3. **Key-profile correlation alone mis-keys melodies that sit on so** → final-note bonus (0.05). Regression test uses
   the real La Cucaracha transcription (`prototype/tests/fixtures/`). The user can always override do in the player.

## Known gaps

- No human-verified reference annotations → no real accuracy numbers. Next step: annotate 10–20 clips of the songs
  target users actually play.
- Slide cleanup prefers in-key notes, so genuine chromatic/blue notes that are short get "cleaned" (Exact view keeps them).
- Key estimate still wrong on Mary Had a Little Lamb (the user sets do = C in the player). Chord tones as
  evidence made things worse (I–V reads as IV–I a fifth up). Untried: phrase-final notes, first/last chord, bass notes.
- Chord accuracy unmeasured; triads only.
- Repeated syllables on one pitch are sometimes merged into one long note (without separation, seen once).
- No rhythm/beat grid: durations are shown as bar lengths, not musical note values.
- Weight licences (GAME, RoFormer checkpoint) unverified.
