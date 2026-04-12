"""JSON file I/O operations."""

import json
from tkinter import filedialog, messagebox

from config import FILE_TYPES


class FileHandler:
    """Handles opening, saving, and tracking the current JSON file."""

    def __init__(self):
        self.current_file = None

    def new_file(self):
        self.current_file = None

    def open_file(self):
        """Open a JSON file and return parsed data, or None on cancel/error."""
        path = filedialog.askopenfilename(filetypes=FILE_TYPES)
        if not path:
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.current_file = path
            return data
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")
            return None

    def save_file(self, data):
        """Save to current file, or prompt Save As if no file set."""
        if self.current_file:
            return self._write_file(self.current_file, data)
        return self.save_file_as(data)

    def save_file_as(self, data):
        """Prompt for a file path and save."""
        path = filedialog.asksaveasfilename(
            filetypes=FILE_TYPES, defaultextension=".json"
        )
        if not path:
            return False
        self.current_file = path
        return self._write_file(path, data)

    def _write_file(self, path, data):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent="\t", ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")
            return False
