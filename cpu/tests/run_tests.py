#!/usr/bin/env python3
"""End-to-end tests for the SAN-16 CPU.

Each case assembles a .sasm program, runs the generated San file in a fresh
Python process, and compares stdout with the expected text.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from sanasm import Assembler  # noqa: E402

EMULATOR = ROOT / "emulator" / "cpu.san"
RUNNER = ROOT / "tools" / "run_san.py"

PRIMES_TO_200 = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
    67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137,
    139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199,
]

CASES = {
    "hello": "Hello from SAN-16!\n",
    "factorial": "40320\n",
    "factorial_recursive": "40320\n",
    "memory_sum": "45\n",
    "bitops": (
        "0x00F0\n0xFFF0\n0xFF00\n0x0F0F\n0x0002\n0x0001\n"
        "0xC000\n0x8001\n0xC000\n"
    ),
    "signed_input": "12\n999\n",
    "reverse_string": "Hello, SAN-16!\n!61-NAS ,olleH\n",
    "bubble_sort": "1\n5\n7\n13\n17\n23\n42\n64\n88\n99\n",
    "fibonacci": (
        "0\n1\n1\n2\n3\n5\n8\n13\n21\n34\n55\n89\n144\n233\n377\n610\n"
        "987\n1597\n2584\n4181\n"
    ),
    "sieve": "".join(f"{p}\n" for p in PRIMES_TO_200),
    "charout": "A\nB\n",
    "advanced": "77\n0x0000\n0x0001\n0x0003\n0x8001\n0xC000\n1234\n",
    "loop_bench": "41748\n",
}


def generate(name: str, source_path: Path, out_path: Path) -> None:
    asm = Assembler()
    image, inputs = asm.assemble(source_path.read_text(encoding="utf-8"))
    parts = [
        f"// generated test: {name}",
        EMULATOR.read_text(encoding="utf-8"),
        "",
        "dec PROGRAM = " + repr(image).replace("'", ""),
        "",
        "dec INPUT = " + repr(inputs),
        "",
        "boot(PROGRAM, INPUT)",
        "",
    ]
    out_path.write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    failures = 0
    total_start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="san16-tests-") as tmp:
        tmpdir = Path(tmp)
        for name, expected in CASES.items():
            source = ROOT / "programs" / f"{name}.sasm"
            if not source.exists():
                print(f"FAIL {name}: missing {source}")
                failures += 1
                continue
            generated = tmpdir / f"{name}.san"
            generate(name, source, generated)
            started = time.perf_counter()
            try:
                proc = subprocess.run(
                    [sys.executable, str(RUNNER), str(generated)],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                elapsed = time.perf_counter() - started
                print(f"FAIL {name:<22} {elapsed:6.2f}s  timeout")
                failures += 1
                continue
            elapsed = time.perf_counter() - started
            actual = proc.stdout
            if proc.returncode != 0 or actual != expected:
                failures += 1
                print(f"FAIL {name:<22} {elapsed:6.2f}s  exit={proc.returncode}")
                if actual != expected:
                    print("  expected:", repr(expected[:160]))
                    print("  actual  :", repr(actual[:160]))
                if proc.stderr:
                    print("  stderr  :", proc.stderr.strip().splitlines()[-1])
            else:
                print(f"ok   {name:<22} {elapsed:6.2f}s")

    total_elapsed = time.perf_counter() - total_start
    print(f"\n{len(CASES) - failures}/{len(CASES)} passed in {total_elapsed:.2f}s")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
