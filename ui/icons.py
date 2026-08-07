"""Vector icons drawn straight onto a tk.Canvas.

No image files and no PIL: every icon is a handful of lines, arcs and polygons
so the app runs from a stock Python install with nothing but tkinter. Each
function draws into `canvas` centred on (cx, cy) inside an s x s box and
returns the list of item ids it created, so callers can retag or delete them.

Signature: fn(canvas, cx, cy, s, color, width=2, **kw) -> [item_id, ...]
"""


def _w(s, width):
    """Scale the stroke a little with the icon so small icons stay crisp."""
    return max(1, min(width, round(s / 8)))


def download(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    h = s * 0.5
    ids = [
        c.create_line(cx, cy - h * 0.9, cx, cy + h * 0.25,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx - h * 0.45, cy - h * 0.2, cx, cy + h * 0.3,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx + h * 0.45, cy - h * 0.2, cx, cy + h * 0.3,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx - h * 0.8, cy + h * 0.75, cx + h * 0.8, cy + h * 0.75,
                      fill=color, width=lw, capstyle="round"),
    ]
    return ids


def upload(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    h = s * 0.5
    return [
        c.create_line(cx, cy + h * 0.35, cx, cy - h * 0.8,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx - h * 0.45, cy - h * 0.3, cx, cy - h * 0.85,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx + h * 0.45, cy - h * 0.3, cx, cy - h * 0.85,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx - h * 0.8, cy + h * 0.75, cx + h * 0.8, cy + h * 0.75,
                      fill=color, width=lw, capstyle="round"),
    ]


def table(c, cx, cy, s, color, width=2):
    """Spreadsheet / CSV glyph."""
    lw = _w(s, width)
    h = s * 0.42
    return [
        c.create_rectangle(cx - h, cy - h, cx + h, cy + h,
                           outline=color, width=lw),
        c.create_line(cx - h, cy - h * 0.25, cx + h, cy - h * 0.25,
                      fill=color, width=lw),
        c.create_line(cx - h, cy + h * 0.4, cx + h, cy + h * 0.4,
                      fill=color, width=lw),
        c.create_line(cx - h * 0.15, cy - h * 0.25, cx - h * 0.15, cy + h,
                      fill=color, width=lw),
    ]


def compare(c, cx, cy, s, color, width=2):
    """Two offset panes."""
    lw = _w(s, width)
    h = s * 0.38
    return [
        c.create_rectangle(cx - h * 1.15, cy - h * 1.15, cx + h * 0.35,
                           cy + h * 0.35, outline=color, width=lw),
        c.create_rectangle(cx - h * 0.35, cy - h * 0.35, cx + h * 1.15,
                           cy + h * 1.15, outline=color, width=lw),
    ]


def search(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    r = s * 0.3
    ox, oy = cx - s * 0.06, cy - s * 0.06
    return [
        c.create_oval(ox - r, oy - r, ox + r, oy + r, outline=color, width=lw),
        c.create_line(ox + r * 0.75, oy + r * 0.75, cx + s * 0.42, cy + s * 0.42,
                      fill=color, width=lw, capstyle="round"),
    ]


def tag(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    h = s * 0.42
    return [
        c.create_polygon(cx - h, cy - h, cx + h * 0.2, cy - h, cx + h,
                         cy, cx + h * 0.2, cy + h, cx - h, cy + h,
                         outline=color, fill="", width=lw, joinstyle="round"),
        c.create_oval(cx - h * 0.55, cy - h * 0.2, cx - h * 0.15, cy + h * 0.2,
                      outline=color, width=lw),
    ]


def refresh(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    r = s * 0.36
    a = s * 0.16
    return [
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=25, extent=290,
                     style="arc", outline=color, width=lw),
        c.create_polygon(cx + r * 0.75, cy - r * 0.95,
                         cx + r * 0.75 + a, cy - r * 0.95 + a * 0.2,
                         cx + r * 0.75 + a * 0.15, cy - r * 0.95 + a,
                         fill=color, outline=color),
    ]


def undo(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    r = s * 0.34
    return [
        c.create_arc(cx - r, cy - r * 0.7, cx + r, cy + r * 1.3,
                     start=20, extent=200, style="arc", outline=color, width=lw),
        c.create_line(cx - r, cy + r * 0.3, cx - r, cy - r * 0.45,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx - r, cy - r * 0.45, cx - r * 0.35, cy - r * 0.1,
                      fill=color, width=lw, capstyle="round"),
    ]


def trash(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    h = s * 0.4
    return [
        c.create_line(cx - h, cy - h * 0.55, cx + h, cy - h * 0.55,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx - h * 0.35, cy - h * 0.55, cx - h * 0.3, cy - h,
                      fill=color, width=lw),
        c.create_line(cx + h * 0.35, cy - h * 0.55, cx + h * 0.3, cy - h,
                      fill=color, width=lw),
        c.create_line(cx - h * 0.3, cy - h, cx + h * 0.3, cy - h,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx - h * 0.7, cy - h * 0.35, cx - h * 0.5, cy + h,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx + h * 0.7, cy - h * 0.35, cx + h * 0.5, cy + h,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx - h * 0.5, cy + h, cx + h * 0.5, cy + h,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx, cy - h * 0.3, cx, cy + h * 0.65,
                      fill=color, width=lw, capstyle="round"),
    ]


def check(c, cx, cy, s, color, width=2):
    lw = _w(s, width) + 1
    h = s * 0.36
    return [
        c.create_line(cx - h, cy + h * 0.05, cx - h * 0.25, cy + h * 0.8,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx - h * 0.25, cy + h * 0.8, cx + h, cy - h * 0.75,
                      fill=color, width=lw, capstyle="round"),
    ]


def cross(c, cx, cy, s, color, width=2):
    lw = _w(s, width) + 1
    h = s * 0.32
    return [
        c.create_line(cx - h, cy - h, cx + h, cy + h,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx + h, cy - h, cx - h, cy + h,
                      fill=color, width=lw, capstyle="round"),
    ]


def warning(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    h = s * 0.44
    return [
        c.create_polygon(cx, cy - h, cx + h, cy + h * 0.8, cx - h, cy + h * 0.8,
                         outline=color, fill="", width=lw, joinstyle="round"),
        c.create_line(cx, cy - h * 0.3, cx, cy + h * 0.2,
                      fill=color, width=lw, capstyle="round"),
        c.create_oval(cx - lw * 0.6, cy + h * 0.45, cx + lw * 0.6, cy + h * 0.45 + lw * 1.2,
                      fill=color, outline=color),
    ]


def info(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    r = s * 0.42
    return [
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=lw),
        c.create_line(cx, cy - r * 0.1, cx, cy + r * 0.5,
                      fill=color, width=lw, capstyle="round"),
        c.create_oval(cx - lw * 0.6, cy - r * 0.55, cx + lw * 0.6, cy - r * 0.55 + lw * 1.2,
                      fill=color, outline=color),
    ]


def moon(c, cx, cy, s, color, width=2):
    """Crescent, built as a filled disc with a bite taken out via a second arc."""
    r = s * 0.4
    return [
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=55, extent=250,
                     style="chord", fill=color, outline=color),
    ]


def sun(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    r = s * 0.2
    ids = [c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline=color)]
    import math
    for i in range(8):
        angle = math.radians(i * 45)
        x1 = cx + math.cos(angle) * r * 1.7
        y1 = cy + math.sin(angle) * r * 1.7
        x2 = cx + math.cos(angle) * r * 2.4
        y2 = cy + math.sin(angle) * r * 2.4
        ids.append(c.create_line(x1, y1, x2, y2, fill=color, width=lw,
                                 capstyle="round"))
    return ids


def users(c, cx, cy, s, color, width=2, fill=""):
    """Two overlapping person glyphs - the app's own mark."""
    lw = _w(s, width)
    ids = []
    # Back figure, offset right and slightly smaller.
    hr = s * 0.13
    ids.append(c.create_oval(cx + s * 0.08 - hr, cy - s * 0.26 - hr,
                             cx + s * 0.08 + hr, cy - s * 0.26 + hr,
                             outline=color, fill=fill or color, width=lw))
    ids.append(c.create_arc(cx - s * 0.10, cy - s * 0.06, cx + s * 0.40, cy + s * 0.40,
                            start=0, extent=180, style="chord",
                            outline=color, fill=fill or color, width=lw))
    # Front figure.
    hr = s * 0.16
    ids.append(c.create_oval(cx - s * 0.13 - hr, cy - s * 0.22 - hr,
                             cx - s * 0.13 + hr, cy - s * 0.22 + hr,
                             outline=color, fill=fill or color, width=lw))
    ids.append(c.create_arc(cx - s * 0.42, cy + s * 0.02, cx + s * 0.16, cy + s * 0.50,
                            start=0, extent=180, style="chord",
                            outline=color, fill=fill or color, width=lw))
    return ids


def shield(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    h = s * 0.44
    return [
        c.create_polygon(cx, cy - h, cx + h * 0.8, cy - h * 0.6,
                         cx + h * 0.8, cy + h * 0.15, cx, cy + h,
                         cx - h * 0.8, cy + h * 0.15, cx - h * 0.8, cy - h * 0.6,
                         outline=color, fill="", width=lw, joinstyle="round"),
    ]


def key(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    r = s * 0.17
    return [
        c.create_oval(cx - s * 0.38 - r, cy - r, cx - s * 0.38 + r, cy + r,
                      outline=color, width=lw),
        c.create_line(cx - s * 0.38 + r, cy, cx + s * 0.42, cy,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx + s * 0.20, cy, cx + s * 0.20, cy + s * 0.18,
                      fill=color, width=lw, capstyle="round"),
        c.create_line(cx + s * 0.38, cy, cx + s * 0.38, cy + s * 0.22,
                      fill=color, width=lw, capstyle="round"),
    ]


def note(c, cx, cy, s, color, width=2):
    lw = _w(s, width)
    h = s * 0.42
    return [
        c.create_rectangle(cx - h * 0.8, cy - h, cx + h * 0.8, cy + h,
                           outline=color, width=lw),
        c.create_line(cx - h * 0.45, cy - h * 0.4, cx + h * 0.45, cy - h * 0.4,
                      fill=color, width=lw),
        c.create_line(cx - h * 0.45, cy, cx + h * 0.45, cy,
                      fill=color, width=lw),
        c.create_line(cx - h * 0.45, cy + h * 0.4, cx + h * 0.1, cy + h * 0.4,
                      fill=color, width=lw),
    ]


def inbox(c, cx, cy, s, color, width=2):
    """Empty-state glyph: an open tray."""
    lw = _w(s, width)
    h = s * 0.4
    return [
        c.create_polygon(cx - h, cy - h * 0.8, cx + h, cy - h * 0.8,
                         cx + h, cy + h * 0.8, cx - h, cy + h * 0.8,
                         outline=color, fill="", width=lw, joinstyle="round"),
        c.create_line(cx - h, cy + h * 0.1, cx - h * 0.4, cy + h * 0.1,
                      fill=color, width=lw),
        c.create_line(cx - h * 0.4, cy + h * 0.1, cx - h * 0.2, cy + h * 0.4,
                      fill=color, width=lw),
        c.create_line(cx - h * 0.2, cy + h * 0.4, cx + h * 0.2, cy + h * 0.4,
                      fill=color, width=lw),
        c.create_line(cx + h * 0.2, cy + h * 0.4, cx + h * 0.4, cy + h * 0.1,
                      fill=color, width=lw),
        c.create_line(cx + h * 0.4, cy + h * 0.1, cx + h, cy + h * 0.1,
                      fill=color, width=lw),
    ]


ICONS = {
    "download": download,
    "upload": upload,
    "table": table,
    "compare": compare,
    "search": search,
    "tag": tag,
    "refresh": refresh,
    "undo": undo,
    "trash": trash,
    "check": check,
    "cross": cross,
    "warning": warning,
    "info": info,
    "moon": moon,
    "sun": sun,
    "users": users,
    "shield": shield,
    "key": key,
    "note": note,
    "inbox": inbox,
}


def draw(canvas, name, cx, cy, size, color, width=2, **kw):
    fn = ICONS.get(name)
    if fn is None:
        return []
    return fn(canvas, cx, cy, size, color, width, **kw)
