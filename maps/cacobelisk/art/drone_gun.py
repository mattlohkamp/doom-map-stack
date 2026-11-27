"""Draws the drone gun (2026-11-27, chat: "a weapon where you're holding one of the blue drones, and it fires the same
pattern as they do"): a cyan station drone held close in front of the player, seen from behind, into ../sprites/.

The model is the drone's own (maps/cacobelisk/art/drone_sprites.py: sphere, crest, side pods, thruster), turned to
face away from the player (its visor points downrange and can't be seen) and tipped a little towards them, so the
dome and the crest are what shows; held close, so its lower half and its pods run off the bottom of the screen.
No hands (the mapper, second pass: drawn hands didn't look right, and held this close there's little to see of them).
Third pass (in the game): a third smaller, and hacked: a panel torn out of its back, a circuit board inside, wires
hanging out (the player rewired it to fire).
What the player sees of its visor is its light spilling over the far rim, and the flare as a bolt leaves.

Sprites (CBGN, first person; offsets put it bottom centre):
  A, B  ready: the visor's faint light drifting along the rim, left then right (the drone's idle sweep), and a
        spark now and then off a cut wire hanging out of the hacked-open hatch on its back;
  C, D  charging (its stare): the glow rising over the rim;
  E     a bolt: the flare over the rim, the drone kicked 4 pixels down.
CBGP A0: the pickup, a drone powered down (visor dark, no jet), drawn by the drone's own renderer.

Run from the repo root (the repo's Python, AGENTS.md):
    uv run --project src python assets/art/drone_gun.py [preview.png]
"""

from __future__ import annotations

import importlib.util
import math
import struct
import sys
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "src" / "dms").is_dir())
OUT = HERE.parent / "sprites"

# The drone's own model and helpers.
_spec = importlib.util.spec_from_file_location("drone_sprites", ROOT / "maps" / "cacobelisk" / "art" / "drone_sprites.py")
ds = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ds)
ds.KIND = "cyan"

# 2026-11-27 (chat, in the game: "comically big"): a third smaller (the sphere 80 -> 54 pixels), and a little more of it
# showing, for the hacked-open hatch on its back and the wires hanging out of it.
W, H = 184, 80                 # the first-person picture; its bottom edge is the screen's
CX, CY = 92, 78                # the sphere's centre, at the picture's foot
K = 4.3                        # pixels per model unit (the sphere: 12.5 -> 54 pixels)
TILT = math.radians(20)        # its top tipped towards the player
SS = 3                         # samples per pixel each way
LEFT, TOP = -(160 - CX), -(200 - H - 32)   # offsets: centred, its bottom on the screen's (Doom's 320 x 200)

# The hacked-open hatch (2026-11-27, the mapper: "a busted open panel with circuits and wires hanging out exposed,
# implying the player hacked it"): torn out of the back, facing the player, in the view's terms (its surface turned
# HATCH_U either way, from HATCH_V0 to HATCH_V1 up). No cyan in it: it mustn't read as a visor.
HATCH_U, HATCH_V0, HATCH_V1 = 0.36, 0.12, 0.58
BOARD, TRACE, CHIP, PIN = (34, 80, 40), (186, 150, 62), (26, 26, 30), (190, 190, 196)
RIM = (176, 176, 182)
WIRES = [(-0.62, (196, 40, 30), -9), (-0.22, (222, 190, 40), 4), (0.2, (50, 92, 214), -3), (0.62, (70, 70, 74), 11)]
COPPER, SPARK = (214, 140, 62), (255, 250, 200)

HALO = (90, 225, 255)
FLARE = (210, 255, 255)
PODS = [(-15.5, -1.0, 0.0), (15.5, -1.0, 0.0)]
POD_R = 5.2


def to_view(v):
    """Model to view: turned to face away (yaw 180), then its top tipped towards the viewer."""
    x, y, z = -v[0], v[1], -v[2]
    ca, sa = math.cos(TILT), math.sin(TILT)
    return (x, y * ca - z * sa, y * sa + z * ca)


def to_model(v):
    ca, sa = math.cos(TILT), math.sin(TILT)
    x, y, z = v
    y, z = y * ca + z * sa, -y * sa + z * ca
    return (-x, y, -z)


