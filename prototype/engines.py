"""Model wrappers that load once and are reused for every chunk and every job.

Loading the separator checkpoint and the GAME model takes several seconds
each; with progressive processing a song is many chunks, so reloading per
chunk would waste time without changing results.
"""

from __future__ import annotations

import csv
import shutil
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAME_DIR = HERE / "vendor" / "GAME"
GAME_MODEL = HERE / "models" / "game-medium" / "GAME-1.0-medium" / "model.pt"
SEPARATOR_MODEL = "vocals_mel_band_roformer.ckpt"

_lock = threading.Lock()
_separator = None
_game = None


class VocalSeparator:
    def __init__(self) -> None:
        from audio_separator.separator import Separator

        # Both stems: the model computes the accompaniment anyway, and chords are read from it.
        self._separator = Separator(model_file_dir=str(HERE / "models" / "separator"))
        self._separator.load_model(model_filename=SEPARATOR_MODEL)

    def separate(self, mix_wav: Path, vocals_wav: Path, accompaniment_wav: Path) -> None:
        self._separator.output_dir = str(vocals_wav.parent)
        if self._separator.model_instance is not None:
            self._separator.model_instance.output_dir = str(vocals_wav.parent)
        # Stem names come from each model's config and differ in case ("(Vocals)", "(vocals)").
        outputs = [Path(o).name for o in self._separator.separate(str(mix_wav))]
        vocal = [name for name in outputs if "(vocals)" in name.lower()]
        if len(vocal) != 1:
            raise RuntimeError(f"Expected exactly one vocal stem from the separator, got: {outputs}")
        for name in outputs:
            shutil.move(vocals_wav.parent / name, vocals_wav if name == vocal[0] else accompaniment_wav)


class GameTranscriber:
    """openvpi GAME with the same defaults as its `infer.py extract` command."""

    def __init__(self) -> None:
        if str(GAME_DIR) not in sys.path:
            sys.path.insert(0, str(GAME_DIR))
        from inference.api import load_inference_model

        self._model, lang_map = load_inference_model(GAME_MODEL)
        self._language_id = 0  # universal; GAME's default when no language is given

    def transcribe(self, vocal_wav: Path) -> list[tuple[float, float, float]]:
        """Return (onset, offset, midi_pitch) tuples in seconds relative to the file."""
        import torch
        from inference.api import infer_model
        from inference.callbacks import SaveCombinedTextFileCallback
        from inference.data import SlicedAudioFileIterableDataset
        from inference.slicer2 import Slicer
        from lib.config.schema import ValidationConfig

        # GAME's D3PM boundary sampling draws random numbers; re-running the same
        # audio gave ~92% matching notes. A fixed seed makes results repeatable.
        torch.manual_seed(0)

        sr = self._model.inference_config.features.audio_sample_rate
        dataset = SlicedAudioFileIterableDataset(
            filemap={vocal_wav.name: vocal_wav},
            samplerate=sr,
            slicer=Slicer(sr=sr, threshold=-40.0, min_length=1000, min_interval=200, max_sil_kept=100),
            language=self._language_id,
        )
        callback = SaveCombinedTextFileCallback(output_dir=vocal_wav.parent, file_format="csv",
                                                pitch_format="number", round_pitch=False)
        infer_model(
            model=self._model,
            dataset=dataset,
            config=ValidationConfig(
                d3pm_sample_t0=0.0,
                d3pm_sample_steps=8,
                d3pm_sample_ts=None,
                boundary_decoding_threshold=0.2,
                boundary_decoding_radius=round(0.02 / self._model.timestep),
                note_presence_threshold=0.2,
            ),
            callbacks=[callback],
            batch_size=4,
        )
        notes_csv = vocal_wav.with_suffix(".csv")
        if not notes_csv.exists():  # GAME writes nothing when the slicer finds only silence
            return []
        with open(notes_csv, newline="") as f:
            return [(float(r["onset"]), float(r["offset"]), float(r["pitch"])) for r in csv.DictReader(f)]


def separator() -> VocalSeparator:
    global _separator
    with _lock:
        if _separator is None:
            _separator = VocalSeparator()
        return _separator


def game() -> GameTranscriber:
    global _game
    with _lock:
        if _game is None:
            _game = GameTranscriber()
        return _game
