# Audio transcription engine research notes

This is a **candidate shortlist**, not a benchmark report. The prior discussion compared project descriptions and likely fit at a high level. No candidate was installed, run, or scored in the current environment. Confirm all current repository state, releases, model assets, and licenses from upstream before implementation.

## Product requirement the engine must serve

Input is audio; output needs note events with:
- pitch (MIDI or a stable equivalent),
- onset/start time in seconds,
- offset/end time in seconds,
- confidence/uncertainty where available,
- optional source/voice/part identity,
- ideally rests/gaps preserved by the downstream event representation.

The product then estimates or accepts a tonic/key and maps pitches to movable-do solfa. A model that produces a plausible MIDI file is not automatically good enough: note boundaries and melodic accuracy must be tested because they drive syllable highlighting.

## Candidates previously discussed

### 1. Spotify Basic Pitch
**Role to investigate:** simple baseline for audio-to-MIDI, especially a single prominent pitched source.

- Previously described as an open-source neural transcription model with an Apache 2.0 code license.
- Produces note activations/onsets/contours and post-processes them into note events/MIDI.
- Potential advantage: comparatively approachable baseline and useful ecosystem.
- Potential limitation: general-purpose pitch transcription can struggle with dense polyphony, vocals mixed with accompaniment, harmonics, noisy recordings, and precise note boundaries.
- Next action: inspect the current upstream repo and supported Python/runtime versions; verify the license for both code and any model assets; run it on the same benchmark clips as the other candidates.

Upstream starting point (verify current URL and status): https://github.com/spotify/basic-pitch

### 2. Google Magenta MT3
**Role to investigate:** research-grade multi-instrument audio-to-symbolic transcription for more complex mixtures.

- Previously described as a Transformer that generates symbolic note events from audio/spectrogram features.
- Potential advantage: designed for multi-instrument transcription rather than only a single melody.
- Potential limitation: heavier research stack and deployment/latency complexity; performance on singing/choir audio cannot be assumed from general multi-instrument results.
- Next action: inspect the official repository, available checkpoints, inference requirements, checkpoint license, and reproducibility; compare against simpler models.

Upstream starting point (verify current URL and status): https://github.com/magenta/mt3

### 3. GAME (singing voice to MIDI)
**Role to investigate:** singing-focused pitch/note transcription, potentially the best-aligned candidate for a vocal-melody MVP.

- Previously discussed as a singing-voice-to-MIDI model.
- Potential advantage: task focus is closer to a person singing a melody than general instrument transcription.
- Limitations to investigate: supported singing styles, accompaniment/noise robustness, monophonic vs polyphonic output, timing accuracy, maintenance, inference cost, and rights to model weights.
- Next action: identify and inspect the exact authoritative upstream repository/checkpoint (the earlier conversation named “GAME” but did not preserve a verified canonical URL). Do not guess the repo or assume it supports choir transcription.

### 4. Demucs
**Role to investigate:** optional vocal/instrument stem separation before transcription, not a note-transcription engine by itself.

- Could isolate vocals from accompaniment before a singing-oriented transcription model.
- Potential benefit: reduced accompaniment interference.
- Risk: separation artifacts may remove/alter pitches or note attacks and can worsen transcription. Adds latency, compute, and another model/license.
- Next action: only test if baseline results show accompaniment is a major failure mode. Compare downstream note accuracy on original mix versus separated vocal stem; don't add it by default.

Upstream starting point (verify current URL and status): https://github.com/facebookresearch/demucs

### 5. NeuralNote / MuScriptor
**Role to investigate:** general audio-to-MIDI / multi-instrument transcription tools.

- Previously discussed as potentially useful for general transcription and possibly C++/ggml-oriented deployment.
- Major caveat from earlier research notes: bundled model weights were described as **CC BY-NC 4.0**, which is non-commercial. Treat commercial use as blocked until current upstream code, weights, and their licenses are separately confirmed. Code license does not automatically cover weights.
- Next action: inspect the exact project and assets; don't rely on a wrapper's open-source status as proof that the full stack can be used commercially.

The exact canonical repository and asset/version mapping were not preserved in the conversation; verify rather than invent links.

## Suggested comparison matrix

Run each viable candidate on the same audio, same reference annotations, and documented hardware/software. Do not compare a model on easy clips against another model on hard clips.

| Dimension | What to measure |
|---|---|
| Note pitch | note precision/recall/F1 with a defined semitone tolerance; pitch error |
| Onset timing | onset precision/recall/F1 within documented timing tolerance |
| Offset/duration | offset error and duration error; long-note stability |
| Melody usability | fraction of melody events a human considers correct and singable |
| Key/tonic | tonic accuracy separately from transcription |
| Solfa result | syllable accuracy after applying a verified tonic and chosen convention |
| Robustness | clean voice, voice + accompaniment, phone/noisy audio, choir if in scope |
| Speed | real-time factor, peak memory, CPU/GPU needs, cold-start time |
| Integration | install complexity, Python/runtime compatibility, API/service suitability |
| Licensing | code, checkpoint weights, dependencies, training/evaluation data restrictions |
| Operations | model download size, reproducible versions, maintenance, offline/server deployment |

Define the scoring method before running tests. Report per-condition results, not just one blended number. Keep key-estimation errors separate from note-transcription errors so a wrong tonic does not obscure the source of a solfa mistake.

## Recommended evaluation workflow

1. Create 10–30 short representative clips for an initial bake-off (the eventual set should be larger).
2. Obtain human-verified reference note events, tonic/key, and intended solfa convention. Ensure audio and annotations can legally be used.
3. Include difficult cases relevant to the target user, not only public benchmark datasets.
4. Run a baseline candidate (Basic Pitch is a reasonable first baseline) and a singing-focused candidate (GAME, once exact repo/checkpoint is identified).
5. Add MT3 if mixed/polyphonic transcription is required and installation/license checks pass.
6. Test Demucs only as an ablation: original audio vs separated vocals.
7. Inspect false positives, missed notes, octave errors, note merges/splits, and onset/offset drift.
8. Select the simplest candidate that meets a product-defined quality threshold on target audio. If none passes, narrow scope or design a correction workflow rather than claiming success.
9. Record commands, dependency lock versions, model/checkpoint hashes, hardware, licenses, metrics, and known failure modes in the repository.

## Important unknowns

- Is the MVP single singer/melody, or choir/multiple simultaneous voices?
- Must it work on audio with full instrumental accompaniment?
- Is processing expected locally/offline, or on a server?
- What is the target latency and maximum upload length?
- Is commercial use required from day one?
- Which solfa convention(s) should be supported (major movable-do, minor convention, chromatic syllables, fixed-do, local traditions)?
- What accuracy threshold is acceptable, and what should the UI do when the model is uncertain?

## Bottom line

Do not choose a “winner” yet. The previous discussion suggested **GAME for singing melody**, **Basic Pitch as an accessible baseline**, and **MT3 for more complex mixtures**. Those are hypotheses to test. The only defensible selection comes from reproducible evaluation on representative, legally usable audio plus a license audit.
