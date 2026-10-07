import os
import random
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------- Database ----------
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT, category TEXT, amount REAL, note TEXT)""")
conn.commit()

# ---------- Colors ----------
NAVY = "#12304A"
TEAL = "#0E8A83"
ORANGE = "#F59E0B"
GREEN = "#2E9E5B"
RED = "#D64545"
BLUE = "#2E86DE"
BG = "#F3F6F9"
WHITE = "#FFFFFF"
TEXT = "#1F2D3A"
GREY = "#6B7A89"

CATEGORIES = {
    "Food": "#F59E0B",
    "Travel": "#0E8A83",
    "Shopping": "#E4572E",
    "Bills": "#2E86DE",
    "Health": "#2E9E5B",
    "Other": "#8D99A6",
}
ROW_TINT = {
    "Food": "#FDEBCB",
    "Travel": "#D3EFED",
    "Shopping": "#FADAD0",
    "Bills": "#D6E6F7",
    "Health": "#D6EFDF",
    "Other": "#E6EAEE",
}


def darken(hex_color, f=0.82):
    r, g, b = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


def make_button(parent, text, color, command, width=12):
    btn = tk.Button(parent, text=text, command=command, bg=color, fg="white",
                    activebackground=darken(color), activeforeground="white",
                    font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                    padx=14, pady=8, cursor="hand2", width=width)
    hover = darken(color)
    btn.bind("<Enter>", lambda e: btn.config(bg=hover))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def get_summary():
    total, count = cur.execute(
        "SELECT COALESCE(SUM(amount),0), COUNT(*) FROM expenses").fetchone()
    row = cur.execute(
        "SELECT category, SUM(amount) s FROM expenses "
        "GROUP BY category ORDER BY s DESC LIMIT 1").fetchone()
    top = row[0] if row else "-"
    return total, count, top


# ---------- Page 1: Welcome ----------
class WelcomePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=NAVY)
        center = tk.Frame(self, bg=NAVY)
        center.place(relx=0.5, rely=0.5, anchor="center")

        canvas = tk.Canvas(center, width=260, height=130, bg=NAVY,
                           highlightthickness=0)
        canvas.pack()
        colors = [ORANGE, TEAL, BLUE, GREEN, "#E4572E"]
        heights = [50, 80, 65, 110, 90]
        for i, (c, h) in enumerate(zip(colors, heights)):
            x = 20 + i * 48
            canvas.create_rectangle(x, 125 - h, x + 34, 125, fill=c, outline="")
        canvas.create_line(10, 126, 250, 126, fill="#3C5A75", width=2)

        self.title_lbl = tk.Label(center, text="", bg=NAVY, fg="white",
                                  font=("Segoe UI", 34, "bold"))
        self.title_lbl.pack(pady=(20, 6))
        tk.Label(center, text="Track every rupee. Understand where your money goes.",
                 bg=NAVY, fg="#9FB6CC", font=("Segoe UI", 13)).pack()

        chips = tk.Frame(center, bg=NAVY)
        chips.pack(pady=22)
        for text, color in [("Add Expenses", ORANGE), ("Live Totals", TEAL),
                            ("Pie Chart", BLUE), ("Saved Offline", GREEN)]:
            tk.Label(chips, text=text, bg=color, fg="white",
                     font=("Segoe UI", 10, "bold"), padx=12, pady=5
                     ).pack(side="left", padx=6)

        make_button(center, "Get Started", ORANGE,
                    lambda: app.show("MainPage"), 18).pack(pady=10)
        tk.Label(center, text="Built with Python  |  Tkinter  |  SQLite  |  Matplotlib",
                 bg=NAVY, fg="#6F8AA3", font=("Segoe UI", 10)).pack(pady=(30, 0))

    def on_show(self):
        self.full = "Welcome to Expense Tracker"
        self.title_lbl.config(text="")
        self.type_text(0)

    def type_text(self, i):
        if i <= len(self.full):
            self.title_lbl.config(text=self.full[:i])
            self.after(60, lambda: self.type_text(i + 1))


# ---------- Page 2: Main ----------
class MainPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._status_job = None

        # Header
        header = tk.Frame(self, bg=TEAL, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Expense Tracker", bg=TEAL, fg="white",
                 font=("Segoe UI", 20, "bold")).pack(side="left", padx=20)
        make_button(header, "Finish", ORANGE,
                    lambda: app.show("ThankYouPage"), 10).pack(side="right", padx=20)
        tk.Label(header, text=date.today().strftime("%d %b %Y"), bg=TEAL,
                 fg="#D9F2F0", font=("Segoe UI", 11)).pack(side="right", padx=10)

        # Summary cards
        cards = tk.Frame(self, bg=BG)
        cards.pack(fill="x", padx=20, pady=(15, 5))
        self.total_val = self.make_card(cards, "TOTAL SPENT", ORANGE)
        self.count_val = self.make_card(cards, "ENTRIES", TEAL)
        self.top_val = self.make_card(cards, "TOP CATEGORY", BLUE)

        # Body
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=10)
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(body, bg=WHITE)
        right.pack(side="right", fill="y", padx=(15, 0))

        # Form
        form = tk.Frame(left, bg=WHITE)
        form.pack(fill="x")
        inner = tk.Frame(form, bg=WHITE)
        inner.pack(fill="x", padx=15, pady=12)
        tk.Label(inner, text="Add New Expense", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 12, "bold")).grid(row=0, column=0,
                                                     columnspan=3, sticky="w",
                                                     pady=(0, 8))
        self.cat_var = tk.StringVar(value="Food")
        self.amount_var = tk.StringVar()
        self.note_var = tk.StringVar()

        for col, label in enumerate(["Category", "Amount (Rs)", "Note"]):
            tk.Label(inner, text=label, bg=WHITE, fg=GREY,
                     font=("Segoe UI", 9, "bold")).grid(row=1, column=col,
                                                        sticky="w", padx=(0, 10))
        ttk.Combobox(inner, textvariable=self.cat_var, values=list(CATEGORIES),
                     state="readonly", width=12, font=("Segoe UI", 10)
                     ).grid(row=2, column=0, padx=(0, 10), pady=4, sticky="w")
        self.amount_entry = self.make_entry(inner, self.amount_var, 12)
        self.amount_entry.grid(row=2, column=1, padx=(0, 10), pady=4, sticky="w")
        note_entry = self.make_entry(inner, self.note_var, 24)
        note_entry.grid(row=2, column=2, pady=4, sticky="w")
        self.amount_entry.bind("<Return>", self.add_expense)
        note_entry.bind("<Return>", self.add_expense)

        btn_row = tk.Frame(inner, bg=WHITE)
        btn_row.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        make_button(btn_row, "Add Expense", GREEN, self.add_expense, 14).pack(side="left")
        make_button(btn_row, "Delete Selected", RED, self.delete_expense, 14
                    ).pack(side="left", padx=10)
        self.status = tk.Label(btn_row, text="", bg=WHITE, font=("Segoe UI", 10, "bold"))
        self.status.pack(side="left", padx=10)

        # Table header + filter
        bar = tk.Frame(left, bg=BG)
        bar.pack(fill="x", pady=(12, 4))
        tk.Label(bar, text="Expense List", bg=BG, fg=NAVY,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        flt = ttk.Combobox(bar, textvariable=self.filter_var, state="readonly",
                           values=["All"] + list(CATEGORIES), width=12)
        flt.pack(side="right")
        tk.Label(bar, text="Filter:", bg=BG, fg=GREY,
                 font=("Segoe UI", 10)).pack(side="right", padx=6)
        flt.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Table
        table_frame = tk.Frame(left, bg=WHITE)
        table_frame.pack(fill="both", expand=True)
        cols = ("Date", "Category", "Amount", "Note")
        self.table = ttk.Treeview(table_frame, columns=cols, show="headings")
        widths = {"Date": 95, "Category": 95, "Amount": 90, "Note": 220}
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=widths[c], anchor="w")
        for cat, tint in ROW_TINT.items():
            self.table.tag_configure(cat, background=tint)
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=sb.set)
        self.table.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Chart
        tk.Label(right, text="Spending by Category", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 12, "bold")).pack(pady=(12, 0))
        self.fig = Figure(figsize=(4.4, 4.2), dpi=100, facecolor=WHITE)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def make_card(self, parent, title, color):
        card = tk.Frame(parent, bg=WHITE)
        card.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Frame(card, bg=color, width=6).pack(side="left", fill="y")
        inner = tk.Frame(card, bg=WHITE)
        inner.pack(side="left", padx=14, pady=10)
        tk.Label(inner, text=title, bg=WHITE, fg=GREY,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        val = tk.Label(inner, text="-", bg=WHITE, fg=color,
                       font=("Segoe UI", 20, "bold"))
        val.pack(anchor="w")
        return val

    def make_entry(self, parent, var, width):
        return tk.Entry(parent, textvariable=var, width=width, font=("Segoe UI", 10),
                        relief="flat", highlightthickness=1,
                        highlightbackground="#C9D3DD", highlightcolor=TEAL)

    def show_status(self, msg, color):
        self.status.config(text=msg, fg=color)
        if self._status_job:
            self.after_cancel(self._status_job)
        self._status_job = self.after(3000, lambda: self.status.config(text=""))

    def add_expense(self, event=None):
        try:
            amt = float(self.amount_var.get().strip())
            if amt <= 0:
                raise ValueError
        except ValueError:
            self.show_status("Enter a valid amount (more than 0)", RED)
            return
        cat = self.cat_var.get()
        cur.execute("INSERT INTO expenses (date, category, amount, note) VALUES (?,?,?,?)",
                    (date.today().isoformat(), cat, amt, self.note_var.get().strip()))
        conn.commit()
        self.amount_var.set("")
        self.note_var.set("")
        self.amount_entry.focus()
        self.show_status(f"Added Rs {amt:,.2f} to {cat}", GREEN)
        self.refresh()

    def delete_expense(self):
        sel = self.table.selection()
        if not sel:
            self.show_status("Select a row first", RED)
            return
        if messagebox.askyesno("Delete", "Delete this expense?"):
            cur.execute("DELETE FROM expenses WHERE id=?", (int(sel[0]),))
            conn.commit()
            self.show_status("Expense deleted", GREEN)
            self.refresh()

    def refresh(self):
        for r in self.table.get_children():
            self.table.delete(r)
        f = self.filter_var.get()
        if f == "All":
            rows = cur.execute("SELECT id, date, category, amount, note "
                               "FROM expenses ORDER BY id DESC").fetchall()
        else:
            rows = cur.execute("SELECT id, date, category, amount, note FROM expenses "
                               "WHERE category=? ORDER BY id DESC", (f,)).fetchall()
        for id_, d, c, a, n in rows:
            self.table.insert("", "end", iid=str(id_),
                              values=(d, c, f"{a:,.2f}", n), tags=(c,))
        total, count, top = get_summary()
        self.total_val.config(text=f"Rs {total:,.0f}")
        self.count_val.config(text=str(count))
        self.top_val.config(text=top)
        self.update_chart()

    def update_chart(self):
        self.ax.clear()
        data = cur.execute("SELECT category, SUM(amount) FROM expenses "
                           "GROUP BY category ORDER BY 2 DESC").fetchall()
        if not data:
            self.ax.text(0.5, 0.5, "No expenses yet\nAdd one to see the chart",
                         ha="center", va="center", fontsize=12, color=GREY,
                         transform=self.ax.transAxes)
            self.ax.axis("off")
        else:
            labels = [d[0] for d in data]
            vals = [d[1] for d in data]
            colors = [CATEGORIES.get(l, "#8D99A6") for l in labels]
            self.ax.pie(vals, labels=labels, colors=colors, autopct="%1.0f%%",
                        startangle=90, pctdistance=0.78,
                        wedgeprops={"width": 0.45, "edgecolor": "white"},
                        textprops={"fontsize": 9})
            self.ax.text(0, 0, f"Rs {sum(vals):,.0f}", ha="center", va="center",
                         fontsize=12, fontweight="bold", color=NAVY)
        self.canvas.draw()

    def on_show(self):
        self.refresh()
        self.amount_entry.focus()


# ---------- Page 3: Thank You ----------
class ThankYouPage(tk.Frame):
    TIPS = [
        "Tip: Note down expenses daily - small spends add up fast.",
        "Tip: Check your chart every week to spot where money leaks.",
        "Tip: Set a monthly limit for Food and Shopping.",
        "Tip: Save first, spend what is left.",
    ]

    def __init__(self, parent, app):
        super().__init__(parent, bg=TEAL)
        card = tk.Frame(self, bg=WHITE)
        card.place(relx=0.5, rely=0.5, anchor="center")
        inner = tk.Frame(card, bg=WHITE)
        inner.pack(padx=50, pady=35)

        tk.Label(inner, text="Thank You!", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 32, "bold")).pack()
        tk.Label(inner, text="Thanks for using Expense Tracker.\n"
                             "Small savings today, big goals tomorrow.",
                 bg=WHITE, fg=GREY, font=("Segoe UI", 12)).pack(pady=8)

        stats = tk.Frame(inner, bg=WHITE)
        stats.pack(pady=18)
        self.total_lbl = self.stat(stats, "TOTAL SPENT", ORANGE)
        self.count_lbl = self.stat(stats, "ENTRIES", TEAL)
        self.top_lbl = self.stat(stats, "TOP CATEGORY", BLUE)

        self.tip_lbl = tk.Label(inner, text="", bg=WHITE, fg=GREEN,
                                font=("Segoe UI", 11, "italic"))
        self.tip_lbl.pack(pady=(0, 16))

        row = tk.Frame(inner, bg=WHITE)
        row.pack()
        make_button(row, "Back to App", TEAL, lambda: app.show("MainPage"), 14
                    ).pack(side="left", padx=8)
        make_button(row, "Exit", RED, lambda: self.exit_app(app), 14
                    ).pack(side="left", padx=8)

    def stat(self, parent, title, color):
        box = tk.Frame(parent, bg=color)
        box.pack(side="left", padx=8)
        tk.Label(box, text=title, bg=color, fg="white",
                 font=("Segoe UI", 9, "bold")).pack(padx=22, pady=(10, 0))
        val = tk.Label(box, text="-", bg=color, fg="white",
                       font=("Segoe UI", 20, "bold"))
        val.pack(padx=22, pady=(0, 10))
        return val

    def on_show(self):
        total, count, top = get_summary()
        self.total_lbl.config(text=f"Rs {total:,.0f}")
        self.count_lbl.config(text=str(count))
        self.top_lbl.config(text=top)
        self.tip_lbl.config(text=random.choice(self.TIPS))

    def exit_app(self, app):
        conn.close()
        app.destroy()


# ---------- App ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Tracker")
        self.geometry("1100x680")
        self.minsize(1000, 640)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=WHITE, fieldbackground=WHITE,
                        foreground=TEXT, rowheight=28, font=("Segoe UI", 10),
                        borderwidth=0)
        style.configure("Treeview.Heading", background=NAVY, foreground="white",
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#9ED8D3")],
                  foreground=[("selected", TEXT)])
        style.map("Treeview.Heading", background=[("active", NAVY)])

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        self.pages = {}
        for P in (WelcomePage, MainPage, ThankYouPage):
            page = P(container, self)
            self.pages[P.__name__] = page
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.show("WelcomePage")

    def show(self, name):
        page = self.pages[name]
        page.tkraise()
        if hasattr(page, "on_show"):
            page.on_show()


App().mainloop()
