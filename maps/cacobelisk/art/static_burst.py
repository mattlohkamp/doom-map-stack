"""Draws the drones' static (2026-11-26, chat): three bursts of radio static, into ../sounds/.

Noise, coloured (a radio's hiss is not flat), chopped into an irregular stutter, a machine that has been hit, not a
creature. Three takes (CBSTAT1-3), one per job (sndinfo.txt, 2026-11-27): pain, death, idle; zscript.zs varies the
pain one's pitch a little on each play. 2026-11-27 (chat): the first three were one recipe with different seeds and
sounded alike, so each take has its own character now:
  CBSTAT1  crunch: low, dark, a heavy 60 Hz-ish buzz under a coarse stutter (a shorted circuit);
  CBSTAT2  squelch: bright hiss with a radio's falling whistle through it, cut off clean (a jammed channel);
  CBSTAT3  sputter: fast, ragged dropouts with loud crackles and a short high beep at the start (a fault alarm).
Seeded: the same files every run.

Run from the repo root (the repo's Python, AGENTS.md):
    uv run --project src python maps/cacobelisk/art/static_burst.py
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "sounds"
RATE = 22050

# name: (seconds, seed, character)
TAKES = {
    "CBSTAT1": (0.36, 11, dict(smooth=0.12, hiss=0.15, burst=(0.030, 0.070), gap=(0.004, 0.018), crackle=0.002,
                               buzz=(55, 70), buzz_level=0.35, whistle=None, beep=None, decay=0.5)),
    "CBSTAT2": (0.30, 22, dict(smooth=0.70, hiss=0.80, burst=(0.060, 0.120), gap=(0.000, 0.006), crackle=0.001,
                               buzz=None, buzz_level=0.0, whistle=(2400, 700), beep=None, decay=0.25)),
    "CBSTAT3": (0.42, 33, dict(smooth=0.40, hiss=0.50, burst=(0.006, 0.020), gap=(0.006, 0.030), crackle=0.012,
                               buzz=(180, 220), buzz_level=0.10, whistle=None, beep=(1800, 0.05), decay=0.8)),
}


def take(seconds: float, seed: int, c: dict) -> list[float]:
    rng = random.Random(seed)
    n = int(seconds * RATE)
    gate = [0.0] * n                          # the stutter: bursts and gaps
    i = 0
    while i < n:
        on = int(rng.uniform(*c["burst"]) * RATE)
        level = rng.uniform(0.5, 1.0)
        for k in range(i, min(n, i + on)):
            gate[k] = level
        i += on + int(rng.uniform(*c["gap"]) * RATE)
    buzz_f = rng.uniform(*c["buzz"]) if c["buzz"] else 0
    out = [0.0] * n
    lo = 0.0
    phase = 0.0
    for k in range(n):
        t = k / n
        w = rng.uniform(-1, 1)
        lo += c["smooth"] * (w - lo)          # low-passed noise ...
        s = (1 - c["hiss"]) * lo + c["hiss"] * (w - lo)   # ... mixed with its hiss
        if rng.random() < c["crackle"]:
            s += rng.choice((-1, 1)) * rng.uniform(0.7, 1.2)
        if buzz_f:                            # a square buzz
            s += c["buzz_level"] * (1 if math.sin(2 * math.pi * buzz_f * k / RATE) > 0 else -1)
        if c["whistle"]:                      # a falling whistle, under the gate's chop
            f0, f1 = c["whistle"]
            phase += 2 * math.pi * (f0 + (f1 - f0) * t) / RATE
            s = 0.6 * s + 0.4 * math.sin(phase)
        g = gate[k]
        if c["beep"] and k < c["beep"][1] * RATE:          # a short beep, ahead of the static
            s = math.sin(2 * math.pi * c["beep"][0] * k / RATE)
            g = 0.7
        env = min(1.0, k / (0.003 * RATE)) * (1 - t) ** c["decay"]
        out[k] = s * g * env
    peak = max(abs(x) for x in out) or 1
    return [x / peak * 0.85 for x in out]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (seconds, seed, character) in TAKES.items():
        samples = take(seconds, seed, character)
        with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(b"".join(struct.pack("<h", int(x * 32767)) for x in samples))
        print(f"wrote {OUT / name}.wav ({seconds} s)")


if __name__ == "__main__":
    main()
