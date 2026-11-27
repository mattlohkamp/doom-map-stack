"""Draws the rune on the great door's small door (notes #153, #155) into ../textures/CBRUNE.png.

An original sigil, not a letter of any real alphabet: a stave with two horns at its head, an eye (a
diamond with its pupil) across its middle and two splayed feet. Note #155: not a clean stencil but daubed
on in a hurry with a broad, half-dry brush: wobbly strokes made of bristle streaks, ragged ends, uneven
paint, a few spatters, and runs dripping down from where the paint pooled.

A white mask on a transparent ground (opacity = how thick the paint is): decaldef.txt's CacobeliskRune
colours it (`shade`). The PNG's grAb offset is the rune's middle, so the decal is centred where it's sprayed.
Seeded: the same picture every run; change SEED for another daub.

Run from the repo root (the repo's Python, AGENTS.md):
    uv run --project src python maps/cacobelisk/art/rune_decal.py
"""

from __future__ import annotations

import math
import random
import struct
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter
from PIL.PngImagePlugin import PngInfo

OUT = Path(__file__).resolve().parents[1] / "textures" / "CBRUNE.png"
W, H = 96, 120         # the picture (decaldef.txt scales it to half on the wall)
SS = 4                 # drawn this many times bigger, then scaled down
SEED = 155
SCALE, OX, OY = 1.25, 8, 4     # the glyph's design grid (64 x 80) onto the picture
TILT = 5               # degrees: not quite upright
BRUSH = 6.5            # the brush's width, in pixels of the picture
BRISTLES = 9

# The glyph, in its 64 x 80 design grid (x right, y down): strokes in the order a hand would paint them.
STROKES = [
    ((32, 6), (32, 70)),                            # the stave
    ((32, 20), (18, 8), (13, 15)),                  # the left horn, its tip turned out
    ((32, 20), (46, 8), (51, 14)),                  # the right horn
    ((32, 29), (18, 41), (32, 53), (46, 41), (32, 29)),   # the eye: a diamond across the stave
    ((32, 63), (19, 75)), ((32, 63), (45, 75)),     # the feet
]
PUPIL = (32, 41, 3.2)  # a dab on the stave in the eye (x, y, radius)
CENTRE = (32, 40)      # the glyph's middle: the decal's anchor


def to_pic(p, rng=None, wobble=0.0):
    """A design-grid point to picture pixels (tilted about the centre, jittered by `wobble`)."""
    x, y = p[0] - CENTRE[0], p[1] - CENTRE[1]
    a = math.radians(TILT)
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    if rng:
        x, y = x + rng.uniform(-wobble, wobble), y + rng.uniform(-wobble, wobble)
    return OX + (CENTRE[0] + x) * SCALE, OY + (CENTRE[1] + y) * SCALE


