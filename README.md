# 🎮 PSN Unfriender

![Python](https://img.shields.io/badge/python-3.8+-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-brightgreen)
![GUI](https://img.shields.io/badge/GUI-Tkinter-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-Active-success)

A modern Python application for managing your **PlayStation Network** friends list.

Whether you have a few friends or hundreds, **PSN Unfriender** makes it easy to audit, back up, organise, and remove friends quickly using either a modern graphical interface or the command line.

---

## ✨ Features

- 🚀 Mass unfriend PlayStation Network friends
- 🖥️ Modern GUI and CLI support
- 🔒 Secure NPSSO authentication
- ⭐ Whitelist friends using regex or exact matches
- 👥 Preview friends before removing them
- 🔍 Search and filter by PSN ID, name or custom tags
- 📝 Add custom notes and tags
- 📁 Export and import CSV/JSON backups
- 📊 Compare friend list backups
- ↩️ Undo previous actions
- 📈 Progress tracking and detailed logging
- 🎨 Fully themed interface — deep indigo dark mode and a clean light mode, both first-class
- 🧩 Custom-built UI component library (cards, pill badges, toasts, modals, toggle switch)
- ⌨️ Hover, press and keyboard-focus states on every control
- 💻 Cross-platform support
- ⚡ Portable — **zero UI dependencies**, pure `tkinter`/`ttk` from the standard library

---

## 📸 Screenshots

> Coming Soon

Add screenshots or animated GIFs here to showcase:

- Main dashboard (dark theme)
- Main dashboard (light theme)
- Friend list with Keep / Remove badges
- Empty state before friends are loaded
- Loading overlay during the PSN fetch
- Unfriend confirmation modal
- Whitelist and notes editing

---

## ❓ Why PSN Unfriender?

Managing large PlayStation Network friend lists manually can be slow and frustrating.

PSN Unfriender automates repetitive tasks while giving you complete control over your friends list.

With whitelist protection, backups and preview functionality, you'll always know exactly what will happen before any friends are removed.

---

## ⚠️ Security

> **Treat your NPSSO token exactly like your PlayStation password.**
>
> Never share it.
> Never upload it to GitHub.
> Never send it to anyone.

---

## 📋 Requirements

- Python 3.8+ (with `tkinter`, which ships with the standard Windows and macOS installers; on Debian/Ubuntu install `python3-tk`)
- Windows / macOS / Linux
- PlayStation Network account
- Internet connection

The interface adds **no dependencies beyond the standard library** — `requirements.txt` covers the PSN API client only.

---

## 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/MrJasonDEX/PSN-Unfriender-Tool.git
cd PSN-Unfriender-Tool
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Copy the configuration

Linux/macOS

```bash
cp configuration.example.json configuration.json
```

Windows

```powershell
copy configuration.example.json configuration.json
```

### Obtain your NPSSO Token

1. Sign into PlayStation.
2. Visit:

```
https://ca.account.sony.com/api/v1/ssocookie
```

3. Copy your token.
4. Paste it into `configuration.json`.

Example:

```json
{
    "npsso_token": "YOUR_NPSSO_TOKEN",
    "nameWhitelistPatterns": [
        ".*Family.*",
        ".*BestFriend.*"
    ]
}
```

---

## ▶️ Running

### Command Line

```bash
python unfriender.py
```

The CLI will:

- Load your friends
- Apply whitelist rules
- Show a preview
- Ask for confirmation
- Remove selected friends

---

### GUI

```bash
python gui.py
```

The window is laid out as **header → connection card → filter bar → friends table → status footer**. It is resizable, with the table taking the flexible space and a 940×600 minimum.

GUI features:

- Load friends, with a loading overlay while the PSN fetch runs
- Live search-as-you-type (debounced) plus tag filtering
- **Select All** and **Clear Selection**, with a live "N selected" badge (`Ctrl+A` / `Escape` while the table is focused)
- Keep / Remove shown as colour-coded pill badges with live counts
- Right-click context menu — whitelist, edit note/tag, move between buckets
- Double-click a row to edit its note
- Drag a row onto the other bucket to move it
- Edit notes and tags
- Manage the whitelist
- Import, export and compare backups
- Determinate progress bar and status footer
- Resilient bulk removal — rate limits are retried, and one failure no longer aborts the batch
- **Stop** button to cancel a removal in progress, with a report of what was already removed
- Toast notifications for routine feedback
- Styled modal dialogs for errors, confirmations and prompts
- Dark and light themes, switchable from the header toggle or the Settings menu
- Empty state shown before any friends are loaded

---

## 🎨 Interface

The UI is built entirely on the Python standard library — `tkinter`, `ttk` and `Canvas`. **No `customtkinter`, `ttkbootstrap`, `Pillow` or image assets are required**, so the app runs on a stock Python install with no network access.

### Design system

Colours are defined as semantic tokens (`surface`, `border`, `text`, `accent`, `danger`, `success`, …) rather than raw hex, so both themes come from the same token names and switching themes restyles the live window instantly — including the `Treeview`, entries, scrollbars and progress bar.

| | Dark (default) | Light |
|---|---|---|
| Background | `#0B0F1D` | `#EDF0F8` |
| Surface | `#131A2E` | `#FFFFFF` |
| Accent | `#2E6BE6` | `#2E6BE6` |

Type scale runs from an 8pt eyebrow to a 17pt display in Segoe UI (with a fallback chain), on a 4/8px spacing rhythm.

All foreground/background pairs meet **WCAG AA (4.5:1)** in both themes. Because a vivid blue cannot brighten on hover without dropping its white label below AA, buttons signal hover with a rim highlight instead of a large fill shift.

### Components

`Button` (4 variants), `InputField`, `ToggleSwitch`, `Badge`, `Card`, `Tooltip`, `Spinner`, `SlimScrollbar`, `EmptyState`, `LoadingOverlay`, `Toast` and `Modal` — all drawn on `Canvas` with hover, press and focus-ring states. Icons are vector shapes drawn in code, not image files.

### Project structure

```
PSN-Unfriender-Tool/
├── gui.py              # GUI application
├── unfriender.py       # PSN API + CLI
├── ui/
│   ├── theme.py        # Design tokens and the ttk stylesheet
│   ├── icons.py        # Canvas-drawn vector icons
│   └── widgets.py      # Component library
├── configuration.json  # Token and whitelist patterns
├── friend_notes.json   # Saved notes and tags
└── unfriender.log      # Action log
```

`python gui.py` remains the entry point, so `run_unfriender.bat` is unaffected.

---

## 📂 Export Formats

Supported formats:

- CSV
- JSON

Backups can be:

- Imported
- Compared
- Restored
- Audited

---

## 📜 Logging

Every action is recorded inside

```
unfriender.log
```

Including:

- Friends loaded
- Friends removed
- API errors
- Imports
- Exports

---

## 🚀 Advanced Features

<details>

<summary>View 100+ Features</summary>

- Mass friend removal
- GUI support
- CLI support
- Secure authentication
- Regex whitelist
- Exact-match whitelist
- Preview removals
- Friend search
- PSN ID search
- Custom tags
- Notes
- CSV export
- JSON export
- CSV import
- JSON import
- Backup creation
- Backup comparison
- Backup restoration
- Undo support
- Progress tracking
- Logging
- Batch operations
- Multi-select
- Drag & drop
- Right-click menus
- Dark mode
- Light mode
- Keyboard shortcuts
- Persistent settings
- Saved notes
- Saved tags
- Regex editor
- Duplicate prevention
- Configuration editor
- Portable
- Modular code
- Friendly error handling
- Export filtered friends
- Import settings
- Backup notes
- Backup tags
- Audit changes
- Multi-account support
- Reload friends
- Restore whitelist
- Cross-platform
- Windows
- macOS
- Linux
- Headless mode
- Large friend list support
- Fast performance
- Minimal dependencies
- Plugin-ready
- Future cloud backups
- Future update checker
- Future scheduling
- Future notifications
- Future API integrations
- Future custom themes
- Future export formats
- Future automation
- Open source
- MIT Licensed
- Easy to contribute
- Lightweight
- Easy maintenance
- Secure token handling
- Friend auditing
- Friend organisation
- Search by name
- Search by PSN ID
- Search by tags
- Search by notes
- Batch tagging
- Batch whitelist
- Configuration backups
- Data portability
- And much more...

</details>

---

## ❓ FAQ

### Where do I get my NPSSO token?

Visit

```
https://ca.account.sony.com/api/v1/ssocookie
```

after signing into your PlayStation account.

---

### Is my token safe?

Yes, as long as you keep it private.

Treat it exactly like your PlayStation password.

---

### Can I preview changes?

Yes.

You'll always see who will be removed before confirming.

---

### Can I stop a removal once it has started?

Yes. While a removal is running, the Unfriend button is replaced by a **Stop** button.

Stop takes effect immediately, even if the tool is mid-way through waiting out a rate limit. It finishes the single removal already in flight — an in-progress request can't be safely aborted — then halts and tells you how many were removed.

Be aware that **anything already removed stays removed.** Stop prevents further removals; it cannot undo the ones that already went through.

---

### Why did a large removal stop part-way through?

It shouldn't any more.

PSN rate-limits rapid bursts of removals. Previously the first rate-limit response aborted the entire batch, so a large run would stop with no report of who had actually been removed.

Now every request has a bounded timeout, rate limits and server errors are retried with backoff (honouring PSN's own `Retry-After`), removals are gently throttled to stay under the limit, and a single failure no longer kills the run. When a batch finishes with errors you get a summary of exactly who could not be removed — they stay on your friends list and can simply be queued again.

---

### Does "Select All" respect my search filter?

No — it deliberately selects your **entire** friends list.

Because rows hidden by a filter don't exist in the table at all, Select All clears the search and tag boxes first, then selects everything. This keeps the selection count and the visible rows in agreement, so what you see is always what's selected.

---

### What does "Undo Last Unfriend" actually do?

It adds the players you just removed to your whitelist, so a future run will not remove them again.

It **cannot re-add them as friends** — PSN requires a new friend request for that. Removing a friend is irreversible, which is why the confirmation dialog states the count and spells this out before you proceed.

---

### Will whitelisted friends be removed?

No.

Whitelist rules always take priority.

---

### Does it work on Windows, macOS and Linux?

Yes.

Any operating system capable of running Python 3.8+ is supported.

---

## 🗺️ Roadmap

- [ ] Redo support
- [ ] Automatic backups
- [ ] Scheduled cleanups
- [ ] Cloud backups
- [ ] Plugin system
- [ ] Update checker
- [ ] More themes
- [ ] Additional export formats
- [ ] Performance improvements

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push your branch.
5. Open a Pull Request.

Bug reports and feature requests are always appreciated.

---

## ⚠️ Disclaimer

PSN Unfriender is an independent open-source project.

It is **not affiliated with, endorsed by, or associated with Sony Interactive Entertainment or PlayStation**.

Use this software entirely at your own risk.

---

## 📄 License

Released under the MIT License.

See the `LICENSE` file for full details.

---

# ⭐ Support

If you find this project useful, please consider leaving a ⭐ on GitHub.

It helps others discover the project and supports future development.

Happy Gaming! 🎮