"""Read and write UDMF TEXTMAP (the text map format; spec: zdoom.org/wiki/UDMF).

    namespace = "zdoom";
    thing { x = 0.0; y = 0.0; type = 1; skill1 = true; user_gid = "start"; }
    vertex { ... }  linedef { ... }  sidedef { ... }  sector { ... }

A Textmap is the global assignments (namespace) plus an ordered list of blocks. Every field is
kept, including ones dms doesn't model (custom `user_*` fields, `comment`, anything the editor
adds), so read -> write never loses data. Values are int, float, bool or str, and keep their type:
`1` stays an int, `1.0` stays a float. Field names are case-insensitive in UDMF; we lowercase them.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

Value = int | float | bool | str

# Block kinds in the order a TEXTMAP lists them; indices into each kind are what linedefs,
# sidedefs etc. refer to, so the relative order within a kind is significant.
KINDS = ("thing", "vertex", "linedef", "sidedef", "sector")


class UdmfError(Exception):
    pass


@dataclass
class Block:
    kind: str
    fields: dict[str, Value] = field(default_factory=dict)

    def get(self, name: str, default: Value | None = None) -> Value | None:
        return self.fields.get(name, default)

    def __getitem__(self, name: str) -> Value:
        return self.fields[name]

    def __setitem__(self, name: str, value: Value) -> None:
        self.fields[name.lower()] = value


@dataclass
class Textmap:
    globals: dict[str, Value] = field(default_factory=lambda: {"namespace": "zdoom"})
    blocks: list[Block] = field(default_factory=list)

    def of(self, kind: str) -> list[Block]:
        return [b for b in self.blocks if b.kind == kind]

    @property
    def things(self) -> list[Block]:
        return self.of("thing")

    @property
    def vertices(self) -> list[Block]:
        return self.of("vertex")

    @property
    def linedefs(self) -> list[Block]:
        return self.of("linedef")

    @property
    def sidedefs(self) -> list[Block]:
        return self.of("sidedef")

    @property
    def sectors(self) -> list[Block]:
        return self.of("sector")


# ---------------------------------------------------------------- parsing

_TOKEN = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<lcomment>//[^\n]*)
  | (?P<bcomment>/\*.*?\*/)
  | (?P<string>"(?:\\.|[^"\\])*")
  | (?P<float>[+-]?(?:[0-9]+\.[0-9]*(?:[eE][+-]?[0-9]+)?|\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+))
  | (?P<hex>0[xX][0-9A-Fa-f]+)
  | (?P<int>[+-]?[0-9]+)
  | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<punct>[{}=;])
    """,
    re.VERBOSE | re.DOTALL,
)


def _unescape(body: str) -> str:
    return re.sub(r"\\(.)", lambda m: m.group(1), body, flags=re.DOTALL)


def _tokens(text: str) -> list[tuple[str, str, int]]:
    out, pos = [], 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            line = text.count("\n", 0, pos) + 1
            raise UdmfError(f"line {line}: unexpected {text[pos:pos + 20]!r}")
        if m.lastgroup not in ("ws", "lcomment", "bcomment"):
            out.append((m.lastgroup, m.group(), pos))
        pos = m.end()
    return out


def _value(kind: str, tok: str) -> Value:
    if kind == "string":
        return _unescape(tok[1:-1])
    if kind == "float":
        return float(tok)
    if kind == "hex":
        return int(tok, 16)
    if kind == "int":
        # UDMF: a leading 0 means octal ("0", "017").
        digits = tok.lstrip("+-")
        sign = -1 if tok.startswith("-") else 1
        return sign * int(digits, 8) if len(digits) > 1 and digits[0] == "0" else int(tok)
    if kind == "ident":
        low = tok.lower()
        if low in ("true", "false"):
            return low == "true"
        return tok  # a bare keyword value; kept as text
    raise UdmfError(f"not a value: {tok!r}")


def parse(text: str) -> Textmap:
    toks = _tokens(text)
    tm = Textmap(globals={}, blocks=[])
    i = 0

    def where(k: int) -> str:
        pos = toks[k][2] if k < len(toks) else len(text)
        return f"line {text.count(chr(10), 0, pos) + 1}"

    def expect(k: int, s: str) -> None:
        if k >= len(toks) or toks[k][1] != s:
            raise UdmfError(f"{where(k)}: expected {s!r}")

    def assignment(k: int, target: dict) -> int:
        name = toks[k][1].lower()
        expect(k + 1, "=")
        if k + 2 >= len(toks):
            raise UdmfError(f"{where(k)}: missing value for {name}")
        vkind, vtok, _ = toks[k + 2]
        try:
            target[name] = _value(vkind, vtok)
        except UdmfError as e:
            raise UdmfError(f"{where(k + 2)}: {e} (for {name})") from None
        expect(k + 3, ";")
        return k + 4

    while i < len(toks):
        kind, tok, _ = toks[i]
        if kind != "ident":
            raise UdmfError(f"{where(i)}: unexpected {tok!r}")
        nxt = toks[i + 1][1] if i + 1 < len(toks) else None
        if nxt == "=":
            i = assignment(i, tm.globals)
        elif nxt == "{":
            block = Block(tok.lower())
            i += 2
            while i < len(toks) and toks[i][1] != "}":
                if toks[i][0] != "ident":
                    raise UdmfError(f"{where(i)}: expected a field name in {block.kind}")
                i = assignment(i, block.fields)
            expect(i, "}")
            i += 1
            tm.blocks.append(block)
        else:
            raise UdmfError(f"{where(i)}: expected '=' or '{{' after {tok!r}")
    return tm


# ---------------------------------------------------------------- writing

def format_value(v: Value) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if not math.isfinite(v):
            raise UdmfError(f"can't write {v} in UDMF")
        if v == int(v) and abs(v) < 1e15:
            return f"{v:.3f}"  # 64.000, like the editor writes
        s = repr(v)
        if "e" in s or "E" in s:
            mant, exp = re.split("[eE]", s)
            if "." not in mant:
                mant += ".0"
            return f"{mant}e{exp}"
        return s
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    raise UdmfError(f"unsupported value type: {type(v).__name__}")


def dump(tm: Textmap) -> str:
    lines = [f"{k} = {format_value(v)};" for k, v in tm.globals.items()]
    lines.append("")
    counters: dict[str, int] = {}
    for b in tm.blocks:
        n = counters.get(b.kind, 0)
        counters[b.kind] = n + 1
        lines.append(f"{b.kind} // {n}")
        lines.append("{")
        lines.extend(f"{k} = {format_value(v)};" for k, v in b.fields.items())
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


def same(a: Textmap, b: Textmap) -> bool:
    """True if two textmaps hold the same data (formatting, comments and field order aside)."""
    if a.globals != b.globals or len(a.blocks) != len(b.blocks):
        return False
    return all(x.kind == y.kind and x.fields == y.fields for x, y in zip(a.blocks, b.blocks))
