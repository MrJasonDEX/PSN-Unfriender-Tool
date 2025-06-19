# PSN Unfriender

- [Prerequisites](#prerequisites)
- [Run the script](#run-the-script)
- [Run the GUI](#run-the-gui)
- [Features](#features)
- [Configuration options](#configuration-options)

Python script and GUI to mass delete PSN friends.

---

## 100 Features/Things You Can Do With PSN Unfriender

1. Mass unfriend PlayStation Network friends.
2. Use a modern GUI for all actions.
3. Enter your NPSSO token securely.
4. Use regex patterns to whitelist friends.
5. Preview friends to keep/remove before unfriending.
6. Search friends by name.
7. Search friends by PSN ID.
8. Filter friends by custom tags/notes.
9. Export your friends list to CSV.
10. Export your friends list to JSON backup.
11. Import a friends list backup.
12. Compare two backups to see added/removed friends.
13. Add notes/tags to friends (e.g., "IRL", "trader").
14. Edit notes/tags for any friend.
15. Right-click to add a friend to the whitelist.
16. Right-click to move a friend between keep/remove.
17. Drag-and-drop to move friends between keep/remove.
18. Undo the last unfriend action (restore to whitelist).
19. Switch between light and dark GUI themes.
20. Progress bar for bulk unfriend operations.
21. Confirmation dialogs before unfriending.
22. Log all actions to a log file.
23. View a history of actions in `unfriender.log`.
24. See the number of friends to keep/remove.
25. See the total number of friends loaded.
26. Double-click to edit a friend's note/tag.
27. Save friend notes/tags in a persistent JSON file.
28. Use the GUI to update whitelist patterns.
29. Help menu with usage instructions.
30. About menu with project info.
31. Error handling with user-friendly messages.
32. Export only filtered friends to CSV/JSON.
33. Multi-select friends for batch actions.
34. Use keyboard navigation in the friends list.
35. Show friend PSN IDs in the GUI.
36. Show friend notes/tags in the GUI.
37. Backup/restore all friend notes/tags.
38. Use the GUI without editing JSON files manually.
39. Use the script in headless/CLI mode if preferred.
40. Support for up to 1000 friends per API call.
41. Modular code for easy extension.
42. Easily update whitelist from the GUI.
43. See which friends match whitelist patterns.
44. Add exact-match patterns with one click.
45. Avoid duplicate whitelist entries.
46. Export/import configuration files.
47. Use the GUI on Windows, Mac, or Linux.
48. Portable: no installation required, just Python.
49. Use a batch file to install and launch the app.
50. See API errors in the GUI/log.
51. Use the app with multiple PSN accounts (by changing token).
52. Quickly re-load friends after changes.
53. See which friends were just unfriended.
54. Restore friends to whitelist after accidental removal.
55. Use the GUI to manage large friend lists efficiently.
56. Use the GUI to manage small friend lists easily.
57. Add friends to whitelist by right-clicking.
58. Add friends to whitelist by dragging.
59. Add friends to whitelist by batch selection.
60. Edit whitelist patterns directly in the GUI.
61. Use regular expressions for advanced whitelisting.
62. Filter friends by any field (name, ID, tag).
63. Export logs for auditing.
64. Use the GUI to manage friend notes/tags.
65. See friend notes/tags in all exports.
66. Use the GUI to backup/restore all data.
67. Compare backups for auditing changes.
68. See a summary of changes after comparing backups.
69. Use the GUI to manage configuration.
70. Use the GUI to manage backups.
71. Use the GUI to manage logs.
72. Use the GUI to manage notes/tags.
73. Use the GUI to manage whitelist.
74. Use the GUI to manage friends.
75. Use the GUI to manage everything!
76. Use the GUI to undo mistakes.
77. Use the GUI to redo actions (future).
78. Use the GUI to schedule backups (future).
79. Use the GUI to schedule cleanups (future).
80. Use the GUI to send feedback (future).
81. Use the GUI to check for updates (future).
82. Use the GUI to customize themes (future).
83. Use the GUI to customize columns (future).
84. Use the GUI to customize exports (future).
85. Use the GUI to customize filters (future).
86. Use the GUI to customize actions (future).
87. Use the GUI to customize everything (future).
88. Use the GUI to integrate with other tools (future).
89. Use the GUI to integrate with cloud storage (future).
90. Use the GUI to integrate with notifications (future).
91. Use the GUI to integrate with plugins (future).
92. Use the GUI to integrate with scripts (future).
93. Use the GUI to integrate with APIs (future).
94. Use the GUI to integrate with web (future).
95. Use the GUI to integrate with mobile (future).
96. Use the GUI to integrate with desktop (future).
97. Use the GUI to integrate with everything (future).
98. Use the GUI to automate repetitive tasks (future).
99. Use the GUI to learn Python GUI programming.
100. Use the GUI to have fun managing your PSN friends!

---

## Prerequisites

- Python 3 ([Download](https://www.python.org/downloads/))
- [Playstation Network](https://www.playstation.com/) Account

## Run the script

:warning: **Treat the npsso token like your password!**

1. Rename the [configuration.example.json](configuration.example.json) file to `configuration.json`
2. Log into the [Playstation website](https://www.playstation.com/)
3. Visit this page: https://ca.account.sony.com/api/v1/ssocookie
4. Copy the npsso token and paste it in the `configuration.json` file
5. Install dependencies: `pip install -r requirements.txt`
6. Run the script `python unfriender.py`

## Run the GUI

1. Install dependencies: `pip install -r requirements.txt`
2. Run the GUI: `python gui.py`
3. Enter your NPSSO token and whitelist patterns (comma separated regex).
4. Click "Load Friends" to see your friends and which will be kept/removed.
5. Use the search bar to filter friends by name or ID.
6. Use the tag field to filter by notes/tags.
7. Right-click friends for more options.
8. Use the menu for help/about.
9. Export/import/compare backups as needed.
10. Click "Unfriend All To Remove" to remove the friends marked for removal.

## Configuration options

The only thing to configure is the friends you want to keep.  
To do this, a list of patterns can be specified in the `configuration.json` file.  

**Example:**  
If you want to keep all friends that have the word "Warrior" or "Wicked" somewhere in their name.  
This is case-sensitive!
```json
{
  "npsso_token": "YOUR TOKEN",
  "nameWhitelistPatterns": [
    ".*Warrior.*",
    ".*Wicked.*"
  ]
}
```
The output of the program then might look like this:
```
Found 12 friends

Friends to remove (9): 
FierceChampion42
MightyDragon99
RadiantPhoenix48
DaringSorcerer64
DaringTitan45
MysticNinja42
VividLegend82
DaringPhoenix41
VividSamurai69

Friends to keep (3): 
WickedNinja30
WickedDragon84
FierceWarrior92
```



