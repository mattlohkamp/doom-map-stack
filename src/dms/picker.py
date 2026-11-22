"""Small windows for choosing a map, used when a launcher is double-clicked.

- `pick_map`: the plain picker (Play, Edit, Pull): the maps in maps/ (title, name, kind) with the last one
  chosen preselected. Double-click, Enter or the action button chooses; Esc or closing the window cancels.
- `pick_session`: Start Session's window: the same list (focused), a "New map..." button, and toggles for
  what to open (board, browser, editor, game, agent). Choosing a map, or creating one, starts the session.

Uses tkinter, which ships with Python, so no extra dependency. (Dropping a map folder onto a launcher
skips the window.)
"""

from __future__ import annotations

import sys
from pathlib import Path

from dms import maps

LAST_PICK = Path("build") / "last-map.txt"


def _last(root: Path) -> str | None:
    try:
        return (root / LAST_PICK).read_text(encoding="utf-8").strip() or None
    except FileNotFoundError:
        return None


def remember(root: Path, name: str) -> None:
    path = root / LAST_PICK
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(name + "\n", encoding="utf-8")


def _window(title: str):
    import tkinter as tk

    if sys.platform == "win32":
        try:  # crisp text on high-DPI screens
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    win = tk.Tk()
    win.title(title)
    return win


def _map_list(parent, root: Path, found: list[maps.MapInfo], on_choose):
    """The list of maps, the last one chosen selected. Returns (tree, selected-map function)."""
    from tkinter import ttk

    cols = ("title", "name", "kind")
    tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse",
                        height=min(max(len(found), 6), 15))
    for col, label, width in (("title", "Title", 260), ("name", "Folder", 180), ("kind", "Kind", 70)):
        tree.heading(col, text=label)
        tree.column(col, width=width, anchor="w")
    for i, m in enumerate(found):
        tree.insert("", "end", iid=str(i), values=(m.title, m.name, m.kind))
    if found:
        last = _last(root)
        start = next((i for i, m in enumerate(found) if m.name == last), 0)
        tree.selection_set(str(start))
        tree.focus(str(start))
        tree.see(str(start))
    tree.bind("<Double-1>", lambda _e: on_choose())

    def selected() -> maps.MapInfo | None:
        sel = tree.selection()
        return found[int(sel[0])] if sel else None

    return tree, selected


def _ask_new_map(root: Path, parent) -> maps.MapInfo | None:
    """Ask for a new map's folder name (checked) and title, and create it. None if cancelled."""
    from tkinter import messagebox, simpledialog

    while True:
        name = simpledialog.askstring(
            "New map - dms", "Folder name for the new map\n(lowercase letters, digits and dashes, e.g. tech-base):",
            parent=parent)
        if name is None:
            return None
        name = name.strip()
        if not maps.NAME_RE.match(name):
            messagebox.showerror("dms", f"{name!r}: use lowercase letters, digits and dashes.", parent=parent)
        elif (root / "maps" / name).exists():
            messagebox.showerror("dms", f"There's already a map called {name}.", parent=parent)
        else:
            break
    title = simpledialog.askstring("New map - dms", "Title (shown in the game; empty: from the name):", parent=parent)
    try:
        return maps.new(root, name, title=(title or "").strip() or None)
    except maps.MapError as e:
        messagebox.showerror("dms", str(e), parent=parent)
        return None


def _show(win, focus) -> None:
    """Bring the window to the front (it's started from a console window), focus `focus`, run it."""
    win.attributes("-topmost", True)
    win.after(200, lambda: win.attributes("-topmost", False))
    win.focus_force()
    focus.focus_set()
    win.mainloop()


