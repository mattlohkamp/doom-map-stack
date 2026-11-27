"""Makes the drone gun's pickup sound (2026-11-27, chat; a draft in the project's assets/ first, the mapper: "incredibly cute and perfect"): the drones' whistle (baby/sight, Freedoom's DSBSPSIT, two
rising chirps), repitched into a wolf whistle, into ../sounds/CBWOLF.wav.

A wolf whistle is a short "whit" up, a breath, then a long "whee-oo": up, then down below where it began. All of it is
the whistle's second chirp (0.24-0.44 s: about 1250 to 2250 Hz), resampled:
  whit  the chirp, a little higher and quicker;
  whee  the chirp again, higher;
  oo    the chirp backwards (so it falls), its pitch sliding down as it goes, ending below where the whee began.
Short fades at every join. Read from the IWAD each run (nothing of Freedoom's is committed but this result, which
carries Freedoom's licence: ../sounds/NOTICE.txt).

Run from the repo root (the repo's Python, AGENTS.md):
    uv run --project src python maps/cacobelisk/art/wolf_whistle.py
"""

from __future__ import annotations

import io
import struct
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "src" / "dms").is_dir())
sys.path.insert(0, str(ROOT / "src"))
from dms import resources  # noqa: E402

OUT = HERE.parent / "sounds" / "CBWOLF.wav"
CHIRP = (0.24, 0.44)          # seconds: the second rising chirp of DSBSPSIT
GAP = 0.08                    # the breath between whit and whee


def source() -> tuple[list[float], int]:
    res, _, _ = resources.load(ROOT)
    data, _ = res.sound_file("DSBSPSIT")
    w = wave.open(io.BytesIO(data))
    rate, n = w.getframerate(), w.getnframes()
    raw = w.readframes(n)
    xs = [(b - 128) / 128 for b in raw] if w.getsampwidth() == 1 else [v / 32768 for (v,) in struct.iter_unpack("<h", raw)]
    return xs, rate


def resample(xs: list[float], rate_at) -> list[float]:
    """Plays xs at a speed that changes as it goes (rate_at(t), t 0..1 through the source): above 1 is higher and
    quicker, below 1 lower and slower. Linear interpolation."""
    out, pos = [], 0.0
    n = len(xs)
    while pos < n - 1:
        i = int(pos)
        f = pos - i
        out.append(xs[i] * (1 - f) + xs[i + 1] * f)
        pos += rate_at(pos / n)
    return out


def fade(xs: list[float], rate: int, inn: float = 0.008, out: float = 0.02) -> list[float]:
    a, b = int(inn * rate), int(out * rate)
    n = len(xs)
    return [x * min(1.0, k / max(a, 1), (n - k) / max(b, 1)) for k, x in enumerate(xs)]


def main() -> None:
    xs, rate = source()
    chirp = xs[int(CHIRP[0] * rate) : int(CHIRP[1] * rate)]
    whit = fade(resample(chirp[len(chirp) // 3 :], lambda t: 1.15), rate)          # the top of it, quick
    whee = fade(resample(chirp, lambda t: 1.3), rate, out=0.004)
    oo = fade(resample(chirp[::-1], lambda t: 1.3 - 0.65 * t), rate, inn=0.004, out=0.08)   # falling, slowing
    mix = whit + [0.0] * int(GAP * rate) + whee + oo
    peak = max(abs(x) for x in mix) or 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", int(x / peak * 0.9 * 32767)) for x in mix))
    print(f"wrote {OUT} ({len(mix) / rate:.2f} s)")


if __name__ == "__main__":
    main()
