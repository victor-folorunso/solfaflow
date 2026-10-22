# SolfaFlow — instructions for coding agents

Read these before changing code:
1. `docs/PROJECT_HANDOFF.md` — product intent, conversation decisions, current state, and immediate next steps.
2. `docs/ENGINE_RESEARCH.md` — candidate transcription engines and what is/isn't verified.
3. `docs/ARCHITECTURE_AND_ROADMAP.md` — proposed system architecture, evaluation plan, and milestones.
4. `docs/DECISIONS.md` — decisions, constraints, and unresolved questions.
5. `README.md` — setup and repository overview.

## Non-negotiable working rules
- Do not claim an audio transcription engine works until it has actually been installed, run, and evaluated on representative audio.
- Keep deterministic solfa conversion separate from probabilistic audio transcription and key/tonic estimation.
- Preserve note timing (onset, offset, rests, duration) end-to-end; synchronized playback is a core product feature, not decoration.
- Benchmark on human-verified reference annotations. Report exact dataset, metrics, model version, environment, and limitations.
- Audit code, model-weight, and dataset licenses separately before any commercial use. Do not assume an open-source inference wrapper means the weights are commercially usable.
- Do not promise 100% transcription accuracy. Surface uncertainty and allow correction.
- Keep the first milestone narrow. Melody-only versus choir/polyphonic transcription is still an unresolved product-scope decision; do not silently assume choir separation is solved.
- Avoid heavyweight model dependencies in the core API until a candidate has passed the benchmark gate.
- Add/update tests for every behavior change. GitHub Actions exists, but a passing run has not yet been verified in the work documented here.
- Clearly label facts, hypotheses, and unverified research. Do not fabricate benchmark results.
