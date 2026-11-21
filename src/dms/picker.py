"""A small window for choosing a map, used when a map launcher is double-clicked.

Lists the maps in maps/ (title, name, kind) with the last one chosen preselected. Double-click,
Enter or the action button chooses; Esc or closing the window cancels. Uses tkinter, which ships
with Python, so no extra dependency. (Dropping a map folder onto the launcher skips this window.)
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


def pick_map(root: Path, action: str) -> maps.MapInfo | None:
    """Show the picker; `action` labels the button ("Play", "Edit"). None if cancelled."""
    import tkinter as tk
    from tkinter import messagebox, ttk

    if sys.platform == "win32":
        try:  # crisp text on high-DPI screens
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass

    found = maps.all_maps(root)
    win = tk.Tk()
    win.title(f"{action} a map - dms")
    if not found:
        win.withdraw()
        messagebox.showinfo("dms", "There are no maps yet.\nCreate one with: .\\dms.ps1 new <name>", parent=win)
        win.destroy()
        return None

    chosen: list[maps.MapInfo] = []
    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=f"Choose a map to {action.lower()}:").pack(anchor="w", pady=(0, 6))

    cols = ("title", "name", "kind")
    tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse", height=min(max(len(found), 4), 15))
    for col, label, width in (("title", "Title", 260), ("name", "Folder", 180), ("kind", "Kind", 70)):
        tree.heading(col, text=label)
        tree.column(col, width=width, anchor="w")
    for i, m in enumerate(found):
        tree.insert("", "end", iid=str(i), values=(m.title, m.name, m.kind))
    tree.pack(fill="both", expand=True)

    last = _last(root)
    start = next((i for i, m in enumerate(found) if m.name == last), 0)
    tree.selection_set(str(start))
    tree.focus(str(start))
    tree.see(str(start))

    def choose(_event=None) -> None:
        sel = tree.selection()
        if sel:
            chosen.append(found[int(sel[0])])
            win.destroy()

    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", pady=(10, 0))
    ttk.Button(buttons, text="Cancel", command=win.destroy).pack(side="right")
    ttk.Button(buttons, text=action, command=choose, default="active").pack(side="right", padx=(0, 6))

    tree.bind("<Double-1>", choose)
    win.bind("<Return>", choose)
    win.bind("<Escape>", lambda _e: win.destroy())

    # Bring the window to the front (it's started from a console window).
    win.attributes("-topmost", True)
    win.after(200, lambda: win.attributes("-topmost", False))
    win.focus_force()
    tree.focus_set()
    win.mainloop()

    if chosen:
        remember(root, chosen[0].name)
        return chosen[0]
    return None
