"""Draws the Cacobelisk drones' sprites and their bolts into ../sprites/.

The drone: a floating metal sphere, the station's answer to the lost soul. Its look is taken from Freedoom's
chaingunner (the helmet's greys, its red visor slit) and revenant (small red running lights): a visor slit
across its front, a crest on top, a pod on each side with a light, a thruster underneath. Drawn by a tiny
ray tracer, every rotation from the same model, and put into Freedoom's palette.

Two kinds (VARIANTS): the cyan drone (CBDC, its small bolt CBBC) and the stronger red drone (CBDR, its
bigger bolt CBBL).

Run from the repo root (the repo's Python, AGENTS.md):
    uv run --project src python maps/cacobelisk/art/drone_sprites.py [preview.png]

Frames: A, B idle (the visor's light sweeps across, the jet flickers); C, D staring (the visor charges up);
E firing; F pain (the visor out). Death uses Freedoom's rocket explosion (MISL), the bolts A-B in flight
and C-E as they pop.
"""

from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from dms import resources  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "sprites"
W, H = 44, 46          # canvas
CX, CY = 22, 20        # the sphere's centre on it
R = 12.5               # the sphere's radius
SS = 4                 # samples per pixel each way
FEET = H - 3           # the actor's feet (grAb y): the jet hangs just below

# kind: (drone sprite, bolt sprite, the bolt's size, its colours: core, hot centre, fringe, pop)
VARIANTS = {
    "cyan": ("CBDC", "CBBC", 1.0, ((60, 200, 255), (230, 255, 255), (10, 110, 200), (90, 220, 255))),
    "red": ("CBDR", "CBBL", 1.35, ((255, 60, 30), (255, 255, 230), (200, 20, 10), (255, 140, 40))),
}
KIND = "red"           # the kind being drawn (main() sets it)

res, _, _ = resources.load(ROOT)
PALETTE = res.palette[:256]


def norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


LIGHT = norm((-0.55, 0.65, 0.6))   # upper left, towards the viewer (in view space: x right, y up, z to the viewer)


def sphere_hit(o, d, c, r):
    """Distance along ray o + t d to the sphere (c, r), or None."""
    oc = (o[0] - c[0], o[1] - c[1], o[2] - c[2])
    b = dot(oc, d)
    q = dot(oc, oc) - r * r
    disc = b * b - q
    if disc < 0:
        return None
    t = -b - math.sqrt(disc)
    return t if t > 0 else None


def box_hit(o, d, lo, hi):
    """Slab test for an axis-aligned box in the model's frame; (t, normal) or None."""
    tmin, tmax, nrm = -1e9, 1e9, None
    for i in range(3):
        if abs(d[i]) < 1e-9:
            if o[i] < lo[i] or o[i] > hi[i]:
                return None
            continue
        t1, t2 = (lo[i] - o[i]) / d[i], (hi[i] - o[i]) / d[i]
        n = [0, 0, 0]
        n[i] = -1 if t1 < t2 else 1
        if t1 > t2:
            t1, t2 = t2, t1
        if t1 > tmin:
            tmin, nrm = t1, tuple(n)
        tmax = min(tmax, t2)
        if tmin > tmax:
            return None
    return (tmin, nrm) if tmin > 0 else None


def shade(base, n, spec=0.5, amb=0.32):
    lam = max(0.0, dot(n, LIGHT))
    h = norm((LIGHT[0], LIGHT[1], LIGHT[2] + 1))
    s = max(0.0, dot(n, h)) ** 18 * spec
    k = amb + (1 - amb) * lam
    return tuple(min(255, c * k + 255 * s) for c in base)


METAL = (150, 150, 158)
DARK = (70, 70, 76)
SEAM = (40, 40, 44)
RED = (255, 30, 20)