def pick_map(root: Path, action: str) -> maps.MapInfo | None:
    """Show the picker; `action` labels the button ("Play", "Edit"). None if cancelled."""
    from tkinter import messagebox, ttk

    found = maps.all_maps(root)
    win = _window(f"{action} a map - dms")
    if not found:
        win.withdraw()
        messagebox.showinfo("dms", "There are no maps yet.\nStart one with Start Session.cmd (New map...).", parent=win)
        win.destroy()
        return None

    chosen: list[maps.MapInfo] = []

    def choose(_event=None) -> None:
        info = selected()
        if info:
            chosen.append(info)
            win.destroy()

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=f"Choose a map to {action.lower()}:").pack(anchor="w", pady=(0, 6))
    tree, selected = _map_list(frame, root, found, choose)
    tree.pack(fill="both", expand=True)
    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", pady=(10, 0))
    ttk.Button(buttons, text="Cancel", command=win.destroy).pack(side="right")
    ttk.Button(buttons, text=action, command=choose, default="active").pack(side="right", padx=(0, 6))
    win.bind("<Return>", choose)
    win.bind("<Escape>", lambda _e: win.destroy())
    _show(win, tree)

    if chosen:
        remember(root, chosen[0].name)
        return chosen[0]
    return None


# What a session can open, in the order shown: key -> (label, hint).
SESSION_PARTS = {
    "board": ("Board", "the board server, in a console window of its own"),
    "browser": ("Browser", "the board's page for this map"),
    "editor": ("Editor", "Ultimate Doom Builder, on this map"),
    "game": ("Game", "UZDoom, playing this map"),
}


def pick_session(root: Path, defaults: dict, agents: dict[str, str],
                 agent_note: str = "its own window; not started twice") -> tuple[maps.MapInfo, dict] | None:
    """Start Session's window. defaults: {"board": bool, ..., "agent": key or ""}; agents: key -> name;
    agent_note: shown under the agent choice (e.g. that one is already running).
    Returns (map, choices) once a map is chosen or created, None if cancelled."""
    import tkinter as tk
    from tkinter import ttk

    found = maps.all_maps(root)
    win = _window("Start a session - dms")
    result: list = []
    toggles = {k: tk.BooleanVar(value=bool(defaults.get(k, True))) for k in SESSION_PARTS}
    names = {"": "(none)", **agents}
    agent_name = tk.StringVar(value=names.get(defaults.get("agent", ""), "(none)"))

    def choices() -> dict:
        key = next((k for k, n in names.items() if n == agent_name.get()), "")
        return {**{k: v.get() for k, v in toggles.items()}, "agent": key}

    def start(_event=None) -> None:
        info = selected()
        if info:
            result.append((info, choices()))
            win.destroy()

    def new_map() -> None:
        info = _ask_new_map(root, win)
        if info:
            result.append((info, choices()))
            win.destroy()

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Choose a map to work on, or start a new one:").grid(row=0, column=0, sticky="w", pady=(0, 6))
    tree, selected = _map_list(frame, root, found, start)
    tree.grid(row=1, column=0, sticky="nsew")
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)

    opts = ttk.LabelFrame(frame, text="Open", padding=(10, 6))
    opts.grid(row=1, column=1, sticky="ns", padx=(12, 0))
    for i, (key, (label, hint)) in enumerate(SESSION_PARTS.items()):
        ttk.Checkbutton(opts, text=label, variable=toggles[key]).grid(row=i, column=0, sticky="w")
        ttk.Label(opts, text=hint, foreground="#666").grid(row=i, column=1, sticky="w", padx=(6, 0))
    row = len(SESSION_PARTS)
    ttk.Label(opts, text="Agent").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Combobox(opts, textvariable=agent_name, values=list(names.values()), state="readonly", width=18).grid(
        row=row, column=1, sticky="w", padx=(6, 0), pady=(8, 0))
    ttk.Label(opts, text=agent_note, foreground="#666", wraplength=330).grid(
        row=row + 1, column=1, sticky="w", padx=(6, 0))

    buttons = ttk.Frame(frame)
    buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    ttk.Button(buttons, text="New map...", command=new_map).pack(side="left")
    ttk.Button(buttons, text="Cancel", command=win.destroy).pack(side="right")
    ttk.Button(buttons, text="Start", command=start, default="active").pack(side="right", padx=(0, 6))
    tree.bind("<Return>", start)
    win.bind("<Escape>", lambda _e: win.destroy())
    _show(win, tree if found else buttons.winfo_children()[0])

    if result:
        remember(root, result[0][0].name)
        return result[0]
    return None
