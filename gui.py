import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import csv
import json
import os
import datetime

import unfriender

LOG_FILE = os.path.join(os.path.dirname(__file__), "unfriender.log")
NOTES_FILE = os.path.join(os.path.dirname(__file__), "friend_notes.json")
BACKUP_FILE = os.path.join(os.path.dirname(__file__), "friends_backup.json")

def log_action(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")

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
        self.root.geometry("900x600")
        self.npsso_token = tk.StringVar()
        self.whitelist_patterns = tk.StringVar()
        self.search_var = tk.StringVar()
        self.tag_var = tk.StringVar()
        self.theme = tk.StringVar(value="Light")
        self.to_keep = []
        self.to_remove = []
        self.all_friends = []
        self.auth = None
        self.last_unfriended = []
        self.notes = load_notes()

        # Top frame for inputs
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="NPSSO Token:").grid(row=0, column=0, sticky="w")
        tk.Entry(top_frame, textvariable=self.npsso_token, width=60, show="*").grid(row=0, column=1, sticky="ew", padx=5)
        tk.Label(top_frame, text="Whitelist Patterns (comma separated regex):").grid(row=1, column=0, sticky="w")
        tk.Entry(top_frame, textvariable=self.whitelist_patterns, width=60).grid(row=1, column=1, sticky="ew", padx=5)
        tk.Button(top_frame, text="Load Friends", command=self.load_friends).grid(row=0, column=2, rowspan=2, padx=5, pady=2)
        tk.Button(top_frame, text="Switch Theme", command=self.switch_theme).grid(row=0, column=3, rowspan=2, padx=5, pady=2)

        # Search and tag filter bar
        search_frame = tk.Frame(root)
        search_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        tk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side=tk.LEFT, padx=5)
        tk.Label(search_frame, text="Tag:").pack(side=tk.LEFT)
        tk.Entry(search_frame, textvariable=self.tag_var, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Apply", command=self.apply_search).pack(side=tk.LEFT)
        tk.Button(search_frame, text="Export CSV", command=self.export_csv).pack(side=tk.RIGHT)
        tk.Button(search_frame, text="Export Backup", command=self.export_backup).pack(side=tk.RIGHT)
        tk.Button(search_frame, text="Import Backup", command=self.import_backup).pack(side=tk.RIGHT)
        tk.Button(search_frame, text="Compare Backups", command=self.compare_backups).pack(side=tk.RIGHT)

        # Treeview for friends
        columns = ("Name", "Action", "ID", "Note/Tag")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="extended")
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("Name", width=250)
        self.tree.column("Action", width=80)
        self.tree.column("ID", width=180)
        self.tree.column("Note/Tag", width=180)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Add right-click context menu
        self.menu = tk.Menu(self.tree, tearoff=0)
        self.menu.add_command(label="Add to Whitelist", command=self.add_selected_to_whitelist)
        self.menu.add_command(label="Edit Note/Tag", command=self.edit_note)
        self.menu.add_command(label="Move to Keep", command=self.move_to_keep)
        self.menu.add_command(label="Move to Remove", command=self.move_to_remove)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.edit_note)

        # Drag-and-drop support
        self.tree.bind("<B1-Motion>", self.drag_motion)
        self.dragged_item = None

        # Progress bar and action buttons
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(side=tk.LEFT, padx=5)
        self.status_label = tk.Label(bottom_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=10)
        tk.Button(bottom_frame, text="Unfriend All To Remove", command=self.unfriend_selected).pack(side=tk.RIGHT)
        tk.Button(bottom_frame, text="Undo Last Unfriend", command=self.undo_last_unfriend).pack(side=tk.RIGHT)

        # Add "About" menu for info/help
        menubar = tk.Menu(root)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.show_about)
        helpmenu.add_command(label="Help", command=self.show_help)
        # New: Settings menu
        settingsmenu = tk.Menu(menubar, tearoff=0)
        settingsmenu.add_command(label="Open Log File", command=self.open_log_file)
        menubar.add_cascade(label="Help", menu=helpmenu)
        menubar.add_cascade(label="Settings", menu=settingsmenu)
        root.config(menu=menubar)

        self.apply_theme()

    def load_friends(self):
        token = self.npsso_token.get().strip()
        patterns = [p.strip() for p in self.whitelist_patterns.get().split(",") if p.strip()]
        if not token:
            messagebox.showerror("Error", "Please enter your NPSSO token.")
            return
        self.tree.delete(*self.tree.get_children())
        self.status_label.config(text="Loading friends...")
        self.progress["value"] = 0
        def worker():
            try:
                self.auth = unfriender.authenticate_with_npsso_token(token)
                to_keep, to_remove = unfriender.get_friends_with_names(self.auth, patterns)
                self.to_keep = to_keep
                self.to_remove = to_remove
                self.all_friends = [("Keep", f[1], f[0]) for f in to_keep] + [("Remove", f[1], f[0]) for f in to_remove]
                self.root.after(0, self.display_friends)
                log_action("Loaded friends list.")
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.status_label.config(text=""))
        threading.Thread(target=worker, daemon=True).start()

    def display_friends(self):
        self.tree.delete(*self.tree.get_children())
        for action, name, pid in self.all_friends:
            note = self.notes.get(name, "")
            self.tree.insert("", "end", values=(name, action, pid, note))
        self.status_label.config(text=f"Loaded {len(self.all_friends)} friends. To remove: {len(self.to_remove)}")
        self.progress["value"] = 0

    def apply_search(self):
        query = self.search_var.get().strip().lower()
        tag = self.tag_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        for action, name, pid in self.all_friends:
            note = self.notes.get(name, "")
            if (query in name.lower() or query in pid.lower()) and (tag in note.lower() if tag else True):
                self.tree.insert("", "end", values=(name, action, pid, note))

    def export_csv(self):
        if not self.all_friends:
            messagebox.showinfo("Info", "No friends loaded.")
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
        messagebox.showinfo("Exported", f"Exported to {path}")
        log_action(f"Exported CSV to {path}")

    def export_backup(self):
        if not self.all_friends:
            messagebox.showinfo("Info", "No friends loaded.")
            return
        data = [{"name": name, "action": action, "id": pid, "note": self.notes.get(name, "")}
                for action, name, pid in self.all_friends]
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Backup", f"Backup exported to {path}")
        log_action(f"Exported backup to {path}")

    def import_backup(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.all_friends = [(item["action"], item["name"], item["id"]) for item in data]
        for item in data:
            if item.get("note"):
                self.notes[item["name"]] = item["note"]
        save_notes(self.notes)
        self.display_friends()
        messagebox.showinfo("Backup", f"Backup imported from {path}")
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
            messagebox.showinfo("Backup Comparison", "\n\n".join(msg))
            log_action(f"Compared backups: {file1} vs {file2}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not compare backups:\n{e}")

    def unfriend_selected(self):
        if not self.to_remove:
            messagebox.showinfo("Info", "No friends to remove.")
            return
        if not messagebox.askyesno("Confirm", f"Are you sure you want to remove {len(self.to_remove)} friends?"):
            return
        self.progress["maximum"] = len(self.to_remove)
        self.progress["value"] = 0
        self.status_label.config(text="Removing friends...")
        to_unfriend = list(self.to_remove)
        def progress_callback(done, total):
            self.progress["value"] = done
            self.status_label.config(text=f"Removing friends... {done}/{total}")
            self.root.update_idletasks()
        def worker():
            try:
                unfriender.remove_friends(self.auth, to_unfriend, progress_callback)
                self.last_unfriended = to_unfriend
                self.root.after(0, lambda: messagebox.showinfo("Done", "Finished removing friends."))
                self.root.after(0, lambda: self.status_label.config(text="Done."))
                self.root.after(0, self.load_friends)
                log_action(f"Unfriended {len(to_unfriend)} friends.")
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def undo_last_unfriend(self):
        if not self.last_unfriended:
            messagebox.showinfo("Undo", "No unfriend action to undo.")
            return
        config_path = os.path.join(os.path.dirname(__file__), "configuration.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}
        if "nameWhitelistPatterns" not in config:
            config["nameWhitelistPatterns"] = []
        for friend in self.last_unfriended:
            name = self.get_name_by_id(friend[0])
            if name:
                pat = f"^{name}$"
                if pat not in config["nameWhitelistPatterns"]:
                    config["nameWhitelistPatterns"].append(pat)
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Undo", "Restored last unfriended friends to whitelist.")
            log_action("Undo last unfriend: restored to whitelist.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not update configuration.json:\n{e}")

    def get_name_by_id(self, pid):
        for action, name, id_ in self.all_friends:
            if id_ == pid:
                return name
        return None

    def show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.menu.post(event.x_root, event.y_root)

    def add_selected_to_whitelist(self):
        selected = self.tree.selection()
        if not selected:
            return
        names = [self.tree.item(i)["values"][0] for i in selected]
        patterns = [f"^{name}$" for name in names]
        config_path = os.path.join(os.path.dirname(__file__), "configuration.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}
        if "nameWhitelistPatterns" not in config:
            config["nameWhitelistPatterns"] = []
        for pat in patterns:
            if pat not in config["nameWhitelistPatterns"]:
                config["nameWhitelistPatterns"].append(pat)
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Whitelist Updated", f"Added {len(patterns)} friend(s) to whitelist.")
            log_action(f"Added to whitelist: {', '.join(names)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not update configuration.json:\n{e}")

    def edit_note(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        for i in selected:
            name = self.tree.item(i)["values"][0]
            old_note = self.notes.get(name, "")
            note = simpledialog.askstring("Edit Note/Tag", f"Enter note/tag for {name}:", initialvalue=old_note)
            if note is not None:
                self.notes[name] = note
                save_notes(self.notes)
                self.display_friends()
                log_action(f"Edited note for {name}: {note}")

    def move_to_keep(self):
        selected = self.tree.selection()
        for i in selected:
            vals = self.tree.item(i)["values"]
            name = vals[0]
            pid = vals[2]
            # Remove from to_remove, add to to_keep
            for idx, f in enumerate(self.to_remove):
                if f[0] == pid:
                    self.to_keep.append(self.to_remove.pop(idx))
                    break
        self.all_friends = [("Keep", f[1], f[0]) for f in self.to_keep] + [("Remove", f[1], f[0]) for f in self.to_remove]
        self.display_friends()
        log_action(f"Moved to keep: {[self.tree.item(i)['values'][0] for i in selected]}")

    def move_to_remove(self):
        selected = self.tree.selection()
        for i in selected:
            vals = self.tree.item(i)["values"]
            name = vals[0]
            pid = vals[2]
            # Remove from to_keep, add to to_remove
            for idx, f in enumerate(self.to_keep):
                if f[0] == pid:
                    self.to_remove.append(self.to_keep.pop(idx))
                    break
        self.all_friends = [("Keep", f[1], f[0]) for f in self.to_keep] + [("Remove", f[1], f[0]) for f in self.to_remove]
        self.display_friends()
        log_action(f"Moved to remove: {[self.tree.item(i)['values'][0] for i in selected]}")

    def drag_motion(self, event):
        # Drag-and-drop: move friend between keep/remove by dragging
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        iid = self.tree.identify_row(event.y)
        if iid and not self.dragged_item:
            self.dragged_item = iid
        elif self.dragged_item and iid and self.dragged_item != iid:
            vals = self.tree.item(self.dragged_item)["values"]
            action = vals[1]
            if action == "Remove":
                self.move_to_keep()
            else:
                self.move_to_remove()
            self.dragged_item = None

    def switch_theme(self):
        if self.theme.get() == "Light":
            self.theme.set("Dark")
        else:
            self.theme.set("Light")
        self.apply_theme()

    def apply_theme(self):
        if self.theme.get() == "Dark":
            self.root.tk_setPalette(background="#222", foreground="#eee", activeBackground="#444", activeForeground="#fff")
        else:
            self.root.tk_setPalette(background="#f0f0f0", foreground="#222", activeBackground="#e0e0e0", activeForeground="#222")

    def show_about(self):
        messagebox.showinfo(
            "About PSN Unfriender",
            "PSN Unfriender GUI\n"
            "Manage your PlayStation Network friends list with ease.\n"
            "Features: bulk unfriend, whitelist, notes, backup, compare, and more.\n"
            "Created with ❤️ using Python and tkinter."
        )

    def show_help(self):
        messagebox.showinfo(
            "Help",
            "1. Enter your NPSSO token (see README for how to get it).\n"
            "2. (Optional) Enter whitelist patterns (comma separated regex).\n"
            "3. Click 'Load Friends' to fetch your friends list.\n"
            "4. Use right-click on a friend for more options (whitelist, notes, move).\n"
            "5. Use the buttons to export/import/compare backups, or to unfriend.\n"
            "6. Use the search and tag fields to filter your friends.\n"
            "7. Switch between light/dark themes with the button.\n"
            "8. Undo last unfriend if needed.\n"
            "9. See the log file for a history of your actions."
        )

    def open_log_file(self):
        import webbrowser
        if os.path.exists(LOG_FILE):
            webbrowser.open(LOG_FILE)
        else:
            messagebox.showinfo("Log", "Log file not found.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PSNUnfrienderGUI(root)
    root.mainloop()
