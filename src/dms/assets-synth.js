// A small General MIDI player for the asset browser (docs/asset-browser.md, Music): plays a song's MIDI
// through UZDoom's own soundfont (.tools/uzdoom/soundfonts/uzdoom.sf2), with Web Audio. Our own code, no
// libraries. It's a preview, close to the game but not exact: the game uses FluidSynth (its filters,
// modulators and reverb are approximated or left out here).
//
//   const sf = DmsSynth.parseSF2(arrayBuffer);  const song = DmsSynth.parseMidi(arrayBuffer);
//   const p = new DmsSynth.Player(audioContext, sf);  p.load(song);  p.play();
//   p.speed = 1.25;  p.transpose = -2;  p.seek(30);  p.stop();
"use strict";
const DmsSynth = (() => {
  // ---- SoundFont 2 --------------------------------------------------------------------------------
  const GEN = { startAddrs: 0, endAddrs: 1, startloopAddrs: 2, endloopAddrs: 3, startAddrsCoarse: 4,
    initialFilterFc: 8, initialFilterQ: 9, endAddrsCoarse: 12, pan: 17, delayVolEnv: 33, attackVolEnv: 34,
    holdVolEnv: 35, decayVolEnv: 36, sustainVolEnv: 37, releaseVolEnv: 38, instrument: 41, keyRange: 43,
    velRange: 44, startloopAddrsCoarse: 45, initialAttenuation: 48, endloopAddrsCoarse: 50, coarseTune: 51,
    fineTune: 52, sampleID: 53, sampleModes: 54, scaleTuning: 56, exclusiveClass: 57, overridingRootKey: 58 };
  const DEFAULTS = { [GEN.initialFilterFc]: 13500, [GEN.delayVolEnv]: -12000, [GEN.attackVolEnv]: -12000,
    [GEN.holdVolEnv]: -12000, [GEN.decayVolEnv]: -12000, [GEN.releaseVolEnv]: -12000, [GEN.scaleTuning]: 100,
    [GEN.overridingRootKey]: -1 };
  // Preset generators add to the instrument's; these don't (ranges, indexes, sample fields).
  const NOT_ADDITIVE = new Set([GEN.instrument, GEN.keyRange, GEN.velRange, GEN.sampleID, GEN.sampleModes,
    GEN.exclusiveClass, GEN.overridingRootKey, 0, 1, 2, 3, 4, 12, 45, 50]);

  function parseSF2(buf) {
    const dv = new DataView(buf), u8 = new Uint8Array(buf);
    const str = (o, n) => { let s = ""; for (let i = 0; i < n && u8[o + i]; i++) s += String.fromCharCode(u8[o + i]); return s; };
    let smpl = null;
    const pd = {};
    (function walk(o, end) {
      while (o + 8 <= end) {
        const id = str(o, 4), size = dv.getUint32(o + 4, true), body = o + 8;
        if (id === "RIFF" || id === "LIST") walk(body + 4, Math.min(end, body + size));
        else if (id === "smpl") smpl = new Int16Array(buf.slice(body, body + size - (size % 2)));
        else pd[id] = { o: body, size };
        o = body + size + (size & 1);
      }
    })(0, buf.byteLength);
    if (!smpl || !pd.phdr) throw new Error("not a SoundFont 2 file");
    const records = (key, sz) => { const r = []; for (let i = 0; i < Math.floor(pd[key].size / sz); i++) r.push(pd[key].o + i * sz); return r; };
    const gensOf = (genKey, from, to) => {
      const g = {};
      for (let i = from; i < to; i++) {
        const o = pd[genKey].o + i * 4, oper = dv.getUint16(o, true);
        g[oper] = (oper === GEN.keyRange || oper === GEN.velRange) ? [u8[o + 2], u8[o + 3]] : dv.getInt16(o + 2, true);
      }
      return g;
    };
    const zones = (bagKey, genKey, first, last, terminal) => {
      const bags = records(bagKey, 4), out = [];
      let global = null;
      for (let b = first; b < last; b++) {
        const g = gensOf(genKey, dv.getUint16(bags[b], true), dv.getUint16(bags[b + 1], true));
        if (g[terminal] === undefined) { if (b === first) global = g; continue; }
        out.push(g);
      }
      return { global: global || {}, zones: out };
    };
    const instRecs = records("inst", 22);
    const instruments = [];
    for (let i = 0; i + 1 < instRecs.length; i++)
      instruments.push(zones("ibag", "igen", dv.getUint16(instRecs[i] + 20, true), dv.getUint16(instRecs[i + 1] + 20, true), GEN.sampleID));
    const presets = {};
    const phdr = records("phdr", 38);
    for (let i = 0; i + 1 < phdr.length; i++) {
      const o = phdr[i], program = dv.getUint16(o + 20, true), bank = dv.getUint16(o + 22, true);
      presets[bank * 128 + program] = { name: str(o, 20), ...zones("pbag", "pgen", dv.getUint16(o + 24, true), dv.getUint16(phdr[i + 1] + 24, true), GEN.instrument) };
    }
    const samples = records("shdr", 46).map(o => ({ name: str(o, 20), start: dv.getUint32(o + 20, true), end: dv.getUint32(o + 24, true),
      loopStart: dv.getUint32(o + 28, true), loopEnd: dv.getUint32(o + 32, true), rate: dv.getUint32(o + 36, true),
      root: u8[o + 40], correction: dv.getInt8(o + 41) }));
    return { smpl, presets, instruments, samples, buffers: new Map() };
  }

  const inRange = (r, v) => !r || (v >= r[0] && v <= r[1]);

  // The regions (instrument zone + sample, generators combined) that sound for a note.
  function regions(sf, bank, program, key, vel) {
    const preset = sf.presets[bank * 128 + program] || (bank === 128 ? sf.presets[128 * 128] : sf.presets[program]) || sf.presets[0];
    if (!preset) return [];
    const out = [];
    for (const pz of preset.zones) {
      const pg = { ...preset.global, ...pz };
      if (!inRange(pg[GEN.keyRange], key) || !inRange(pg[GEN.velRange], vel)) continue;
      const inst = sf.instruments[pg[GEN.instrument]];
      if (!inst) continue;
      for (const iz of inst.zones) {
        const g = { ...DEFAULTS, ...inst.global, ...iz };
        if (!inRange(g[GEN.keyRange], key) || !inRange(g[GEN.velRange], vel)) continue;
        for (const [k, v] of Object.entries(pg)) if (!NOT_ADDITIVE.has(+k)) g[k] = (g[k] || 0) + v;
        const sample = sf.samples[g[GEN.sampleID]];
        if (sample && sample.end > sample.start) out.push({ g, sample, sampleIndex: g[GEN.sampleID] });
      }
    }
    return out;
  }

  function sampleBuffer(ctx, sf, index) {
    let b = sf.buffers.get(index);
    if (!b) {
      const s = sf.samples[index], n = s.end - s.start;
      b = ctx.createBuffer(1, n, Math.max(3000, Math.min(384000, s.rate)));
      const ch = b.getChannelData(0);
      for (let i = 0; i < n; i++) ch[i] = sf.smpl[s.start + i] / 32768;
      sf.buffers.set(index, b);
    }
    return b;
  }

  const seconds = tc => tc <= -12000 ? 0 : Math.pow(2, tc / 1200);

  // ---- MIDI files ---------------------------------------------------------------------------------
  // -> { events: [{t (seconds), ch, type: "on"|"off"|"cc"|"prog"|"bend", a, b}], length }
  function parseMidi(buf) {
    const u8 = new Uint8Array(buf), dv = new DataView(buf);
    const str = (o, n) => String.fromCharCode(...u8.slice(o, o + n));
    if (str(0, 4) !== "MThd") throw new Error("not a MIDI file");
    const ntrk = dv.getUint16(10), division = dv.getUint16(12);
    if (division & 0x8000) throw new Error("SMPTE timing isn't supported");
    let pos = 8 + dv.getUint32(4);
    const raw = [], tempos = [];
    for (let t = 0; t < ntrk && pos + 8 <= u8.length; t++) {
      if (str(pos, 4) !== "MTrk") break;
      const end = pos + 8 + dv.getUint32(pos + 4);
      let i = pos + 8, tick = 0, status = 0;
      const vlq = () => { let v = 0, b; do { b = u8[i++]; v = (v << 7) | (b & 0x7f); } while (b & 0x80 && i < end); return v; };
      while (i < end) {
        tick += vlq();
        if (u8[i] & 0x80) status = u8[i++];
        if (status === 0xff) {
          const kind = u8[i++], n = vlq();
          if (kind === 0x51 && n === 3) tempos.push([tick, (u8[i] << 16) | (u8[i + 1] << 8) | u8[i + 2]]);
          i += n;
        } else if (status === 0xf0 || status === 0xf7) { i += vlq(); }
        else {
          const type = status & 0xf0, ch = status & 0x0f, a = u8[i++], b = (type === 0xc0 || type === 0xd0) ? 0 : u8[i++];
          if (type === 0x90 && b > 0) raw.push([tick, ch, "on", a, b]);
          else if (type === 0x80 || type === 0x90) raw.push([tick, ch, "off", a, 0]);
          else if (type === 0xb0) raw.push([tick, ch, "cc", a, b]);
          else if (type === 0xc0) raw.push([tick, ch, "prog", a, 0]);
          else if (type === 0xe0) raw.push([tick, ch, "bend", a | (b << 7), 0]);
        }
      }
      pos = end;
    }
    tempos.sort((x, y) => x[0] - y[0]);
    raw.sort((x, y) => x[0] - y[0] || (x[2] === "off" ? -1 : 0) - (y[2] === "off" ? -1 : 0));
    // Ticks -> seconds, following tempo changes.
    let ti = 0, lastTick = 0, lastSec = 0, tempo = 500000;
    const toSec = tick => {
      while (ti < tempos.length && tempos[ti][0] <= tick) {
        lastSec += (tempos[ti][0] - lastTick) * tempo / division / 1e6; lastTick = tempos[ti][0]; tempo = tempos[ti][1]; ti++;
      }
      return lastSec + (tick - lastTick) * tempo / division / 1e6;
    };
    const events = raw.map(([tick, ch, type, a, b]) => ({ t: toSec(tick), ch, type, a, b }));
    return { events, length: events.length ? events[events.length - 1].t : 0 };
  }

  // ---- the player ---------------------------------------------------------------------------------
  class Player {
    constructor(ctx, sf) {
      this.ctx = ctx; this.sf = sf;
      this.out = ctx.createGain(); this.out.gain.value = 0.6;
      const comp = ctx.createDynamicsCompressor();
      this.out.connect(comp).connect(ctx.destination);
      this.speed = 1; this.transpose = 0; this.loop = false;
      this.song = null; this.playing = false; this.voices = []; this.onend = null;
      this.pos0 = 0; this.ctx0 = 0; this.next = 0; this.timer = null;
      this.resetChannels();
    }
    set volume(v) { this.out.gain.value = v; }
    get volume() { return this.out.gain.value; }
    resetChannels() {
      this.ch = Array.from({ length: 16 }, (_, i) => ({ program: 0, bank: i === 9 ? 128 : 0, volume: 100, expression: 127,
        pan: 64, sustain: false, bend: 8192, bendRange: 2, rpn: [127, 127] }));
    }
    load(song) { this.stop(); this.song = song; this.pos0 = 0; }
    get position() { return this.playing ? this.pos0 + (this.ctx.currentTime - this.ctx0) * this.speed : this.pos0; }
    get length() { return this.song ? this.song.length : 0; }
    play() {
      if (!this.song || this.playing) return;
      if (this.ctx.state === "suspended") this.ctx.resume();
      this.chase(this.pos0);
      this.ctx0 = this.ctx.currentTime + 0.05; this.playing = true;
      this.timer = setInterval(() => this.pump(), 25); this.pump();
    }
    pause() { if (!this.playing) return; this.pos0 = this.position; this.playing = false; clearInterval(this.timer); this.silence(); }
    stop() { this.pause(); this.pos0 = 0; }
    seek(sec) { const was = this.playing; this.pause(); this.pos0 = Math.max(0, Math.min(sec, this.length)); if (was) this.play(); }
    setSpeed(s) { const p = this.position; this.speed = s; if (this.playing) { this.pos0 = p; this.ctx0 = this.ctx.currentTime; } }
    // Controllers and programs up to `sec` (no notes), so a seek lands with the right instruments.
    chase(sec) {
      this.resetChannels();
      const ev = this.song.events;
      let i = 0;
      for (; i < ev.length && ev[i].t < sec; i++) if (ev[i].type !== "on" && ev[i].type !== "off") this.dispatch(ev[i], this.ctx.currentTime);
      this.next = i;
    }
    pump() {
      const ev = this.song.events, ahead = this.position + 0.2 * this.speed;
      while (this.next < ev.length && ev[this.next].t <= ahead) {
        const e = ev[this.next++];
        this.dispatch(e, Math.max(this.ctx.currentTime, this.ctx0 + (e.t - this.pos0) / this.speed));
      }
      if (this.next >= ev.length && this.position >= this.length + 0.5) {
        if (this.loop) this.seek(0);
        else { this.stop(); if (this.onend) this.onend(); }
      }
    }
    dispatch(e, when) {
      const c = this.ch[e.ch];
      if (e.type === "on") this.noteOn(e.ch, e.a, e.b, when);
      else if (e.type === "off") this.noteOff(e.ch, e.a, when);
      else if (e.type === "prog") c.program = e.a;
      else if (e.type === "bend") { c.bend = e.a; this.bendVoices(e.ch, when); }
      else if (e.type === "cc") {
        const [n, v] = [e.a, e.b];
        if (n === 0) c.bank = e.ch === 9 ? 128 : v;
        else if (n === 7) { c.volume = v; this.levelVoices(e.ch, when); }
        else if (n === 11) { c.expression = v; this.levelVoices(e.ch, when); }
        else if (n === 10) c.pan = v;
        else if (n === 64) { c.sustain = v >= 64; if (!c.sustain) for (const vo of this.voices) if (vo.ch === e.ch && vo.held) this.release(vo, when); }
        else if (n === 101) c.rpn[0] = v; else if (n === 100) c.rpn[1] = v;
        else if (n === 6 && c.rpn[0] === 0 && c.rpn[1] === 0) c.bendRange = v;
        else if (n === 120 || n === 123) for (const vo of this.voices) if (vo.ch === e.ch) this.release(vo, when);
        else if (n === 121) { const keep = c.bank; Object.assign(c, { volume: 100, expression: 127, pan: 64, sustain: false, bend: 8192 }); c.bank = keep; }
      }
    }
    channelGain(ch) { const c = this.ch[ch]; return Math.pow(c.volume / 127, 2) * Math.pow(c.expression / 127, 2); }
    bendCents(ch) { const c = this.ch[ch]; return (c.bend - 8192) / 8192 * c.bendRange * 100; }
    noteOn(ch, key, vel, when) {
      const c = this.ch[ch], drums = ch === 9;
      const k = drums ? key : Math.max(0, Math.min(127, key + this.transpose));
      for (const r of regions(this.sf, drums ? 128 : c.bank, c.program, k, vel)) {
        const g = r.g, s = r.sample, ctx = this.ctx;
        const excl = g[GEN.exclusiveClass];
        if (excl) for (const vo of this.voices) if (vo.ch === ch && vo.excl === excl) this.kill(vo, when);
        const src = ctx.createBufferSource();
        src.buffer = sampleBuffer(ctx, this.sf, r.sampleIndex);
        const root = g[GEN.overridingRootKey] >= 0 ? g[GEN.overridingRootKey] : s.root;
        const cents = (k - root) * g[GEN.scaleTuning] + (g[GEN.coarseTune] || 0) * 100 + (g[GEN.fineTune] || 0) + s.correction;
        src.playbackRate.value = Math.pow(2, cents / 1200);
        src.detune.value = this.bendCents(ch);
        const mode = g[GEN.sampleModes] || 0;
        if (mode === 1 || mode === 3) {
          const ls = s.loopStart - s.start + (g[2] || 0) + (g[45] || 0) * 32768, le = s.loopEnd - s.start + (g[3] || 0) + (g[50] || 0) * 32768;
          if (le > ls) { src.loop = true; src.loopStart = ls / src.buffer.sampleRate; src.loopEnd = le / src.buffer.sampleRate; }
        }
        // Level: the zone's attenuation (centibels; x0.4 as FluidSynth does), velocity, channel volume.
        const atten = Math.max(0, (g[GEN.initialAttenuation] || 0) * 0.4);
        const peak = Math.pow(10, -atten / 200) * Math.pow(vel / 127, 2);
        const env = ctx.createGain(), level = ctx.createGain(), pan = ctx.createStereoPanner();
        level.gain.value = this.channelGain(ch);
        pan.pan.value = Math.max(-1, Math.min(1, (g[GEN.pan] || 0) / 500 + (c.pan - 64) / 64));
        let node = src;
        const fc = g[GEN.initialFilterFc];
        if (fc < 13500) {
          const f = ctx.createBiquadFilter();
          f.type = "lowpass"; f.frequency.value = Math.min(20000, 8.176 * Math.pow(2, fc / 1200)); f.Q.value = Math.max(0, (g[GEN.initialFilterQ] || 0) / 10);
          node.connect(f); node = f;
        }
        node.connect(env).connect(level).connect(pan).connect(this.out);
        // Volume envelope: delay, attack (linear), hold, decay to sustain (exponential, as in dB).
        const d = seconds(g[GEN.delayVolEnv]), a = seconds(g[GEN.attackVolEnv]), h = seconds(g[GEN.holdVolEnv]);
        const dec = seconds(g[GEN.decayVolEnv]), sus = Math.pow(10, -Math.max(0, Math.min(1440, g[GEN.sustainVolEnv] || 0)) / 200);
        const t0 = when + d;
        env.gain.setValueAtTime(0, when);
        env.gain.setValueAtTime(0, t0);
        env.gain.linearRampToValueAtTime(peak, t0 + Math.max(0.001, a));
        env.gain.setTargetAtTime(peak * sus, t0 + a + h, Math.max(0.001, dec * 0.0869));
        src.start(when);
        const voice = { ch, key, src, env, level, peak, sus, excl, held: false, done: false,
          release: Math.max(0.01, seconds(g[GEN.releaseVolEnv])), started: when };
        src.onended = () => { voice.done = true; this.voices = this.voices.filter(v => v !== voice); };
        this.voices.push(voice);
      }
      if (this.voices.length > 128) for (const vo of this.voices.slice(0, this.voices.length - 128)) this.kill(vo, when);
    }
    noteOff(ch, key, when) {
      for (const vo of this.voices) if (vo.ch === ch && vo.key === key && !vo.released) {
        if (this.ch[ch].sustain) vo.held = true; else this.release(vo, when);
      }
    }
    release(vo, when) {
      if (vo.released) return;
      vo.released = true; vo.held = false;
      const t = Math.max(when, vo.started);
      vo.env.gain.cancelScheduledValues(t);
      vo.env.gain.setTargetAtTime(0, t, Math.min(2, vo.release * 0.0869));
      try { vo.src.stop(t + Math.min(8, vo.release) + 0.05); } catch (e) { /* already stopped */ }
    }
    kill(vo, when) {
      vo.released = true;
      vo.env.gain.cancelScheduledValues(when); vo.env.gain.setTargetAtTime(0, when, 0.005);
      try { vo.src.stop(when + 0.03); } catch (e) { /* already stopped */ }
    }
    bendVoices(ch, when) { const c = this.bendCents(ch); for (const vo of this.voices) if (vo.ch === ch) vo.src.detune.setValueAtTime(c, when); }
    levelVoices(ch, when) { const g = this.channelGain(ch); for (const vo of this.voices) if (vo.ch === ch) vo.level.gain.setValueAtTime(g, when); }
    silence() { const now = this.ctx.currentTime; for (const vo of [...this.voices]) this.kill(vo, now); this.voices = []; }
  }

  return { parseSF2, parseMidi, Player, regions };
})();
