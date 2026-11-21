"""Read and write Ultimate Doom Builder's settings file (UDBuilder.cfg).

The format (documented in UDB's Source/Core/IO/Configuration.cs):
    key = value;     value: "string" (C-style escapes), number, true/false/null, or bare word like 4f
    key;             a null value
    key { ... }      a structure; nesting allowed
    // and /* */     comments

Leaf values are kept as their raw source text, so everything we don't touch is written back
unchanged (comments are dropped; UDB rewrites the whole file on exit anyway).
"""

from __future__ import annotations

import re

Struct = dict[str, "str | None | Struct"]

_TOKEN = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<lcomment>//[^\n]*)
  | (?P<bcomment>/\*.*?\*/)
  | (?P<string>"(?:\\.|[^"\\])*")
  | (?P<punct>[{}=;])
  | (?P<word>[^\s{}=;"]+)
    """,
    re.VERBOSE | re.DOTALL,
)


class CfgError(Exception):
    pass


def _tokens(text: str) -> list[str]:
    out, pos = [], 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise CfgError(f"unexpected character at offset {pos}: {text[pos:pos + 20]!r}")
        pos = m.end()
        if m.lastgroup in ("ws", "lcomment", "bcomment"):
            continue
        out.append(m.group())
    return out


def parse(text: str) -> Struct:
    toks = _tokens(text)
    pos = 0

    def struct(top: bool) -> Struct:
        nonlocal pos
        result: Struct = {}
        while pos < len(toks):
            tok = toks[pos]
            if tok == "}":
                if top:
                    raise CfgError("unbalanced '}'")
                pos += 1
                return result
            key = tok
            pos += 1
            nxt = toks[pos] if pos < len(toks) else None
            if nxt == "{":
                pos += 1
                result[key] = struct(False)
            elif nxt == ";":
                pos += 1
                result[key] = None
            elif nxt == "=":
                pos += 1
                if pos + 1 >= len(toks) or toks[pos + 1] != ";":
                    raise CfgError(f"expected 'value;' after '{key} ='")
                result[key] = toks[pos]
                pos += 2
            else:
                raise CfgError(f"unexpected {nxt!r} after {key!r}")
        if not top:
            raise CfgError("missing '}'")
        return result

    return struct(True)


def dump(data: Struct) -> str:
    lines: list[str] = []

    def emit(d: Struct, indent: int) -> None:
        pad = "\t" * indent
        for key, value in d.items():
            if isinstance(value, dict):
                if indent == 0 and lines:
                    lines.append("")
                lines.append(f"{pad}{key}")
                lines.append(f"{pad}{{")
                emit(value, indent + 1)
                lines.append(f"{pad}}}")
                if indent == 0:
                    lines.append("")
            elif value is None:
                lines.append(f"{pad}{key};")
            else:
                lines.append(f"{pad}{key} = {value};")

    emit(data, 0)
    return "\r\n".join(lines) + "\r\n"


def string(value: str) -> str:
    """A raw quoted string value, escaped the way UDB reads it."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def unquote(raw: str) -> str:
    """The text of a raw quoted string value (the reverse of `string`, plus \\n \\r \\t)."""
    if not (len(raw) >= 2 and raw[0] == raw[-1] == '"'):
        return raw
    out, i, body = [], 0, raw[1:-1]
    escapes = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            code = body[i + 1 : i + 4]  # \000: a 3-digit decimal character code
            if len(code) == 3 and code.isdigit():
                out.append(chr(int(code)))
                i += 4
                continue
            out.append(escapes.get(nxt, nxt))
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def boolean(value: bool) -> str:
    return "true" if value else "false"


def integer(value: int) -> str:
    return str(int(value))


def set_path(data: Struct, path: str, value: "str | Struct") -> None:
    """Set a dotted path (e.g. "configurations.uzdoom_doomudmf.enabled"), creating structures."""
    *parents, last = path.split(".")
    d = data
    for p in parents:
        child = d.get(p)
        if not isinstance(child, dict):
            child = {}
            d[p] = child
        d = child
    d[last] = value


def get_path(data: Struct, path: str):
    d = data
    for p in path.split("."):
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d
