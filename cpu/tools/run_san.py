#!/usr/bin/env python3
"""Run a .san program using the San runtime from this repository.

The upstream main.py imports colorama for terminal colouring; this runner is
dependency-free so the emulator can be exercised on a bare Python install.
It imports `src` from the repository root (the parent of this `cpu/` folder).
"""
from __future__ import annotations

import sys
from pathlib import Path

CPU_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CPU_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))

from src.interpreter import Evaluator  # noqa: E402
from src.parser import Parser  # noqa: E402
from src.scanner import Lexer  # noqa: E402


def run_source(source: str) -> None:
    tokens = Lexer(source).tokenise()
    tree = Parser(tokens).parse()
    Evaluator().evaluate(tree)


def run_file(path: str | Path) -> None:
    run_source(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python3 tools/run_san.py <file.san>", file=sys.stderr)
        raise SystemExit(2)
    run_file(sys.argv[1])
