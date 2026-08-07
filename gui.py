import tkinter as tk
from tkinter import ttk, filedialog
import threading
import csv
import json
import os
import re
import datetime

import unfriender
from ui.theme import RADIUS, SPACE, Theme, get_theme, mix
from ui import icons
from ui.widgets import (Badge, Button, Card, EmptyState, InputField,
                        LoadingOverlay, Modal, SlimScrollbar, ThemedCanvas,
                        ThemedFrame, ThemedLabel, ToastManager, ToggleSwitch,
                        draw_round_rect)

LOG_FILE = os.path.join(os.path.dirname(__file__), "unfriender.log")
NOTES_FILE = os.path.join(os.path.dirname(__file__), "friend_notes.json")
BACKUP_FILE = os.path.join(os.path.dirname(__file__), "friends_backup.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "configuration.json")

# The Action column is decorated for legibility, so the raw bucket name is
# recovered through action_from_display() wherever the tree is read back.
ACTION_LABELS = {"Keep": "●  Keep", "Remove": "●  Remove"}

# Above this many selected rows, "Edit Note/Tag" asks once and applies to all
# instead of opening one dialog per friend.
BULK_NOTE_THRESHOLD = 3


def action_from_display(value):
    """Map a displayed Action cell back to the raw "Keep"/"Remove" bucket."""
    return "Keep" if "Keep" in str(value) else "Remove"


def log_action(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")

def load_config():
    """Read configuration.json.

    Returns {} only if the file genuinely does not exist. A file that exists but
    cannot be parsed raises ValueError, so callers never overwrite (and lose)
    an existing npsso_token by treating a parse failure as an empty config.
    """
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        raw = f.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Tolerate trailing commas, the one thing people hand-edit wrong.
        lenient = re.sub(r",(\s*[}\]])", r"\1", raw)
        try:
            return json.loads(lenient)
        except json.JSONDecodeError as e:
            raise ValueError(f"configuration.json is not valid JSON: {e}") from e

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2)

class PSNUnfrienderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PSN Unfriender")
        self.root.geometry("1140x740")
        self.root.minsize(940, 600)
        self.npsso_token = tk.StringVar()
        self.whitelist_patterns = tk.StringVar()
        self.search_var = tk.StringVar()
        self.tag_var = tk.StringVar()
        self.theme = tk.StringVar(value="Dark")
        self.to_keep = []
        self.to_remove = []
        self.all_friends = []
        self.auth = None
        self.last_unfriended = []
        # Set while a removal is running so the worker can be cancelled.
        self._stop_event = None
        self.notes = load_notes()
        self.config_error = None
        self.loaded_once = False
        self._filter_handle = None      # debounce handle for live search
        self._row_base_tags = {}        # iid -> bucket tags, restored on deselect
        self._selected_iids = set()

        # The design system owns every colour, font and ttk style in the app.
        self.ui = Theme(root, mode="dark")
        self.toasts = ToastManager(root)

        # Pre-fill the whitelist box from configuration.json so patterns added
        # via "Add to Whitelist" survive a restart.
        try:
            saved_patterns = load_config().get("nameWhitelistPatterns") or []
            if saved_patterns:
                self.whitelist_patterns.set(", ".join(saved_patterns))
        except ValueError as e:
            self.config_error = str(e)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._build_footer()
        self._build_menubar()

        # Live-as-you-type filtering, debounced so a fast typist does not
        # trigger a full tree rebuild on every keystroke.
        self.search_var.trace_add("write", self._schedule_filter)
        self.tag_var.trace_add("write", self._schedule_filter)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.apply_theme()
        self._show_empty_state()

        if self.config_error:
            self.root.after(220, lambda: Modal.alert(
                self.root,
                "configuration.json could not be read",
                "Whitelist changes made here will not be saved until it is fixed.",
                tone="warning",
                details=self.config_error))

    # --- chrome ---------------------------------------------------------

    def _build_header(self):
        header = ThemedFrame(self.root, token="bg")
        header.grid(row=0, column=0, sticky="ew",
                    padx=SPACE["xl"], pady=(SPACE["lg"], SPACE["md"]))
        header.columnconfigure(1, weight=1)

        self.logo = ThemedCanvas(header, width=44, height=44,
                                 background=self.ui["bg"])
        self.logo.redraw = self._draw_logo
        self.logo.grid(row=0, column=0, rowspan=2, padx=(0, SPACE["md"]))
        self._draw_logo()

        ThemedLabel(header, text="PSN Unfriender", bg_token="bg",
                    fg_token="text", font="display", anchor="w").grid(
                        row=0, column=1, sticky="w")
        ThemedLabel(header,
                    text="Bulk-manage your PlayStation Network friends list",
                    bg_token="bg", fg_token="text_muted", font="small",
                    anchor="w").grid(row=1, column=1, sticky="w")

        right = ThemedFrame(header, token="bg")
        right.grid(row=0, column=2, rowspan=2, sticky="e")

        self.keep_badge = Badge(right, label="Keep", count=0, tone="keep",
                                bg_token="bg")
        self.keep_badge.pack(side=tk.LEFT, padx=(0, SPACE["sm"]))
        self.remove_badge = Badge(right, label="Remove", count=0, tone="remove",
                                  bg_token="bg")
        self.remove_badge.pack(side=tk.LEFT, padx=(0, SPACE["lg"]))

        self.theme_label = ThemedLabel(right, text="Dark", bg_token="bg",
                                       fg_token="text_muted", font="small")
        self.theme_label.pack(side=tk.LEFT, padx=(0, SPACE["sm"]))
        self.theme_toggle = ToggleSwitch(right, command=self._on_theme_toggle,
                                         initial=True, bg_token="bg")
        self.theme_toggle.pack(side=tk.LEFT)

    def _draw_logo(self):
        t = get_theme()
        c = self.logo
        c.configure(background=t["bg"])
        c.delete("all")
        draw_round_rect(c, 1, 1, 43, 43, RADIUS["md"], fill=t["accent"],
                        outline=mix(t["accent"], "#ffffff", 0.18), width=1)
        # Faux highlight so the mark has a little depth without a gradient.
        draw_round_rect(c, 1, 1, 43, 22, RADIUS["md"],
                        fill=mix(t["accent"], "#ffffff", 0.12), outline="")
        icons.users(c, 22, 23, 30, t["accent_fg"], width=1, fill=t["accent_fg"])

    def _build_body(self):
        body = ThemedFrame(self.root, token="bg")
        body.grid(row=1, column=0, sticky="nsew", padx=SPACE["xl"])
        body.columnconfigure(0, weight=1)
        body.rowconfigure(2, weight=1)

        self._build_connection_card(body)
        self._build_filter_bar(body)
        self._build_table(body)

    def _build_connection_card(self, parent):
        card = Card(parent)
        card.grid(row=0, column=0, sticky="ew")
        card.columnconfigure(0, weight=3, uniform="conn")
        card.columnconfigure(1, weight=4, uniform="conn")

        inner = ThemedFrame(card, token="surface_raised")
        inner.pack(fill=tk.X, padx=SPACE["lg"], pady=SPACE["lg"])
        inner.columnconfigure(0, weight=3, uniform="conn")
        inner.columnconfigure(1, weight=4, uniform="conn")

        ThemedLabel(inner, text="NPSSO TOKEN", fg_token="text_faint",
                    font="eyebrow", anchor="w").grid(
                        row=0, column=0, sticky="w", pady=(0, SPACE["xs"]))
        ThemedLabel(inner, text="WHITELIST PATTERNS", fg_token="text_faint",
                    font="eyebrow", anchor="w").grid(
                        row=0, column=1, sticky="w", padx=(SPACE["md"], 0),
                        pady=(0, SPACE["xs"]))

        token_field = InputField(inner, self.npsso_token, icon="key", show="*",
                                 width=30)
        token_field.grid(row=1, column=0, sticky="ew")

        whitelist_field = InputField(inner, self.whitelist_patterns,
                                     icon="shield", width=40)
        whitelist_field.grid(row=1, column=1, sticky="ew", padx=(SPACE["md"], 0))

        self.load_button = Button(inner, text="Load Friends", icon="refresh",
                                  variant="primary", command=self.load_friends,
                                  height=38)
        self.load_button.grid(row=1, column=2, sticky="e", padx=(SPACE["md"], 0))

        ThemedLabel(inner, text="Kept private - never written to disk from here.",
                    fg_token="text_faint", font="micro", anchor="w").grid(
                        row=2, column=0, sticky="w", pady=(SPACE["xs"], 0))
        ThemedLabel(inner,
                    text="Comma-separated regex. Matching players are always kept.",
                    fg_token="text_faint", font="micro", anchor="w").grid(
                        row=2, column=1, sticky="w", padx=(SPACE["md"], 0),
                        pady=(SPACE["xs"], 0))

    def _build_filter_bar(self, parent):
        # Two rows: filtering on top, selection underneath. One row would
        # overflow the 940px minimum window width once both groups are present.
        bar = ThemedFrame(parent, token="bg")
        bar.grid(row=1, column=0, sticky="ew", pady=(SPACE["md"], SPACE["md"]))

        top = ThemedFrame(bar, token="bg")
        top.pack(fill=tk.X)

        search_field = InputField(top, self.search_var, icon="search", width=24,
                                  parent_token="bg")
        search_field.pack(side=tk.LEFT)
        search_field.entry.bind("<Return>", lambda e: self.apply_search())

        tag_field = InputField(top, self.tag_var, icon="tag", width=12,
                               parent_token="bg")
        tag_field.pack(side=tk.LEFT, padx=(SPACE["sm"], 0))
        tag_field.entry.bind("<Return>", lambda e: self.apply_search())

        Button(top, text="Apply", variant="secondary", command=self.apply_search,
               bg_token="bg", height=34).pack(side=tk.LEFT, padx=(SPACE["sm"], 0))

        for text, icon, command, tip in (
            ("Compare", "compare", self.compare_backups, "Compare two backup files"),
            ("Import", "upload", self.import_backup, "Import a backup JSON"),
            ("Backup", "download", self.export_backup, "Export a backup JSON"),
            ("CSV", "table", self.export_csv, "Export the list as CSV"),
        ):
            Button(top, text=text, icon=icon, variant="secondary",
                   command=command, bg_token="bg", height=34, pad_x=11,
                   font="small", tooltip=tip).pack(side=tk.RIGHT,
                                                   padx=(SPACE["sm"], 0))

        bottom = ThemedFrame(bar, token="bg")
        bottom.pack(fill=tk.X, pady=(SPACE["sm"], 0))

        self.select_all_button = Button(
            bottom, text="Select All", icon="check", variant="secondary",
            command=self.select_all, bg_token="bg", height=30, pad_x=11,
            font="small",
            tooltip="Selects every friend in the list. Clears the search and "
                    "tag filters first, so the table shows everything that is "
                    "selected.")
        self.select_all_button.pack(side=tk.LEFT)

        Button(bottom, text="Clear Selection", icon="cross", variant="ghost",
               command=self.clear_selection, bg_token="bg", height=30,
               pad_x=11, font="small",
               tooltip="Deselect everything (Esc in the table)").pack(
                   side=tk.LEFT, padx=(SPACE["xs"], 0))

        self.selection_badge = Badge(bottom, label="0 selected", count=None,
                                     tone="accent", bg_token="bg", height=24)
        self.selection_badge.pack(side=tk.LEFT, padx=(SPACE["md"], 0))

        self.scope_label = ThemedLabel(bottom, text="", bg_token="bg",
                                       fg_token="text_faint", font="micro",
                                       anchor="w")
        self.scope_label.pack(side=tk.LEFT, padx=(SPACE["md"], 0))

    def _build_table(self, parent):
        card = Card(parent, token="surface")
        card.grid(row=2, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        holder = ThemedFrame(card, token="surface")
        holder.grid(row=0, column=0, sticky="nsew")
        holder.columnconfigure(0, weight=1)
        holder.rowconfigure(0, weight=1)

        columns = ("Name", "Action", "ID", "Note/Tag")
        self.tree = ttk.Treeview(holder, columns=columns, show="headings",
                                 selectmode="extended", style="App.Treeview")
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("Name", width=280, minwidth=160)
        self.tree.column("Action", width=130, minwidth=110, anchor="w")
        self.tree.column("ID", width=200, minwidth=140)
        self.tree.column("Note/Tag", width=220, minwidth=120)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = SlimScrollbar(holder, self.tree.yview,
                                       bg_token="surface")
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 4),
                            pady=(38, 6))

        # Overlays live on top of the tree area, shown one at a time.
        self.empty_state = EmptyState(
            holder, icon="inbox", title="No friends loaded yet",
            subtitle="Paste your NPSSO token above and hit Load Friends\n"
                     "to pull your PlayStation Network friends list.")
        self.loading_overlay = LoadingOverlay(holder)

        # Add right-click context menu
        self.menu = tk.Menu(self.tree, tearoff=0)
        self.menu.add_command(label="Add to Whitelist", command=self.add_selected_to_whitelist)
        self.menu.add_command(label="Edit Note/Tag", command=self.edit_note)
        self.menu.add_separator()
        self.menu.add_command(label="Move to Keep", command=self.move_to_keep)
        self.menu.add_command(label="Move to Remove", command=self.move_to_remove)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.edit_note)

        # Drag-and-drop support: pick a row up on press, act only on release.
        self.tree.bind("<ButtonPress-1>", self.drag_start)
        self.tree.bind("<ButtonRelease-1>", self.drag_drop)
        self.dragged_item = None
        self.dragged_action = None

        # Tag backgrounds win over the ttk selection colour in modern Tk, so
        # selected rows get re-tagged instead of relying on the style map.
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Bound to the tree, not to root: an Entry that has focus keeps its own
        # Ctrl+A / Escape behaviour, so typing in the token, whitelist, search
        # or tag boxes is never hijacked by the table shortcuts.
        self.tree.bind("<Control-a>", self._on_select_all_key)
        self.tree.bind("<Control-A>", self._on_select_all_key)
        self.tree.bind("<Escape>", self._on_clear_selection_key)

    def _build_footer(self):
        footer = ThemedFrame(self.root, token="bg")
        footer.grid(row=2, column=0, sticky="ew",
                    padx=SPACE["xl"], pady=(SPACE["md"], SPACE["lg"]))
        footer.columnconfigure(1, weight=1)

        progress_col = ThemedFrame(footer, token="bg")
        progress_col.grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(progress_col, orient="horizontal",
                                        length=190, mode="determinate",
                                        style="App.Horizontal.TProgressbar")
        self.progress.pack(anchor="w")

        self.status_label = ThemedLabel(footer, text="Ready.", bg_token="bg",
                                        fg_token="text_muted", font="small",
                                        anchor="w")
        self.status_label.grid(row=0, column=1, sticky="w", padx=SPACE["lg"])

        actions = ThemedFrame(footer, token="bg")
        actions.grid(row=0, column=2, sticky="e")
        self.undo_button = Button(actions, text="Undo Last Unfriend", icon="undo",
                                  variant="secondary", command=self.undo_last_unfriend,
                                  bg_token="bg", height=38, font="small")
        self.undo_button.pack(side=tk.LEFT, padx=(0, SPACE["sm"]))
        self.unfriend_button = Button(actions, text="Unfriend All To Remove",
                                      icon="trash", variant="danger",
                                      command=self.unfriend_selected,
                                      bg_token="bg", height=38)
        self.unfriend_button.pack(side=tk.LEFT)
        # Takes the unfriend button's place for the duration of a run. Built
        # here but deliberately not packed - _set_removing() swaps the two.
        self.stop_button = Button(actions, text="Stop", icon="cross",
                                  variant="secondary", command=self.stop_removal,
                                  bg_token="bg", height=38,
                                  tooltip="Stop after the current removal")

    def _build_menubar(self):
        # Add "About" menu for info/help
        menubar = tk.Menu(self.root, tearoff=0)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.show_about)
        helpmenu.add_command(label="Help", command=self.show_help)
        # New: Settings menu
        settingsmenu = tk.Menu(menubar, tearoff=0)
        settingsmenu.add_command(label="Open Log File", command=self.open_log_file)
        settingsmenu.add_separator()
        settingsmenu.add_command(label="Switch Theme", command=self.switch_theme)
        menubar.add_cascade(label="Help", menu=helpmenu)
        menubar.add_cascade(label="Settings", menu=settingsmenu)
        self.root.config(menu=menubar)
        self._menus = [menubar, helpmenu, settingsmenu, self.menu]

    # --- shared helpers -------------------------------------------------

    def toast(self, message, tone="info"):
        """Routine feedback goes to a toast, not a blocking message box."""
        self.toasts.show(message, tone=tone)

    def alert(self, title, message, tone="info", details=None):
        return Modal.alert(self.root, title, message, tone=tone, details=details)

    def rebuild_all_friends(self):
        """Rebuild the flat display list from to_keep / to_remove.

        IDs are normalised to str: Tcl converts all-digit strings back to ints
        when read out of the Treeview, so every comparison must go through str.
        """
        self.all_friends = (
            [("Keep", f[1], str(f[0])) for f in self.to_keep]
            + [("Remove", f[1], str(f[0])) for f in self.to_remove]
        )

    def selected_rows(self):
        """Return [(name, id)] for the current selection, as strings."""
        rows = []
        for iid in self.tree.selection():
            vals = self.tree.item(iid)["values"]
            rows.append((str(vals[0]), str(vals[2])))
        return rows

    def move_selection(self, target):
        """Move the selected rows between the keep and remove buckets."""
        rows = self.selected_rows()
        if not rows:
            return 0
        if target == "Keep":
            source, dest = self.to_remove, self.to_keep
        else:
            source, dest = self.to_keep, self.to_remove

        moved = []
        for name, pid in rows:
            for idx, friend in enumerate(source):
                if str(friend[0]) == pid:
                    dest.append(source.pop(idx))
                    moved.append(name)
                    break

        if not moved:
            self.status_label.config(
                text=f"Nothing moved - selection is already under \"{target}\".")
            return 0

        self.rebuild_all_friends()
        # Rebuild the tree first, then reselect by ID: the old iids are gone.
        self.display_friends(select_ids={pid for _, pid in rows})
        self.status_label.config(
            text=f"Moved {len(moved)} to {target}. To remove: {len(self.to_remove)}")
        log_action(f"Moved to {target.lower()}: {', '.join(moved)}")
        self.toast(f"Moved {len(moved)} friend(s) to {target}.",
                   tone="success" if target == "Keep" else "warning")
        return len(moved)

    def load_friends(self):
        token = self.npsso_token.get().strip()
        patterns = [p.strip() for p in self.whitelist_patterns.get().split(",") if p.strip()]
        if not token:
            self.alert("NPSSO token required",
                       "Paste your NPSSO token into the field above, then try "
                       "again. Help > Help explains where to find it.",
                       tone="warning")
            return
        self.tree.delete(*self.tree.get_children())
        self._row_base_tags.clear()
        self.status_label.config(text="Loading friends...")
        self.progress["value"] = 0
        self._show_loading("Contacting PlayStation Network",
                           "Authenticating and fetching your friends list.")
        self.load_button.set_enabled(False)
        def worker():
            try:
                self.auth = unfriender.authenticate_with_npsso_token(token)
                to_keep, to_remove = unfriender.get_friends_with_names(self.auth, patterns)
                self.to_keep = list(to_keep)
                self.to_remove = list(to_remove)
                self.rebuild_all_friends()
                self.root.after(0, self.display_friends)
                self.root.after(0, lambda: self.toast(
                    f"Loaded {len(self.all_friends)} friends.", tone="success"))
                log_action("Loaded friends list.")
            except Exception as e:
                message = str(e)
                self.root.after(0, lambda: self._load_failed(message))
            finally:
                self.root.after(0, lambda: self.load_button.set_enabled(True))
        threading.Thread(target=worker, daemon=True).start()

    def _load_failed(self, message):
        """Marshalled back onto the UI thread - never touch widgets in worker()."""
        self._hide_overlays()
        if not self.all_friends:
            self._show_empty_state()
        self.status_label.config(text="")
        self.alert("Could not load friends", "PlayStation Network rejected the "
                   "request. An expired NPSSO token is the usual cause.",
                   tone="danger", details=message)

    def display_friends(self, select_ids=None):
        """Redraw the tree, honouring the active search/tag filter.

        select_ids is a set of account IDs (str) to reselect after the redraw,
        so a move keeps the rows the user was working with highlighted.
        """
        query = self.search_var.get().strip().lower()
        tag = self.tag_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        self._row_base_tags.clear()
        self._selected_iids.clear()
        shown = 0
        for action, name, pid in self.all_friends:
            pid = str(pid)
            note = self.notes.get(name, "")
            if query and query not in name.lower() and query not in pid.lower():
                continue
            if tag and tag not in note.lower():
                continue
            stripe = "alt" if shown % 2 else "base"
            tags = (f"{action.lower()}_{stripe}",)
            iid = self.tree.insert("", "end",
                                   values=(name, ACTION_LABELS[action], pid, note),
                                   tags=tags)
            self._row_base_tags[iid] = tags
            shown += 1
            if select_ids and pid in select_ids:
                self.tree.selection_add(iid)
        filtered = "" if shown == len(self.all_friends) else f" (showing {shown})"
        self.status_label.config(
            text=f"Loaded {len(self.all_friends)} friends{filtered}. To remove: {len(self.to_remove)}")
        self.progress["value"] = 0
        self.loaded_once = self.loaded_once or bool(self.all_friends)
        self._refresh_counts()
        self._update_selection_ui()
        self._update_overlays(shown)

    def _set_removing(self, active):
        """Swap the unfriend and stop buttons. Must run on the UI thread.

        Kept in one place so the two buttons can never both be visible or both
        be hidden, whichever path a run ends on.
        """
        if active:
            self.unfriend_button.pack_forget()
            self.stop_button.set_text("Stop")
            self.stop_button.set_enabled(True)
            self.stop_button.pack(side=tk.LEFT)
        else:
            self.stop_button.pack_forget()
            self.unfriend_button.pack(side=tk.LEFT)
        self.undo_button.set_enabled(not active)

    def stop_removal(self):
        if self._stop_event is None:
            return
        self._stop_event.set()
        # Disable rather than hide: a second click should do nothing, but the
        # button staying put confirms the first click registered.
        self.stop_button.set_text("Stopping...")
        self.stop_button.set_enabled(False)
        self.status_label.config(
            text="Stopping - finishing the removal already in progress...")
        log_action("Stop requested during removal.")

    def _refresh_counts(self):
        self.keep_badge.set(count=len(self.to_keep))
        self.remove_badge.set(count=len(self.to_remove))
        if self.to_remove:
            self.unfriend_button.set_text(f"Unfriend {len(self.to_remove)} To Remove")
        else:
            self.unfriend_button.set_text("Unfriend All To Remove")

    # --- overlays --------------------------------------------------------

    def _hide_overlays(self):
        self.loading_overlay.stop()
        self.loading_overlay.place_forget()
        self.empty_state.place_forget()

    def _show_loading(self, message, hint=""):
        self.empty_state.place_forget()
        self.loading_overlay.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.loading_overlay.lift()
        self.loading_overlay.start(message, hint)

    def _show_empty_state(self, title=None, subtitle=None):
        self.loading_overlay.stop()
        self.loading_overlay.place_forget()
        if title:
            self.empty_state.set_text(title, subtitle or "")
        self.empty_state.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.empty_state.lift()

    def _update_overlays(self, shown):
        self._hide_overlays()
        if shown:
            return
        if self.all_friends:
            self._show_empty_state(
                "No friends match this filter",
                "Clear the search or tag box to see the full list again.")
        elif self.loaded_once:
            self._show_empty_state(
                "Your friends list is empty",
                "Nothing came back from PlayStation Network.")
        else:
            self._show_empty_state(
                "No friends loaded yet",
                "Paste your NPSSO token above and hit Load Friends\n"
                "to pull your PlayStation Network friends list.")

    # --- filtering -------------------------------------------------------

    def _cancel_pending_filter(self):
        if self._filter_handle is not None:
            try:
                self.root.after_cancel(self._filter_handle)
            except tk.TclError:
                pass
            self._filter_handle = None

    def _schedule_filter(self, *_args):
        """Debounce live filtering: one redraw ~220ms after typing stops."""
        self._cancel_pending_filter()
        self._filter_handle = self.root.after(220, self._run_filter)

    def _run_filter(self):
        self._filter_handle = None
        if self.all_friends:
            # Carry the selection through the redraw via the reselect-by-ID
            # path, so narrowing the filter does not silently drop rows the
            # user had already picked and leave the count wrong.
            self.display_friends(select_ids=self._current_selection_ids())

    def apply_search(self):
        self._cancel_pending_filter()
        self.display_friends(select_ids=self._current_selection_ids())

    # --- selection tinting ------------------------------------------------

    def _current_selection_ids(self):
        """Account IDs (str) of the current selection, for reselect-by-ID."""
        return {pid for _, pid in self.selected_rows()}

    def select_all(self):
        """Select every friend in the list - not just the filtered rows.

        Rows excluded by the search/tag filter are not in the Treeview at all,
        so a selection physically cannot hold them. Rather than tracking a
        shadow set of invisible IDs - which would let the "N selected" badge
        disagree with the visible table immediately before an irreversible bulk
        unfriend - this clears the filter first and then selects what is drawn.
        What you see stays what is selected.
        """
        if not self.all_friends:
            self.toast("No friends loaded yet.", tone="warning")
            return

        was_filtered = bool(self.search_var.get().strip()
                            or self.tag_var.get().strip())
        if was_filtered:
            self.search_var.set("")
            self.tag_var.set("")
            # Clearing the boxes fires the trace, which queues a debounced
            # redraw; cancel it so it cannot wipe the selection 220ms later.
            self._cancel_pending_filter()
            self.display_friends()

        rows = self.tree.get_children()
        if rows:
            self.tree.selection_set(rows)
        self._update_selection_ui()
        if was_filtered:
            self.toast(f"Filter cleared. Selected all {len(rows)} friends.",
                       tone="info")

    def clear_selection(self):
        selected = self.tree.selection()
        if selected:
            self.tree.selection_remove(*selected)
        self._update_selection_ui()

    def _on_select_all_key(self, _event=None):
        self.select_all()
        return "break"

    def _on_clear_selection_key(self, _event=None):
        self.clear_selection()
        return "break"

    def _update_selection_ui(self):
        """Keep the count badge and the scope hint truthful."""
        count = len(self.tree.selection())
        total = len(self.all_friends)
        shown = len(self.tree.get_children())
        self.selection_badge.set(label=f"{count} selected")
        self.select_all_button.set_text(
            f"Select All ({total})" if total else "Select All")
        if not total:
            self.scope_label.configure(text="")
        elif shown != total:
            self.scope_label.configure(
                text=f"Filter active: {shown} of {total} rows shown. "
                     f"Select All clears the filter and takes all {total}.")
        else:
            self.scope_label.configure(text=f"All {total} rows shown.")

    def _on_tree_select(self, _event=None):
        """Re-tag rows on selection.

        Tk >= 8.6.11 gives Treeview *tag* backgrounds priority over the style's
        selected-row map, so the bucket tint would hide the selection entirely.
        Swapping the tag on the changed rows keeps both working.
        """
        current = set(self.tree.selection())
        for iid in self._selected_iids - current:
            if self.tree.exists(iid):
                self.tree.item(iid, tags=self._row_base_tags.get(iid, ()))
        for iid in current - self._selected_iids:
            if self.tree.exists(iid):
                self.tree.item(iid, tags=("selected_row",))
        self._selected_iids = current
        self._update_selection_ui()

    def export_csv(self):
        if not self.all_friends:
            self.toast("No friends loaded yet.", tone="warning")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Action", "ID", "Note/Tag"])
            for action, name, pid in self.all_friends:
                note = self.notes.get(name, "")
                writer.writerow([name, action, pid, note])
        self.toast(f"Exported {len(self.all_friends)} rows to CSV.", tone="success")
        log_action(f"Exported CSV to {path}")

    def export_backup(self):
        if not self.all_friends:
            self.toast("No friends loaded yet.", tone="warning")
            return
        data = [{"name": name, "action": action, "id": pid, "note": self.notes.get(name, "")}
                for action, name, pid in self.all_friends]
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.toast(f"Backup saved: {os.path.basename(path)}", tone="success")
        log_action(f"Exported backup to {path}")

    def import_backup(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            self.alert("Could not import backup",
                       "That file could not be read as a backup JSON.",
                       tone="danger", details=str(e))
            return
        # Restore the keep/remove buckets too, not just the display list -
        # the move commands and "Unfriend All To Remove" work off these.
        self.to_keep = [(str(i["id"]), i["name"]) for i in data if i.get("action") == "Keep"]
        self.to_remove = [(str(i["id"]), i["name"]) for i in data if i.get("action") != "Keep"]
        self.rebuild_all_friends()
        for item in data:
            if item.get("note"):
                self.notes[item["name"]] = item["note"]
        save_notes(self.notes)
        self.loaded_once = True
        self.display_friends()
        self.toast(f"Imported {len(data)} entries from "
                   f"{os.path.basename(path)}.", tone="success")
        log_action(f"Imported backup from {path}")

    def compare_backups(self):
        file1 = filedialog.askopenfilename(title="Select First Backup", filetypes=[("JSON files", "*.json")])
        if not file1:
            return
        file2 = filedialog.askopenfilename(title="Select Second Backup", filetypes=[("JSON files", "*.json")])
        if not file2:
            return
        try:
            with open(file1, "r", encoding="utf-8") as f1, open(file2, "r", encoding="utf-8") as f2:
                data1 = json.load(f1)
                data2 = json.load(f2)
            set1 = set((item["id"], item["name"]) for item in data1)
            set2 = set((item["id"], item["name"]) for item in data2)
            added = set2 - set1
            removed = set1 - set2
            msg = []
            if added:
                msg.append("Friends Added:\n" + "\n".join(f"{n} ({i})" for i, n in added))
            if removed:
                msg.append("Friends Removed:\n" + "\n".join(f"{n} ({i})" for i, n in removed))
            if not msg:
                msg.append("No differences found between backups.")
            summary = (f"{len(added)} added, {len(removed)} removed."
                       if (added or removed) else "The two backups match.")
            self.alert("Backup Comparison", summary, tone="info",
                       details="\n\n".join(msg))
            log_action(f"Compared backups: {file1} vs {file2}")
        except Exception as e:
            self.alert("Could not compare backups",
                       "One of the files could not be read.",
                       tone="danger", details=str(e))

    def unfriend_selected(self):
        if not self.to_remove:
            self.toast("Nothing is queued for removal.", tone="warning")
            return
        # Snapshot the bucket ONCE, up front, and drive both the confirmation
        # text and the removal from that same list. The dialog can therefore
        # never understate what is about to be deleted.
        to_unfriend = list(self.to_remove)
        count = len(to_unfriend)
        preview = "\n".join(name for _pid, name in to_unfriend[:25])
        if count > 25:
            preview += f"\n... and {count - 25} more"
        # Irreversible: "Undo Last Unfriend" only whitelists the names so they
        # are not removed again - it cannot restore the friendships.
        confirmed = Modal.confirm(
            self.root,
            f"Unfriend {count} player{'s' if count != 1 else ''}?",
            "This permanently removes them from your PlayStation Network "
            "friends list. Undo Last Unfriend only adds them to your whitelist "
            "- it cannot restore a friendship. PSN requires a new friend "
            "request for that.",
            confirm_label=f"Yes, unfriend {count}",
            tone="danger", icon="trash", details=preview)
        if not confirmed:
            return
        self.progress["maximum"] = count
        self.progress["value"] = 0
        self.status_label.config(text="Removing friends...")
        self._stop_event = threading.Event()
        self._set_removing(True)
        def progress_callback(done, total):
            # Called from the worker thread, so bounce every widget touch
            # through root.after() rather than updating in place.
            self.root.after(0, lambda: self._unfriend_progress(done, total))
        def worker():
            try:
                # remove_friends isolates per-friend failures, so a rate limit
                # partway through no longer discards the whole run. Report what
                # actually happened rather than assuming everything succeeded.
                result = unfriender.remove_friends(
                    self.auth, to_unfriend, progress_callback,
                    stop_event=self._stop_event)
                removed, failures = result.removed, result.failures
                # Undo must offer only the friends PSN actually accepted.
                self.last_unfriended = removed
                self.root.after(0, lambda: self.status_label.config(
                    text="Stopped." if result.stopped else "Done."))
                self.root.after(0, self.load_friends)
                log_action(
                    f"{'Stopped after unfriending' if result.stopped else 'Unfriended'} "
                    f"{len(removed)} of {count} friends"
                    f"{f', {len(failures)} failed' if failures else ''}.")
                if result.stopped:
                    # Already-removed friends are gone for good, so say so
                    # plainly rather than implying the run simply cancelled.
                    self.root.after(0, lambda: self.alert(
                        "Removal stopped",
                        f"Stopped after removing {len(removed)} of {count}. "
                        "Those removals are permanent. The remaining "
                        f"{count - len(removed)} are still on your friends "
                        "list and the list has been reloaded.",
                        tone="warning"))
                elif failures:
                    detail = "\n".join(
                        f"{f[1]}: {err}" for f, err in failures[:25])
                    if len(failures) > 25:
                        detail += f"\n... and {len(failures) - 25} more"
                    self.root.after(0, lambda: self.alert(
                        "Finished with errors",
                        f"Removed {len(removed)} of {count}. "
                        f"{len(failures)} could not be removed and are still "
                        "on your friends list - the list has been reloaded, so "
                        "you can queue them again.",
                        tone="warning", details=detail))
                else:
                    self.root.after(0, lambda: self.toast(
                        f"Removed {len(removed)} friend(s).", tone="success"))
            except Exception as e:
                message = str(e)
                self.root.after(0, lambda: self.alert(
                    "Unfriending stopped", "The request failed part-way "
                    "through. Reload the list to see the current state.",
                    tone="danger", details=message))
            finally:
                self.root.after(0, lambda: self._set_removing(False))
                self._stop_event = None
        threading.Thread(target=worker, daemon=True).start()

    def _unfriend_progress(self, done, total):
        self.progress["value"] = done
        self.status_label.config(text=f"Removing friends... {done}/{total}")

    def undo_last_unfriend(self):
        if not self.last_unfriended:
            self.toast("No unfriend action to undo.", tone="warning")
            return
        try:
            config = load_config()
        except ValueError as e:
            self.alert("configuration.json could not be read",
                       "Fix the file, then try again.", tone="danger",
                       details=str(e))
            return
        patterns = config.setdefault("nameWhitelistPatterns", [])
        for friend in self.last_unfriended:
            # Fall back to the name stored alongside the ID: the friend is gone
            # from all_friends after the post-unfriend reload.
            name = self.get_name_by_id(friend[0]) or (friend[1] if len(friend) > 1 else None)
            if name:
                pat = f"^{re.escape(name)}$"
                if pat not in patterns:
                    patterns.append(pat)
        try:
            save_config(config)
            self.whitelist_patterns.set(", ".join(patterns))
            self.alert(
                "Added to whitelist",
                "The last unfriended players will not be removed again.\n\n"
                "Note: this does not re-add them as friends - PSN requires a "
                "new friend request for that.",
                tone="warning")
            log_action("Undo last unfriend: restored to whitelist.")
        except Exception as e:
            self.alert("Could not update configuration.json",
                       "The whitelist was not saved.", tone="danger",
                       details=str(e))

    def get_name_by_id(self, pid):
        for action, name, id_ in self.all_friends:
            if str(id_) == str(pid):
                return name
        return None

    def show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            # Keep an existing multi-row selection: right-clicking inside it
            # should act on all of it, not collapse it to one row.
            if iid not in self.tree.selection():
                self.tree.selection_set(iid)
            self.menu.post(event.x_root, event.y_root)

    def add_selected_to_whitelist(self):
        rows = self.selected_rows()
        if not rows:
            self.toast("Select one or more friends first.", tone="warning")
            return
        try:
            config = load_config()
        except ValueError as e:
            self.alert("configuration.json could not be read",
                       "Fix the file, then try again.", tone="danger",
                       details=str(e))
            return

        patterns = config.setdefault("nameWhitelistPatterns", [])
        added = []
        for name, _pid in rows:
            # Escape the name: online IDs may contain regex metacharacters.
            pat = f"^{re.escape(name)}$"
            if pat not in patterns:
                patterns.append(pat)
                added.append(name)

        try:
            save_config(config)
        except Exception as e:
            self.alert("Could not update configuration.json",
                       "The whitelist was not saved.", tone="danger",
                       details=str(e))
            return

        # Reflect the saved patterns in the entry box so the next "Load Friends"
        # uses them, and move the rows to Keep so it takes effect immediately.
        self.whitelist_patterns.set(", ".join(patterns))
        moved = self.move_selection("Keep")

        log_action(f"Added to whitelist: {', '.join(n for n, _ in rows)}")
        self.toast(f"Whitelisted {len(added)} new pattern(s). "
                   f"Moved {moved} to Keep.", tone="success")
        self.status_label.config(
            text=f"Whitelisted {len(rows)} friend(s). To remove: {len(self.to_remove)}")

    def edit_note(self, event=None):
        # Snapshot the selection up front: display_friends() destroys the iids.
        rows = self.selected_rows()
        if not rows:
            return
        # Per-row prompting is right for a handful of rows and hostile for
        # hundreds - and Select All now routinely selects the whole list.
        if len(rows) > BULK_NOTE_THRESHOLD:
            return self._edit_notes_bulk(rows)
        changed = False
        for name, _pid in rows:
            old_note = self.notes.get(name, "")
            note = Modal.ask_string(self.root, "Edit Note/Tag",
                                    f"Note or tag for {name}",
                                    initial=old_note,
                                    message="Tags are searchable from the "
                                            "filter bar.")
            if note is not None:
                self.notes[name] = note
                changed = True
                log_action(f"Edited note for {name}: {note}")
        if changed:
            save_notes(self.notes)
            self.display_friends(select_ids={pid for _, pid in rows})
            self.toast("Notes saved.", tone="success")

    def _edit_notes_bulk(self, rows):
        """Ask once, apply to every selected row.

        Prefilled with the shared note when the selection already agrees, so
        the common "retag this whole group" case is a single confirm.
        """
        existing = {self.notes.get(name, "") for name, _pid in rows}
        initial = existing.pop() if len(existing) == 1 else ""
        note = Modal.ask_string(
            self.root, "Edit Note/Tag",
            f"Note or tag for all {len(rows)} selected friends",
            initial=initial,
            message=f"This replaces the existing note on all {len(rows)} "
                    f"selected friends. Leave it empty to clear them. "
                    f"Tags are searchable from the filter bar.")
        if note is None:
            return
        for name, _pid in rows:
            self.notes[name] = note
        save_notes(self.notes)
        log_action(f"Bulk-edited note for {len(rows)} friends: {note}")
        self.display_friends(select_ids={pid for _, pid in rows})
        self.toast(f"Note applied to {len(rows)} friends.", tone="success")

    def move_to_keep(self):
        self.move_selection("Keep")

    def move_to_remove(self):
        self.move_selection("Remove")

    def drag_start(self, event):
        iid = self.tree.identify_row(event.y)
        if iid and self.tree.identify("region", event.x, event.y) == "cell":
            self.dragged_item = iid
            self.dragged_action = action_from_display(self.tree.item(iid)["values"][1])
        else:
            self.dragged_item = None
            self.dragged_action = None

    def drag_drop(self, event):
        source_iid, source_action = self.dragged_item, self.dragged_action
        self.dragged_item = None
        self.dragged_action = None
        if not source_iid:
            return
        target_iid = self.tree.identify_row(event.y)
        # Only a drop onto a row in the *other* bucket counts as a move;
        # a plain click or double-click lands on itself and does nothing.
        if not target_iid or target_iid == source_iid:
            return
        target_action = action_from_display(self.tree.item(target_iid)["values"][1])
        if target_action == source_action:
            return
        self.tree.selection_set(source_iid)
        self.move_selection(target_action)

    # --- theming ---------------------------------------------------------

    def switch_theme(self):
        if self.theme.get() == "Light":
            self.theme.set("Dark")
        else:
            self.theme.set("Light")
        self.apply_theme()
        self.theme_toggle.set(self.theme.get() == "Dark")

    def _on_theme_toggle(self, is_dark):
        self.theme.set("Dark" if is_dark else "Light")
        self.apply_theme()

    def apply_theme(self):
        """Restyle the whole live window through ttk.Style + token broadcast.

        Note this is *not* tk_setPalette: that leaves every ttk widget (the
        Treeview above all) untouched, which is what made the old dark mode
        half-applied.
        """
        self.ui.set_mode("dark" if self.theme.get() == "Dark" else "light")
        t = self.ui
        self.theme_label.configure(text=self.theme.get())

        # Bucket tints for the table. Keep and Remove read at a glance, and the
        # alternating stripe keeps long lists scannable.
        self.tree.tag_configure("keep_base", background=t["row_keep"],
                                foreground=t["success_text"])
        self.tree.tag_configure("keep_alt", background=t["row_keep_alt"],
                                foreground=t["success_text"])
        self.tree.tag_configure("remove_base", background=t["row_remove"],
                                foreground=t["danger_text"])
        self.tree.tag_configure("remove_alt", background=t["row_remove_alt"],
                                foreground=t["danger_text"])
        self.tree.tag_configure("selected_row", background=t["row_selected"],
                                foreground=t["text"])

        for menu in getattr(self, "_menus", []):
            t.style_menu(menu)

    # --- info ------------------------------------------------------------

    def show_about(self):
        self.alert(
            "About PSN Unfriender",
            "Manage your PlayStation Network friends list with ease.\n\n"
            "Bulk unfriend, whitelist, notes, backups and comparison - built "
            "with Python and tkinter, no third-party UI toolkit.",
            tone="info")

    def show_help(self):
        self.alert(
            "How to use PSN Unfriender",
            "Nine steps from token to a tidy friends list.",
            tone="info",
            details=(
                "1. Enter your NPSSO token (see README for how to get it).\n"
                "2. (Optional) Enter whitelist patterns (comma separated regex).\n"
                "3. Click 'Load Friends' to fetch your friends list.\n"
                "4. Use right-click on a friend for more options (whitelist, notes, move).\n"
                "5. Use the buttons to export/import/compare backups, or to unfriend.\n"
                "6. Use the search and tag fields to filter your friends.\n"
                "7. Switch between light/dark themes with the toggle in the header.\n"
                "8. Undo last unfriend if needed.\n"
                "9. See the log file for a history of your actions.\n\n"
                "Tip: drag a row onto a row in the other bucket to move it."))

    def open_log_file(self):
        import webbrowser
        if os.path.exists(LOG_FILE):
            webbrowser.open(LOG_FILE)
        else:
            self.toast("Log file not found.", tone="warning")

    # --- shutdown --------------------------------------------------------

    def _on_close(self):
        """Cancel every pending after() before tearing the window down."""
        if self._filter_handle is not None:
            try:
                self.root.after_cancel(self._filter_handle)
            except tk.TclError:
                pass
            self._filter_handle = None
        self.loading_overlay.stop()
        self.toasts.clear()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PSNUnfrienderGUI(root)
    root.mainloop()
