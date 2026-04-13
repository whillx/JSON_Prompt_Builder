"""Locale handler for multi-language UI support."""

import json
import os

from config import LOCALE_DIR

DEFAULT_LANG = "en"


class LocaleHandler:
    """Loads and serves translated strings from JSON locale files."""

    def __init__(self, lang=None):
        self._strings = {}
        self._available = self._scan_languages()
        self.set_language(lang or DEFAULT_LANG)

    def _scan_languages(self):
        """Return a dict of {code: display_name} for available locale files.

        Each locale file can declare a ``language_name`` key (e.g.
        "English", "Français") which is used as the display name in the
        Language menu.  Falls back to the file's base name if missing.
        """
        langs = {}
        if not os.path.isdir(LOCALE_DIR):
            return langs
        for fname in sorted(os.listdir(LOCALE_DIR)):
            if fname.lower().endswith(".json") and not fname.startswith("suggestion_"):
                code = os.path.splitext(fname)[0]
                # Try to read the display name from the file itself
                display = code
                try:
                    path = os.path.join(LOCALE_DIR, fname)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    display = data.get("language_name", code)
                except Exception:
                    pass
                langs[code] = display
        return langs

    @property
    def available_languages(self):
        """Return {code: display_name} for all available locale files."""
        return dict(self._available)

    @property
    def current_language(self):
        return self._lang

    def set_language(self, lang):
        """Load the given language file. Falls back to English on error."""
        path = os.path.join(LOCALE_DIR, f"{lang}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._strings = json.load(f)
            self._lang = lang
        except Exception:
            if lang != DEFAULT_LANG:
                self.set_language(DEFAULT_LANG)
            else:
                self._strings = {}
                self._lang = lang

    def t(self, key):
        """Translate a key. Returns the key itself if not found."""
        return self._strings.get(key, key)
