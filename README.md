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
- 🌙 Light & Dark themes
- 💻 Cross-platform support
- ⚡ Portable with minimal setup

---

## 📸 Screenshots

> Coming Soon

Add screenshots or animated GIFs here to showcase:

- Main Dashboard
- Friend List
- Whitelist Editor
- Backup Manager
- Dark Theme

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

- Python 3.8+
- Windows / macOS / Linux
- PlayStation Network account
- Internet connection

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

GUI Features:

- Load Friends
- Search Friends
- Filter Friends
- Edit Notes
- Edit Tags
- Manage Whitelist
- Import Backups
- Export Backups
- Compare Backups
- Dark Mode
- Progress Bar
- Confirmation Dialogs

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