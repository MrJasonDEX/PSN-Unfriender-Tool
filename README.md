# PSN Unfriender

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%2C%20macOS%2C%20Linux-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

---

**PSN Unfriender** is a modern Python script and GUI for managing your PlayStation Network friends list.  
Easily mass-unfriend, whitelist, tag, backup, and audit your friends — all with a user-friendly interface.

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Run the Script (CLI)](#run-the-script-cli)
  - [Run the GUI](#run-the-gui)
- [Configuration](#configuration)
- [FAQ](#faq)
- [License](#license)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

---

## Features

- Mass unfriend PlayStation Network friends
- Modern GUI and CLI support
- Enter your NPSSO token securely
- Regex patterns to whitelist friends
- Preview friends to keep/remove before unfriending
- Search/filter by name, PSN ID, or custom tags/notes
- Export/import friends list to CSV/JSON
- Compare backups to see added/removed friends
- Add/edit notes/tags for friends
- Undo last unfriend action (restore to whitelist)
- Light/dark GUI themes
- Progress bar and confirmation dialogs
- Full action logging (`unfriender.log`)
- Multi-select and batch actions
- Portable: no installation required, just Python

<details>
<summary>See 100 things you can do with PSN Unfriender</summary>

<!-- Keep your 100 features list here for completeness, but collapsed by default -->
<ol>
<li>Mass unfriend PlayStation Network friends.</li>
<li>Use a modern GUI for all actions.</li>
<li>Enter your NPSSO token securely.</li>
<li>Use regex patterns to whitelist friends.</li>
<li>Preview friends to keep/remove before unfriending.</li>
<li>Search friends by name.</li>
<li>Search friends by PSN ID.</li>
<li>Filter friends by custom tags/notes.</li>
<li>Export your friends list to CSV.</li>
<li>Export your friends list to JSON backup.</li>
<li>Import a friends list backup.</li>
<li>Compare two backups to see added/removed friends.</li>
<li>Add notes/tags to friends (e.g., "IRL", "trader").</li>
<li>Edit notes/tags for any friend.</li>
<li>Right-click to add a friend to the whitelist.</li>
<li>Right-click to move a friend between keep/remove.</li>
<li>Drag-and-drop to move friends between keep/remove.</li>
<li>Undo the last unfriend action (restore to whitelist).</li>
<li>Switch between light and dark GUI themes.</li>
<li>Progress bar for bulk unfriend operations.</li>
<li>Confirmation dialogs before unfriending.</li>
<li>Log all actions to a log file.</li>
<li>View a history of actions in <code>unfriender.log</code>.</li>
<li>See the number of friends to keep/remove.</li>
<li>See the total number of friends loaded.</li>
<li>Double-click to edit a friend's note/tag.</li>
<li>Save friend notes/tags in a persistent JSON file.</li>
<li>Use the GUI to update whitelist patterns.</li>
<li>Help menu with usage instructions.</li>
<li>About menu with project info.</li>
<li>Error handling with user-friendly messages.</li>
<li>Export only filtered friends to CSV/JSON.</li>
<li>Multi-select friends for batch actions.</li>
<li>Use keyboard navigation in the friends list.</li>
<li>Show friend PSN IDs in the GUI.</li>
<li>Show friend notes/tags in the GUI.</li>
<li>Backup/restore all friend notes/tags.</li>
<li>Use the GUI without editing JSON files manually.</li>
<li>Use the script in headless/CLI mode if preferred.</li>
<li>Support for up to 1000 friends per API call.</li>
<li>Modular code for easy extension.</li>
<li>Easily update whitelist from the GUI.</li>
<li>See which friends match whitelist patterns.</li>
<li>Add exact-match patterns with one click.</li>
<li>Avoid duplicate whitelist entries.</li>
<li>Export/import configuration files.</li>
<li>Use the GUI on Windows, Mac, or Linux.</li>
<li>Portable: no installation required, just Python.</li>
<li>Use a batch file to install and launch the app.</li>
<li>See API errors in the GUI/log.</li>
<li>Use the app with multiple PSN accounts (by changing token).</li>
<li>Quickly re-load friends after changes.</li>
<li>See which friends were just unfriended.</li>
<li>Restore friends to whitelist after accidental removal.</li>
<li>Use the GUI to manage large friend lists efficiently.</li>
<li>Use the GUI to manage small friend lists easily.</li>
<li>Add friends to whitelist by right-clicking.</li>
<li>Add friends to whitelist by dragging.</li>
<li>Add friends to whitelist by batch selection.</li>
<li>Edit whitelist patterns directly in the GUI.</li>
<li>Use regular expressions for advanced whitelisting.</li>
<li>Filter friends by any field (name, ID, tag).</li>
<li>Export logs for auditing.</li>
<li>Use the GUI to manage friend notes/tags.</li>
<li>See friend notes/tags in all exports.</li>
<li>Use the GUI to backup/restore all data.</li>
<li>Compare backups for auditing changes.</li>
<li>See a summary of changes after comparing backups.</li>
<li>Use the GUI to manage configuration.</li>
<li>Use the GUI to manage backups.</li>
<li>Use the GUI to manage logs.</li>
<li>Use the GUI to manage notes/tags.</li>
<li>Use the GUI to manage whitelist.</li>
<li>Use the GUI to manage friends.</li>
<li>Use the GUI to manage everything!</li>
<li>Use the GUI to undo mistakes.</li>
<li>Use the GUI to redo actions (future).</li>
<li>Use the GUI to schedule backups (future).</li>
<li>Use the GUI to schedule cleanups (future).</li>
<li>Use the GUI to send feedback (future).</li>
<li>Use the GUI to check for updates (future).</li>
<li>Use the GUI to customize themes (future).</li>
<li>Use the GUI to customize columns (future).</li>
<li>Use the GUI to customize exports (future).</li>
<li>Use the GUI to customize filters (future).</li>
<li>Use the GUI to customize actions (future).</li>
<li>Use the GUI to customize everything (future).</li>
<li>Use the GUI to integrate with other tools (future).</li>
<li>Use the GUI to integrate with cloud storage (future).</li>
<li>Use the GUI to integrate with notifications (future).</li>
<li>Use the GUI to integrate with plugins (future).</li>
<li>Use the GUI to integrate with scripts (future).</li>
<li>Use the GUI to integrate with APIs (future).</li>
<li>Use the GUI to integrate with web (future).</li>
<li>Use the GUI to integrate with mobile (future).</li>
<li>Use the GUI to integrate with desktop (future).</li>
<li>Use the GUI to integrate with everything (future).</li>
<li>Use the GUI to automate repetitive tasks (future).</li>
<li>Use the GUI to learn Python GUI programming.</li>
<li>Use the GUI to have fun managing your PSN friends!</li>
</ol>
</details>

---

## Screenshots

<!-- Add screenshots or animated GIFs here to showcase the GUI and core features -->
<!-- Example: -->
<!-- ![Main GUI](screenshots/main_gui.png) -->

---

## Prerequisites

- Python 3.8+ ([Download](https://www.python.org/downloads/))
- A [PlayStation Network](https://www.playstation.com/) account

---

## Installation

1. **Clone or download** this repository.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Copy the example configuration**:
   ```bash
   cp configuration.example.json configuration.json
   ```
4. **Get your NPSSO token**:
   - Log in at [PlayStation.com](https://www.playstation.com/)
   - Visit: https://ca.account.sony.com/api/v1/ssocookie
   - Copy the token and paste it into `configuration.json` under `"npsso_token"`.

---

## Usage

### Run the Script (CLI)

:warning: **Treat your NPSSO token like your password!**

```bash
python unfriender.py
```

- The script will show which friends will be kept or removed based on your whitelist patterns.
- Confirm before unfriending.

### Run the GUI

```bash
python gui.py
```

- Enter your NPSSO token and (optionally) whitelist patterns (comma separated regex).
- Click **Load Friends** to see your friends and which will be kept/removed.
- Use the search bar and tag field to filter friends.
- Right-click friends for more options.
- Export/import/compare backups as needed.
- Click **Unfriend All To Remove** to remove the friends marked for removal.

---

## Configuration

Edit `configuration.json` to set your NPSSO token and whitelist patterns.

**Example:**
```json
{
  "npsso_token": "YOUR_NPSSO_TOKEN_HERE",
  "nameWhitelistPatterns": [
    ".*Warrior.*",
    ".*Wicked.*"
  ]
}
```
- Regex patterns are case-sensitive.
- Friends matching whitelist patterns are kept and won’t be unfriended.

---

## FAQ

**Q: Where do I get my NPSSO token?**  
A: Log in at [PlayStation.com](https://www.playstation.com/), then visit https://ca.account.sony.com/api/v1/ssocookie and copy the token.

**Q: Is my NPSSO token safe?**  
A: Treat it like your password. Never share it publicly.

**Q: Will I accidentally unfriend people I want to keep?**  
A: No, if you add whitelist regex patterns correctly, those friends are protected. You can also preview before unfriending.

**Q: Can I use this on Windows/macOS/Linux?**  
A: Yes! As long as Python 3.8+ is installed, it works cross-platform.

---

## License

This project is licensed under the MIT License — see the LICENSE file for details.

---

## Roadmap

- [ ] Undo/redo actions in GUI
- [ ] Scheduled backups and cleanups
- [ ] Update notifications
- [ ] Plugin and API integrations
- [ ] Customizable GUI themes and filters
- [ ] Cloud backup support
- [ ] More export/import formats

---

## Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to your branch (`git push origin feature-name`)
5. Open a Pull Request

---

Happy managing your PSN friends! 🎮



