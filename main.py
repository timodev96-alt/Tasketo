import json
import os
import math
import random
import tkinter as tk
import platform
from tkinter import font as tkfont
from tkinter import messagebox
from datetime import datetime, date
import uuid

APP_TITLE = "Tasketo"
if platform.system() == "Windows":
    base_path = os.getenv('APPDATA')
    base_path = os.path.join(base_path, "Tasketo")
else:
    base_path = os.path.expanduser("~/.tasketo")
if not os.path.exists(base_path):
    os.makedirs(base_path)
DATA_FILE = os.path.join(base_path, "tasketo_data.json")

PRIORITIES = ["Low", "Medium", "High"]
PRIORITY_COLORS = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#ef4444"}
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

DEFAULT_CATEGORIES = ["Personal", "Work", "Shopping", "Health", "Other"]
CATEGORY_COLORS = {
    "Personal": "#6366f1",
    "Work": "#0ea5e9",
    "Shopping": "#ec4899",
    "Health": "#14b8a6",
    "Other": "#8b5cf6",
}

CONFETTI_COLORS = ["#f43f5e", "#f59e0b", "#10b981", "#3b82f6", "#a855f7", "#ec4899", "#22d3ee"]

# ---- Accent themes: pick a vibe ----
ACCENTS = [
    {"name": "Indigo",  "accent": "#6366f1", "hover": "#4f46e5", "glow": "#a5b4fc", "grad": "#312e81"},
    {"name": "Pink",    "accent": "#ec4899", "hover": "#db2777", "glow": "#f9a8d4", "grad": "#831843"},
    {"name": "Emerald", "accent": "#10b981", "hover": "#059669", "glow": "#6ee7b7", "grad": "#064e3b"},
    {"name": "Amber",   "accent": "#f59e0b", "hover": "#d97706", "glow": "#fde68a", "grad": "#78350f"},
    {"name": "Sky",     "accent": "#0ea5e9", "hover": "#0284c7", "glow": "#7dd3fc", "grad": "#0c4a6e"},
]

LIGHT_BASE = {
    "bg": "#f4f5f7", "surface": "#ffffff", "surface_alt": "#eef0f4",
    "text": "#1f2430", "text_dim": "#6b7280", "border": "#e2e4e9",
    "danger": "#ef4444", "done_text": "#9ca3af", "shadow": "#d7d9e0",
}
DARK_BASE = {
    "bg": "#0d0f14", "surface": "#171a23", "surface_alt": "#1f232f",
    "text": "#e7e9ee", "text_dim": "#8b90a0", "border": "#2b2f3d",
    "danger": "#f87171", "done_text": "#565b6b", "shadow": "#000000",
}


def gen_id():
    return uuid.uuid4().hex[:10]


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c))) for c in rgb)


def lerp_color(c1, c2, t):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex((r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t))


def rounded_rect_points(x1, y1, x2, y2, r):
    """Point list for a smooth rounded rectangle, for use with create_polygon(smooth=True)."""
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
             x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]


class Task:
    def __init__(self, text, category="Personal", priority="Medium",
                 due="", done=False, starred=False, created=None, task_id=None):
        self.id = task_id or gen_id()
        self.text = text
        self.category = category
        self.priority = priority
        self.due = due
        self.done = done
        self.starred = starred
        self.created = created or datetime.now().isoformat()

    def to_dict(self):
        return {"id": self.id, "text": self.text, "category": self.category,
                "priority": self.priority, "due": self.due, "done": self.done,
                "starred": self.starred, "created": self.created}

    @staticmethod
    def from_dict(d):
        return Task(d.get("text", ""), d.get("category", "Personal"),
                     d.get("priority", "Medium"), d.get("due", ""),
                     d.get("done", False), d.get("starred", False),
                     d.get("created"), d.get("id"))


class RoundedButton(tk.Canvas):
    """Flat pill button with a soft glow on hover."""

    def __init__(self, parent, text, command, bg, fg, hover_bg=None, glow=None,
                 width=90, height=34, radius=17, font=None):
        super().__init__(parent, width=width, height=height, bg=parent["bg"],
                          highlightthickness=0, bd=0, cursor="hand2")
        self.command = command
        self.bg_color = bg
        self.hover_color = hover_bg or bg
        self.fg_color = fg
        self.glow = glow
        self.width, self.height, self.radius = width, height, radius
        self.font = font or ("Segoe UI", 10, "bold")
        self.text = text
        self._draw(self.bg_color)
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self._draw(self.hover_color, True))
        self.bind("<Leave>", lambda e: self._draw(self.bg_color, False))

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        points = rounded_rect_points(x1, y1, x2, y2, r)
        return self.create_polygon(points, smooth=True, **kw)

    def _draw(self, color, hovered=False):
        self.delete("all")
        if hovered and self.glow:
            self._round_rect(0, 0, self.width, self.height, self.radius + 2,
                              fill=self.glow, outline="")
        self._round_rect(1, 1, self.width - 1, self.height - 1, self.radius, fill=color, outline="")
        self.create_text(self.width / 2, self.height / 2, text=self.text,
                          fill=self.fg_color, font=self.font)


