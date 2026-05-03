"""Application constants and default template."""

import json
import os

APP_TITLE = "JSON Prompt Builder"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(APP_DIR, "examples")
LOCALE_DIR = os.path.join(APP_DIR, "locale")
SUGGESTION_DIR = os.path.join(APP_DIR, "Suggestion")
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


def load_suggestions():
    """Load value suggestions from the Suggestion folder.

    Each .txt file in the folder is one suggestion list. The filename
    (without extension) is the field name; each non-empty line is a
    suggested value. Returns a dict mapping lowercase field names to
    lists of suggestion strings.
    """
    result = {}
    if not os.path.isdir(SUGGESTION_DIR):
        return result
    for entry in os.listdir(SUGGESTION_DIR):
        if not entry.lower().endswith(".txt"):
            continue
        key = os.path.splitext(entry)[0].lower()
        path = os.path.join(SUGGESTION_DIR, entry)
        try:
            with open(path, "r", encoding="utf-8") as f:
                values = [line.strip() for line in f if line.strip()]
        except Exception:
            continue
        if values:
            result[key] = values
    return result
