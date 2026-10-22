"""Languages shown in the combo boxes: Whisper code -> display name."""
LANGUAGES = {
    "en": "English", "fa": "Persian (Farsi)", "ar": "Arabic", "de": "German",
    "fr": "French", "es": "Spanish", "it": "Italian", "pt": "Portuguese",
    "nl": "Dutch", "ru": "Russian", "tr": "Turkish", "uk": "Ukrainian",
    "pl": "Polish", "sv": "Swedish", "zh": "Chinese", "ja": "Japanese",
    "ko": "Korean", "hi": "Hindi", "ur": "Urdu", "he": "Hebrew",
}


def language_name(code: str | None) -> str:
    if not code:
        return "Unknown"
    return LANGUAGES.get(code, code)
