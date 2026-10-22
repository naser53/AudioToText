# AudioToText

A small Flask web app that turns an audio or video file into text, runs fully on your own computer, and is free to use.

- **Transcription:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (local Whisper)
- **Translation:** any model served by [Ollama](https://ollama.com) (local by default)
- **Speaker names (optional):** [pyannote.audio](https://github.com/pyannote/pyannote-audio)

You choose the original language (or auto-detect), the language to translate to (or none), and the output format:

| Format | File | Contents |
|---|---|---|
| Raw text | `.txt` | The spoken text, one line per segment |
| Subtitles | `.srt` | Numbered, timed subtitles (max 2 lines of 42 characters) |
| Meeting | `.meeting.txt` | Speaker, start and end time, duration and text for each turn |

## Setup (Windows)

```powershell
cd C:\Claude\PRJ\AudioToText
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Python 3.10 or newer works (tested install on 3.14). ffmpeg must be on PATH for decoding audio. The first run downloads the Whisper model (`small` is about 500 MB).

### Translation with Ollama

Install Ollama, then pull a model, for example:

```powershell
ollama pull llama3.1
```

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Where Ollama runs |
| `OLLAMA_MODEL` | `llama3.1` | Model used for translation |
| `OLLAMA_API_KEY` | (none) | Only needed for a hosted Ollama |

### Speaker detection (optional, for Meeting format)

1. Create a free account on huggingface.co and accept the terms of `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0`.
2. Create an access token, then:

```powershell
pip install pyannote.audio
$env:HF_TOKEN = "hf_..."
```

Without it, Meeting format labels everyone "Speaker 1".

## Run

```powershell
python app.py
```

Open http://127.0.0.1:5000. Other settings: `WHISPER_MODEL` (tiny, base, small, medium, large-v3), `WHISPER_DEVICE` (auto, cpu, cuda), `HOST`, `PORT`, `MAX_UPLOAD_MB`.