def in_hatch(nv):
    """The hatch's colour where the sphere's view-space normal is nv, or None outside it: a torn edge (bright bent
    metal), then inside, the circuit board: traces, chips with pins, darker under the top edge (it's recessed)."""
    u = nv[0] / HATCH_U
    v = (nv[1] - HATCH_V0) / (HATCH_V1 - HATCH_V0)
    # The torn outline: wavy, not a neat rectangle.
    eu = 1 + 0.07 * math.sin(v * 9) + 0.03 * math.sin(v * 23 + 1)
    ev0 = 0.05 * math.sin(u * 7)
    ev1 = 1 + 0.06 * math.sin(u * 11 + 2) + 0.03 * math.sin(u * 23)
    inside = abs(u) < eu and ev0 < v < ev1
    if not inside:
        near = abs(u) < eu + 0.07 and ev0 - 0.06 < v < ev1 + 0.06
        return ds.shade(RIM, nv, 0.6, 0.45) if near else None
    col = BOARD
    tx, ty = (u + 1) * 6.0, v * 7.0                  # traces on a loose grid, not every line
    if (abs(tx % 1 - 0.5) < 0.07 and int(tx) % 3 != 1) or (abs(ty % 1 - 0.5) < 0.08 and int(ty) % 2 == 0):
        col = TRACE
    for cu, cv, hw, hh in ((-0.45, 0.62, 0.22, 0.16), (0.3, 0.35, 0.28, 0.13), (0.55, 0.78, 0.14, 0.1)):
        if abs(u - cu) < hw and abs(v - cv) < hh:
            col = CHIP
        elif abs(u - cu) < hw - 0.03 and hh <= abs(v - cv) < hh + 0.06 and int((u - cu) * 40) % 2 == 0:
            col = PIN
    shadow = 0.45 + 0.55 * min(1.0, (ev1 - v) / 0.25, (eu - abs(u)) / 0.2)     # recessed: dark under the rim
    return tuple(int(c * shadow) for c in col)


def view_point(u: float, v: float) -> tuple[float, float]:
    """Where a point of the hatch (u, v as in_hatch) lands on the picture."""
    nx = u * HATCH_U
    ny = HATCH_V0 + v * (HATCH_V1 - HATCH_V0)
    return CX + nx * ds.R * K, CY - ny * ds.R * K


def wires(img: Image.Image, spark: bool) -> Image.Image:
    """Wires pulled out of the hatch, hanging over its lower edge and off the bottom of the screen; one cut short with
    bare copper (and, with spark, a spark jumping off it)."""
    from PIL import ImageDraw
    out = img.copy()
    dr = ImageDraw.Draw(out)
    tip = None
    for k, (u, colour, swing) in enumerate(WIRES):
        x0, y0 = view_point(u, 0.25)
        x1, y1 = view_point(u, -0.05)                 # over the torn lower edge
        short = k == 1                                 # the cut one ends in mid-air
        x3, y3 = x1 + swing, (y1 + 9) if short else H + 4
        pts = []
        cx, cy = x1 + swing * 0.2, y1 + 2
        for i in range(17):                            # a quadratic curve: out of the hatch, then hanging down
            t = i / 16
            a = (1 - t) ** 2
            pts.append((a * x0 + 2 * (1 - t) * t * cx + t * t * x3, a * y0 + 2 * (1 - t) * t * cy + t * t * y3))
        dark = tuple(int(c * 0.55) for c in colour)
        dr.line(pts, fill=(*dark, 255), width=3)
        dr.line([(x + 0.4, y) for x, y in pts], fill=(*colour, 255), width=1)
        if short:
            tip = pts[-1]
            dr.line([tip, (tip[0] + 1, tip[1] + 2)], fill=(*COPPER, 255), width=1)
    if spark and tip:
        x, y = int(tip[0] + 1), int(tip[1] + 3)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 1), (-2, 2), (1, 3)):
            if 0 <= x + dx < W and 0 <= y + dy < H:
                out.putpixel((x + dx, y + dy), (*SPARK, 255))
    return out


