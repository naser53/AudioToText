"""Optional speaker detection with pyannote.audio.

Needs `pip install pyannote.audio` and a free Hugging Face token (HF_TOKEN)
after accepting the terms of pyannote/speaker-diarization-3.1 on huggingface.co.
Without them, every segment is labelled "Speaker 1".
"""
import os
from functools import lru_cache

from .models import Segment

PIPELINE_NAME = "pyannote/speaker-diarization-3.1"


def is_available() -> bool:
    if not os.environ.get("HF_TOKEN"):
        return False
    try:
        import pyannote.audio  # noqa: F401
    except ImportError:
        return False
    return True


@lru_cache(maxsize=1)
def _load_pipeline():
    from pyannote.audio import Pipeline

    return Pipeline.from_pretrained(PIPELINE_NAME, use_auth_token=os.environ["HF_TOKEN"])


def speaker_turns(path: str) -> list[tuple[float, float, str]]:
    diarization = _load_pipeline()(path)
    return [(turn.start, turn.end, label)
            for turn, _, label in diarization.itertracks(yield_label=True)]


def assign_speakers(segments: list[Segment], turns: list[tuple[float, float, str]]) -> None:
    """Give each segment the speaker that overlaps it most, renamed Speaker 1, 2, ..."""
    names: dict[str, str] = {}
    for seg in segments:
        best, best_overlap = None, 0.0
        for start, end, label in turns:
            overlap = min(seg.end, end) - max(seg.start, start)
            if overlap > best_overlap:
                best, best_overlap = label, overlap
        if best is None:
            seg.speaker = "Speaker 1" if not names else next(iter(names.values()))
            continue
        if best not in names:
            names[best] = f"Speaker {len(names) + 1}"
        seg.speaker = names[best]


def label_speakers(path: str, segments: list[Segment]) -> bool:
    """Fill in seg.speaker. Returns True if real speaker detection was used."""
    if is_available():
        assign_speakers(segments, speaker_turns(path))
        return True
    for seg in segments:
        seg.speaker = "Speaker 1"
    return False
