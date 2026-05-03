"""Tree widget for viewing and editing JSON data."""

import tkinter as tk
from tkinter import ttk


class JsonTreeView(ttk.Frame):
    """Displays JSON as an editable tree with inline editing and context menus."""

    def __init__(self, parent, locale=None, suggestions=None):
        super().__init__(parent)
        self._locale = locale
        self._suggestions = suggestions or {}
        self._edit_entry = None
        self._edit_item = None
        self._edit_column = None
        self._suggestion_listbox = None
        self._root_is_list = False
        self._detail_updating = False
        self._clipboard = None
        self._drag_item = None
        self._drag_start_y = 0
        self._drag_threshold = 5
        self._dragging = False
        self._drop_indicator = None
        self._setup_widgets()
        self._setup_tags()
        self._setup_bindings()

    # ── Widget setup ──────────────────────────────────────────────

    def _setup_widgets(self):
        # Main paned window: tree on top, detail panel on bottom
        self._paned = ttk.PanedWindow(self, orient="vertical")
        self._paned.pack(fill="both", expand=True)

        # ── Tree pane ──
        tree_frame = ttk.Frame(self._paned)
        self.tree = ttk.Treeview(
            tree_frame, columns=("value",), selectmode="browse"
        )
        self.tree.heading("#0", text=self._t("tree_heading_key"), anchor="w")
        self.tree.heading("value", text=self._t("tree_heading_value"), anchor="w")
        self.tree.column("#0", width=250, minwidth=100)
        self.tree.column("value", width=400, minwidth=100)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self._paned.add(tree_frame, weight=3)

        # ── Detail pane ──
        detail_frame = ttk.Frame(self._paned)

        # Key row
        key_row = ttk.Frame(detail_frame)
        key_row.pack(fill="x", padx=4, pady=(4, 2))
        self._detail_key_label = ttk.Label(
            key_row, text=self._t("tree_heading_key") + ":",
            width=6, anchor="w",
        )
        self._detail_key_label.pack(side="left")
        self._detail_key_var = tk.StringVar()
        self._detail_key_entry = ttk.Entry(
            key_row, textvariable=self._detail_key_var
        )
        self._detail_key_entry.pack(side="left", fill="x", expand=True)

        # Value row (Text widget for multi-line display and editing)
        val_row = ttk.Frame(detail_frame)
        val_row.pack(fill="both", expand=True, padx=4, pady=(2, 4))
        self._detail_val_label = ttk.Label(
            val_row, text=self._t("tree_heading_value") + ":",
            width=6, anchor="nw",
        )
        self._detail_val_label.pack(side="left", anchor="n")
        self._detail_value = tk.Text(
            val_row, wrap="word", height=3,
            font=("TkDefaultFont",), relief="sunken", borderwidth=1,
        )
        self._detail_value.pack(side="left", fill="both", expand=True)
        detail_vsb = ttk.Scrollbar(
            val_row, orient="vertical", command=self._detail_value.yview
        )
        detail_vsb.pack(side="right", fill="y")
        self._detail_value.configure(yscrollcommand=detail_vsb.set)

        self._paned.add(detail_frame, weight=1)

    def _setup_tags(self):
        self.tree.tag_configure("dict", foreground="#0066cc")
        self.tree.tag_configure("list", foreground="#cc6600")
        self.tree.tag_configure("str", foreground="#006600")
        self.tree.tag_configure("num", foreground="#990099")
        self.tree.tag_configure("bool", foreground="#cc0000")
        self.tree.tag_configure("null", foreground="#999999")

    def _setup_bindings(self):
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Delete>", lambda e: self.remove_item())
        self.tree.bind("<Insert>", lambda e: self.add_sibling())
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Drag-and-drop reordering
        self.tree.bind("<ButtonPress-1>", self._on_drag_start)
        self.tree.bind("<B1-Motion>", self._on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._on_drag_end)

        # Apply detail panel edits back to the tree
        self._detail_key_var.trace_add("write", self._on_detail_key_changed)
        self._detail_value.bind("<KeyRelease>", self._on_detail_value_changed)

    def _t(self, key):
        """Translate a key, or return the key itself if no locale is set."""
        if self._locale:
            return self._locale.t(key)
        return key

    def update_locale(self, locale):
        """Update the locale and refresh translatable UI text."""
        self._locale = locale
        self.tree.heading("#0", text=self._t("tree_heading_key"))
        self.tree.heading("value", text=self._t("tree_heading_value"))
        self._detail_key_label.configure(
            text=self._t("tree_heading_key") + ":"
        )
        self._detail_val_label.configure(
            text=self._t("tree_heading_value") + ":"
        )

    # ── Detail panel ──────────────────────────────────────────────

    def _on_tree_select(self, event=None):
        """Populate the detail panel with the selected item's data."""
        self._detail_updating = True
        selected = self.tree.selection()
        if not selected:
            self._detail_key_var.set("")
            self._detail_value.delete("1.0", "end")
            self._detail_key_entry.configure(state="disabled")
            self._detail_value.configure(state="disabled")
            self._detail_updating = False
            return

        item = selected[0]
        key = self.tree.item(item, "text")
        value = self.tree.item(item, "values")[0]
        tags = self.tree.item(item, "tags")

        # Key: disable editing for list indices
        parent = self.tree.parent(item)
        parent_tags = self.tree.item(parent, "tags") if parent else ()
        is_list_child = "list" in parent_tags

        self._detail_key_entry.configure(state="normal")
        self._detail_key_var.set(key)
        if is_list_child:
            self._detail_key_entry.configure(state="disabled")

        # Value: disable editing for containers
        is_container = "dict" in tags or "list" in tags
        self._detail_value.configure(state="normal")
        self._detail_value.delete("1.0", "end")
        self._detail_value.insert("1.0", value)
        if is_container:
            self._detail_value.configure(state="disabled")

        self._detail_updating = False

    def _on_detail_key_changed(self, *args):
        """Sync key edits from the detail panel back to the tree."""
        if self._detail_updating:
            return
        selected = self.tree.selection()
        if not selected:
            return
        new_key = self._detail_key_var.get()
        self.tree.item(selected[0], text=new_key)

    def _on_detail_value_changed(self, event=None):
        """Sync value edits from the detail panel back to the tree."""
        if self._detail_updating:
            return
        selected = self.tree.selection()
        if not selected:
            return
        new_value = self._detail_value.get("1.0", "end-1c")
        self.tree.item(selected[0], values=(new_value,))

    # ── Loading JSON into the tree ────────────────────────────────

    def load_json(self, data):
        """Replace tree contents with the given JSON data."""
        self.clear()
        self._root_is_list = isinstance(data, list)
        if isinstance(data, dict):
            self._insert_dict_items("", data)
        elif isinstance(data, list):
            self._insert_list_items("", data)

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def _insert_dict_items(self, parent, data):
        for key, value in data.items():
            self._insert_item(parent, str(key), value)

    def _insert_list_items(self, parent, data):
        for i, value in enumerate(data):
            self._insert_item(parent, f"[{i}]", value)

    def _insert_item(self, parent, key, value):
        if isinstance(value, dict):
            node = self.tree.insert(
                parent, "end", text=key,
                values=("{...}",), tags=("dict",), open=True,
            )
            self._insert_dict_items(node, value)
        elif isinstance(value, list):
            node = self.tree.insert(
                parent, "end", text=key,
                values=(f"[{len(value)} items]",), tags=("list",), open=True,
            )
            self._insert_list_items(node, value)
        elif isinstance(value, bool):
            self.tree.insert(
                parent, "end", text=key,
                values=(str(value).lower(),), tags=("bool",),
            )
        elif isinstance(value, (int, float)):
            self.tree.insert(
                parent, "end", text=key,
                values=(str(value),), tags=("num",),
            )
        elif value is None:
            self.tree.insert(
                parent, "end", text=key,
                values=("null",), tags=("null",),
            )
        else:
            self.tree.insert(
                parent, "end", text=key,
                values=(str(value),), tags=("str",),
            )

    # ── Extracting JSON from the tree ─────────────────────────────

    def to_json(self):
        """Convert the current tree back to a Python object."""
        root_children = self.tree.get_children("")
        if self._root_is_list:
            return self._children_to_list(root_children)
        return self._children_to_dict(root_children)

    def _children_to_dict(self, children):
        result = {}
        for child in children:
            key = self.tree.item(child, "text")
            result[key] = self._item_to_value(child)
        return result

    def _children_to_list(self, children):
        return [self._item_to_value(child) for child in children]

    def _item_to_value(self, item):
        tags = self.tree.item(item, "tags")
        if "dict" in tags:
            return self._children_to_dict(self.tree.get_children(item))
        if "list" in tags:
            return self._children_to_list(self.tree.get_children(item))
        return self._parse_leaf_value(item)

    def _parse_leaf_value(self, item):
        tags = self.tree.item(item, "tags")
        val = self.tree.item(item, "values")[0]
        if "bool" in tags:
            return val.lower() == "true"
        if "num" in tags:
            try:
                return int(val)
            except ValueError:
                try:
                    return float(val)
                except ValueError:
                    return val
        if "null" in tags:
            return None
        return val

    # ── Tree editing operations ───────────────────────────────────

    def add_sibling(self, value_type="str"):
        """Add a sibling node after the selected item."""
        selected = self.tree.selection()
        if not selected:
            self._add_new_item("", "end", value_type)
            return

        item = selected[0]
        parent = self.tree.parent(item)
        index = self.tree.index(item) + 1
        self._add_new_item(parent, index, value_type)

        if parent:
            parent_tags = self.tree.item(parent, "tags")
            if "list" in parent_tags:
                self._reindex_list(parent)
                self._update_list_count(parent)

    def remove_item(self):
        """Remove the selected item."""
        selected = self.tree.selection()
        if not selected:
            return

        item = selected[0]
        parent = self.tree.parent(item)
        next_item = self.tree.next(item)
        prev_item = self.tree.prev(item)

        self.tree.delete(item)

        if parent:
            parent_tags = self.tree.item(parent, "tags")
            if "list" in parent_tags:
                self._reindex_list(parent)
                self._update_list_count(parent)

        if next_item and self.tree.exists(next_item):
            self.tree.selection_set(next_item)
        elif prev_item and self.tree.exists(prev_item):
            self.tree.selection_set(prev_item)
        elif parent:
            self.tree.selection_set(parent)

    def add_child(self, value_type="str"):
        """Add a child node to the selected container (dict or list)."""
        selected = self.tree.selection()
        if not selected:
            return

        item = selected[0]
        tags = self.tree.item(item, "tags")
        if "dict" not in tags and "list" not in tags:
            return

        if "list" in tags:
            children = self.tree.get_children(item)
            key = f"[{len(children)}]"
        else:
            key = "new_key"

        if value_type == "dict":
            new_item = self.tree.insert(
                item, "end", text=key,
                values=("{...}",), tags=("dict",), open=True,
            )
        elif value_type == "list":
            new_item = self.tree.insert(
                item, "end", text=key,
                values=("[0 items]",), tags=("list",), open=True,
            )
        else:
            new_item = self.tree.insert(
                item, "end", text=key,
                values=("value",), tags=("str",),
            )

        if "list" in tags:
            self._update_list_count(item)

        self.tree.item(item, open=True)
        self.tree.selection_set(new_item)
        self.tree.see(new_item)

    def convert_type(self, new_type):
        """Convert the selected item to a different value type."""
        selected = self.tree.selection()
        if not selected:
            return

        item = selected[0]
        tags = self.tree.item(item, "tags")
        current_type = tags[0] if tags else "str"
        if current_type == new_type:
            return

        # Remove children when converting away from a container
        if current_type in ("dict", "list"):
            for child in self.tree.get_children(item):
                self.tree.delete(child)

        defaults = {
            "dict": ("{...}", "dict"),
            "list": ("[0 items]", "list"),
            "str": ("value", "str"),
            "num": ("0", "num"),
            "bool": ("true", "bool"),
            "null": ("null", "null"),
        }
        display, tag = defaults[new_type]
        self.tree.item(item, values=(display,), tags=(tag,))

    # ── Helpers ───────────────────────────────────────────────────

    def _add_new_item(self, parent, index, value_type):
        parent_tags = self.tree.item(parent, "tags") if parent else ()
        key = "[0]" if "list" in parent_tags else "new_key"

        if value_type == "dict":
            new_item = self.tree.insert(
                parent, index, text=key,
                values=("{...}",), tags=("dict",), open=True,
            )
        elif value_type == "list":
            new_item = self.tree.insert(
                parent, index, text=key,
                values=("[0 items]",), tags=("list",), open=True,
            )
        else:
            new_item = self.tree.insert(
                parent, index, text=key,
                values=("value",), tags=("str",),
            )

        self.tree.selection_set(new_item)
        self.tree.see(new_item)
        return new_item

    def _reindex_list(self, parent):
        for i, child in enumerate(self.tree.get_children(parent)):
            self.tree.item(child, text=f"[{i}]")

    def _update_list_count(self, parent):
        count = len(self.tree.get_children(parent))
        self.tree.item(parent, values=(f"[{count} items]",))

    # ── Copy and paste ───────────────────────────────────────────

    def copy_item(self):
        """Copy the selected item (and its children) to the clipboard."""
        selected = self.tree.selection()
        if not selected:
            return
        item = selected[0]
        key = self.tree.item(item, "text")
        value = self._item_to_value(item)
        tags = list(self.tree.item(item, "tags"))
        self._clipboard = {"key": key, "value": value, "tag": tags[0] if tags else "str"}

    def paste_item(self):
        """Paste the clipboard item as a sibling after the selected item."""
        if not self._clipboard:
            return
        selected = self.tree.selection()
        if not selected:
            # Paste at root level
            parent = ""
            index = "end"
        else:
            item = selected[0]
            parent = self.tree.parent(item)
            index = self.tree.index(item) + 1

        key = self._clipboard["key"]
        value = self._clipboard["value"]

        # If pasting into a list parent, key will be reindexed automatically
        parent_tags = self.tree.item(parent, "tags") if parent else ()
        is_list_parent = "list" in parent_tags
        if not parent and self._root_is_list:
            is_list_parent = True

        if is_list_parent:
            key = "[0]"  # Placeholder, will be reindexed

        new_item = self._insert_item_at(parent, index, key, value)

        if is_list_parent:
            self._reindex_list(parent)
            if parent:
                self._update_list_count(parent)

        self.tree.selection_set(new_item)
        self.tree.see(new_item)

    def _insert_item_at(self, parent, index, key, value):
        """Insert a value (possibly nested) at a specific position and return the item id."""
        if isinstance(value, dict):
            node = self.tree.insert(
                parent, index, text=key,
                values=("{...}",), tags=("dict",), open=True,
            )
            for k, v in value.items():
                self._insert_item_at(node, "end", str(k), v)
            return node
        elif isinstance(value, list):
            node = self.tree.insert(
                parent, index, text=key,
                values=(f"[{len(value)} items]",), tags=("list",), open=True,
            )
            for i, v in enumerate(value):
                self._insert_item_at(node, "end", f"[{i}]", v)
            return node
        elif isinstance(value, bool):
            return self.tree.insert(
                parent, index, text=key,
                values=(str(value).lower(),), tags=("bool",),
            )
        elif isinstance(value, (int, float)):
            return self.tree.insert(
                parent, index, text=key,
                values=(str(value),), tags=("num",),
            )
        elif value is None:
            return self.tree.insert(
                parent, index, text=key,
                values=("null",), tags=("null",),
            )
        else:
            return self.tree.insert(
                parent, index, text=key,
                values=(str(value),), tags=("str",),
            )

    # ── Inline editing ────────────────────────────────────────────

    def _on_double_click(self, event):
        if self._edit_entry:
            self._finish_edit()

        region = self.tree.identify("region", event.x, event.y)
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not item:
            return

        tags = self.tree.item(item, "tags")

        if region == "tree" or column == "#0":
            # Don't edit keys of list items (they're auto-indexed)
            parent = self.tree.parent(item)
            if parent:
                parent_tags = self.tree.item(parent, "tags")
                if "list" in parent_tags:
                    return
            self._start_edit(item, "#0")
        elif region == "cell" and column == "#1":
            # Only edit values on leaf nodes
            if "dict" in tags or "list" in tags:
                return
            self._start_edit(item, "value")

    def _get_suggestions_for_item(self, item):
        """Return suggestion list if the item's key matches a suggestion key."""
        key = self.tree.item(item, "text").lower()
        return self._suggestions.get(key, [])

    def _start_edit(self, item, column):
        bbox = self.tree.bbox(item, column)
        if not bbox:
            self.tree.see(item)
            self.tree.update_idletasks()
            bbox = self.tree.bbox(item, column)
            if not bbox:
                return

        if column == "#0":
            current = self.tree.item(item, "text")
        else:
            current = self.tree.item(item, "values")[0]

        entry = tk.Entry(self.tree)
        entry.place(x=bbox[0], y=bbox[1], width=max(bbox[2], 150), height=bbox[3])
        entry.insert(0, current)
        entry.select_range(0, "end")
        entry.focus_set()

        self._edit_entry = entry
        self._edit_item = item
        self._edit_column = column

        entry.bind("<Return>", lambda e: self._finish_edit())
        entry.bind("<Escape>", lambda e: self._cancel_edit())
        entry.bind("<FocusOut>", lambda e: self._on_edit_focus_out())

        # Show suggestion dropdown for value columns with matching keys
        if column == "value":
            suggestions = self._get_suggestions_for_item(item)
            if suggestions:
                self._show_suggestions(entry, bbox, suggestions)

    def _show_suggestions(self, entry, bbox, suggestions):
        """Show a dropdown listbox with suggestions below the edit entry."""
        self._dismiss_suggestions()

        listbox = tk.Listbox(
            self.tree, relief="solid", borderwidth=1,
            selectmode="browse", exportselection=False,
        )
        for s in suggestions:
            listbox.insert("end", s)

        # Position below the entry
        max_visible = min(len(suggestions), 8)
        row_height = 18
        lb_height = max_visible * row_height + 4
        lb_width = max(bbox[2], 150)
        listbox.place(x=bbox[0], y=bbox[1] + bbox[3], width=lb_width, height=lb_height)
        listbox.lift()

        self._suggestion_listbox = listbox
        self._suggestion_all = suggestions

        # Typing in the entry filters the list
        entry.bind("<KeyRelease>", self._on_suggestion_filter)
        listbox.bind("<ButtonRelease-1>", lambda e: self._pick_suggestion())
        listbox.bind("<Return>", lambda e: self._pick_suggestion())

    def _on_suggestion_filter(self, event):
        """Filter the suggestion listbox based on current entry text."""
        if not self._suggestion_listbox or not self._edit_entry:
            return
        # Ignore navigation keys
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        query = self._edit_entry.get().lower()
        self._suggestion_listbox.delete(0, "end")
        for s in self._suggestion_all:
            if query in s.lower():
                self._suggestion_listbox.insert("end", s)

    def _pick_suggestion(self):
        """Insert the selected suggestion into the edit entry."""
        if not self._suggestion_listbox or not self._edit_entry:
            return
        sel = self._suggestion_listbox.curselection()
        if not sel:
            return
        value = self._suggestion_listbox.get(sel[0])
        self._edit_entry.delete(0, "end")
        self._edit_entry.insert(0, value)
        self._dismiss_suggestions()
        self._finish_edit()

    def _dismiss_suggestions(self):
        """Remove the suggestion dropdown if it exists."""
        if self._suggestion_listbox:
            self._suggestion_listbox.destroy()
            self._suggestion_listbox = None
            self._suggestion_all = []

    def _on_edit_focus_out(self):
        """Handle focus leaving the edit entry."""
        # Check if focus went to the suggestion listbox — if so, don't finish
        focused = self.tree.focus_get()
        if focused is self._suggestion_listbox:
            return
        self._finish_edit()

    def _finish_edit(self):
        if not self._edit_entry:
            return

        new_value = self._edit_entry.get()
        entry = self._edit_entry
        item = self._edit_item
        column = self._edit_column

        self._edit_entry = None
        self._edit_item = None
        self._edit_column = None

        self._dismiss_suggestions()

        if column == "#0":
            self.tree.item(item, text=new_value)
        else:
            self.tree.item(item, values=(new_value,))

        entry.destroy()
        self._on_tree_select()

    def _cancel_edit(self):
        if not self._edit_entry:
            return
        self._dismiss_suggestions()
        entry = self._edit_entry
        self._edit_entry = None
        self._edit_item = None
        self._edit_column = None
        entry.destroy()

    # ── Context menu ──────────────────────────────────────────────

    def _on_right_click(self, event):
        t = self._t
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)

        menu = tk.Menu(self, tearoff=0)
        tags = self.tree.item(item, "tags") if item else ()

        # Add Sibling submenu
        add_menu = tk.Menu(menu, tearoff=0)
        add_menu.add_command(
            label=t("type_string"), command=lambda: self.add_sibling("str")
        )
        add_menu.add_command(
            label=t("type_object"), command=lambda: self.add_sibling("dict")
        )
        add_menu.add_command(
            label=t("type_array"), command=lambda: self.add_sibling("list")
        )
        menu.add_cascade(label=t("ctx_add_sibling"), menu=add_menu)

        # Add Child submenu (only for containers)
        if item and ("dict" in tags or "list" in tags):
            child_menu = tk.Menu(menu, tearoff=0)
            child_menu.add_command(
                label=t("type_string"), command=lambda: self.add_child("str")
            )
            child_menu.add_command(
                label=t("type_object"), command=lambda: self.add_child("dict")
            )
            child_menu.add_command(
                label=t("type_array"), command=lambda: self.add_child("list")
            )
            menu.add_cascade(label=t("ctx_add_child"), menu=child_menu)

        if item:
            menu.add_separator()

            # Convert To submenu
            type_menu = tk.Menu(menu, tearoff=0)
            type_menu.add_command(
                label=t("type_string"), command=lambda: self.convert_type("str")
            )
            type_menu.add_command(
                label=t("type_number"), command=lambda: self.convert_type("num")
            )
            type_menu.add_command(
                label=t("type_boolean"), command=lambda: self.convert_type("bool")
            )
            type_menu.add_command(
                label=t("type_null"), command=lambda: self.convert_type("null")
            )
            type_menu.add_command(
                label=t("type_object"), command=lambda: self.convert_type("dict")
            )
            type_menu.add_command(
                label=t("type_array"), command=lambda: self.convert_type("list")
            )
            menu.add_cascade(label=t("ctx_convert_to"), menu=type_menu)

            menu.add_separator()
            menu.add_command(label=t("ctx_copy"), command=self.copy_item)

        # Paste is available when clipboard has data
        if self._clipboard:
            menu.add_command(label=t("ctx_paste"), command=self.paste_item)

        if item:
            menu.add_separator()
            menu.add_command(label=t("ctx_remove"), command=self.remove_item)

        menu.post(event.x_root, event.y_root)

    # ── Drag-and-drop reordering ─────────────────────────────────

    def _on_drag_start(self, event):
        """Record the item under the cursor as a potential drag source."""
        item = self.tree.identify_row(event.y)
        if item:
            self._drag_item = item
            self._drag_start_y = event.y
            self._dragging = False

    def _on_drag_motion(self, event):
        """Show a drop indicator line while dragging."""
        if not self._drag_item or not self.tree.exists(self._drag_item):
            return

        # Only start dragging after moving past the threshold
        if not self._dragging:
            if abs(event.y - self._drag_start_y) < self._drag_threshold:
                return
            self._dragging = True
            self.tree.configure(cursor="hand2")

        # Determine the drop target position
        target = self.tree.identify_row(event.y)
        if not target or target == self._drag_item:
            self._remove_drop_indicator()
            return

        # Only allow reordering among siblings (same parent)
        drag_parent = self.tree.parent(self._drag_item)
        target_parent = self.tree.parent(target)
        if drag_parent != target_parent:
            self._remove_drop_indicator()
            return

        # Draw drop indicator line
        bbox = self.tree.bbox(target)
        if not bbox:
            return

        mid_y = bbox[1] + bbox[3] // 2
        if event.y < mid_y:
            indicator_y = bbox[1]  # Above the target
        else:
            indicator_y = bbox[1] + bbox[3]  # Below the target

        self._draw_drop_indicator(indicator_y)

    def _on_drag_end(self, event):
        """Move the dragged item to the drop position."""
        self._remove_drop_indicator()
        self.tree.configure(cursor="")

        if not self._dragging or not self._drag_item:
            self._drag_item = None
            self._dragging = False
            return

        if not self.tree.exists(self._drag_item):
            self._drag_item = None
            self._dragging = False
            return

        target = self.tree.identify_row(event.y)
        if not target or target == self._drag_item:
            self._drag_item = None
            self._dragging = False
            return

        # Only allow reordering among siblings
        drag_parent = self.tree.parent(self._drag_item)
        target_parent = self.tree.parent(target)
        if drag_parent != target_parent:
            self._drag_item = None
            self._dragging = False
            return

        # Determine insert position (above or below target)
        bbox = self.tree.bbox(target)
        if bbox:
            mid_y = bbox[1] + bbox[3] // 2
            target_index = self.tree.index(target)
            if event.y < mid_y:
                new_index = target_index
            else:
                new_index = target_index + 1

            # Adjust if dragging downward (source removal shifts indices)
            drag_index = self.tree.index(self._drag_item)
            if drag_index < new_index:
                new_index -= 1

            self.tree.move(self._drag_item, drag_parent, new_index)
            self.tree.selection_set(self._drag_item)

            # Reindex if parent is a list
            parent_tags = self.tree.item(drag_parent, "tags") if drag_parent else ()
            if not drag_parent and self._root_is_list:
                self._reindex_list(drag_parent)
            elif "list" in parent_tags:
                self._reindex_list(drag_parent)

            self._on_tree_select()

        self._drag_item = None
        self._dragging = False

    def _draw_drop_indicator(self, y):
        """Draw a horizontal line in the tree to indicate the drop position."""
        self._remove_drop_indicator()
        # Use a small frame as the indicator line
        self._drop_indicator = tk.Frame(
            self.tree, height=2, bg="#4444ff", relief="flat"
        )
        tree_width = self.tree.winfo_width()
        self._drop_indicator.place(x=0, y=y, width=tree_width, height=2)

    def _remove_drop_indicator(self):
        """Remove the drop indicator line."""
        if self._drop_indicator:
            self._drop_indicator.destroy()
            self._drop_indicator = None