def render() -> Image.Image:
    """The drone from behind: plain metal, its seams and rivets, the crest; nothing lit (the visor is downrange)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    d = to_model((0.0, 0.0, -1.0))
    for py in range(H):
        for pxx in range(W):
            acc, hits = [0.0, 0.0, 0.0], 0
            for sj in range(SS):
                for si in range(SS):
                    x = (pxx + (si + 0.5) / SS - CX) / K
                    y = (CY - (py + (sj + 0.5) / SS)) / K
                    o = to_model((x, y, 200.0))
                    best, col = None, None
                    t = ds.sphere_hit(o, d, (0, 0, 0), ds.R)
                    if t is not None:
                        p = (o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t)
                        n = ds.norm(p)
                        lat = math.asin(max(-1, min(1, n[1])))
                        lon = math.atan2(n[0], n[2])          # 0 = its front (downrange), +-pi its back
                        base = ds.METAL
                        if abs(lat + 0.55) < 0.05:
                            base = ds.SEAM                     # the seam round its lower half
                        elif lat > 0.3 and abs(math.sin(lon * 3)) < 0.05:
                            base = ds.SEAM                     # panel lines on the dome, every 60 degrees
                        elif lat < -0.55:
                            base = ds.DARK
                        if abs(lat + 0.42) < 0.05 and abs(math.sin(lon * 6)) < 0.18:
                            base = (205, 205, 210)             # rivets above the seam
                        best, col = t, ds.shade(base, to_view(n), 0.18)   # a soft shine: a sharp one read as a bulb
                        hatch = in_hatch(to_view(n))
                        if hatch is not None:
                            col = hatch
                    bh = ds.box_hit(o, d, (-1.6, 9.0, -1.0), (1.6, 14.5, 6.0))           # the crest, its back end snapped off (it ran down over the hatch)
                    if bh and (best is None or bh[0] < best):
                        best, col = bh[0], ds.shade((120, 120, 128), to_view(bh[1]), 0.3)
                    for c in PODS:                                                       # the side pods
                        t = ds.sphere_hit(o, d, c, POD_R)
                        if t is not None and (best is None or t < best):
                            p = (o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t)
                            n = ds.norm((p[0] - c[0], p[1] - c[1], p[2] - c[2]))
                            best = t
                            col = ds.shade(ds.SEAM, to_view(n), 0.2) if abs(n[0]) > 0.85 else ds.shade(ds.DARK, to_view(n), 0.6)
                    if col is not None:
                        acc = [acc[i] + col[i] for i in range(3)]
                        hits += 1
            if hits * 2 >= SS * SS:
                px[pxx, py] = (int(acc[0] / hits), int(acc[1] / hits), int(acc[2] / hits), 255)
    return img


def glow_over_rim(img: Image.Image, level: float, centre: float | None, flare: bool) -> Image.Image:
    """The visor's light, which faces downrange, spilling over the drone's far (upper) rim, and the flare.
    centre: where along the rim it sits (-1 left .. 1 right; None: all along the top)."""
    out = img.copy()
    p = out.load()
    rim_r = ds.R * K
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - CX, y + 0.5 - CY
            dist = math.hypot(dx, dy)
            up = -dy / max(dist, 1e-6)                           # 1 straight up, 0 at the sides
            across = dx / max(dist, 1e-6)                        # -1 left .. 1 right along the rim
            k = 0.0
            if up > 0.15 and dist > rim_r - 1:
                along = 1.0 if centre is None else max(0.0, 1 - abs(across - centre) * 2.2)
                k = level * up * along * max(0.0, 1 - (dist - rim_r) / (8.0 * K / 6.4))
            core = 0.0
            if flare:
                fx, fy = CX, CY - rim_r * 0.94
                fd = math.hypot((x + 0.5 - fx) * 0.55, y + 0.5 - fy)
                core = 1.4 * max(0.0, 1 - fd / (22.0 * K / 6.4))
                k = max(k, core)
            if k <= 0.12 or (p[x, y][3] and core < 0.75):
                continue                                         # only where nothing nearer covers it, but the flare's core
            if k < 0.45 and (x + y) % 2:                         # dithered at its edge
                continue
            p[x, y] = (*(FLARE if k > 0.85 else HALO), 255)
    return out


def save(img: Image.Image, name: str, ox: int, oy: int) -> None:
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", ox, oy))
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / f"{name}.png", pnginfo=info)


def main() -> None:
    for old in OUT.glob("CBG*.png"):
        old.unlink()
    frames = {  # letter: glow level, where along the rim, flare, kick (pixels down), a spark off the cut wire
        "A": (0.35, -0.55, False, 0, False),
        "B": (0.35, 0.55, False, 0, True),
        "C": (0.55, None, False, 0, False),
        "D": (1.0, None, False, 0, True),
        "E": (1.0, None, True, 3, True),
    }
    base = render()
    sheet = []
    for letter, (level, centre, flare, kick, spark) in frames.items():
        img = ds.to_palette(glow_over_rim(wires(base, spark), level, centre, flare))
        save(img, f"CBGN{letter}0", LEFT, TOP - kick)
        sheet.append(img)
    # The pickup: the drone's own picture, front view, powered down, resting on its thruster.
    pick = ds.to_palette(ds.render(0.0, 0.0, None, 0.0))
    save(pick, "CBGPA0", ds.CX, ds.CY + 16)
    if len(sys.argv) > 1:   # a preview: each frame on the game's 320 x 200 screen, side by side, 2x
        cols = 3
        rows = (len(sheet) + cols - 1) // cols
        prev = Image.new("RGBA", (cols * 324, rows * 204), (20, 20, 24, 255))
        for i, im in enumerate(sheet):
            ox, oy = (i % cols) * 324 + 2, (i // cols) * 204 + 2
            screen = Image.new("RGBA", (320, 200), (44, 48, 56, 255))
            screen.paste((58, 52, 44, 255), (0, 100, 320, 200))
            screen.alpha_composite(im, (-LEFT, 32 - TOP + (3 if i == 4 else 0)))  # (E kicked down)
            prev.alpha_composite(screen, (ox, oy))
        prev.alpha_composite(pick, ((len(sheet) % cols) * 324 + 140, (len(sheet) // cols) * 204 + 80))
        prev.resize((prev.width * 2, prev.height * 2), Image.NEAREST).save(sys.argv[1])
    print(f"wrote CBGN A-E and CBGP A0 to {OUT}")


if __name__ == "__main__":
    main()
