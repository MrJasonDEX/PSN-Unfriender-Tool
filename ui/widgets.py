"""Canvas-drawn components for the PSN Unfriender UI.

ttk cannot give us rounded buttons, pill badges, a toggle switch, a slim
scrollbar or toasts, so those are drawn on tk.Canvas. Every widget here
subscribes to the Theme and redraws itself on a theme switch, and every
after() loop it starts is cancelled when the widget is destroyed - closing the
window must not leave callbacks firing into dead widgets.
"""

import math
import tkinter as tk
from tkinter import ttk

from . import icons
from .theme import RADIUS, SPACE, get_theme, mix


# --- geometry ---------------------------------------------------------------

def round_rect_points(x1, y1, x2, y2, r):
    """Corner points for a smoothed polygon that reads as a rounded rect."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r, x2, y1 + r, x2, y2 - r, x2, y2 - r,
        x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1,
    ]


def draw_round_rect(canvas, x1, y1, x2, y2, r, **kw):
    return canvas.create_polygon(round_rect_points(x1, y1, x2, y2, r),
                                 smooth=True, **kw)


# --- base -------------------------------------------------------------------

class ThemedCanvas(tk.Canvas):
    """A canvas that redraws itself whenever the theme mode changes."""

    def __init__(self, parent, **kw):
        kw.setdefault("highlightthickness", 0)
        kw.setdefault("borderwidth", 0)
        kw.setdefault("takefocus", 0)
        self.theme = get_theme()
        super().__init__(parent, **kw)
        self._unsubscribe = self.theme.subscribe(self._on_theme_change)
        self._after_ids = set()
        self.bind("<Destroy>", self._on_destroy, add="+")

    # after() bookkeeping so nothing fires into a destroyed widget ---------
    def after_tracked(self, ms, callback):
        def wrapped():
            self._after_ids.discard(handle)
            callback()
        handle = self.after(ms, wrapped)
        self._after_ids.add(handle)
        return handle

    def cancel_tracked(self, handle):
        if handle in self._after_ids:
            self._after_ids.discard(handle)
            try:
                self.after_cancel(handle)
            except tk.TclError:
                pass

    def cancel_all(self):
        for handle in list(self._after_ids):
            try:
                self.after_cancel(handle)
            except tk.TclError:
                pass
        self._after_ids.clear()

    def _on_destroy(self, event):
        if event.widget is not self:
            return
        self.cancel_all()
        self._unsubscribe()

    def _on_theme_change(self):
        self.theme = get_theme()
        self.invalidate_cache()
        self.redraw()

    def invalidate_cache(self):
        """Drop anything memoised from the *previous* palette.

        Widgets here are expected to resolve `self.theme[...]` live inside
        redraw(). Any subclass that instead caches a concrete hex string on the
        instance across redraws - typically because a colour animation writes
        interpolated values into it - MUST clear that cache here, and cancel
        the in-flight animation too: an animation started under the old palette
        keeps writing colours mixed from it, so clearing alone is not enough.
        """

    def redraw(self):  # pragma: no cover - overridden
        pass


# --- button -----------------------------------------------------------------

VARIANTS = {
    # variant -> (fill token, hover token, press token, fg token, border token)
    "primary": ("accent", "accent_hover", "accent_press", "accent_fg", None),
    "danger": ("danger", "danger_hover", "danger_press", "danger_fg", None),
    "secondary": ("surface_raised", "surface_hover", "surface_hover", "text", "border_strong"),
    "ghost": (None, "surface_hover", "surface_hover", "text_muted", None),
}


class Button(ThemedCanvas):
    """Rounded button with hover fade, press state and a keyboard focus ring.

    `bg_token` must name the token of whatever this button sits on, because a
    canvas has no transparency - the corners outside the rounded rect are
    painted with it.
    """

    def __init__(self, parent, text="", command=None, variant="primary",
                 icon=None, icon_only=False, height=34, radius=RADIUS["md"],
                 min_width=None, pad_x=14, font="body", bg_token="surface_raised",
                 tooltip=None, **kw):
        self.text = text
        self.command = command
        self.variant = variant if variant in VARIANTS else "primary"
        self.icon = icon
        self.icon_only = icon_only
        self.radius = radius
        self.pad_x = pad_x
        self.font_name = font
        self.bg_token = bg_token
        self._hover = False
        self._pressed = False
        self._focused = False
        self._disabled = False
        self._fade_handle = None
        self._current_fill = None

        theme = get_theme()
        width = self._measure(theme, height)
        if min_width:
            width = max(width, min_width)
        super().__init__(parent, width=width, height=height,
                         background=theme[bg_token], takefocus=1, **kw)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Return>", self._on_key_activate)
        self.bind("<space>", self._on_key_activate)
        self.bind("<Configure>", lambda e: self.redraw())

        self._tooltip = Tooltip(self, tooltip) if tooltip else None
        self.redraw()

    # -- theming -----------------------------------------------------------

    def invalidate_cache(self):
        """Force the fill to be re-resolved against the new palette.

        _current_fill holds a concrete hex - the hover fade interpolates into
        it - and redraw() only recomputes it when it is None. Without this, a
        theme switch repaints the button body in the *old* theme's colour while
        the canvas background and the label, which re-read tokens every draw,
        update correctly: the button ends up half-restyled.
        """
        if self._fade_handle is not None:
            # A fade started under the old palette would otherwise keep writing
            # mixes of two dead colours straight back into _current_fill.
            self.cancel_tracked(self._fade_handle)
            self._fade_handle = None
        self._current_fill = None

    # -- sizing ------------------------------------------------------------

    def _measure(self, theme, height):
        if self.icon_only:
            return height
        font = theme.font(self.font_name)
        width = font.measure(self.text) + self.pad_x * 2
        if self.icon:
            width += int(height * 0.45) + SPACE["sm"]
        return width

    def set_text(self, text):
        self.text = text
        self.configure(width=self._measure(self.theme, int(self["height"])))
        self.redraw()

    def set_enabled(self, enabled):
        self._disabled = not enabled
        self.configure(cursor="" if not enabled else "hand2")
        self.redraw()

    # -- colours -----------------------------------------------------------

    def _target_fill(self):
        t = self.theme
        fill_tok, hover_tok, press_tok, _fg, _border = VARIANTS[self.variant]
        if self._disabled:
            return t[fill_tok] if fill_tok else t[self.bg_token]
        if self._pressed:
            return t[press_tok]
        if self._hover:
            return t[hover_tok]
        return t[fill_tok] if fill_tok else t[self.bg_token]

    def _fg_color(self):
        t = self.theme
        _f, _h, _p, fg_tok, _b = VARIANTS[self.variant]
        color = t[fg_tok]
        if self._disabled:
            return mix(color, t[self.bg_token], 0.55)
        if self.variant == "ghost" and (self._hover or self._focused):
            return t["text"]
        return color

    # -- drawing -----------------------------------------------------------

    def redraw(self):
        t = self.theme
        self.configure(background=t[self.bg_token])
        self.delete("all")
        w = self.winfo_width() or int(self["width"])
        h = self.winfo_height() or int(self["height"])
        if w <= 1 or h <= 1:
            return

        if self._current_fill is None:
            self._current_fill = self._target_fill()
        fill = self._current_fill

        _f, _hv, _p, _fg, border_tok = VARIANTS[self.variant]
        if border_tok:
            outline = t[border_tok]
        elif self._hover and not self._pressed and not self._disabled:
            # Rim highlight. Filled buttons cannot brighten much on hover
            # without dropping the white label below AA contrast, so the hover
            # affordance is carried by the edge instead of the fill.
            outline = mix(fill, "#FFFFFF", 0.38)
        else:
            outline = fill

        # Focus ring sits just outside the button body.
        if self._focused and not self._disabled:
            draw_round_rect(self, 0.5, 0.5, w - 0.5, h - 0.5,
                            self.radius + 2, fill="", outline=t["accent_ring"],
                            width=2)
            inset = 3
        else:
            inset = 1

        draw_round_rect(self, inset, inset, w - inset, h - inset, self.radius,
                        fill=fill, outline=outline, width=1)

        fg = self._fg_color()
        icon_size = int(h * 0.5)
        if self.icon_only:
            icons.draw(self, self.icon, w / 2, h / 2, icon_size, fg)
        elif self.icon:
            font = t.font(self.font_name)
            text_w = font.measure(self.text)
            total = icon_size + SPACE["sm"] + text_w
            x = (w - total) / 2
            icons.draw(self, self.icon, x + icon_size / 2, h / 2, icon_size, fg)
            self.create_text(x + icon_size + SPACE["sm"], h / 2 + 1,
                             text=self.text, anchor="w", fill=fg, font=font)
        else:
            self.create_text(w / 2, h / 2 + 1, text=self.text, fill=fg,
                             font=t.font(self.font_name))

    # -- hover fade --------------------------------------------------------

    def _animate_to(self, target, steps=5, interval=16):
        """Cheap colour fade so hover feels soft instead of snapping."""
        if self._fade_handle is not None:
            self.cancel_tracked(self._fade_handle)
            self._fade_handle = None
        start = self._current_fill or target

        def step(i):
            self._current_fill = mix(start, target, i / steps)
            self.redraw()
            if i < steps:
                self._fade_handle = self.after_tracked(interval, lambda: step(i + 1))
            else:
                self._fade_handle = None
        step(1)

    # -- events ------------------------------------------------------------

    def _on_enter(self, _event):
        if self._disabled:
            return
        self._hover = True
        self.configure(cursor="hand2")
        self._animate_to(self._target_fill())

    def _on_leave(self, _event):
        self._hover = False
        self._pressed = False
        self._animate_to(self._target_fill())

    def _on_press(self, _event):
        if self._disabled:
            return
        self._pressed = True
        self.focus_set()
        self._current_fill = self._target_fill()
        self.redraw()

    def _on_release(self, event):
        if self._disabled or not self._pressed:
            return
        self._pressed = False
        self._animate_to(self._target_fill())
        # Only fire if the pointer is still inside - matches native behaviour.
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            if self.command:
                self.command()

    def _on_key_activate(self, _event):
        if not self._disabled and self.command:
            self.command()
        return "break"

    def _on_focus_in(self, _event):
        self._focused = True
        self.redraw()

    def _on_focus_out(self, _event):
        self._focused = False
        self.redraw()


class Tooltip:
    """Small delayed tooltip, used for icon-only buttons."""

    def __init__(self, widget, text, delay=550):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip = None
        self.handle = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")
        widget.bind("<Destroy>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self.handle = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self.handle is not None:
            try:
                self.widget.after_cancel(self.handle)
            except tk.TclError:
                pass
            self.handle = None

    def _show(self):
        if self.tip or not self.text:
            return
        t = get_theme()
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.configure(background=t["border_strong"])
        label = tk.Label(self.tip, text=self.text, background=t["surface_raised"],
                         foreground=t["text"], font=t.font("small"),
                         padx=8, pady=4, borderwidth=0)
        label.pack(padx=1, pady=1)
        self.tip.update_idletasks()
        self.tip.wm_geometry(f"+{x - self.tip.winfo_width() // 2}+{y}")

    def _hide(self, _event=None):
        self._cancel()
        if self.tip:
            try:
                self.tip.destroy()
            except tk.TclError:
                pass
            self.tip = None


# --- badge ------------------------------------------------------------------

TONES = {
    "keep": ("success_soft", "success_text", "success"),
    "remove": ("danger_soft", "danger_text", "danger"),
    "accent": ("accent_soft", "accent_text", "accent"),
    "neutral": ("surface_hover", "text_muted", "text_faint"),
    "warning": ("warning_soft", "warning_text", "warning"),
}


class Badge(ThemedCanvas):
    """Pill badge - a coloured dot, a label and a count."""

    def __init__(self, parent, label="", count=None, tone="neutral",
                 bg_token="surface_raised", height=26, dot=True, **kw):
        self.label = label
        self.count = count
        self.tone = tone if tone in TONES else "neutral"
        self.bg_token = bg_token
        self.dot = dot
        theme = get_theme()
        super().__init__(parent, width=self._measure(theme), height=height,
                         background=theme[bg_token], **kw)
        self.bind("<Configure>", lambda e: self.redraw())
        self.redraw()

    def _measure(self, theme):
        text = self._text()
        width = theme.font("small_strong").measure(text) + 24
        if self.dot:
            width += 12
        return width

    def _text(self):
        if self.count is None:
            return self.label
        return f"{self.label}  {self.count}" if self.label else str(self.count)

    def set(self, label=None, count=None, tone=None):
        if label is not None:
            self.label = label
        if count is not None:
            self.count = count
        if tone is not None:
            self.tone = tone if tone in TONES else self.tone
        self.configure(width=self._measure(self.theme))
        self.redraw()

    def redraw(self):
        t = self.theme
        self.configure(background=t[self.bg_token])
        self.delete("all")
        w = self.winfo_width() or int(self["width"])
        h = self.winfo_height() or int(self["height"])
        if w <= 1 or h <= 1:
            return
        bg_tok, fg_tok, dot_tok = TONES[self.tone]
        draw_round_rect(self, 1, 1, w - 1, h - 1, h / 2,
                        fill=t[bg_tok], outline=mix(t[bg_tok], t[dot_tok], 0.25),
                        width=1)
        x = 12
        if self.dot:
            r = 3.5
            self.create_oval(x - r, h / 2 - r, x + r, h / 2 + r,
                             fill=t[dot_tok], outline=t[dot_tok])
            x += 12
        self.create_text(x, h / 2 + 1, text=self._text(), anchor="w",
                         fill=t[fg_tok], font=t.font("small_strong"))


# --- containers -------------------------------------------------------------

class Card(tk.Frame):
    """Panel with a 1px border. Uses highlightthickness so it resizes cleanly."""

    def __init__(self, parent, token="surface_raised", border="border", **kw):
        self.token = token
        self.border_token = border
        theme = get_theme()
        kw.setdefault("highlightthickness", 1)
        super().__init__(parent, background=theme[token],
                         highlightbackground=theme[border],
                         highlightcolor=theme[border], **kw)
        self._unsubscribe = theme.subscribe(self._restyle)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _restyle(self):
        theme = get_theme()
        self.configure(background=theme[self.token],
                       highlightbackground=theme[self.border_token],
                       highlightcolor=theme[self.border_token])

    def _on_destroy(self, event):
        if event.widget is self:
            self._unsubscribe()


class ThemedFrame(tk.Frame):
    """Plain frame whose background follows a token."""

    def __init__(self, parent, token="surface", **kw):
        self.token = token
        theme = get_theme()
        super().__init__(parent, background=theme[token], **kw)
        self._unsubscribe = theme.subscribe(self._restyle)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _restyle(self):
        self.configure(background=get_theme()[self.token])

    def _on_destroy(self, event):
        if event.widget is self:
            self._unsubscribe()


class ThemedLabel(tk.Label):
    """Label bound to a background token and a foreground token."""

    def __init__(self, parent, text="", bg_token="surface_raised",
                 fg_token="text", font="body", **kw):
        self.bg_token = bg_token
        self.fg_token = fg_token
        self.font_name = font
        theme = get_theme()
        super().__init__(parent, text=text, background=theme[bg_token],
                         foreground=theme[fg_token], font=theme.font(font), **kw)
        self._unsubscribe = theme.subscribe(self._restyle)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _restyle(self):
        theme = get_theme()
        self.configure(background=theme[self.bg_token],
                       foreground=theme[self.fg_token],
                       font=theme.font(self.font_name))

    def _on_destroy(self, event):
        if event.widget is self:
            self._unsubscribe()


# --- input ------------------------------------------------------------------

class InputField(ThemedFrame):
    """Bordered input group: optional icon + ttk.Entry, with a 2-tone focus ring.

    The outer frame paints the halo, the inner frame paints the 1px border, and
    the ttk.Entry itself is borderless - that is the only way to get a focus
    ring that grows without the widget changing size.
    """

    def __init__(self, parent, textvariable, placeholder="", icon=None,
                 show=None, width=20, bg_token="surface_raised",
                 parent_token="surface_raised", **kw):
        self.parent_token = parent_token
        self.field_token = bg_token
        self.icon_name = icon
        self._focused = False
        super().__init__(parent, token=parent_token, highlightthickness=2,
                         **kw)
        theme = get_theme()
        self.configure(highlightbackground=theme[parent_token],
                       highlightcolor=theme[parent_token])

        self.inner = tk.Frame(self, background=theme[bg_token],
                              highlightthickness=1,
                              highlightbackground=theme["border"],
                              highlightcolor=theme["border"])
        self.inner.pack(fill=tk.BOTH, expand=True)

        if icon:
            self.icon_canvas = ThemedCanvas(self.inner, width=26, height=26,
                                            background=theme[bg_token])
            self.icon_canvas.redraw = self._draw_icon
            self.icon_canvas.pack(side=tk.LEFT, padx=(6, 0))
            self._draw_icon()
        else:
            self.icon_canvas = None

        self.entry = ttk.Entry(self.inner, textvariable=textvariable,
                               style="App.TEntry", width=width, show=show,
                               font=theme.font("body"))
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                        padx=(8 if not icon else 4, 8), pady=6)
        self.entry.bind("<FocusIn>", self._on_focus_in, add="+")
        self.entry.bind("<FocusOut>", self._on_focus_out, add="+")

    def _draw_icon(self):
        if not self.icon_canvas:
            return
        theme = get_theme()
        self.icon_canvas.configure(background=theme[self.field_token])
        self.icon_canvas.delete("all")
        color = theme["accent"] if self._focused else theme["text_faint"]
        icons.draw(self.icon_canvas, self.icon_name, 13, 13, 16, color)

    def _apply_border(self):
        """Paint the halo, the 1px border and the icon for the current state.

        One place resolves all four colours, so a theme switch and a focus
        change cannot drift apart.
        """
        theme = get_theme()
        if self._focused:
            halo, border = theme["accent_ring"], theme["accent"]
        else:
            halo, border = theme[self.parent_token], theme["border"]
        self.configure(highlightbackground=halo, highlightcolor=halo)
        self.inner.configure(background=theme[self.field_token],
                             highlightbackground=border, highlightcolor=border)
        self._draw_icon()

    def _restyle(self):
        super()._restyle()
        theme = get_theme()
        self.entry.configure(font=theme.font("body"))
        # Re-derive focus from Tk rather than assuming it was lost: switching
        # the theme does not move keyboard focus, so a focused field must keep
        # its ring instead of silently reverting to the resting border.
        try:
            self._focused = self.entry.focus_get() is self.entry
        except (KeyError, tk.TclError):
            self._focused = False
        self._apply_border()

    def _on_focus_in(self, _event):
        self._focused = True
        self._apply_border()

    def _on_focus_out(self, _event):
        self._focused = False
        self._apply_border()


# --- toggle switch ----------------------------------------------------------

class ToggleSwitch(ThemedCanvas):
    """Animated track + knob, with sun/moon icons. Used for the theme switch."""

    def __init__(self, parent, command=None, initial=True, width=54, height=28,
                 bg_token="bg", **kw):
        self.command = command
        self.on = initial
        self.bg_token = bg_token
        self._pos = 1.0 if initial else 0.0
        self._hover = False
        self._focused = False
        self._anim_handle = None
        theme = get_theme()
        super().__init__(parent, width=width, height=height,
                         background=theme[bg_token], takefocus=1, **kw)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Return>", self._on_click)
        self.bind("<space>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<FocusIn>", lambda e: (setattr(self, "_focused", True), self.redraw()))
        self.bind("<FocusOut>", lambda e: (setattr(self, "_focused", False), self.redraw()))
        self.redraw()

    def redraw(self):
        t = self.theme
        self.configure(background=t[self.bg_token])
        self.delete("all")
        w = int(self["width"])
        h = int(self["height"])
        pad = 3
        track_fill = mix(t["surface_raised"], t["accent"], self._pos * 0.85)
        if self._focused:
            draw_round_rect(self, 0.5, 0.5, w - 0.5, h - 0.5, h / 2,
                            fill="", outline=t["accent_ring"], width=2)
        draw_round_rect(self, pad, pad, w - pad, h - pad, (h - pad * 2) / 2,
                        fill=track_fill,
                        outline=mix(t["border_strong"], t["accent"], self._pos),
                        width=1)

        knob_r = (h - pad * 2) / 2 - 2
        travel = (w - pad * 2) - knob_r * 2 - 4
        cx = pad + 2 + knob_r + travel * self._pos
        cy = h / 2
        knob_color = t["accent_fg"] if self._pos > 0.5 else t["text_muted"]
        self.create_oval(cx - knob_r, cy - knob_r, cx + knob_r, cy + knob_r,
                         fill=knob_color, outline=knob_color)
        glyph = t["accent"] if self._pos > 0.5 else t["surface_raised"]
        if self._pos > 0.5:
            icons.moon(self, cx, cy, knob_r * 1.5, glyph)
        else:
            icons.sun(self, cx, cy, knob_r * 1.6, glyph, width=1)

    def _animate(self, target):
        if self._anim_handle is not None:
            self.cancel_tracked(self._anim_handle)
        steps = 7
        start = self._pos

        def step(i):
            # Ease-out so the knob decelerates into place.
            p = i / steps
            self._pos = start + (target - start) * (1 - (1 - p) ** 2)
            self.redraw()
            if i < steps:
                self._anim_handle = self.after_tracked(14, lambda: step(i + 1))
            else:
                self._pos = target
                self._anim_handle = None
                self.redraw()
        step(1)

    def _on_click(self, _event=None):
        self.focus_set()
        self.on = not self.on
        self._animate(1.0 if self.on else 0.0)
        if self.command:
            self.command(self.on)
        return "break"

    def set(self, on):
        if on == self.on:
            return
        self.on = on
        self._animate(1.0 if on else 0.0)

    def _on_enter(self, _e):
        self._hover = True
        self.configure(cursor="hand2")

    def _on_leave(self, _e):
        self._hover = False


# --- spinner ----------------------------------------------------------------

class Spinner(ThemedCanvas):
    """Indeterminate arc spinner. Only runs while it is actually visible."""

    def __init__(self, parent, size=26, bg_token="surface", width=3, **kw):
        self.size = size
        self.bg_token = bg_token
        self.stroke = width
        self.angle = 0
        self._running = False
        self._handle = None
        theme = get_theme()
        super().__init__(parent, width=size, height=size,
                         background=theme[bg_token], **kw)
        self.redraw()

    def redraw(self):
        t = self.theme
        self.configure(background=t[self.bg_token])
        self.delete("all")
        s = self.size
        pad = self.stroke + 1
        self.create_arc(pad, pad, s - pad, s - pad, start=0, extent=359.9,
                        style="arc", outline=mix(t[self.bg_token], t["accent"], 0.22),
                        width=self.stroke)
        self.create_arc(pad, pad, s - pad, s - pad, start=self.angle, extent=105,
                        style="arc", outline=t["accent"], width=self.stroke)

    def start(self):
        if self._running:
            return
        self._running = True
        self._tick()

    def _tick(self):
        if not self._running:
            return
        self.angle = (self.angle - 14) % 360
        self.redraw()
        self._handle = self.after_tracked(34, self._tick)

    def stop(self):
        self._running = False
        if self._handle is not None:
            self.cancel_tracked(self._handle)
            self._handle = None


# --- slim scrollbar ---------------------------------------------------------

class SlimScrollbar(ThemedCanvas):
    """Canvas scrollbar with the Treeview yscrollcommand/yview protocol.

    Hides itself when the content fits, which keeps the table edge clean.
    """

    def __init__(self, parent, command, width=10, bg_token="surface", **kw):
        self.command = command
        self.bg_token = bg_token
        self.first = 0.0
        self.last = 1.0
        self._hover = False
        self._drag_offset = None
        theme = get_theme()
        super().__init__(parent, width=width, background=theme[bg_token], **kw)
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    # Treeview calls this via yscrollcommand.
    def set(self, first, last):
        self.first, self.last = float(first), float(last)
        self.redraw()

    def _thumb_bounds(self):
        h = self.winfo_height()
        if h <= 1 or (self.first <= 0.0 and self.last >= 1.0):
            return None
        top = self.first * h
        height = max(28, (self.last - self.first) * h)
        top = min(top, h - height)
        return top, top + height

    def redraw(self):
        t = self.theme
        self.configure(background=t[self.bg_token])
        self.delete("all")
        bounds = self._thumb_bounds()
        if bounds is None:
            return
        w = int(self["width"])
        top, bottom = bounds
        inset = 2 if self._hover else 3
        color = t["accent"] if (self._hover or self._drag_offset is not None) \
            else t["scrollbar"]
        draw_round_rect(self, inset, top + 2, w - inset, bottom - 2,
                        (w - inset * 2) / 2, fill=color, outline=color)

    def _on_enter(self, _e):
        self._hover = True
        self.redraw()

    def _on_leave(self, _e):
        self._hover = False
        self.redraw()

    def _on_press(self, event):
        bounds = self._thumb_bounds()
        if bounds is None:
            return
        top, bottom = bounds
        if top <= event.y <= bottom:
            self._drag_offset = event.y - top
        else:
            # Click on the track: jump so the thumb centres on the pointer.
            h = self.winfo_height()
            span = self.last - self.first
            frac = max(0.0, min(1.0, (event.y / h) - span / 2))
            self.command("moveto", frac)
            self._drag_offset = (bottom - top) / 2
        self.redraw()

    def _on_drag(self, event):
        if self._drag_offset is None:
            return
        h = self.winfo_height()
        if h <= 1:
            return
        frac = max(0.0, min(1.0, (event.y - self._drag_offset) / h))
        self.command("moveto", frac)

    def _on_release(self, _event):
        self._drag_offset = None
        self.redraw()


# --- overlays: empty state / loading ---------------------------------------

class EmptyState(ThemedFrame):
    """Centred icon + headline + hint, shown over the table when it has no rows."""

    def __init__(self, parent, icon="inbox", title="", subtitle="",
                 token="surface", **kw):
        super().__init__(parent, token=token, **kw)
        theme = get_theme()
        self.icon_name = icon
        holder = ThemedFrame(self, token=token)
        holder.place(relx=0.5, rely=0.45, anchor="center")

        self.art = ThemedCanvas(holder, width=88, height=88,
                                background=theme[token])
        self.art.redraw = self._draw_art
        self.art.pack()
        self._draw_art()

        self.title_label = ThemedLabel(holder, text=title, bg_token=token,
                                       fg_token="text", font="title")
        self.title_label.pack(pady=(SPACE["md"], SPACE["xs"]))
        self.subtitle_label = ThemedLabel(holder, text=subtitle, bg_token=token,
                                          fg_token="text_muted", font="small",
                                          justify="center")
        self.subtitle_label.pack()

    def _draw_art(self):
        theme = get_theme()
        self.art.configure(background=theme[self.token])
        self.art.delete("all")
        draw_round_rect(self.art, 8, 8, 80, 80, RADIUS["lg"],
                        fill=mix(theme[self.token], theme["accent"], 0.10),
                        outline=mix(theme[self.token], theme["accent"], 0.22),
                        width=1)
        icons.draw(self.art, self.icon_name, 44, 44, 40,
                   mix(theme["text_faint"], theme["accent"], 0.4), width=2)

    def set_text(self, title, subtitle):
        self.title_label.configure(text=title)
        self.subtitle_label.configure(text=subtitle)


class LoadingOverlay(ThemedFrame):
    """Spinner + message shown over the table while the PSN fetch runs."""

    def __init__(self, parent, token="surface", **kw):
        super().__init__(parent, token=token, **kw)
        holder = ThemedFrame(self, token=token)
        holder.place(relx=0.5, rely=0.45, anchor="center")
        self.spinner = Spinner(holder, size=42, bg_token=token, width=4)
        self.spinner.pack()
        self.label = ThemedLabel(holder, text="Loading...", bg_token=token,
                                 fg_token="text", font="title")
        self.label.pack(pady=(SPACE["md"], SPACE["xs"]))
        self.hint = ThemedLabel(holder, text="", bg_token=token,
                                fg_token="text_muted", font="small")
        self.hint.pack()
        # Skeleton rows behind the spinner give the area some structure.
        self.skeleton = ThemedCanvas(self, background=get_theme()[token])
        self.skeleton.redraw = self._draw_skeleton
        self.skeleton.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.skeleton.bind("<Configure>", lambda e: self._draw_skeleton())
        holder.lift()
        self._holder = holder

    def _draw_skeleton(self):
        theme = get_theme()
        c = self.skeleton
        c.configure(background=theme[self.token])
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w <= 1:
            return
        tint = mix(theme[self.token], theme["text_faint"], 0.12)
        y = 14
        row = 0
        while y < h - 12:
            widths = (0.28, 0.10, 0.22, 0.14)
            x = 16
            for frac in widths:
                bar_w = (w - 32) * frac
                draw_round_rect(c, x, y, x + bar_w, y + 10, 5,
                                fill=tint, outline=tint)
                x += bar_w + 18
            y += 30
            row += 1
            if row > 40:
                break

    def start(self, message="Loading...", hint=""):
        self.label.configure(text=message)
        self.hint.configure(text=hint)
        self._draw_skeleton()
        self.spinner.start()
        self._holder.lift()

    def stop(self):
        self.spinner.stop()


# --- toasts -----------------------------------------------------------------

TOAST_TONES = {
    "info": ("accent", "info"),
    "success": ("success", "check"),
    "error": ("danger", "warning"),
    "warning": ("warning", "warning"),
}


class Toast(ThemedCanvas):
    """One toast. Slides in from the right, then slides back out."""

    WIDTH = 330

    def __init__(self, manager, message, tone="info", duration=3600):
        self.manager = manager
        self.message = message
        self.tone = tone if tone in TOAST_TONES else "info"
        self.duration = duration
        theme = get_theme()
        self._lines = self._wrap(theme, message)
        height = max(52, 26 + len(self._lines) * 18)
        super().__init__(manager.root, width=self.WIDTH, height=height,
                         background=theme["bg"])
        self.height = height
        self._offset = 1.0     # 1.0 = fully off-screen to the right
        self._dismissed = False
        self.bind("<Button-1>", lambda e: self.dismiss())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self._hover = False
        self._dismiss_handle = None
        self.redraw()

    def _wrap(self, theme, message, max_width=250):
        font = theme.font("small")
        lines = []
        for paragraph in str(message).split("\n"):
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            current = words[0]
            for word in words[1:]:
                if font.measure(current + " " + word) <= max_width:
                    current += " " + word
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        return lines[:4]

    def redraw(self):
        t = self.theme
        self.configure(background=t["bg"])
        self.delete("all")
        w, h = self.WIDTH, self.height
        color_tok, icon_name = TOAST_TONES[self.tone]
        accent = t[color_tok]
        body = t["surface_raised"]
        # Soft drop shadow: a second rounded rect offset by 2px.
        draw_round_rect(self, 4, 5, w - 2, h - 1, RADIUS["md"],
                        fill=mix(t["bg"], t["shadow"], 0.55), outline="")
        draw_round_rect(self, 3, 2, w - 3, h - 4, RADIUS["md"],
                        fill=body, outline=t["border_strong"], width=1)
        # Accent rail down the left edge.
        draw_round_rect(self, 3, 2, 9, h - 4, 3, fill=accent, outline=accent)
        icons.draw(self, icon_name, 28, h / 2, 18, accent)
        y = (h - len(self._lines) * 18) / 2 + 9
        for line in self._lines:
            self.create_text(48, y, text=line, anchor="w", fill=t["text"],
                             font=self.theme.font("small"))
            y += 18

    def _on_enter(self, _e):
        self._hover = True
        self.configure(cursor="hand2")

    def _on_leave(self, _e):
        self._hover = False

    def show(self, y):
        self.place(relx=1.0, x=int(self.WIDTH * self._offset) - SPACE["lg"],
                   y=y, anchor="ne")
        self._animate(0.0, then=self._schedule_dismiss)

    def move_to(self, y):
        self.place_configure(y=y)

    def _animate(self, target, then=None):
        steps = 8
        start = self._offset

        def step(i):
            p = i / steps
            self._offset = start + (target - start) * (1 - (1 - p) ** 3)
            try:
                self.place_configure(x=int(self.WIDTH * self._offset) - SPACE["lg"])
            except tk.TclError:
                return
            if i < steps:
                self.after_tracked(14, lambda: step(i + 1))
            elif then:
                then()
        step(1)

    def _schedule_dismiss(self):
        if self.duration:
            self._dismiss_handle = self.after_tracked(self.duration, self._maybe_dismiss)

    def _maybe_dismiss(self):
        # Hovering a toast keeps it around so it can actually be read.
        if self._hover:
            self._dismiss_handle = self.after_tracked(1200, self._maybe_dismiss)
        else:
            self.dismiss()

    def dismiss(self):
        if self._dismissed:
            return
        self._dismissed = True
        self._animate(1.15, then=self._destroy)

    def _destroy(self):
        self.manager.remove(self)
        try:
            self.destroy()
        except tk.TclError:
            pass


class ToastManager:
    """Stacks toasts up from the bottom-right corner of the window."""

    def __init__(self, root, bottom_margin=64):
        self.root = root
        self.bottom_margin = bottom_margin
        self.toasts = []

    def show(self, message, tone="info", duration=3600):
        toast = Toast(self, message, tone=tone, duration=duration)
        self.toasts.append(toast)
        self._layout(new=toast)
        return toast

    def remove(self, toast):
        if toast in self.toasts:
            self.toasts.remove(toast)
        self._layout()

    def _layout(self, new=None):
        # Newest at the bottom; older ones slide upward.
        height = self.root.winfo_height() or 700
        y = height - self.bottom_margin
        for toast in reversed(self.toasts):
            y -= toast.height + SPACE["sm"]
            if toast is new:
                toast.show(y)
            else:
                toast.move_to(y)

    def clear(self):
        for toast in list(self.toasts):
            toast.dismiss()


# --- modal ------------------------------------------------------------------

class Modal(tk.Toplevel):
    """Themed modal dialog. Replaces messagebox for anything routine.

    `buttons` is a list of (label, variant, value) - clicking one closes the
    dialog and makes `result` that value. Escape maps to `escape_value`.
    """

    def __init__(self, parent, title, message="", tone="info", icon=None,
                 buttons=(("OK", "primary", True),), escape_value=None,
                 details=None, prompt=None, prompt_initial="", width=460):
        theme = get_theme()
        super().__init__(parent, background=theme["surface"])
        self.theme = theme
        self.result = escape_value
        self.escape_value = escape_value
        self._prompt_var = tk.StringVar(value=prompt_initial) if prompt is not None else None

        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        self.configure(padx=0, pady=0)

        accent_tok = {"info": "accent", "success": "success",
                      "danger": "danger", "warning": "warning"}.get(tone, "accent")
        icon_name = icon or {"info": "info", "success": "check",
                             "danger": "warning", "warning": "warning"}.get(tone, "info")
        self._accent_tok = accent_tok
        self._icon_name = icon_name
        self._details_text = None

        # Accent rail across the top so tone reads instantly.
        rail = ThemedCanvas(self, height=4, background=theme[accent_tok])
        rail.pack(fill=tk.X)
        self._rail = rail

        body = ThemedFrame(self, token="surface")
        body.pack(fill=tk.BOTH, expand=True, padx=SPACE["xl"], pady=SPACE["xl"])

        head = ThemedFrame(body, token="surface")
        head.pack(fill=tk.X)

        art = ThemedCanvas(head, width=44, height=44, background=theme["surface"])
        art.pack(side=tk.LEFT, anchor="n", padx=(0, SPACE["md"]))
        self._art = art
        # Bind the draw to the canvas so the Theme's own broadcast repaints it;
        # both fills below are mix() results, which bake in two palette values.
        art.redraw = self._draw_art
        self._draw_art()

        text_col = ThemedFrame(head, token="surface")
        text_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ThemedLabel(text_col, text=title, bg_token="surface", fg_token="text",
                    font="title", anchor="w", justify="left").pack(fill=tk.X)
        if message:
            ThemedLabel(text_col, text=message, bg_token="surface",
                        fg_token="text_muted", font="body", anchor="w",
                        justify="left", wraplength=width - 120).pack(
                            fill=tk.X, pady=(SPACE["sm"], 0))

        if prompt is not None:
            ThemedLabel(body, text=prompt, bg_token="surface",
                        fg_token="text_muted", font="small", anchor="w").pack(
                            fill=tk.X, pady=(SPACE["lg"], SPACE["xs"]))
            field = InputField(body, self._prompt_var, icon="note", width=40,
                               parent_token="surface")
            field.pack(fill=tk.X)
            field.entry.bind("<Return>", lambda e: self._close(True))
            self.after(60, field.entry.focus_set)

        if details:
            wrap = Card(body, token="surface_sunken")
            wrap.pack(fill=tk.BOTH, expand=True, pady=(SPACE["lg"], 0))
            text = tk.Text(wrap, height=min(16, max(5, details.count("\n") + 2)),
                           width=52, wrap="word", relief="flat",
                           background=theme["surface_sunken"],
                           foreground=theme["text_muted"],
                           font=theme.font("mono"), borderwidth=0,
                           highlightthickness=0, padx=SPACE["md"],
                           pady=SPACE["md"], insertbackground=theme["text"])
            text.insert("1.0", details)
            text.configure(state="disabled")
            self._details_text = text
            scroll = SlimScrollbar(wrap, text.yview, bg_token="surface_sunken")
            text.configure(yscrollcommand=scroll.set)
            scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=SPACE["sm"])
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        footer = ThemedFrame(body, token="surface")
        footer.pack(fill=tk.X, pady=(SPACE["xl"], 0))
        first_button = None
        for label, variant, value in reversed(list(buttons)):
            btn = Button(footer, text=label, variant=variant,
                         bg_token="surface",
                         command=lambda v=value: self._close(v))
            btn.pack(side=tk.RIGHT, padx=(SPACE["sm"], 0))
            if first_button is None:
                first_button = btn

        self.bind("<Escape>", lambda e: self._close(self.escape_value))
        self.protocol("WM_DELETE_WINDOW", lambda: self._close(self.escape_value))

        # A modal grabs input, so the theme cannot normally change underneath
        # it - but nothing guarantees that, and the Toplevel background, rail,
        # art and details Text are all painted once at construction.
        self._unsubscribe = theme.subscribe(self._restyle)
        self.bind("<Destroy>", self._on_destroy, add="+")

        self.update_idletasks()
        self._centre_on(parent)
        try:
            self.grab_set()
        except tk.TclError:
            pass
        if prompt is None and first_button is not None:
            first_button.focus_set()

    def _draw_art(self):
        t = get_theme()
        self._art.configure(background=t["surface"])
        self._art.delete("all")
        draw_round_rect(self._art, 2, 2, 42, 42, RADIUS["md"],
                        fill=mix(t["surface"], t[self._accent_tok], 0.16),
                        outline=mix(t["surface"], t[self._accent_tok], 0.3),
                        width=1)
        icons.draw(self._art, self._icon_name, 22, 22, 22, t[self._accent_tok])

    def _restyle(self):
        t = get_theme()
        self.configure(background=t["surface"])
        self._rail.configure(background=t[self._accent_tok])
        self._draw_art()
        if self._details_text is not None:
            self._details_text.configure(background=t["surface_sunken"],
                                         foreground=t["text_muted"],
                                         insertbackground=t["text"])

    def _on_destroy(self, event):
        if event.widget is self:
            self._unsubscribe()

    def _centre_on(self, parent):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        try:
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            pw, ph = parent.winfo_width(), parent.winfo_height()
        except tk.TclError:
            px = py = 0
            pw = ph = 0
        if pw <= 1:
            pw, ph = self.winfo_screenwidth(), self.winfo_screenheight()
            px = py = 0
        self.geometry(f"+{px + (pw - w) // 2}+{py + max(0, (ph - h) // 3)}")

    def _close(self, value):
        self.result = value
        if self._prompt_var is not None and value:
            self.result = self._prompt_var.get()
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    # -- convenience --------------------------------------------------------

    @classmethod
    def alert(cls, parent, title, message, tone="info", details=None, icon=None):
        dialog = cls(parent, title, message, tone=tone, details=details,
                     icon=icon, buttons=(("Got it", "primary", True),),
                     escape_value=True)
        parent.wait_window(dialog)
        return dialog.result

    @classmethod
    def confirm(cls, parent, title, message, confirm_label="Confirm",
                tone="danger", details=None, icon=None):
        dialog = cls(parent, title, message, tone=tone, details=details,
                     icon=icon, escape_value=False,
                     buttons=(("Cancel", "secondary", False),
                              (confirm_label,
                               "danger" if tone == "danger" else "primary", True)))
        parent.wait_window(dialog)
        return bool(dialog.result)

    @classmethod
    def ask_string(cls, parent, title, prompt, initial="", message=""):
        """Themed replacement for simpledialog.askstring.

        Returns None when cancelled, so callers can still distinguish
        "cleared the note" from "changed nothing".
        """
        dialog = cls(parent, title, message, tone="info", icon="note",
                     prompt=prompt, prompt_initial=initial, escape_value=None,
                     buttons=(("Cancel", "secondary", None),
                              ("Save", "primary", True)))
        parent.wait_window(dialog)
        return dialog.result
