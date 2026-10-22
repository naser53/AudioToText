"""Output formats: raw text, .srt subtitles and meeting minutes."""
import textwrap

from .languages import language_name
from .models import Segment, Transcript

SRT_LINE_WIDTH = 42
SRT_MAX_LINES = 2
SRT_MAX_SECONDS = 7.0


def _clock(seconds: float, sep: str = ",") -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}{sep}{ms:03}"


def _short_clock(seconds: float) -> str:
    return _clock(seconds)[:8]


def _duration(seconds: float) -> str:
    m, s = divmod(int(round(seconds)), 60)
    return f"{m}m {s:02}s" if m else f"{s}s"


def to_raw_text(t: Transcript) -> str:
    """Plain text, one paragraph per segment."""
    return "\n".join(s.text.strip() for s in t.segments if s.text.strip()) + "\n"


def _split_for_subtitles(seg: Segment) -> list[Segment]:
    """Break a long segment into subtitle-sized pieces, sharing its time by text length."""
    lines = textwrap.wrap(seg.text.strip(), SRT_LINE_WIDTH)
    if not lines:
        return []
    chunks = [lines[i:i + SRT_MAX_LINES] for i in range(0, len(lines), SRT_MAX_LINES)]
    if len(chunks) == 1 and seg.duration <= SRT_MAX_SECONDS:
        return [Segment(seg.start, seg.end, "\n".join(lines), seg.speaker)]

    total = sum(len(" ".join(c)) for c in chunks)
    pieces, cursor = [], seg.start
    for chunk in chunks:
        share = seg.duration * len(" ".join(chunk)) / total
        pieces.append(Segment(cursor, cursor + share, "\n".join(chunk), seg.speaker))
        cursor += share
    return pieces


def to_srt(t: Transcript) -> str:
    blocks = []
    for seg in t.segments:
        for piece in _split_for_subtitles(seg):
            n = len(blocks) + 1
            blocks.append(f"{n}\n{_clock(piece.start)} --> {_clock(piece.end)}\n{piece.text}\n")
    return "\n".join(blocks)


def merge_speaker_turns(segments: list[Segment]) -> list[Segment]:
    """Join consecutive segments from the same speaker into one turn."""
    turns: list[Segment] = []
    for seg in segments:
        if not seg.text.strip():
            continue
        if turns and turns[-1].speaker == seg.speaker:
            turns[-1].end = seg.end
            turns[-1].text += " " + seg.text.strip()
        else:
            turns.append(Segment(seg.start, seg.end, seg.text.strip(), seg.speaker))
    return turns


def to_meeting(t: Transcript, title: str = "Meeting transcript") -> str:
    turns = merge_speaker_turns(t.segments)
    total = t.segments[-1].end if t.segments else 0.0
    speakers = sorted({s.speaker or "Speaker 1" for s in turns},
                      key=lambda name: (len(name), name))

    lang = language_name(t.language)
    if t.translated_to:
        lang += f" (translated to {language_name(t.translated_to)})"

    out = [title, "=" * len(title),
           f"Language: {lang}",
           f"Total duration: {_duration(total)}",
           f"Speakers: {', '.join(speakers) if speakers else '-'}",
           ""]
    for turn in turns:
        out.append(f"[{_short_clock(turn.start)} - {_short_clock(turn.end)}] "
                   f"{turn.speaker or 'Speaker 1'} ({_duration(turn.duration)})")
        out.append(turn.text)
        out.append("")
    return "\n".join(out)


FORMATS = {
    "text": ("Raw text", ".txt", to_raw_text),
    "srt": ("Subtitles (.srt)", ".srt", to_srt),
    "meeting": ("Meeting (speaker, time, text)", ".txt", to_meeting),
}


def render(t: Transcript, fmt: str) -> tuple[str, str]:
    """Return (file content, file extension) for a format key."""
    _, ext, fn = FORMATS[fmt]
    return fn(t), ext