def path(rng, pts, step=0.6):
    """A stroke through `pts` as a hand would paint it: corners jittered, each leg bowed a little, sampled
    every `step` pixels."""
    P = [to_pic(p, rng, 1.6) for p in pts]
    out = []
    for (x0, y0), (x1, y1) in zip(P, P[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        bow = rng.uniform(-0.09, 0.09) * L
        n = max(2, int(L / step))
        for i in range(n):
            t = i / n
            b = bow * 4 * t * (1 - t)
            out.append((x0 + (x1 - x0) * t + nx * b, y0 + (y1 - y0) * t + ny * b))
    out.append(P[-1])
    return out


def stroke(rng, pts) -> tuple[Image.Image, list]:
    """One stroke of a half-dry brush: bristles side by side, each its own streak, thinning towards the
    end as the brush runs dry. Returns the layer and where paint pooled (for drips)."""
    layer = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(layer)
    line = path(rng, pts)
    width = BRUSH * rng.uniform(0.85, 1.15)
    pools = []
    for b in range(BRISTLES):
        off = (b / (BRISTLES - 1) - 0.5) * width
        start = rng.randint(0, 3)
        end = len(line) - rng.randint(0, max(1, len(line) // 6))    # some bristles give out early: a ragged end
        strength = rng.uniform(0.8, 1.0)
        gap = 0
        for i in range(start, end - 1):
            (x0, y0), (x1, y1) = line[i], line[i + 1]
            L = math.hypot(x1 - x0, y1 - y0) or 1
            nx, ny = -(y1 - y0) / L, (x1 - x0) / L
            dry = i / len(line)                                       # 0 fresh .. 1 the end of the stroke
            if gap > 0:
                gap -= 1
                continue
            if rng.random() < 0.004 + 0.03 * dry:                     # the brush skips: a bare streak
                gap = rng.randint(2, 8)
                continue
            a = strength * (1.0 - 0.3 * dry) * rng.uniform(0.85, 1.0)
            w = width / BRISTLES * 1.9
            d.line([((x0 + nx * off) * SS, (y0 + ny * off) * SS), ((x1 + nx * off) * SS, (y1 + ny * off) * SS)],
                   fill=round(255 * a), width=max(1, round(w * SS)))
    # Paint pools where the brush lands and where a stroke turns: drips start there.
    for i in (0, len(line) // 2, len(line) - 1):
        if rng.random() < 0.8:
            pools.append(line[i])
    return layer, pools


def drip(d, rng, x, y):
    """A run of paint down from (x, y): thin, wavering a little, a bead at its end."""
    length = rng.uniform(6, 22)
    w = rng.uniform(1.0, 2.0)
    a = rng.uniform(0.7, 0.95)
    n = int(length / 0.5)
    px = x
    for i in range(n):
        t = i / n
        nx = px + rng.uniform(-0.12, 0.12)
        d.line([(px * SS, (y + length * t) * SS), (nx * SS, (y + length * (t + 1 / n)) * SS)],
               fill=round(255 * a * (1 - 0.25 * t)), width=max(1, round(w * (1 - 0.4 * t) * SS)))
        px = nx
    r = w * 0.9
    d.ellipse([(px - r) * SS, (y + length - r) * SS, (px + r) * SS, (y + length + r * 1.4) * SS], fill=round(255 * a))


def draw() -> Image.Image:
    rng = random.Random(SEED)
    big = Image.new("L", (W * SS, H * SS), 0)
    pools = []
    for pts in STROKES:
        layer, p = stroke(rng, pts)
        big = ImageChops.lighter(big, layer)
        pools += p
    d = ImageDraw.Draw(big)
    px, py = to_pic(PUPIL[:2], rng, 0.8)
    r = PUPIL[2] * SCALE
    d.ellipse([(px - r) * SS, (py - r * 0.8) * SS, (px + r) * SS, (py + r) * SS], fill=235)
    for x, y in rng.sample(pools, min(7, len(pools))):            # runs from some of the pools
        drip(d, rng, x + rng.uniform(-1.5, 1.5), y)
    for _ in range(26):                                            # spatters near the strokes
        x, y = rng.choice(pools)
        a, dist = rng.uniform(0, 2 * math.pi), rng.uniform(4, 13)
        rr = rng.uniform(0.3, 1.1)
        cx, cy = x + math.cos(a) * dist, y + math.sin(a) * dist
        d.ellipse([(cx - rr) * SS, (cy - rr) * SS, (cx + rr) * SS, (cy + rr) * SS], fill=round(255 * rng.uniform(0.5, 0.9)))
    alpha = big.filter(ImageFilter.GaussianBlur(SS * 0.2)).resize((W, H), Image.LANCZOS)
    # Uneven paint: thinner in patches (a soft noise over the whole daub).
    noise = Image.effect_noise((W // 6, H // 6), 60).resize((W, H), Image.BICUBIC)
    alpha = ImageChops.multiply(alpha, noise.point(lambda v: max(185, min(255, v + 110))))
    out = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    out.putalpha(alpha)
    return out


def main() -> None:
    img = draw()
    OUT.parent.mkdir(exist_ok=True)
    cx, cy = to_pic(CENTRE)
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", round(cx), round(cy)))   # the decal's anchor: the rune's middle
    img.save(OUT, pnginfo=info, optimize=True)
    print(f"wrote {OUT} ({W} x {H}, anchored at {round(cx)}, {round(cy)})")


if __name__ == "__main__":
    main()
