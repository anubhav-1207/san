# SAN-16 benchmarks and test timings

These numbers were measured while moving the emulator into the San repository,
against the repository runtime at commit `54c53c6` (the boolean-token fix).

## Environment

| Item | Value |
| --- | --- |
| Host | Android phone, OpenCode Mobile built-in Ubuntu |
| Python | CPython 3.12.3 |
| San runtime | repository `src/` at `54c53c6` |
| CPU implementation | `cpu/emulator/cpu.san` |
| Date | 2026-11-16 |

All timings are wall-clock and include starting a fresh Python process,
reading/parsing the generated `.san` file (the CPU source plus the program
image), booting the CPU and running the guest program.  Startup is roughly
0.6 seconds, so short demos are dominated by parsing rather than execution.
The machine is a phone and timings vary by a few percent with system load.

## Reproduce

```bash
cd cpu

# End-to-end tests, with per-case timing
python3 tests/run_tests.py

# Every demo, with guest instruction counts
python3 tools/bench.py
```

`tools/bench.py` builds each program with `--cycles` and extracts the
`INSTR_COUNT` reported after `boot()`.

## End-to-end test run

Command:

```bash
python3 tests/run_tests.py
```

| Test | Time |
| --- | ---: |
| `hello` | 0.75 s |
| `factorial` | 0.67 s |
| `factorial_recursive` | 0.87 s |
| `memory_sum` | 0.83 s |
| `bitops` | 0.72 s |
| `signed_input` | 0.70 s |
| `reverse_string` | 0.92 s |
| `bubble_sort` | 1.43 s |
| `fibonacci` | 0.73 s |
| `sieve` | 3.68 s |
| `charout` | 0.70 s |
| `advanced` | 0.85 s |
| `loop_bench` | 3.18 s |
| **13 tests** | **16.42 s** |

All 13 tests passed.  Each case assembles in the test process and then runs in
a fresh subprocess, so the table measures the real generated program from
startup to output.

## Demo benchmark with instruction counts

Command:

```bash
python3 tools/bench.py
```

| Program | Time | Guest instructions |
| --- | ---: | ---: |
| `advanced` | 1.06 s | 23 |
| `bitops` | 0.66 s | 29 |
| `bubble_sort` | 1.68 s | 665 |
| `charout` | 0.88 s | 7 |
| `factorial` | 0.84 s | 36 |
| `factorial_recursive` | 1.09 s | 64 |
| `fibonacci` | 0.81 s | 124 |
| `hello` | 0.85 s | 4 |
| `loop_bench` | 3.33 s | 3,004 |
| `memory_sum` | 0.90 s | 108 |
| `rand_time` | 0.74 s | 5 |
| `reverse_string` | 1.07 s | 148 |
| `sieve` | 3.93 s | 3,871 |
| `signed_input` | 0.70 s | 15 |
| **Total** | **18.94 s** | |

## Throughput

Long-running programs give the clearest estimate:

| Program | Instructions | Time | Raw rate |
| --- | ---: | ---: | ---: |
| `sieve` | 3,871 | 3.93 s | ~985 instr/s |
| `loop_bench` | 3,004 | 3.33 s | ~902 instr/s |
| `bubble_sort` | 665 | 1.68 s | ~396 instr/s |

Subtracting roughly 0.6 seconds of process/parser startup, the steady-state
rate is around **900-1000 San-emulated guest instructions per second**.  Short
programs look slower because startup dominates: `hello` executes only four
guest instructions but still takes about 0.6-0.9 seconds.

The cost breakdown is discussed in
[architecture.md](architecture.md#performance-model).  The main costs are the
San tree-walking interpreter, one-element-array register/memory cells, software
bitwise operations, and San function-call overhead.

## What was tested

The suite covers:

- instruction fetching/decoding and `HALT`
- immediate loads and register moves
- ALU add/subtract/multiply/divide/modulo and 16-bit wrapping
- signed division/remainder and multiply-high
- carry/borrow arithmetic
- AND/OR/XOR/NOT, shifts, arithmetic shifts and rotates
- signed and unsigned comparisons and branches
- load/store with base+offset addressing
- stack push/pop and recursive `CALL`/`RET`
- indirect `CALLR`
- strings: NUL-terminated output and in-place reversal
- line buffering and character output
- preloaded input
- array processing: bubble sort and the Sieve of Eratosthenes
- random and clock instructions

The demos and tests are intentionally small in source size but exercise all of
the machine's major state: registers, memory, flags, stack, PC and I/O.
