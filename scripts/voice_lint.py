#!/usr/bin/env python3
"""Minimal vendored voice_lint for source-decay-ledger.

Mirrors the procurement-negotiation-lab pattern. The full lint hooks into
the lab's voice_lint in spec 0099; this v0.1 version covers the banned-word
list and a few structural patterns.

Usage: python scripts/voice_lint.py PATH [PATH...]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

BANNED = [
    "leverage",
    "demonstrates",
    "comprehensive",
    "synergy",
    "best-in-class",
    "robust solution",
    "industry-leading",
    "seamlessly",
    "cutting-edge",
    "thought-provoking",
    "game-changer",
]

STRUCTURAL: list[tuple[str, re.Pattern[str]]] = [
    (
        "antithetical-dash",
        re.compile(
            r"\b(?:is|are|isn['’]t|aren['’]t)\b[^.!?\n]{0,80}(?:[;—]|--)\s*\w",
            re.IGNORECASE,
        ),
    ),
    ("the-point-is", re.compile(r"\bthe\s+point\s+(?:is|isn['’]t)\b", re.IGNORECASE)),
    ("not-just-but", re.compile(r"\bnot\s+just\b[^.!?\n]{1,60}\bbut\b", re.IGNORECASE)),
]


def scan(path: Path) -> list[str]:
    hits: list[str] = []
    if not path.exists() or path.is_dir():
        return hits
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return hits
    for i, line in enumerate(text.splitlines(), start=1):
        lower = line.lower()
        for word in BANNED:
            if word.lower() in lower:
                hits.append(f"{path}:{i}: banned:{word!r} -> {line.strip()[:80]}")
        for label, pat in STRUCTURAL:
            if pat.search(line):
                hits.append(f"{path}:{i}: {label} -> {line.strip()[:80]}")
    return hits


def iter_files(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    for r in roots:
        if r.is_file():
            out.append(r)
        elif r.is_dir():
            for ext in ("*.md", "*.mdx", "*.rst"):
                out.extend(r.rglob(ext))
    return out


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: voice_lint.py PATH [PATH...]", file=sys.stderr)
        return 2
    files = iter_files([Path(a) for a in argv])
    hits: list[str] = []
    for f in files:
        hits.extend(scan(f))
    if hits:
        for h in hits:
            print(h)
        return 1
    print(f"voice_lint: clean ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