def render(yaw: float, visor: float, sweep: float | None, jet: float, flash: bool = False):
    """One picture. yaw: where the drone faces, 0 = at the viewer, + = to the picture's left.
    visor: 0 (out) .. 1 (white hot); sweep: where along the visor its light sits (-1..1), None = all lit."""
    cy, sy = math.cos(yaw), math.sin(yaw)
    # The model's frame: forward +z (at a viewer when yaw is 0), up +y. to_view turns it by yaw; to_model back.
    to_view = lambda v: (cy * v[0] - sy * v[2], v[1], sy * v[0] + cy * v[2])
    to_model = lambda v: (cy * v[0] + sy * v[2], v[1], -sy * v[0] + cy * v[2])
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    pods = [((-15.5, -1.0, 0.0), 5.2), ((15.5, -1.0, 0.0), 5.2)]
    for py in range(H):
        for pxx in range(W):
            acc = [0.0, 0.0, 0.0]
            hits = 0
            for sj in range(SS):
                for si in range(SS):
                    x = pxx + (si + 0.5) / SS - CX
                    y = CY - (py + (sj + 0.5) / SS)
                    o_v = (x, y, 100.0)
                    d_v = (0.0, 0.0, -1.0)
                    o, d = to_model(o_v), to_model(d_v)
                    best, col = None, None
                    # the main sphere
                    t = sphere_hit(o, d, (0, 0, 0), R)
                    if t is not None:
                        p = (o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t)
                        n = norm(p)
                        lat = math.asin(max(-1, min(1, n[1])))
                        lon = math.atan2(n[0], n[2])            # 0 = straight ahead
                        base = METAL
                        glow = None
                        if abs(lat) < 0.17 and abs(lon) < 0.95:  # the visor slit
                            if visor <= 0:
                                base = (30, 10, 10) if KIND == "red" else (10, 24, 30)
                            else:
                                u = lon / 0.95
                                k = 1.0 if sweep is None else max(0.0, 1 - abs(u - sweep) * 1.6)
                                k = 0.25 + 0.75 * k
                                core = 1 - abs(lat) / 0.17
                                v = visor * k
                                if KIND == "red":   # red, to orange, to white hot
                                    glow = (min(255, 120 + 135 * v + 100 * max(0, v - 0.6) * core),
                                            min(255, 10 + 150 * max(0, v - 0.55) * (0.5 + core)),
                                            min(255, 5 + 200 * max(0, v - 0.8) * core))
                                else:               # cyan, to white
                                    glow = (min(255, 10 + 240 * max(0, v - 0.7) * (0.5 + core)),
                                            min(255, 100 + 155 * v),
                                            min(255, 120 + 135 * v + 60 * core))
                        elif abs(lat) < 0.24 and abs(lon) < 1.05:   # its rim
                            base = SEAM
                        elif abs(lat + 0.55) < 0.05:                 # a seam round the lower half
                            base = SEAM
                        elif lat > 0.3 and abs(math.sin(lon * 3)) < 0.05:
                            base = SEAM                              # panel lines on the dome, every 60 degrees
                        elif lat < -0.55:
                            base = DARK                              # the darker underside
                        if abs(lat + 0.42) < 0.05 and (abs(math.sin(lon * 6)) < 0.18):
                            base = (205, 205, 210)                    # rivets above the seam
                        best = t
                        col = glow if glow else shade(base, to_view(n))
                    # the crest on top (front to back)
                    bh = box_hit(o, d, (-1.6, 9.0, -8.0), (1.6, 14.5, 6.0))
                    if bh and (best is None or bh[0] < best):
                        best = bh[0]
                        col = shade((120, 120, 128), to_view(bh[1]), 0.3)
                    # the side pods, a red light at each one's front
                    for c, r in pods:
                        t = sphere_hit(o, d, c, r)
                        if t is not None and (best is None or t < best):
                            p = (o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t)
                            n = norm((p[0] - c[0], p[1] - c[1], p[2] - c[2]))
                            best = t
                            if n[2] > 0.8:
                                on, off = ((255, 60, 40), (90, 20, 20)) if KIND == "red" else ((70, 235, 255), (20, 70, 85))
                                col = on if visor > 0 else off
                            elif abs(n[0]) > 0.85:
                                col = shade(SEAM, to_view(n), 0.2)        # its open end, a vent
                            else:
                                col = shade(DARK, to_view(n), 0.6)
                    # the thruster under it
                    bh = box_hit(o, d, (-4.0, -15.5, -4.0), (4.0, -10.0, 4.0))
                    if bh and (best is None or bh[0] < best):
                        best = bh[0]
                        col = shade((95, 95, 100), to_view(bh[1]), 0.2)
                    if col is not None:
                        acc[0] += col[0]
                        acc[1] += col[1]
                        acc[2] += col[2]
                        hits += 1
            if hits * 2 >= SS * SS:
                px[pxx, py] = (int(acc[0] / hits), int(acc[1] / hits), int(acc[2] / hits), 255)
    # the jet: a short flame under the thruster, drawn flat (it always points down)
    if jet > 0:
        for py in range(CY + 15, min(H, CY + 15 + int(4 + 6 * jet))):
            depth = (py - (CY + 15)) / (4 + 6 * jet)
            half = 3.2 * (1 - depth)
            for pxx in range(W):
                dx = abs(pxx + 0.5 - CX)
                if dx <= half and px[pxx, py][3] == 0:
                    hot = (1 - depth) * (1 - dx / max(half, 0.1) * 0.6)
                    px[pxx, py] = (int(120 + 135 * hot), int(160 + 95 * hot), 255, 255)
    if flash:   # a flare round the visor when it fires
        fx, fy = CX - int(R * math.sin(yaw) * 0.95), CY
        for py in range(H):
            for pxx in range(W):
                dd = math.hypot(pxx + 0.5 - fx, (py + 0.5 - fy) * 1.6)
                if dd < 6.5 and math.cos(yaw) > -0.2:
                    k = 1 - dd / 6.5
                    r0, g0, b0, a0 = px[pxx, py]
                    if a0 == 0:
                        r0 = g0 = b0 = 0
                    if k > 0.25 or a0:
                        fr, fg, fb = (255, 230, 160) if KIND == "red" else (200, 255, 255)   # the flare: warm, or cyan-white
                        px[pxx, py] = (min(255, int(r0 * (1 - k) + fr * k)), min(255, int(g0 * (1 - k) + fg * k)),
                                       min(255, int(b0 * (1 - k) + fb * k)), 255)
    return img


