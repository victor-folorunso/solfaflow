import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from chunking import (  # noqa: E402
    PAD_SECONDS,
    Chunk,
    energy_envelope,
    plan_chunks,
    stitch,
)
from keyboard import RawNote  # noqa: E402


def test_chunks_cover_song_without_gaps_and_first_is_short():
    chunks = plan_chunks(200.0)
    assert chunks[0].core_start == 0.0
    assert chunks[-1].core_end == 200.0
    for a, b in zip(chunks, chunks[1:]):
        assert a.core_end == b.core_start
    assert chunks[0].core_end == pytest.approx(12.0)
    assert all(c.core_end - c.core_start <= 30.0 + 6.0 for c in chunks)


def test_padding_is_clamped_to_song():
    chunks = plan_chunks(50.0)
    assert chunks[0].start == 0.0
    assert chunks[0].end == pytest.approx(chunks[0].core_end + PAD_SECONDS)
    assert chunks[-1].end == 50.0


def test_short_song_is_one_chunk():
    assert len(plan_chunks(8.0)) == 1


def test_tiny_tail_is_merged_into_previous_chunk():
    chunks = plan_chunks(33.0)  # 12 + 20 would leave a 1 s tail
    assert chunks[-1].core_end == 33.0
    assert chunks[-1].core_end - chunks[-1].core_start > 6.0


def test_cut_moves_to_quiet_point_near_target():
    sr = 1000
    audio = np.ones(sr * 40, dtype=np.float32)
    audio[int(13.5 * sr):int(13.7 * sr)] = 0.0  # a breath 1.5 s after the 12 s target
    chunks = plan_chunks(40.0, energy_envelope(audio, sr))
    assert chunks[0].core_end == pytest.approx(13.5, abs=0.1)


def test_stitch_keeps_owned_notes_and_lets_them_run_into_padding():
    chunk = Chunk(1, core_start=12.0, core_end=30.0, start=9.0, end=33.0)
    local = [
        RawNote(1.0, 2.0, 60),   # 10-11 s: in leading padding, owned by previous chunk
        RawNote(3.5, 4.0, 62),   # 12.5 s: owned
        RawNote(20.5, 22.0, 64),  # 29.5-31 s: starts in core, runs into padding: kept whole
        RawNote(21.5, 22.5, 65),  # 30.5 s: trailing padding, owned by next chunk
    ]
    kept = stitch(chunk, local, is_last=False)
    assert [(n.start, n.end, n.pitch) for n in kept] == [(12.5, 13.0, 62), (29.5, 31.0, 64)]


def test_adjacent_chunks_never_duplicate_or_drop_a_note():
    a = Chunk(0, 0.0, 12.0, 0.0, 15.0)
    b = Chunk(1, 12.0, 30.0, 9.0, 33.0)
    # The same sung note seen by both chunks (song time 11.8-12.6 s).
    from_a = stitch(a, [RawNote(11.8, 12.6, 60)], is_last=False)
    from_b = stitch(b, [RawNote(11.8 - 9.0, 12.6 - 9.0, 60)], is_last=True)
    assert len(from_a) + len(from_b) == 1
