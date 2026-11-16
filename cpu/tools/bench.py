#!/usr/bin/env python3
"""Build and time every demo program, reporting guest instruction counts.

Usage:
    python3 tools/bench.py
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from sanasm import build  # noqa: E402

EMULATOR = ROOT / "emulator" / "cpu.san"
RUNNER = ROOT / "tools" / "run_san.py"
BUILD = ROOT / "build"


def main() -> int:
    sources = sorted((ROOT / "programs").glob("*.sasm"))
    if not sources:
        print("no programs found", file=sys.stderr)
        return 1

    rows: list[tuple[str, float, str]] = []
    total_start = time.perf_counter()
    for source in sources:
        name = source.stem
        output = BUILD / f"bench-{name}.san"
        build(source, output, EMULATOR, run=False, cycles=True)
        started = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, str(RUNNER), str(output)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        elapsed = time.perf_counter() - started
        match = re.search(r"^cycles:\s*\n\s*(\d+)", proc.stdout, re.MULTILINE)
        cycles = match.group(1) if match else "?"
        if proc.returncode != 0:
            cycles = f"exit {proc.returncode}"
        rows.append((name, elapsed, cycles))

    total = time.perf_counter() - total_start
    width = max(len(name) for name, _, _ in rows)
    print(f"{'program'.ljust(width)}  {'seconds':>8}  {'cycles':>8}")
    print(f"{'-' * width}  {'-' * 8}  {'-' * 8}")
    for name, elapsed, cycles in rows:
        print(f"{name.ljust(width)}  {elapsed:8.2f}  {cycles:>8}")
    print(f"\ntotal: {total:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