def to_palette(img: Image.Image) -> Image.Image:
    """The metal (greys) to its nearest colour in Freedoom's palette; the glowing parts (visor, lights, jet, bolts:
    any strong colour) stay as drawn, since the palette has no cyan and UZDoom's hardware renderer shows them as they are."""
    out = img.copy()
    p = out.load()
    cache = {}
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = p[x, y]
            if not a or max(r, g, b) - min(r, g, b) > 40:
                continue
            key = (r, g, b)
            if key not in cache:
                cache[key] = min(PALETTE, key=lambda c: (c[0] - r) ** 2 * 3 + (c[1] - g) ** 2 * 4 + (c[2] - b) ** 2 * 2)
            p[x, y] = (*cache[key], 255)
    return out


def save(img: Image.Image, name: str, ox: int, oy: int) -> None:
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", ox, oy))
    img.save(OUT / f"{name}.png", pnginfo=info)


def bolt(frame: int) -> Image.Image:
    """The bolt, in its kind's colours and size: a small hot spark (A, B), then a pop (C, D, E)."""
    _, _, s, (core, hot, fringe, pop) = VARIANTS[KIND]
    size = round(15 * s) | 1
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    p = img.load()
    c = size / 2
    mix = lambda a, b, k: tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))
    for y in range(size):
        for x in range(size):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c)
            if frame < 2:
                rr = (3.2 if frame == 0 else 3.8) * s
                if d < rr:
                    k = 1 - d / rr
                    p[x, y] = (*mix(core, hot, k * k), 255)
                elif d < rr + 1.6 * s and (x + y + frame) % 2 == 0:
                    p[x, y] = (*fringe, 255)
            else:
                ring = (frame - 1) * 2.2 * s
                if abs(d - ring) < 1.1 * s and (x * 7 + y * 3 + frame) % 3:
                    k = 1 - (frame - 2) / 3
                    p[x, y] = (*mix(fringe, pop, k), 255)
                elif frame == 2 and d < 2.2 * s:
                    p[x, y] = (*hot, 255)
    return img


def main() -> None:
    global KIND
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("CB*.png"):
        old.unlink()
    rotations = [("1", None), ("2", "8"), ("3", "7"), ("4", "6"), ("5", None)]
    frames = {  # frame: visor, sweep, jet, flash
        "A": (0.7, -0.5, 0.6, False),
        "B": (0.7, 0.5, 1.0, False),
        "C": (0.85, None, 0.8, False),
        "D": (1.0, None, 1.0, False),
        "E": (1.0, None, 1.0, True),
        "F": (0.0, None, 0.3, False),
    }
    sheet = []
    for KIND, (drone, shot, _, _) in VARIANTS.items():
        for letter, (visor, sweep, jet, flash) in frames.items():
            row = []
            for rot, mirror in rotations:
                yaw = (int(rot) - 1) * math.pi / 4
                img = to_palette(render(yaw, visor, sweep, jet, flash))
                name = f"{drone}{letter}{rot}" + (f"{letter}{mirror}" if mirror else "")
                save(img, name, CX, FEET)
                row.append(img)
            sheet.append(row)
        brow = []
        for k, letter in enumerate("ABCDE"):
            img = to_palette(bolt(k))
            save(img, f"{shot}{letter}0", img.width // 2, img.height // 2)
            brow.append(img)
        sheet.append(brow)
    if len(sys.argv) > 1:   # a preview sheet, 4x, on a grey ground
        cols = max(len(r) for r in sheet)
        prev = Image.new("RGBA", (cols * (W + 4), len(sheet) * (H + 4)), (60, 60, 66, 255))
        for j, row in enumerate(sheet):
            for i, im in enumerate(row):
                prev.alpha_composite(im, (i * (W + 4), j * (H + 4)))
        prev.resize((prev.width * 3, prev.height * 3), Image.NEAREST).save(sys.argv[1])
    print(f"wrote {len(list(OUT.glob('*.png')))} sprites to {OUT}")


if __name__ == "__main__":
    main()
