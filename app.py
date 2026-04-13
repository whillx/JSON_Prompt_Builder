"""Main application window with menus and toolbar."""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

from config import APP_TITLE, EXAMPLES_DIR, load_default_template, load_suggestions
from file_handler import FileHandler
from json_tree import JsonTreeView
from locale_handler import LocaleHandler
from tooltip import Tooltip
from user_settings import load_settings, save_settings


class App:
    """Top-level application: window, menus, toolbar, and tree view."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("800x600")
        self.root.minsize(500, 350)

        self.file_handler = FileHandler()
        saved_lang = load_settings().get("language", "en")
        self.locale = LocaleHandler(saved_lang)

        self._toolbar_frame = None
        self._tooltips = []

        self._setup_menu()
        self._setup_toolbar()
        self._setup_tree()
        self._setup_shortcuts()

        self.json_tree.load_json(
            load_default_template(self.locale.current_language)
        )
        self._update_title()

    # ── Menu bar ──────────────────────────────────────────────────

    def _setup_menu(self):
        self._menubar = tk.Menu(self.root)
        self._build_menus()
        self.root.config(menu=self._menubar)

    def _build_menus(self):
        t = self.locale.t
        self._menubar.delete(0, "end")

        # ── File menu ──
        file_menu = tk.Menu(self._menubar, tearoff=0)
        file_menu.add_command(
            label=t("file_new"), command=self._new_file, accelerator="Ctrl+N"
        )
        file_menu.add_command(
            label=t("file_open"), command=self._open_file, accelerator="Ctrl+O"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label=t("file_save"), command=self._save_file, accelerator="Ctrl+S"
        )
        file_menu.add_command(
            label=t("file_save_as"),
            command=self._save_file_as,
            accelerator="Ctrl+Shift+S",
        )
        file_menu.add_separator()

        self._examples_menu = tk.Menu(
            file_menu, tearoff=0, postcommand=self._refresh_examples
        )
        file_menu.add_cascade(
            label=t("file_load_example"), menu=self._examples_menu
        )

        file_menu.add_separator()
        file_menu.add_command(label=t("file_exit"), command=self._on_exit)
        self._menubar.add_cascade(label=t("menu_file"), menu=file_menu)

        # ── Edit menu ──
        edit_menu = tk.Menu(self._menubar, tearoff=0)
        edit_menu.add_command(
            label=t("edit_add_sibling"),
            command=lambda: self.json_tree.add_sibling(),
            accelerator="Insert",
        )
        edit_menu.add_command(
            label=t("edit_remove"),
            command=lambda: self.json_tree.remove_item(),
            accelerator="Delete",
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label=t("edit_add_child"),
            command=lambda: self.json_tree.add_child(),
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label=t("edit_clear_all"), command=self._clear_all
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label=t("edit_expand_all"), command=self._expand_all
        )
        edit_menu.add_command(
            label=t("edit_collapse_all"), command=self._collapse_all
        )
        self._menubar.add_cascade(label=t("menu_edit"), menu=edit_menu)

        # ── Language menu ──
        lang_menu = tk.Menu(self._menubar, tearoff=0)
        for code, name in self.locale.available_languages.items():
            lang_menu.add_radiobutton(
                label=name,
                value=code,
                variable=self._get_lang_var(),
                command=lambda c=code: self._switch_language(c),
            )
        self._menubar.add_cascade(label=t("menu_language"), menu=lang_menu)

    def _get_lang_var(self):
        if not hasattr(self, "_lang_var"):
            self._lang_var = tk.StringVar(value=self.locale.current_language)
        return self._lang_var

    # ── Toolbar ───────────────────────────────────────────────────

    def _setup_toolbar(self):
        self._toolbar_frame = ttk.Frame(self.root)
        self._toolbar_frame.pack(fill="x", padx=4, pady=2)
        self._build_toolbar()

    def _build_toolbar(self):
        t = self.locale.t
        self._tooltips.clear()
        self._add_child_label = None
        self._add_child_btn = None

        for widget in self._toolbar_frame.winfo_children():
            widget.destroy()

        # ── Add Sibling group ──
        ttk.Label(
            self._toolbar_frame, text=t("toolbar_add_sibling_label")
        ).pack(side="left", padx=(4, 2))

        btn = ttk.Button(
            self._toolbar_frame, text=t("toolbar_add_string"), width=9,
            command=lambda: self.json_tree.add_sibling("str"),
        )
        btn.pack(side="left", padx=2)
        self._tooltips.append(Tooltip(btn, t("tooltip_add_string")))

        btn = ttk.Button(
            self._toolbar_frame, text=t("toolbar_add_object"), width=9,
            command=lambda: self.json_tree.add_sibling("dict"),
        )
        btn.pack(side="left", padx=2)
        self._tooltips.append(Tooltip(btn, t("tooltip_add_object")))

        btn = ttk.Button(
            self._toolbar_frame, text=t("toolbar_add_array"), width=9,
            command=lambda: self.json_tree.add_sibling("list"),
        )
        btn.pack(side="left", padx=2)
        self._tooltips.append(Tooltip(btn, t("tooltip_add_array")))

        ttk.Separator(self._toolbar_frame, orient="vertical").pack(
            side="left", fill="y", padx=6, pady=2
        )

        # ── Add Child ──
        self._add_child_label = ttk.Label(
            self._toolbar_frame, text=t("toolbar_add_child_label")
        )
        self._add_child_label.pack(side="left", padx=(4, 2))
        self._add_child_btn = ttk.Button(
            self._toolbar_frame, text=t("toolbar_add_child"), width=9,
            command=lambda: self.json_tree.add_child(),
        )
        self._add_child_btn.pack(side="left", padx=2)
        self._tooltips.append(Tooltip(self._add_child_btn, t("tooltip_add_child")))

        ttk.Separator(self._toolbar_frame, orient="vertical").pack(
            side="left", fill="y", padx=6, pady=2
        )

        # ── Remove ──
        btn = ttk.Button(
            self._toolbar_frame, text=t("toolbar_remove"), width=9,
            command=lambda: self.json_tree.remove_item(),
        )
        btn.pack(side="left", padx=2)
        self._tooltips.append(Tooltip(btn, t("tooltip_remove")))

        # Sync initial state
        self._on_tree_selection_changed()

    # ── Tree view ─────────────────────────────────────────────────

    def _setup_tree(self):
        self.json_tree = JsonTreeView(
            self.root, self.locale,
            suggestions=load_suggestions(self.locale.current_language),
        )
        self.json_tree.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.json_tree.tree.bind("<<TreeviewSelect>>", self._on_tree_selection_changed)

    def _on_tree_selection_changed(self, event=None):
        """Grey out Add Child when the selected item cannot have children."""
        selected = self.json_tree.tree.selection()
        if selected:
            tags = self.json_tree.tree.item(selected[0], "tags")
            can_have_children = "dict" in tags or "list" in tags
        else:
            can_have_children = False
        state = "normal" if can_have_children else "disabled"
        if hasattr(self, "_add_child_btn"):
            self._add_child_btn.configure(state=state)
            self._add_child_label.configure(
                foreground="" if can_have_children else "gray"
            )

    # ── Keyboard shortcuts ────────────────────────────────────────

    def _setup_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self._new_file())
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self._save_file_as())

    # ── Language switching ────────────────────────────────────────

    def _switch_language(self, lang_code):
        self.locale.set_language(lang_code)
        self._get_lang_var().set(lang_code)
        save_settings(language=lang_code)

        # Rebuild all UI text
        self._build_menus()
        self._build_toolbar()
        self.json_tree.update_locale(self.locale)
        self.json_tree.update_suggestions(load_suggestions(lang_code))
        self._update_title()

        # Reload the default template in the new language
        # (only if currently showing an untitled/new file)
        if not self.file_handler.current_file:
            self.json_tree.load_json(
                load_default_template(self.locale.current_language)
            )

    # ── File operations ───────────────────────────────────────────

    def _new_file(self):
        self.file_handler.new_file()
        self.json_tree.load_json(
            load_default_template(self.locale.current_language)
        )
        self._update_title()

    def _open_file(self):
        data = self.file_handler.open_file()
        if data is not None:
            self.json_tree.load_json(data)
            self._update_title()

    def _save_file(self):
        data = self.json_tree.to_json()
        if self.file_handler.save_file(data):
            self._update_title()

    def _save_file_as(self):
        data = self.json_tree.to_json()
        if self.file_handler.save_file_as(data):
            self._update_title()

    # ── Clear all ─────────────────────────────────────────────────

    def _clear_all(self):
        t = self.locale.t
        if messagebox.askyesno(
            t("confirm_clear_all_title"), t("confirm_clear_all_msg")
        ):
            self.json_tree.clear()

    # ── Examples ──────────────────────────────────────────────────

    def _refresh_examples(self):
        """Rescan the examples folder and rebuild the submenu."""
        t = self.locale.t
        self._examples_menu.delete(0, "end")

        if not os.path.isdir(EXAMPLES_DIR):
            self._examples_menu.add_command(
                label=t("examples_no_folder"), state="disabled"
            )
            return

        files = sorted(
            f for f in os.listdir(EXAMPLES_DIR)
            if f.lower().endswith(".json")
        )

        if not files:
            self._examples_menu.add_command(
                label=t("examples_none_found"), state="disabled"
            )
            return

        for filename in files:
            display = os.path.splitext(filename)[0].replace("_", " ").title()
            path = os.path.join(EXAMPLES_DIR, filename)
            self._examples_menu.add_command(
                label=display,
                command=lambda p=path: self._load_example(p),
            )

    def _load_example(self, path):
        """Load an example JSON file into the tree."""
        t = self.locale.t
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror(
                t("error_title"), f"{t('error_load_example')}\n{e}"
            )
            return

        self.file_handler.new_file()
        self.json_tree.load_json(data)
        self._update_title()

    # ── Tree helpers ──────────────────────────────────────────────

    def _expand_all(self):
        for item in self._all_items():
            self.json_tree.tree.item(item, open=True)

    def _collapse_all(self):
        for item in self._all_items():
            self.json_tree.tree.item(item, open=False)

    def _all_items(self):
        """Yield all tree item IDs recursively."""
        stack = list(self.json_tree.tree.get_children(""))
        while stack:
            item = stack.pop()
            yield item
            stack.extend(self.json_tree.tree.get_children(item))

    # ── Window ────────────────────────────────────────────────────

    def _update_title(self):
        t = self.locale.t
        path = self.file_handler.current_file
        suffix = path if path else t("title_untitled")
        self.root.title(f"{APP_TITLE} - {suffix}")

    def _on_exit(self):
        self.root.quit()

    def run(self):
        self.root.mainloop()
