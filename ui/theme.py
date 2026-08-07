"""Design tokens and ttk styling for the PSN Unfriender UI.

Everything visual comes from one semantic token layer (surface / border / text /
accent / danger / success ...) so the dark and light themes are the *same* UI
with a different token table - never a pile of if-dark-then-black branches.

ttk widgets are restyled through ttk.Style on top of the "clam" theme, which is
the only built-in theme that honours custom fieldbackground, bordercolor and
element layouts. tk_setPalette is deliberately NOT used: it does not touch ttk
widgets at all, which is why the old Treeview stayed white in dark mode.

Canvas-drawn widgets cannot be restyled by ttk, so they subscribe() to the
Theme and redraw themselves when the mode changes.
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# --- spacing scale (4 / 8 rhythm) -------------------------------------------

SPACE = {
    "xxs": 2,
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

RADIUS = {"sm": 6, "md": 9, "lg": 14, "pill": 999}

# --- font stack -------------------------------------------------------------

UI_FONT_STACK = ("Segoe UI", "Segoe UI Variable Text", "Tahoma",
                 "DejaVu Sans", "Helvetica")
MONO_FONT_STACK = ("Consolas", "Cascadia Mono", "DejaVu Sans Mono", "Courier New")

# --- token tables -----------------------------------------------------------
# Deep indigo/navy foundation with a vivid blue accent. Palette mood only -
# no Sony marks, logos or trademarked assets anywhere in this app.

DARK = {
    "mode": "dark",
    "bg": "#0B0F1D",             # window background, deepest layer
    "surface": "#131A2E",        # panels / table body
    "surface_raised": "#1A2338",  # cards, toolbar
    "surface_hover": "#232E4A",
    "surface_sunken": "#0E1424",
    "border": "#26314E",
    "border_strong": "#38466C",
    "text": "#E9EDF9",
    "text_muted": "#98A4C4",
    "text_faint": "#818BA9",
    "accent": "#2E6BE6",
    # Only a slight lift: white button labels need the fill to stay dark enough
    # for AA (4.5:1), so hover is reinforced with a rim highlight in Button
    # rather than by brightening the fill further.
    "accent_hover": "#3370E9",
    "accent_press": "#2255BE",
    "accent_fg": "#FFFFFF",
    "accent_soft": "#17274B",
    "accent_ring": "#25457F",
    "accent_text": "#608FEC",
    # Deep enough that white button labels clear WCAG AA (4.9:1), which the
    # brighter #E5484D did not.
    "danger": "#CC3A41",
    "danger_hover": "#D2434A",
    "danger_press": "#A72A30",
    "danger_fg": "#FFFFFF",
    "danger_soft": "#37161C",
    "danger_text": "#FF8E90",
    "success": "#2CB67D",
    "success_soft": "#0F2E24",
    "success_text": "#5FDCA8",
    "warning": "#E8A33D",
    "warning_soft": "#33240F",
    "warning_text": "#F4C179",
    "table_header": "#1A2338",
    "row_keep": "#111A2A",
    "row_keep_alt": "#14202F",
    "row_remove": "#1C1622",
    "row_remove_alt": "#211826",
    "row_selected": "#26407E",
    "scrollbar": "#33406A",
    "shadow": "#05070E",
}

LIGHT = {
    "mode": "light",
    "bg": "#EDF0F8",
    "surface": "#FFFFFF",
    "surface_raised": "#FFFFFF",
    "surface_hover": "#E8EEFB",
    "surface_sunken": "#F4F6FC",
    "border": "#D5DCEE",
    "border_strong": "#B4BFDA",
    "text": "#121A2E",
    "text_muted": "#57648A",
    "text_faint": "#646B7F",
    "accent": "#2E6BE6",
    "accent_hover": "#1F5BD4",
    "accent_press": "#1A4CB2",
    "accent_fg": "#FFFFFF",
    "accent_soft": "#E1EAFD",
    "accent_ring": "#B9D0FA",
    "accent_text": "#2A61D1",
    "danger": "#D22B33",
    "danger_hover": "#BC2129",
    "danger_press": "#9E1A22",
    "danger_fg": "#FFFFFF",
    "danger_soft": "#FCE6E7",
    "danger_text": "#A81C24",
    "success": "#12855A",
    "success_soft": "#DCF4E9",
    "success_text": "#0B6544",
    "warning": "#B4700B",
    "warning_soft": "#FBEFD9",
    "warning_text": "#8C5606",
    # Distinct from `surface` so the table heading separates from the rows -
    # in light mode both surface and surface_raised are pure white.
    "table_header": "#F1F4FB",
    "row_keep": "#FFFFFF",
    "row_keep_alt": "#F5FAF7",
    "row_remove": "#FEF7F7",
    "row_remove_alt": "#FDF1F1",
    "row_selected": "#CFE0FD",
    "scrollbar": "#BCC6DE",
    "shadow": "#AEB7CC",
}


# --- colour maths -----------------------------------------------------------

def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def mix(color_a, color_b, t):
    """Blend two hex colours. t=0 -> color_a, t=1 -> color_b."""
    ra, ga, ba = hex_to_rgb(color_a)
    rb, gb, bb = hex_to_rgb(color_b)
    return rgb_to_hex((ra + (rb - ra) * t,
                       ga + (gb - ga) * t,
                       ba + (bb - ba) * t))


_ACTIVE = None


def get_theme():
    """The Theme instance for this process (widgets look themselves up)."""
    return _ACTIVE


class Theme:
    """Token table + ttk stylesheet + a redraw broadcast for canvas widgets."""

    def __init__(self, root, mode="dark"):
        global _ACTIVE
        _ACTIVE = self
        self.root = root
        self.mode = mode
        self.tokens = dict(DARK if mode == "dark" else LIGHT)
        self._subscribers = []
        self.style = ttk.Style(root)
        try:
            self.style.theme_use("clam")
        except tk.TclError:  # pragma: no cover - clam ships with every Tk
            pass
        self._build_fonts()
        self.apply()

    # -- tokens ------------------------------------------------------------

    def __getitem__(self, key):
        return self.tokens[key]

    def get(self, key, default=None):
        return self.tokens.get(key, default)

    @property
    def is_dark(self):
        return self.mode == "dark"

    # -- fonts -------------------------------------------------------------

    def _pick_family(self, stack, fallback):
        available = set(tkfont.families(self.root))
        for family in stack:
            if family in available:
                return family
        return fallback

    def _build_fonts(self):
        ui = self._pick_family(UI_FONT_STACK, "TkDefaultFont")
        mono = self._pick_family(MONO_FONT_STACK, "TkFixedFont")
        self.family = ui
        self.mono_family = mono
        # Type scale. Kept deliberately small - six steps is plenty for a
        # single-window tool, and more steps only invite inconsistency.
        self.fonts = {
            "display": tkfont.Font(family=ui, size=17, weight="bold"),
            "title": tkfont.Font(family=ui, size=12, weight="bold"),
            "subtitle": tkfont.Font(family=ui, size=10),
            "eyebrow": tkfont.Font(family=ui, size=8, weight="bold"),
            "body": tkfont.Font(family=ui, size=10),
            "body_strong": tkfont.Font(family=ui, size=10, weight="bold"),
            "small": tkfont.Font(family=ui, size=9),
            "small_strong": tkfont.Font(family=ui, size=9, weight="bold"),
            "micro": tkfont.Font(family=ui, size=8),
            "mono": tkfont.Font(family=mono, size=9),
        }

    def font(self, name):
        return self.fonts[name]

    # -- subscriptions -----------------------------------------------------

    def subscribe(self, callback):
        """Register a canvas widget's redraw. Returns an unsubscribe callable."""
        self._subscribers.append(callback)

        def unsubscribe():
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass
        return unsubscribe

    def _broadcast(self):
        for callback in list(self._subscribers):
            try:
                callback()
            except tk.TclError:
                # Widget went away between the destroy event and the redraw.
                self._subscribers.remove(callback)

    # -- mode switching ----------------------------------------------------

    def set_mode(self, mode):
        if mode == self.mode:
            return
        self.mode = mode
        self.tokens = dict(DARK if mode == "dark" else LIGHT)
        self.apply()
        self._broadcast()

    def toggle(self):
        self.set_mode("light" if self.is_dark else "dark")
        return self.mode

    # -- the stylesheet ----------------------------------------------------

    def apply(self):
        t = self.tokens
        s = self.style
        self.root.configure(background=t["bg"])

        # Classic tk widgets that still exist (menus, labels, frames) pick up
        # these defaults; ttk widgets are configured explicitly below.
        for pattern, value in (
            ("*Menu.background", t["surface_raised"]),
            ("*Menu.foreground", t["text"]),
            ("*Menu.activeBackground", t["accent"]),
            ("*Menu.activeForeground", t["accent_fg"]),
            ("*Menu.selectColor", t["accent"]),
            ("*Menu.relief", "flat"),
            ("*Menu.borderWidth", 0),
            ("*Menu.activeBorderWidth", 0),
            ("*TCombobox*Listbox.background", t["surface_raised"]),
            ("*TCombobox*Listbox.foreground", t["text"]),
            ("*TCombobox*Listbox.selectBackground", t["accent"]),
            ("*TCombobox*Listbox.selectForeground", t["accent_fg"]),
        ):
            self.root.option_add(pattern, value)

        s.configure(".",
                    background=t["surface"],
                    foreground=t["text"],
                    fieldbackground=t["surface"],
                    bordercolor=t["border"],
                    darkcolor=t["surface"],
                    lightcolor=t["surface"],
                    troughcolor=t["surface_sunken"],
                    focuscolor=t["accent"],
                    selectbackground=t["accent"],
                    selectforeground=t["accent_fg"],
                    insertcolor=t["text"],
                    font=self.fonts["body"])

        s.configure("TFrame", background=t["surface"])
        s.configure("TLabel", background=t["surface"], foreground=t["text"])
        s.configure("TSeparator", background=t["border"])

        # --- Entry ---------------------------------------------------------
        # Border is drawn by the wrapping InputField frame (so the focus ring
        # can be two-tone), hence borderwidth 0 here.
        s.configure("App.TEntry",
                    fieldbackground=t["surface_raised"],
                    foreground=t["text"],
                    insertcolor=t["text"],
                    bordercolor=t["surface_raised"],
                    lightcolor=t["surface_raised"],
                    darkcolor=t["surface_raised"],
                    borderwidth=0,
                    relief="flat",
                    padding=(2, 6))
        s.map("App.TEntry",
              fieldbackground=[("disabled", t["surface_sunken"])],
              foreground=[("disabled", t["text_faint"])])

        # --- Combobox ------------------------------------------------------
        s.configure("App.TCombobox",
                    fieldbackground=t["surface_raised"],
                    background=t["surface_raised"],
                    foreground=t["text"],
                    arrowcolor=t["text_muted"],
                    bordercolor=t["border"],
                    lightcolor=t["surface_raised"],
                    darkcolor=t["surface_raised"],
                    borderwidth=0,
                    padding=(6, 5))
        s.map("App.TCombobox",
              fieldbackground=[("readonly", t["surface_raised"])],
              arrowcolor=[("active", t["accent"])],
              bordercolor=[("focus", t["accent"])])

        # --- Progressbar ---------------------------------------------------
        s.configure("App.Horizontal.TProgressbar",
                    troughcolor=t["surface_sunken"],
                    background=t["accent"],
                    lightcolor=t["accent"],
                    darkcolor=t["accent"],
                    bordercolor=t["surface_sunken"],
                    borderwidth=0,
                    thickness=6)

        # --- Scrollbar (ttk fallback; the table uses the canvas one) --------
        s.configure("App.Vertical.TScrollbar",
                    background=t["scrollbar"],
                    troughcolor=t["surface"],
                    bordercolor=t["surface"],
                    lightcolor=t["scrollbar"],
                    darkcolor=t["scrollbar"],
                    arrowcolor=t["text_muted"],
                    borderwidth=0,
                    arrowsize=12)
        s.map("App.Vertical.TScrollbar",
              background=[("active", t["accent"])])

        # --- Treeview ------------------------------------------------------
        # Strip the sunken border clam draws around the tree area.
        try:
            s.layout("App.Treeview", [("App.Treeview.treearea",
                                       {"sticky": "nswe"})])
        except tk.TclError:
            s.layout("App.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        s.configure("App.Treeview",
                    background=t["surface"],
                    fieldbackground=t["surface"],
                    foreground=t["text"],
                    bordercolor=t["surface"],
                    lightcolor=t["surface"],
                    darkcolor=t["surface"],
                    borderwidth=0,
                    relief="flat",
                    rowheight=30,
                    font=self.fonts["body"])
        s.map("App.Treeview",
              background=[("selected", t["row_selected"])],
              foreground=[("selected", t["text"])])

        s.configure("App.Treeview.Heading",
                    background=t["table_header"],
                    foreground=t["text_muted"],
                    bordercolor=t["border"],
                    lightcolor=t["table_header"],
                    darkcolor=t["table_header"],
                    relief="flat",
                    borderwidth=0,
                    padding=(10, 9),
                    font=self.fonts["small_strong"])
        s.map("App.Treeview.Heading",
              background=[("active", t["surface_hover"])],
              foreground=[("active", t["text"])])

        # --- Menubutton / misc --------------------------------------------
        s.configure("App.TMenubutton",
                    background=t["surface_raised"],
                    foreground=t["text"],
                    arrowcolor=t["text_muted"],
                    borderwidth=0,
                    padding=(10, 6))

    # -- convenience for tk (non-ttk) widgets ------------------------------

    def style_menu(self, menu):
        """Apply tokens to a tk.Menu (dropdowns are Tk-drawn and honour these)."""
        menu.configure(background=self.tokens["surface_raised"],
                       foreground=self.tokens["text"],
                       activebackground=self.tokens["accent"],
                       activeforeground=self.tokens["accent_fg"],
                       activeborderwidth=0,
                       borderwidth=0,
                       relief="flat",
                       font=self.fonts["body"])
