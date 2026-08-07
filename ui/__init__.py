"""UI layer for the PSN Unfriender tool: design tokens, icons and widgets.

Pure tkinter/ttk - no third-party dependencies, no image files. `gui.py` is
still the entry point (`python gui.py`); this package only holds the
presentation pieces so gui.py can stay about behaviour.
"""

from .theme import RADIUS, SPACE, Theme, get_theme, mix  # noqa: F401

__all__ = ["Theme", "get_theme", "mix", "SPACE", "RADIUS"]
