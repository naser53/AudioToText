"""Translation through an Ollama model (local by default, free).

Settings (environment variables):
  OLLAMA_HOST     default http://localhost:11434
  OLLAMA_MODEL    default llama3.1
  OLLAMA_API_KEY  optional, only for a hosted Ollama that needs one
"""
import json
import os
import urllib.request

from .languages import language_name
from .models import Segment

BATCH_SIZE = 20


def _settings():
    return (os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/"),
            os.environ.get("OLLAMA_MODEL", "llama3.1"),
            os.environ.get("OLLAMA_API_KEY"))


def _chat(prompt: str) -> str:
    host, model, api_key = _settings()
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }).encode()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(f"{host}/api/chat", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read())["message"]["content"]


def _translate_batch(lines: list[str], source: str, target: str) -> list[str]:
    numbered = {str(i): line for i, line in enumerate(lines)}
    prompt = (
        f"Translate each value of this JSON object from {language_name(source)} "
        f"to {language_name(target)}. Keep the same keys, translate only the values, "
        f"and reply with the JSON object only.\n\n{json.dumps(numbered, ensure_ascii=False)}"
    )
    try:
        result = json.loads(_chat(prompt))
    except (json.JSONDecodeError, KeyError):
        result = {}
    # Fall back to one line at a time for anything the batch missed.
    out = []
    for i, line in enumerate(lines):
        value = result.get(str(i)) if isinstance(result, dict) else None
        if not isinstance(value, str) or not value.strip():
            single = json.loads(_chat(prompt.split("\n\n")[0] + "\n\n"
                                      + json.dumps({"0": line}, ensure_ascii=False)))
            value = single.get("0", line)
        out.append(value.strip())
    return out


def translate_segments(segments: list[Segment], source: str, target: str,
                       progress=None) -> None:
    """Translate segment texts in place, keeping their timing."""
    if not segments or source == target:
        return
    for i in range(0, len(segments), BATCH_SIZE):
        batch = segments[i:i + BATCH_SIZE]
        for seg, text in zip(batch, _translate_batch([s.text for s in batch], source, target)):
            seg.text = text
        if progress:
            progress("translating", min((i + BATCH_SIZE) / len(segments), 1.0))


def is_reachable() -> bool:
    host, _, api_key = _settings()
    req = urllib.request.Request(f"{host}/api/tags")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=3):
            return True
    except OSError:
        return False
