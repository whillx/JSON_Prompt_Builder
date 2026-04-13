"""Application constants and default template."""

import json
import os

APP_TITLE = "JSON Prompt Builder"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(APP_DIR, "examples")
LOCALE_DIR = os.path.join(APP_DIR, "locale")
FILE_TYPES = [("JSON files", "*.json"), ("All files", "*.*")]

# Maps language codes to their simple_example file names.
# Falls back to simple_example.json for unlisted languages.
_TEMPLATE_FILES = {
    "en": "simple_example.json",
    "fr": "simple_example_FR.json",
}


def load_default_template(lang="en"):
    """Load the default template for the given language."""
    filename = _TEMPLATE_FILES.get(lang, _TEMPLATE_FILES["en"])
    path = os.path.join(EXAMPLES_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_suggestions(lang="en"):
    """Load value suggestions for the given language.

    Returns a dict mapping lowercase keys to lists of suggestion strings.
    Falls back to English if the requested language file is missing.
    """
    path = os.path.join(LOCALE_DIR, f"suggestion_{lang}.json")
    if not os.path.isfile(path) and lang != "en":
        path = os.path.join(LOCALE_DIR, "suggestion_en.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {k.lower(): v for k, v in raw.items()}
    except Exception:
        return {}