class Tasketo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.title(f"{APP_TITLE}")
        self.geometry("900x720")
        self.minsize(740, 580)

        self.dark_mode = False
        self.accent_idx = 0
        self.tasks = []
        self.categories = list(DEFAULT_CATEGORIES)
        self.filter_mode = "All"
        self.search_text = ""
        self._last_deleted = None
        self._current_pct = 0.0

        self._load()
        self._rebuild_theme()
        self._build_fonts()
        self.configure(bg=self.theme["bg"])
        self._build_ui()
        self._refresh()

        self.bind("<Control-z>", lambda e: self._undo_delete())

    # ---------- theme ----------
    def _move_window(self, event):
        x = self.winfo_x() + (event.x - self._offsetx)
        y = self.winfo_y() + (event.y - self._offsety)
        self.geometry(f"+{x}+{y}")

    def _start_move(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def _close_app(self):
        self.destroy()
    def _rebuild_theme(self):
        base = DARK_BASE if self.dark_mode else LIGHT_BASE
        acc = ACCENTS[self.accent_idx]
        self.theme = dict(base)
        self.theme["accent"] = acc["accent"]
        self.theme["accent_hover"] = acc["hover"]
        self.theme["glow"] = acc["glow"]
        self.theme["grad"] = acc["grad"]
        self.accent_name = acc["name"]

    # ---------- persistence ----------
    def _load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.tasks = [Task.from_dict(d) for d in data.get("tasks", [])]
                self.categories = data.get("categories", DEFAULT_CATEGORIES)
                self.dark_mode = data.get("dark_mode", False)
                self.accent_idx = data.get("accent_idx", 0) % len(ACCENTS)
            except Exception:
                self.tasks = []
        else:
            self.tasks = [
                Task("Welcome to Tasketo! Double-click a task to edit it.", "Personal", "Medium"),
                Task("Tap the circle to check things off ✔", "Personal", "Low"),
                Task("Try the accent dots up top — pick your vibe 🎨", "Work", "High",
                     due=date.today().isoformat()),
            ]

    def _save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "tasks": [t.to_dict() for t in self.tasks],
                    "categories": self.categories,
                    "dark_mode": self.dark_mode,
                    "accent_idx": self.accent_idx,
                }, f, indent=2)
        except Exception as e:
            print("Save failed:", e)

    # ---------- fonts ----------
    def _build_fonts(self):
        self.f_logo = tkfont.Font(family="Segoe UI", size=22, weight="bold")
        self.f_tag = tkfont.Font(family="Segoe UI", size=9, weight="bold")
        self.f_h2 = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.f_body = tkfont.Font(family="Segoe UI", size=11)
        self.f_small = tkfont.Font(family="Segoe UI", size=9)
        self.f_strike = tkfont.Font(family="Segoe UI", size=11, overstrike=1)

    # ---------- UI ----------
    def _build_ui(self):
        t = self.theme

        # ===== Gradient hero header =====
        hero_h = 100
        self.hero = tk.Canvas(self, height=hero_h, highlightthickness=0, bd=0)
        self.hero.pack(fill="x")
        self.hero.bind("<ButtonPress-1>", lambda e: self.hero.bind("<B1-Motion>", self._move_window))
        self.hero.bind("<ButtonPress-1>", self._start_move)
        self.hero.bind("<B1-Motion>", self._move_window)        
        self.hero.tag_bind("close", "<Button-1>", lambda e: self._close_app())
        self.hero.bind("<Configure>", lambda e: self._paint_hero())

        # ===== Add-task card =====
        add_card = tk.Frame(self, bg=t["surface"], highlightbackground=t["border"],
                             highlightthickness=1)
        add_card.pack(fill="x", padx=24, pady=(16, 8))

        inner = tk.Frame(add_card, bg=t["surface"])
        inner.pack(fill="x", padx=16, pady=14)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(inner, textvariable=self.entry_var, font=self.f_body,
                               bg=t["surface_alt"], fg=t["text"], relief="flat",
                               insertbackground=t["text"])
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self._add_task())
        self._placeholder(self.entry, "What's the move? ✏️", t)

        self.cat_var = tk.StringVar(value=self.categories[0])
        cat_menu = tk.OptionMenu(inner, self.cat_var, *self.categories)
        self._style_optionmenu(cat_menu, t)
        cat_menu.pack(side="left", padx=4)
        self.cat_menu = cat_menu

        add_cat_btn = RoundedButton(inner, "+ Cat", self._prompt_add_category,
                                    bg=t["surface_alt"], fg=t["text"], hover_bg=t["border"],
                                    width=68, height=32, radius=16,
                                    font=("Segoe UI", 9, "bold"))
        add_cat_btn.pack(side="left", padx=(0, 4))

        self.pri_var = tk.StringVar(value="Medium")
        pri_menu = tk.OptionMenu(inner, self.pri_var, *PRIORITIES)
        self._style_optionmenu(pri_menu, t)
        pri_menu.pack(side="left", padx=4)

        self.due_var = tk.StringVar()
        due_entry = tk.Entry(inner, textvariable=self.due_var, width=11, font=self.f_small,
                              bg=t["surface_alt"], fg=t["text"], relief="flat",
                              insertbackground=t["text"])
        due_entry.pack(side="left", ipady=8, padx=4)
        self._placeholder(due_entry, "YYYY-MM-DD", t)
        self.due_entry = due_entry

        add_btn = RoundedButton(inner, "+ Add", self._add_task, bg=t["accent"], fg="#ffffff",
                                 hover_bg=t["accent_hover"], glow=t["glow"],
                                 width=90, height=36, radius=18)
        add_btn.pack(side="left", padx=(8, 0))

        # ===== Filter / search bar =====
        filt = tk.Frame(self, bg=t["bg"])
        filt.pack(fill="x", padx=24, pady=(4, 6))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(filt, textvariable=self.search_var, font=self.f_body,
                                 bg=t["surface"], fg=t["text"], relief="flat",
                                 insertbackground=t["text"], highlightthickness=1,
                                 highlightbackground=t["border"])
        search_entry.pack(side="left", fill="x", expand=True, ipady=6)
        self._placeholder(search_entry, "🔍 Search tasks…", t)
        search_entry.bind("<KeyRelease>", self._on_search)
        search_entry.bind("<Escape>", lambda e: self._clear_search(search_entry))
        self.search_entry = search_entry

        self.filter_buttons = {}
        for mode in ["All", "Today", "Starred", "Active", "Completed"]:
            b = tk.Label(filt, text=mode, font=self.f_small, bg=t["bg"], fg=t["text_dim"],
                         cursor="hand2", padx=10, pady=4)
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda e, m=mode: self._set_filter(m))
            self.filter_buttons[mode] = b

        self.sort_var = tk.StringVar(value="Priority")
        sort_menu = tk.OptionMenu(filt, self.sort_var, "Starred", "Priority", "Due Date", "Newest",
                                   command=lambda v: self._refresh())
        self._style_optionmenu(sort_menu, t, small=True)
        sort_menu.pack(side="left", padx=(6, 0))

        clear_btn = tk.Label(filt, text="Clear done", font=self.f_small, bg=t["bg"],
                             fg=t["text_dim"], cursor="hand2", padx=10, pady=4)
        clear_btn.pack(side="right", padx=2)
        clear_btn.bind("<Button-1>", lambda e: self._clear_completed())

        # ===== Task list =====
        list_container = tk.Frame(self, bg=t["bg"])
        list_container.pack(fill="both", expand=True, padx=24, pady=(0, 6))

        self.canvas = tk.Canvas(list_container, bg=t["bg"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.list_frame = tk.Frame(self.canvas, bg=t["bg"])

        self.list_frame.bind("<Configure>",
                              lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>",
                          lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>",
                              lambda e: self.canvas.yview_scroll(int(-e.delta / 40), "units"))

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # ===== Footer =====
        footer = tk.Frame(self, bg=t["bg"])
        footer.pack(fill="x", padx=24, pady=(0, 18))

        self.stats_label = tk.Label(footer, font=self.f_small, bg=t["bg"], fg=t["text_dim"])
        self.stats_label.pack(side="left")

        self.progress_bg = tk.Canvas(footer, height=10, bg=t["bg"], highlightthickness=0)
        self.progress_bg.pack(side="right", fill="x", expand=True, padx=(16, 0))
        self.progress_bg.bind("<Configure>", lambda e: self._paint_progress(self._current_pct))

        self._paint_hero()

    def _paint_hero(self):
        """Draws the header: gradient wash, glass shimmer, glowing logo badge,
        title with a drop shadow, a live status line, and a frosted control
        pill on the right holding the accent swatches + theme toggle."""
        c = self.hero
        c.delete("all")
        t = self.theme
        w = c.winfo_width() or 900
        h = 100
        c.configure(height=h, bg=t["grad"])

        shadow_tone = lerp_color(t["grad"], "#000000", 0.35)

        # ---- base gradient wash (deep -> accent), slightly eased ----
        steps = 72
        for i in range(steps):
            frac = i / steps
            color = lerp_color(t["grad"], t["accent"], frac ** 1.6)
            x0 = int(w * i / steps)
            x1 = int(w * (i + 1) / steps) + 1
            c.create_rectangle(x0, 0, x1, h, fill=color, outline="")

        # ---- diagonal "glass" shimmer sweeping across the banner ----
        shimmer_color = lerp_color(t["accent"], "#ffffff", 0.55)
        band_w = max(80, int(w * 0.22))
        bx = w * 0.32
        c.create_polygon(
            bx, -4, bx + band_w, -4, bx + band_w - 55, h + 4, bx - 55, h + 4,
            fill=shimmer_color, outline="", stipple="gray25"
        )

        # ---- crisp accent line along the bottom edge ----
        c.create_rectangle(0, h - 3, w, h, fill=t["accent"], outline="")

        # ---- logo badge: soft shadow + glow ring + core ----
        bx0, by0, br = 28, h / 2, 23
        c.create_oval(bx0 - br + 3, by0 - br + 5, bx0 + br + 3, by0 + br + 5,
                      fill=shadow_tone, outline="")
        c.create_oval(bx0 - br, by0 - br, bx0 + br, by0 + br, fill=t["glow"], outline="")
        c.create_oval(bx0 - br + 6, by0 - br + 6, bx0 + br - 6, by0 + br - 6,
                      fill=t["accent"], outline="")
        c.create_text(bx0, by0, text="⚡", font=("Segoe UI", 18, "bold"), fill="#ffffff")

        # ---- title with a subtle drop shadow for depth ----
        title_x = bx0 + br + 16
        c.create_text(title_x + 1, by0 - 14 + 1, text=APP_TITLE, font=self.f_logo,
                      fill=shadow_tone, anchor="w")
        c.create_text(title_x, by0 - 14, text=APP_TITLE, font=self.f_logo,
                      fill="#ffffff", anchor="w")

        active_count = len([x for x in self.tasks if not x.done])
        due_today = len([x for x in self.tasks if x.due == date.today().isoformat() and not x.done])
        done_count = len([x for x in self.tasks if x.done])
        status = (f"{active_count} active   ·   {due_today} due today   ·   "
                  f"🔥 {done_count} all-time   ·   {self.accent_name} mode")
        c.create_text(title_x, by0 + 15, text=status, font=self.f_small, fill="#f1f1ff", anchor="w")
        dot_r = 8
        dot_gap = 24
        n = len(ACCENTS)
        pad = 14
        pill_w = pad * 2 + (n - 1) * dot_gap + dot_r * 2 + 14 + 30
        pill_h = 44
        pill_x2 = w - 18
        pill_x1 = pill_x2 - pill_w
        pill_y1 = h / 2 - pill_h / 2
        pill_y2 = h / 2 + pill_h / 2

        panel_fill = lerp_color(t["grad"], "#ffffff", 0.16)
        c.create_polygon(rounded_rect_points(pill_x1, pill_y1, pill_x2, pill_y2, pill_h / 2),
                          smooth=True, fill=panel_fill, outline="", stipple="gray50")

        start_x = pill_x1 + pad + dot_r
        for i, acc in enumerate(ACCENTS):
            cx = start_x + i * dot_gap
            cy = h / 2
            is_active = i == self.accent_idx
            tag = f"swatch_{i}"
            if is_active:
                c.create_oval(cx - dot_r - 4, cy - dot_r - 4, cx + dot_r + 4, cy + dot_r + 4,
                              outline="#ffffff", width=2, tags=tag)
            c.create_oval(cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r,
                          fill=acc["accent"], outline="", tags=tag)
            c.tag_bind(tag, "<Button-1>", lambda e, idx=i: self._set_accent(idx))
            c.tag_bind(tag, "<Enter>", lambda e: c.configure(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda e: c.configure(cursor=""))

        sep_x = start_x + (n - 1) * dot_gap + dot_r + 12
        c.create_line(sep_x, pill_y1 + 9, sep_x, pill_y2 - 9,
                      fill=lerp_color(panel_fill, "#000000", 0.25))

        toggle_x = sep_x + 20
        c.create_text(toggle_x, h / 2, text="☀️" if self.dark_mode else "🌙",
                      font=("Segoe UI", 14), tags="theme_toggle")
        c.tag_bind("theme_toggle", "<Button-1>", lambda e: self._toggle_theme())
        c.tag_bind("theme_toggle", "<Enter>", lambda e: c.configure(cursor="hand2"))
        c.tag_bind("theme_toggle", "<Leave>", lambda e: c.configure(cursor=""))
        close_x = w - 40
        close_y = 30
        c.create_oval(close_x-12, close_y-12, close_x+12, close_y+12, fill=t["danger"], outline="")
        c.create_text(close_x, close_y, text="✕", fill="white", font=("Segoe UI", 10, "bold"), tags="close_btn")

        c.tag_bind("close_btn", "<Button-1>", lambda e: self._close_app())
        c.tag_bind("close_btn", "<Enter>", lambda e: c.configure(cursor="hand2"))
        c.tag_bind("close_btn", "<Leave>", lambda e: c.configure(cursor=""))

    def _set_accent(self, idx):
        self.accent_idx = idx
        self._save()
        self._rebuild_theme()
        self._rebuild_all()

    def _placeholder(self, widget, text, t):
        widget.config(fg=t["text_dim"])
        widget.insert(0, text)

        def on_focus_in(e):
            if widget.get() == text:
                widget.delete(0, tk.END)
                widget.config(fg=t["text"])

        def on_focus_out(e):
            if not widget.get():
                widget.insert(0, text)
                widget.config(fg=t["text_dim"])

        widget.bind("<FocusIn>", on_focus_in)
        widget.bind("<FocusOut>", on_focus_out)
        widget._placeholder_text = text

    def _real_value(self, widget):
        v = widget.get()
        return "" if v == getattr(widget, "_placeholder_text", None) else v

    def _style_optionmenu(self, menu, t, small=False):
        menu.config(bg=t["surface_alt"], fg=t["text"], relief="flat",
                     highlightthickness=0, activebackground=t["accent"],
                     activeforeground="#ffffff", font=self.f_small if small else self.f_body,
                     bd=0, padx=8, pady=4, cursor="hand2")
        menu["menu"].config(bg=t["surface"], fg=t["text"], activebackground=t["accent"],
                             activeforeground="#ffffff", relief="flat")

    # ---------- actions ----------
    def _add_task(self):
        text = self._real_value(self.entry).strip()
        if not text:
            self.entry.focus_set()
            return
        due = self._real_value(self.due_entry).strip()
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Invalid date", "Please use the format YYYY-MM-DD.")
                return
        task = Task(text, self.cat_var.get(), self.pri_var.get(), due)
        self.tasks.append(task)
        self.entry.delete(0, tk.END)
        self.entry.focus_set()
        self._save()
        self._refresh()

    def _toggle_done(self, task_id, widget=None):
        becoming_done = False
        for t in self.tasks:
            if t.id == task_id:
                t.done = not t.done
                becoming_done = t.done
        self._save()
        self._refresh()
        if becoming_done and widget is not None:
            self._celebrate(widget)

    def _delete_task(self, task_id):
        for i, t in enumerate(self.tasks):
            if t.id == task_id:
                self._last_deleted = (i, t)
                self.tasks.pop(i)
                break
        self._save()
        self._refresh()

    def _undo_delete(self):
        if self._last_deleted:
            idx, task = self._last_deleted
            self.tasks.insert(min(idx, len(self.tasks)), task)
            self._last_deleted = None
            self._save()
            self._refresh()

    def _celebrate(self, widget):
        """Little confetti burst near the checkbox that was just completed."""
        try:
            self.update_idletasks()
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() + widget.winfo_height() // 2
        except Exception:
            return
        size = 140
        pop = tk.Toplevel(self)
        pop.overrideredirect(True)
        try:
            pop.attributes("-topmost", True)
        except Exception:
            pass
        pop.geometry(f"{size}x{size}+{x - size // 2}+{y - size // 2}")
        bgc = self.theme["bg"]
        try:
            pop.configure(bg=bgc)
            pop.attributes("-transparentcolor", bgc)
        except Exception:
            pass
        cv = tk.Canvas(pop, width=size, height=size, bg=bgc, highlightthickness=0)
        cv.pack()
        cx, cy = size / 2, size / 2
        particles = []
        for _ in range(16):
            ang = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.0, 5.0)
            dx, dy = speed * math.cos(ang), speed * math.sin(ang)
            r = random.uniform(2.5, 4.5)
            item = cv.create_oval(cx - r, cy - r, cx + r, cy + r,
                                   fill=random.choice(CONFETTI_COLORS), outline="")
            particles.append([item, dx, dy])

        frame = [0]

        def step():
            frame[0] += 1
            for p in particles:
                cv.move(p[0], p[1], p[2])
                p[2] += 0.18
                p[1] *= 0.96
            if frame[0] < 20:
                pop.after(28, step)
            else:
                try:
                    pop.destroy()
                except Exception:
                    pass

        step()

    def _edit_task_inline(self, task):
        t = self.theme
        win = tk.Toplevel(self)
        win.title("Edit task")
        win.configure(bg=t["surface"])
        win.geometry("380x260")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        pad = {"padx": 16, "pady": 6}
        tk.Label(win, text="Task", bg=t["surface"], fg=t["text_dim"], font=self.f_small).pack(
            anchor="w", **pad)
        text_var = tk.StringVar(value=task.text)
        e = tk.Entry(win, textvariable=text_var, font=self.f_body, bg=t["surface_alt"],
                      fg=t["text"], relief="flat", insertbackground=t["text"])
        e.pack(fill="x", padx=16, ipady=6)
        e.focus_set()
        e.select_range(0, tk.END)

        row = tk.Frame(win, bg=t["surface"])
        row.pack(fill="x", **pad)
        tk.Label(row, text="Category", bg=t["surface"], fg=t["text_dim"], font=self.f_small).pack(
            side="left")
        cat_var = tk.StringVar(value=task.category)
        cm = tk.OptionMenu(row, cat_var, *self.categories)
        self._style_optionmenu(cm, t, small=True)
        cm.pack(side="left", padx=8)

        pri_var = tk.StringVar(value=task.priority)
        pm = tk.OptionMenu(row, pri_var, *PRIORITIES)
        self._style_optionmenu(pm, t, small=True)
        pm.pack(side="left", padx=4)

        row2 = tk.Frame(win, bg=t["surface"])
        row2.pack(fill="x", **pad)
        tk.Label(row2, text="Due (YYYY-MM-DD)", bg=t["surface"], fg=t["text_dim"],
                 font=self.f_small).pack(side="left")
        due_var = tk.StringVar(value=task.due)
        de = tk.Entry(row2, textvariable=due_var, width=12, font=self.f_small,
                      bg=t["surface_alt"], fg=t["text"], relief="flat",
                      insertbackground=t["text"])
        de.pack(side="left", padx=8)

        def save_and_close():
            new_due = due_var.get().strip()
            if new_due:
                try:
                    datetime.strptime(new_due, "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Invalid date", "Please use the format YYYY-MM-DD.")
                    return
            task.text = text_var.get().strip() or task.text
            task.category = cat_var.get()
            task.priority = pri_var.get()
            task.due = new_due
            self._save()
            self._refresh()
            win.destroy()

        btn_row = tk.Frame(win, bg=t["surface"])
        btn_row.pack(fill="x", pady=14)
        RoundedButton(btn_row, "Save", save_and_close, bg=t["accent"], fg="#fff",
                      hover_bg=t["accent_hover"], glow=t["glow"], width=100, height=34).pack(
            side="right", padx=16)
        RoundedButton(btn_row, "Cancel", win.destroy, bg=t["surface_alt"], fg=t["text"],
                      hover_bg=t["border"], width=90, height=34).pack(side="right")

    def _prompt_add_category(self):
        t = self.theme
        win = tk.Toplevel(self)
        win.title("Add category")
        win.configure(bg=t["surface"])
        win.geometry("320x140")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="New category", bg=t["surface"], fg=t["text_dim"], font=self.f_small).pack(
            anchor="w", padx=16, pady=(16, 4))
        cat_var = tk.StringVar()
        entry = tk.Entry(win, textvariable=cat_var, font=self.f_body, bg=t["surface_alt"],
                         fg=t["text"], relief="flat", insertbackground=t["text"])
        entry.pack(fill="x", padx=16, ipady=6)
        entry.focus_set()

        def save_cat():
            name = cat_var.get().strip()
            if not name:
                return
            if name not in self.categories:
                self.categories.append(name)
                self._update_category_menu()
                self.cat_var.set(name)
                self._save()
            win.destroy()

        row = tk.Frame(win, bg=t["surface"])
        row.pack(fill="x", pady=16, padx=16)
        RoundedButton(row, "Save", save_cat, bg=t["accent"], fg="#fff",
                      hover_bg=t["accent_hover"], glow=t["glow"], width=90, height=34).pack(
            side="right", padx=4)
        RoundedButton(row, "Cancel", win.destroy, bg=t["surface_alt"], fg=t["text"],
                      hover_bg=t["border"], width=90, height=34).pack(side="right")

    def _update_category_menu(self):
        if not hasattr(self, "cat_menu"):
            return
        menu = self.cat_menu["menu"]
        menu.delete(0, "end")
        for cat in self.categories:
            menu.add_command(label=cat, command=lambda value=cat: self.cat_var.set(value))

    def _clear_completed(self):
        if not any(t.done for t in self.tasks):
            return
        if not messagebox.askyesno("Clear completed tasks", "Delete all completed tasks?"):
            return
        self.tasks = [t for t in self.tasks if not t.done]
        self._save()
        self._refresh()

    def _toggle_star(self, task_id):
        for t in self.tasks:
            if t.id == task_id:
                t.starred = not t.starred
        self._save()
        self._refresh()

    def _on_search(self, event=None):
        val = self._real_value(self.search_entry)
        self.search_text = val.lower().strip()
        self._refresh()

    def _clear_search(self, widget):
        widget.delete(0, tk.END)
        widget.focus_set()
        self.search_text = ""
        self._refresh()

    def _set_filter(self, mode):
        self.filter_mode = mode
        self._refresh()

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._save()
        self._rebuild_theme()
        self._rebuild_all()

    def _rebuild_all(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg=self.theme["bg"])
        self._build_ui()
        self._refresh()

    # ---------- rendering ----------
    def _visible_tasks(self):
        tasks = list(self.tasks)
        if self.filter_mode == "Active":
            tasks = [t for t in tasks if not t.done]
        elif self.filter_mode == "Completed":
            tasks = [t for t in tasks if t.done]
        elif self.filter_mode == "Today":
            today = date.today().isoformat()
            tasks = [t for t in tasks if t.due == today and not t.done]
        elif self.filter_mode == "Starred":
            tasks = [t for t in tasks if t.starred]
        if self.search_text:
            tasks = [t for t in tasks if self.search_text in t.text.lower()
                     or self.search_text in t.category.lower()]

        sort_mode = self.sort_var.get() if hasattr(self, "sort_var") else "Priority"
        if sort_mode == "Starred":
            tasks.sort(key=lambda t: (t.done, not t.starred,
                                      PRIORITY_ORDER.get(t.priority, 1), t.created))
        elif sort_mode == "Priority":
            tasks.sort(key=lambda t: (t.done, PRIORITY_ORDER.get(t.priority, 1)))
        elif sort_mode == "Due Date":
            tasks.sort(key=lambda t: (t.done, t.due == "", t.due))
        else:
            tasks.sort(key=lambda t: (t.done, t.created))
        return tasks

    def _refresh(self):
        t = self.theme
        for child in self.list_frame.winfo_children():
            child.destroy()

        for mode, lbl in self.filter_buttons.items():
            if mode == self.filter_mode:
                lbl.config(bg=t["accent"], fg="#ffffff")
            else:
                lbl.config(bg=t["bg"], fg=t["text_dim"])

        visible = self._visible_tasks()
        if not visible:
            empty = tk.Label(self.list_frame, text="✨  Nothing here — enjoy the calm!",
                              font=self.f_body, bg=t["bg"], fg=t["text_dim"], pady=40)
            empty.pack(fill="x")
        else:
            for task in visible:
                self._render_row(task)

        total = len(self.tasks)
        done = len([x for x in self.tasks if x.done])
        starred = len([x for x in self.tasks if x.starred])
        pct = (done / total * 100) if total else 0
        self.stats_label.config(text=f"{done}/{total} completed  ·  {starred} starred  ·  {int(pct)}%")
        self._animate_progress(pct)
        self._paint_hero()

    def _animate_progress(self, target):
        diff = target - self._current_pct
        if abs(diff) < 0.6:
            self._current_pct = target
            self._paint_progress(target)
            return
        self._current_pct += diff * 0.25
        self._paint_progress(self._current_pct)
        self.after(16, lambda: self._animate_progress(target))

    def _paint_progress(self, pct):
        self.progress_bg.delete("all")
        w = self.progress_bg.winfo_width() or 400
        h = 10
        t = self.theme
        self.progress_bg.create_rectangle(0, 0, w, h, fill=t["surface_alt"], outline="")
        fill_w = max(0, int(w * pct / 100))
        if fill_w:
            # soft glow behind the fill
            self.progress_bg.create_rectangle(0, -2, fill_w, h + 2, fill=t["glow"], outline="")
            self.progress_bg.create_rectangle(0, 0, fill_w, h, fill=t["accent"], outline="")

    def _render_row(self, task):
        t = self.theme
        overdue = False
        if task.due and not task.done:
            try:
                overdue = datetime.strptime(task.due, "%Y-%m-%d").date() < date.today()
            except ValueError:
                overdue = False

        # shadow layer for a floating-card feel
        wrapper = tk.Frame(self.list_frame, bg=t["bg"])
        wrapper.pack(fill="x", pady=5)
        shadow = tk.Frame(wrapper, bg=t["shadow"])
        shadow.place(x=3, y=3, relwidth=1, relheight=1)

        card = tk.Frame(wrapper, bg=t["surface"], highlightbackground=t["border"],
                         highlightthickness=1)
        card.pack(fill="x")

        def on_enter(e):
            card.config(highlightbackground=t["accent"], highlightthickness=2)

        def on_leave(e):
            card.config(highlightbackground=t["border"], highlightthickness=1)

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        strip = tk.Frame(card, bg=PRIORITY_COLORS.get(task.priority, t["border"]), width=5)
        strip.pack(side="left", fill="y")

        body = tk.Frame(card, bg=t["surface"])
        body.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        top_row = tk.Frame(body, bg=t["surface"])
        top_row.pack(fill="x")

        chk = tk.Canvas(top_row, width=22, height=22, bg=t["surface"], highlightthickness=0,
                         cursor="hand2")
        color = t["accent"] if task.done else t["border"]
        chk.create_oval(3, 3, 19, 19, outline=color, width=2, fill=t["accent"] if task.done else "")
        if task.done:
            chk.create_line(7, 11, 10, 15, 15, 6, fill="#ffffff", width=2)
        chk.pack(side="left", padx=(0, 10))
        chk.bind("<Button-1>", lambda e, w=chk: self._toggle_done(task.id, w))

        star_lbl = tk.Label(top_row, text="★" if task.starred else "☆",
                             font=("Segoe UI", 12), bg=t["surface"],
                             fg=t["accent"] if task.starred else t["text_dim"],
                             cursor="hand2")
        star_lbl.pack(side="left", padx=(0, 6))
        star_lbl.bind("<Button-1>", lambda e, task_id=task.id: self._toggle_star(task_id))

        label_font = self.f_strike if task.done else self.f_body
        label_fg = t["done_text"] if task.done else t["text"]
        lbl = tk.Label(top_row, text=task.text, font=label_font, bg=t["surface"], fg=label_fg,
                        anchor="w", justify="left", wraplength=440)
        lbl.pack(side="left", fill="x", expand=True)
        lbl.bind("<Double-Button-1>", lambda e: self._edit_task_inline(task))

        del_btn = tk.Label(top_row, text="🗑", font=self.f_small, bg=t["surface"],
                            fg=t["text_dim"], cursor="hand2")
        del_btn.pack(side="right", padx=4)
        del_btn.bind("<Button-1>", lambda e: self._delete_task(task.id))
        del_btn.bind("<Enter>", lambda e: del_btn.config(fg=t["danger"]))
        del_btn.bind("<Leave>", lambda e: del_btn.config(fg=t["text_dim"]))

        edit_btn = tk.Label(top_row, text="✎", font=self.f_small, bg=t["surface"],
                             fg=t["text_dim"], cursor="hand2")
        edit_btn.pack(side="right", padx=4)
        edit_btn.bind("<Button-1>", lambda e: self._edit_task_inline(task))
        edit_btn.bind("<Enter>", lambda e: edit_btn.config(fg=t["accent"]))
        edit_btn.bind("<Leave>", lambda e: edit_btn.config(fg=t["text_dim"]))

        meta = tk.Frame(body, bg=t["surface"])
        meta.pack(fill="x", pady=(6, 0), padx=(32, 0))

        cat_color = CATEGORY_COLORS.get(task.category, t["accent"])
        pill = tk.Label(meta, text=f" {task.category} ", font=self.f_small,
                         bg=cat_color, fg="#ffffff", padx=2)
        pill.pack(side="left")

        pri_lbl = tk.Label(meta, text=f"  {task.priority} priority", font=self.f_small,
                            bg=t["surface"], fg=PRIORITY_COLORS.get(task.priority))
        pri_lbl.pack(side="left", padx=(8, 0))

        if task.due:
            due_color = t["danger"] if overdue else t["text_dim"]
            due_text = f"  ⏰ {task.due}" + ("  (overdue)" if overdue else "")
            tk.Label(meta, text=due_text, font=self.f_small, bg=t["surface"],
                     fg=due_color).pack(side="left", padx=(8, 0))


if __name__ == "__main__":
    app = Tasketo()
    app.mainloop()