"""Read and write user preferences from user.ini."""

import configparser
import os

from config import APP_DIR

_INI_PATH = os.path.join(APP_DIR, "user.ini")
_SECTION = "preferences"


def load_settings():
    """Return a dict of saved user preferences."""
    config = configparser.ConfigParser()
    config.read(_INI_PATH, encoding="utf-8")
    if config.has_section(_SECTION):
        return dict(config[_SECTION])
    return {}


def save_settings(**kwargs):
    """Merge the given key-value pairs into user.ini and write to disk."""
    config = configparser.ConfigParser()
    config.read(_INI_PATH, encoding="utf-8")
    if not config.has_section(_SECTION):
        config.add_section(_SECTION)
    for key, value in kwargs.items():
        config[_SECTION][key] = str(value)
    with open(_INI_PATH, "w", encoding="utf-8") as f:
        config.write(f)
