"""Audio file -> Transcript, with optional translation and speaker labels."""
from . import diarize, translate
from .models import Transcript
from .transcribe import DEFAULT_MODEL, transcribe


def process_audio(path: str, source_lang: str | None = None, target_lang: str | None = None,
                  speakers: bool = False, model_size: str = DEFAULT_MODEL,
                  progress=None) -> Transcript:
    """source_lang=None auto-detects; target_lang=None keeps the original language."""
    transcript = transcribe(path, language=source_lang, model_size=model_size, progress=progress)

    if speakers:
        if progress:
            progress("detecting speakers", 0.0)
        diarize.label_speakers(path, transcript.segments)

    if target_lang and target_lang != transcript.language:
        translate.translate_segments(transcript.segments, transcript.language, target_lang,
                                     progress=progress)
        transcript.translated_to = target_lang

    return transcript
