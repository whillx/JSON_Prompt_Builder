# JSON Prompt Builder

A small Tkinter desktop app for creating and editing JSON-style prompts for AI image and video generation. The prompt is shown as an editable tree. It runs on Windows, macOS and Linux.

## Running

The project uses [uv](https://docs.astral.sh/uv/) so it doesn't depend on the system Python:

```
uv run main.py
```

uv reads `.python-version`, downloads that Python if needed (uv-managed Python includes Tkinter on every OS), creates `.venv/`, and runs the app. The launchers `JSON_Prompt_Builder.bat` (Windows) and `JSON_Prompt_Builder.command` (macOS/Linux) do the same thing and fall back to the system `python` / `python3` if uv isn't installed.

There is no test suite. To check that a change works, launch the app and try the feature. For a quick import check:

```
uv run python -c "from app import App; print('imports OK')"
```

## Constraints

- **Standard library only.** The app must run on a plain Python install with Tkinter. Don't add third-party dependencies without asking. If one is ever needed, add it with `uv add <package>` so `pyproject.toml` and `uv.lock` stay in sync.
- **Cross-platform.** Build paths with `os.path.join` from the constants in `config.py`, never with hard-coded separators or absolute paths. Data folders are resolved relative to `APP_DIR`, so the app works from any current directory.
- **LF line endings.** `.gitattributes` stores text files as LF (`.bat` files as CRLF). Don't commit CRLF files.
- **Folder and file names are case-sensitive** on Linux and macOS, even though Windows ignores case. Use lowercase names for data folders and suggestion files.
- **Python version.** `requires-python` in `pyproject.toml` is the minimum. `.python-version` pins the version used for development.

## Code layout

| File | Role |
|---|---|
| `main.py` | Entry point. Creates `App` and runs it. |
| `app.py` | Main window: menus, toolbar, shortcuts, file actions, clipboard export, examples menu, language switching. |
| `json_tree.py` | `JsonTreeView`: the tree widget, with inline editing, detail panel, drag-and-drop, copy/paste, type conversion and the suggestion dropdown. |
| `file_handler.py` | Opening and saving JSON files. |
| `config.py` | App constants, data folder paths, `load_default_template()`, `load_suggestions()`. |
| `locale_handler.py` | `LocaleHandler`: loads `locale/<code>.json` and translates keys with `t(key)`. |
| `user_settings.py` | Reads and writes preferences (currently just the language) in `user.ini`, which is git-ignored. |
| `tooltip.py` | Hover tooltip widget. |

Data folders, all read at runtime:

- `examples/`: every `.json` file here appears under **File > Load Example**. File names are shown with underscores replaced by spaces, in title case.
- `locale/`: one JSON file of UI strings per language.
- `suggestion/`: value suggestion lists, one `.txt` file per field.

## Conventions

- **UI text goes through the locale.** Never hard-code user-visible strings. Add the key to every file in `locale/` (`en.json` and `fr.json`) and use `self.locale.t("key")`.
- **Adding a language.** Copy `locale/en.json` to `locale/<code>.json` and translate every value, including `"language_name"` (the name shown in the Language menu). The language is picked up automatically. Optionally add `examples/empty_template_<CODE>.json` (uppercase code) as its default template.
- **Default template.** `load_default_template(lang)` loads `examples/empty_template_<LANG>.json` and falls back to `examples/empty_template.json`. That file is the source of truth for the starting structure; don't duplicate it in code or docs.
- **Suggestions.** The suggestion file name (without `.txt`) is compared, ignoring case, with the key of the value being edited. For values inside an array, the array's key is used. Suggestions are re-read on each edit, so new files work without restarting. They don't depend on the UI language. Keys in the templates use snake_case (`time_of_day`), and so do the suggestion files (`time_of_day.txt`).

## Product behaviour

These are the intended features. Keep them working when changing the code.

- The JSON prompt is shown as a tree. The schema is fully dynamic: users can build any structure from scratch, and the default template is only a starting point they can edit or delete.
- Add sibling or child fields (string, object, array) and remove fields, from the toolbar, the right-click menu or the keyboard (`Insert`, `Delete`).
- Double-click a key or value to edit it in place. A resizable detail panel shows long values with word wrap.
- One field can hold several comma-separated values (e.g. `"style": "Photorealistic, Cinematic"`).
- Convert a field between String, Number, Boolean, Null, Object and Array from the right-click menu.
- Drag and drop to reorder items among their siblings. A blue line shows where the item will land.
- Right-click to copy any item (string, object or array), then paste it on another entry. The pasted item is inserted as a sibling; it never overwrites the selected entry.
- A filterable suggestion dropdown appears when editing a value whose key matches a suggestion file. Typing filters the list.
- New, open, save and save as JSON files (`Ctrl+N`, `Ctrl+O`, `Ctrl+S`, `Ctrl+Shift+S`).
- Copy the prompt to the clipboard as JSON, as condensed JSON (empty values and empty containers removed), or as flat text (`key: val, val; key: val;`).
- Load example templates from **File > Load Example**.
- Expand all, collapse all, and clear all from the Edit menu.
- English and French UI. The chosen language is saved to `user.ini` and restored on the next launch.
