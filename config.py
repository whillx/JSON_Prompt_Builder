"""Application constants and default template."""

import json
import os

APP_TITLE = "JSON Prompt Builder"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(APP_DIR, "examples")
LOCALE_DIR = os.path.join(APP_DIR, "locale")
FILE_TYPES = [("JSON files", "*.json"), ("All files", "*.*")]

_DEFAULT_TEMPLATE_BASE = "empty_template"


def load_default_template(lang="en"):
    """Load the default template for the given language.

    Looks for empty_template_{LANG}.json (e.g. empty_template_FR.json)
    in the examples folder. Falls back to empty_template.json for
    English or when no localized file exists.
    """
    if lang and lang.lower() != "en":
        localized = f"{_DEFAULT_TEMPLATE_BASE}_{lang.upper()}.json"
        path = os.path.join(EXAMPLES_DIR, localized)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    # Fallback to the base English template
    path = os.path.join(EXAMPLES_DIR, f"{_DEFAULT_TEMPLATE_BASE}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_suggestions(lang="en"):
    """Load value suggestions for the given language.

    Always loads English as a base, then merges the target language on top.
    Returns a dict mapping lowercase keys to lists of suggestion strings.
    """
    result = {}
    # Always load English as the base
    en_path = os.path.join(LOCALE_DIR, "suggestion_en.json")
    try:
        with open(en_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        result = {k.lower(): v for k, v in raw.items()}
    except Exception:
        pass
    # Merge language-specific suggestions on top
    if lang != "en":
        lang_path = os.path.join(LOCALE_DIR, f"suggestion_{lang}.json")
        try:
            with open(lang_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            result.update({k.lower(): v for k, v in raw.items()})
        except Exception:
            pass
    return result
