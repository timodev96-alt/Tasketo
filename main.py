import json
import os
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox
from datetime import datetime, date
import uuid

APP_TITLE = "Tasketo"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

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

LIGHT = {
    "bg": "#f4f5f7",
    "surface": "#ffffff",
    "surface_alt": "#eef0f4",
    "text": "#1f2430",
    "text_dim": "#6b7280",
    "accent": "#4f46e5",
    "accent_hover": "#4338ca",
    "border": "#e2e4e9",
    "danger": "#ef4444",
    "done_text": "#9ca3af",
}

DARK = {
    "bg": "#111318",
    "surface": "#1b1e27",
    "surface_alt": "#232735",
    "text": "#e7e9ee",
    "text_dim": "#8b90a0",
    "accent": "#818cf8",
    "accent_hover": "#a5b4fc",
    "border": "#2b2f3d",
    "danger": "#f87171",
    "done_text": "#5b5f6d",
}


def gen_id():
    return uuid.uuid4().hex[:10]


class Task:
    def __init__(self, text, category="Personal", priority="Medium",
                 due="", done=False, created=None, task_id=None):
        self.id = task_id or gen_id()
        self.text = text
        self.category = category
        self.priority = priority
        self.due = due  # "YYYY-MM-DD" or ""
        self.done = done
        self.created = created or datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id, "text": self.text, "category": self.category,
            "priority": self.priority, "due": self.due, "done": self.done,
            "created": self.created,
        }

    @staticmethod
    def from_dict(d):
        return Task(d.get("text", ""), d.get("category", "Personal"),
                     d.get("priority", "Medium"), d.get("due", ""),
                     d.get("done", False), d.get("created"), d.get("id"))


class RoundedButton(tk.Canvas):
    """A simple flat 'pill' button drawn on a canvas for a softer look than ttk defaults."""

    def __init__(self, parent, text, command, bg, fg, hover_bg=None,
                 width=90, height=34, radius=17, font=None):
        super().__init__(parent, width=width, height=height, bg=parent["bg"],
                          highlightthickness=0, bd=0, cursor="hand2")
        self.command = command
        self.bg_color = bg
        self.hover_color = hover_bg or bg
        self.fg_color = fg
        self.width, self.height, self.radius = width, height, radius
        self.font = font or ("Segoe UI", 10, "bold")
        self.text = text
        self._draw(self.bg_color)
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self._draw(self.hover_color))
        self.bind("<Leave>", lambda e: self._draw(self.bg_color))

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
                  x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        return self.create_polygon(points, smooth=True, **kw)

    def _draw(self, color):
        self.delete("all")
        self._round_rect(1, 1, self.width-1, self.height-1, self.radius, fill=color, outline="")
        self.create_text(self.width/2, self.height/2, text=self.text,
                          fill=self.fg_color, font=self.font)

    def set_bg(self, parent_bg):
        self.configure(bg=parent_bg)


class TodoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("880x680")
        self.minsize(720, 560)

        self.dark_mode = False
        self.theme = LIGHT
        self.tasks = []
        self.categories = list(DEFAULT_CATEGORIES)
        self.filter_mode = "All"
        self.sort_mode = "Priority"
        self.search_text = ""
        self._last_deleted = None
        self.row_widgets = {}

        self.configure(bg=self.theme["bg"])
        self._build_fonts()
        self._load()
        self._build_ui()
        self._refresh()

        self.bind("<Control-z>", lambda e: self._undo_delete())

    # ---------- persistence ----------
    def _load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.tasks = [Task.from_dict(d) for d in data.get("tasks", [])]
                self.categories = data.get("categories", DEFAULT_CATEGORIES)
                self.dark_mode = data.get("dark_mode", False)
                self.theme = DARK if self.dark_mode else LIGHT
            except Exception:
                self.tasks = []
        else:
            self.tasks = [
                Task("Welcome to Tasketo! Double-click me to edit.", "Personal", "Medium"),
                Task("Check off tasks by clicking the circle", "Personal", "Low"),
                Task("Try adding a task with a due date below", "Work", "High",
                     due=date.today().isoformat()),
            ]

    def _save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "tasks": [t.to_dict() for t in self.tasks],
                    "categories": self.categories,
                    "dark_mode": self.dark_mode,
                }, f, indent=2)
        except Exception as e:
            print("Save failed:", e)

    # ---------- fonts ----------
    def _build_fonts(self):
        self.f_title = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        self.f_h2 = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.f_body = tkfont.Font(family="Segoe UI", size=11)
        self.f_small = tkfont.Font(family="Segoe UI", size=9)
        self.f_strike = tkfont.Font(family="Segoe UI", size=11, overstrike=1)

    # ---------- UI ----------
    def _build_ui(self):
        t = self.theme

        # ===== Header =====
        header = tk.Frame(self, bg=t["bg"])
        header.pack(fill="x", padx=24, pady=(20, 10))

        tk.Label(header, text="✓ Tasketo", font=self.f_title,
                 bg=t["bg"], fg=t["accent"]).pack(side="left")

        self.theme_btn = RoundedButton(
            header, "🌙 Dark" if not self.dark_mode else "☀️ Light",
            self._toggle_theme, bg=t["surface_alt"], fg=t["text"],
            hover_bg=t["border"], width=100, height=34, radius=17,
            font=("Segoe UI", 10))
        self.theme_btn.pack(side="right")

        # ===== Add-task card =====
        add_card = tk.Frame(self, bg=t["surface"], highlightbackground=t["border"],
                             highlightthickness=1)
        add_card.pack(fill="x", padx=24, pady=8)
        self._add_card = add_card

        inner = tk.Frame(add_card, bg=t["surface"])
        inner.pack(fill="x", padx=16, pady=14)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(inner, textvariable=self.entry_var, font=self.f_body,
                               bg=t["surface_alt"], fg=t["text"], relief="flat",
                               insertbackground=t["text"])
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.insert(0, "")
        self.entry.bind("<Return>", lambda e: self._add_task())
        self._placeholder(self.entry, "What needs to be done?", t)

        self.cat_var = tk.StringVar(value=self.categories[0])
        cat_menu = tk.OptionMenu(inner, self.cat_var, *self.categories)
        self._style_optionmenu(cat_menu, t)
        cat_menu.pack(side="left", padx=4)

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

        add_btn = RoundedButton(inner, "+ Add", self._add_task, bg=t["accent"],
                                 fg="#ffffff", hover_bg=t["accent_hover"],
                                 width=90, height=36, radius=18)
        add_btn.pack(side="left", padx=(8, 0))
        self.add_btn = add_btn

        # ===== Filter / search bar =====
        filt = tk.Frame(self, bg=t["bg"])
        filt.pack(fill="x", padx=24, pady=(4, 6))
        self._filt = filt

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
        for mode in ["All", "Active", "Completed"]:
            b = tk.Label(filt, text=mode, font=self.f_small, bg=t["bg"], fg=t["text_dim"],
                         cursor="hand2", padx=10, pady=4)
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda e, m=mode: self._set_filter(m))
            self.filter_buttons[mode] = b

        self.sort_var = tk.StringVar(value="Priority")
        sort_menu = tk.OptionMenu(filt, self.sort_var, "Priority", "Due Date", "Newest",
                                   command=lambda v: self._refresh())
        self._style_optionmenu(sort_menu, t, small=True)
        sort_menu.pack(side="left", padx=(6, 0))

        # ===== Task list (scrollable) =====
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

        # ===== Footer: stats + progress =====
        footer = tk.Frame(self, bg=t["bg"])
        footer.pack(fill="x", padx=24, pady=(0, 18))
        self._footer = footer

        self.stats_label = tk.Label(footer, font=self.f_small, bg=t["bg"], fg=t["text_dim"])
        self.stats_label.pack(side="left")

        self.progress_bg = tk.Canvas(footer, height=8, bg=t["bg"], highlightthickness=0)
        self.progress_bg.pack(side="right", fill="x", expand=True, padx=(16, 0))
        self.progress_bg.bind("<Configure>", lambda e: self._draw_progress())

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

    def _toggle_done(self, task_id):
        for t in self.tasks:
            if t.id == task_id:
                t.done = not t.done
        self._save()
        self._refresh()

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
                      hover_bg=t["accent_hover"], width=100, height=34).pack(side="right", padx=16)
        RoundedButton(btn_row, "Cancel", win.destroy, bg=t["surface_alt"], fg=t["text"],
                      hover_bg=t["border"], width=90, height=34).pack(side="right")

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
        self.theme = DARK if self.dark_mode else LIGHT
        self._save()
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
        if self.search_text:
            tasks = [t for t in tasks if self.search_text in t.text.lower()
                     or self.search_text in t.category.lower()]

        sort_mode = self.sort_var.get() if hasattr(self, "sort_var") else "Priority"
        if sort_mode == "Priority":
            tasks.sort(key=lambda t: (t.done, PRIORITY_ORDER.get(t.priority, 1)))
        elif sort_mode == "Due Date":
            tasks.sort(key=lambda t: (t.done, t.due == "", t.due))
        else:  # Newest
            tasks.sort(key=lambda t: (t.done, t.created), reverse=False)
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
        pct = int((done / total) * 100) if total else 0
        self.stats_label.config(text=f"{done}/{total} completed  ·  {pct}%")
        self._draw_progress(pct)

    def _draw_progress(self, pct=None):
        if pct is None:
            total = len(self.tasks)
            done = len([x for x in self.tasks if x.done])
            pct = int((done / total) * 100) if total else 0
        self.progress_bg.delete("all")
        w = self.progress_bg.winfo_width() or 400
        h = 8
        t = self.theme
        self.progress_bg.create_rectangle(0, 0, w, h, fill=t["surface_alt"], outline="")
        fill_w = max(4, int(w * pct / 100)) if pct else 0
        if fill_w:
            self.progress_bg.create_rectangle(0, 0, fill_w, h, fill=t["accent"], outline="")

    def _render_row(self, task):
        t = self.theme
        overdue = False
        if task.due and not task.done:
            try:
                overdue = datetime.strptime(task.due, "%Y-%m-%d").date() < date.today()
            except ValueError:
                overdue = False

        card = tk.Frame(self.list_frame, bg=t["surface"], highlightbackground=t["border"],
                         highlightthickness=1)
        card.pack(fill="x", pady=5)

        # priority strip
        strip = tk.Frame(card, bg=PRIORITY_COLORS.get(task.priority, t["border"]), width=5)
        strip.pack(side="left", fill="y")

        body = tk.Frame(card, bg=t["surface"])
        body.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        top_row = tk.Frame(body, bg=t["surface"])
        top_row.pack(fill="x")

        # checkbox circle
        chk = tk.Canvas(top_row, width=22, height=22, bg=t["surface"], highlightthickness=0,
                         cursor="hand2")
        color = t["accent"] if task.done else t["border"]
        chk.create_oval(3, 3, 19, 19, outline=color, width=2,
                         fill=t["accent"] if task.done else "")
        if task.done:
            chk.create_line(7, 11, 10, 15, 15, 6, fill="#ffffff", width=2)
        chk.pack(side="left", padx=(0, 10))
        chk.bind("<Button-1>", lambda e: self._toggle_done(task.id))

        label_font = self.f_strike if task.done else self.f_body
        label_fg = t["done_text"] if task.done else t["text"]
        lbl = tk.Label(top_row, text=task.text, font=label_font, bg=t["surface"], fg=label_fg,
                        anchor="w", justify="left", wraplength=440)
        lbl.pack(side="left", fill="x", expand=True)
        lbl.bind("<Double-Button-1>", lambda e: self._edit_task_inline(task))
        chk.bind("<Enter>", lambda e: None)

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

        # meta row: category pill + due date
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
    app = TodoApp()
    app.mainloop()