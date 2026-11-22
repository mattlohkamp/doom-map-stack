# Ambient sound tester (spec, not built)

*Specced 2026-11-22 at the mapper's request, alongside the texture browser (`docs/texture-browser.md`);
not implemented yet. Listed in `PLAN.md` §8.*

A page next to the board for auditioning the game's sounds as ambience: pick a sound, shape it (volume,
pitch, loop, fades, gaps), hear it, then hand the result to Claude for a map.

## What the engine lets us adjust (UZDoom 5)

What a map's script (or SNDINFO) can control, so the tester offers exactly these and nothing it can't
deliver in the game:

| Control | How, in the game | Notes |
|---|---|---|
| **Volume** | `A_StartSound(..., volume)`; change while playing: `A_SoundVolume(slot, v)` | 0-1 |
| **Fade in / out** | the script steps `A_SoundVolume` every tic | any curve; ends with `A_StopSound` |
| **Loop** | `CHANF_LOOPING` | seamless only if the sound itself loops cleanly |
| **Pitch** | `A_StartSound(..., pitch)`; change while playing: `A_SoundPitch` | pitch and speed are tied: 0.5 = an octave down and twice as long; no separate time-stretch |
| **Random pitch** | SNDINFO `$pitchshift` | a little variation each time it plays |
| **Distance falloff** | `attenuation`: `ATTN_NONE` (everywhere), `ATTN_NORM`, `ATTN_IDLE`, `ATTN_STATIC` (dies off fast) | how far it carries |
| **Start point** | `A_StartSound(..., startTime)` | start part-way in, e.g. so two loops don't line up |
| **Where it comes from** | the actor playing it (position), or SNDINFO `$ambient ... surround` / point | |
| **Now and then** | the script (random gaps between plays), or SNDINFO `$ambient ... random min max` / `periodic n` with AmbientSound things (14001-14064) | |
| **Pick one of several** | SNDINFO `$random name { a b c }` | e.g. `world/spark` is three sparks |
| **Room reverb** | sector sound environments (`SoundEnvironment` things, SNDINFO `$environment`) | needs EFX (the game reported "EFX enabled") |

Sounds available without adding files: Freedoom's 109 (`DS*` in `freedoom2.wad`) and UZDoom's own (sparks,
quake rumble, ice, railgun...), by their SNDINFO names (`world/quake`, `weapons/sawidle`...). Our own sound
files (CC0, packed with a map) are a later step.

## The page

- `/sounds` on the board's server, in another tab (with `/textures`, same rules: standard library on the
  server, one HTML file, no front-end libraries).
- **List:** every sound with its SNDINFO name, the lump it plays, its length; grouped (machines, doors and
  lifts, monsters, weapons, world, UI) from the name's prefix (`plats/`, `doors/`, `world/`...); search box.
- **Player:** the server converts each lump for the browser on request (Doom's own sound format -> WAV;
  OGG as is; cached under `build/`, never committed, like the textures). The page plays it with Web Audio:
  volume (gain), pitch (playback rate with pitch following, as in the engine), loop, fade in / out (gain
  ramps), a start point, and "now and then" (random gaps between plays). Falloff as a "distance" slider
  using the engine's attenuation curves, so "how it sounds from 300 away" can be heard.
- **Layering:** several sounds at once (a hum + an occasional tink + a far growl), each with its own
  settings, to hear the whole ambience together.
- **Hand it to Claude:** "Send to Claude" makes a note in the map's inbox with the settings
  (`world/quake, loop, volume 0.3, pitch 0.8, fade in 2 s, ATTN_STATIC, at the switch obelisk`), and Claude
  writes it into the map's script. "Copy" gives the same as text.
- **In-game check** (later): play the chosen settings in the running game, from where the player stands,
  through the live link (`DMSLIVE`), since the browser can only approximate the engine's mixing and reverb.

## Build order

1. Sound list (from SNDINFO in `uzdoom.pk3` and the IWAD's lumps) + converting to WAV + play/stop.
2. Volume, pitch, loop, fades, start point; "Send to Claude" and "Copy".
3. Distance falloff, "now and then", layering.
4. The in-game check through the live link.
