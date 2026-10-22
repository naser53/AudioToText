"""Speech to text with faster-whisper (runs locally, free)."""
import os
from functools import lru_cache

from .models import Segment, Transcript

DEFAULT_MODEL = os.environ.get("WHISPER_MODEL", "small")


@lru_cache(maxsize=2)
def _load_model(size: str):
    from faster_whisper import WhisperModel

    device = os.environ.get("WHISPER_DEVICE", "auto")
    compute_type = os.environ.get("WHISPER_COMPUTE_TYPE", "default")
    return WhisperModel(size, device=device, compute_type=compute_type)


def transcribe(path: str, language: str | None = None, model_size: str = DEFAULT_MODEL,
               progress=None) -> Transcript:
    """Transcribe an audio or video file. language=None means auto-detect."""
    model = _load_model(model_size)
    segments_iter, info = model.transcribe(path, language=language or None, vad_filter=True)

    segments = []
    for seg in segments_iter:
        segments.append(Segment(start=seg.start, end=seg.end, text=seg.text.strip()))
        if progress and info.duration:
            progress("transcribing", min(seg.end / info.duration, 1.0))
    return Transcript(language=info.language, segments=segments)
