# SAN-16: a 16-bit CPU emulator written in San

SAN-16 is a complete 16-bit CPU and assembler toolchain implemented in the
[San programming language](https://github.com/anubhav-1207/san).  It lives in
the `cpu/` folder of the San repository and is meant as a stress test: real
control flow, memory, stacks, subroutines, arithmetic, bit operations, string
processing and I/O, all running through San's tree-walking interpreter.

The CPU is written in `emulator/cpu.san`.  The assembler is a small Python
tool because San has no file I/O; the emulator itself is 100% San.

```bash
cd cpu

# Assemble, run and print the result
python3 tools/sanasm.py programs/sieve.sasm --run

# Add --cycles to report how many guest instructions were executed
python3 tools/sanasm.py programs/sieve.sasm --run --cycles

# Run the end-to-end test suite, with per-case timing
python3 tests/run_tests.py

# Time every demo and report instruction counts
python3 tools/bench.py
```

`--run` writes `build/<name>.san` and executes it with `tools/run_san.py`, a
dependency-free runner that imports the San runtime from the repository root.

## Documentation

- [docs/architecture.md](docs/architecture.md) — how the CPU works, the
  execution cycle, memory representation and design decisions
- [docs/ISA.md](docs/ISA.md) — full instruction-set reference
- [docs/benchmarks.md](docs/benchmarks.md) — measured test and benchmark times
- [docs/language-notes.md](docs/language-notes.md) — San bugs found and
  workarounds used

## What the CPU can do

| Feature | Detail |
| --- | --- |
| Word size | 16-bit data, 16-bit addresses |
| Registers | 16 general purpose (R0-R15; R15 is the stack pointer) |
| Memory | 64K x 16-bit words, word-addressable, lazily allocated |
| Instructions | Fixed 32-bit, stored as two 16-bit words |
| Arithmetic | add, subtract, multiply, divide, modulo, signed divide/modulo, multiply-high, add/subtract-with-carry |
| Logic | and, or, xor, not, test |
| Shifts | logical/arithmetic shifts, rotates; register and immediate forms |
| Flow | absolute jumps, eleven conditional branches, CALL/RET, indirect JMPR/CALLR |
| Stack | PUSH/POP/PUSHI in memory through R15 |
| Memory | LD/ST with base register + 16-bit offset |
| I/O | decimal, hex, character, NUL-terminated string, input stream, random, clock |
| Flags | Z (zero), C (carry/borrow), N (negative), V (signed overflow) |

The instruction set and encoding are documented in [docs/ISA.md](docs/ISA.md).

## Memory map

| Range | Use |
| --- | --- |
| `0x0000` | reset vector: execution starts here |
| `0x0000-0x0FFE` | program and data (the demo programs stay well below this) |
| `0x0FFF` | initial stack pointer; the stack grows down |
| `0x1000-0xFFFF` | free memory / heap |

Memory is word-addressed.  Reading an address that has never been written
returns zero.  Writing one allocates the cells up to that address, so a
program that touches only the bottom of memory does not pay for all 64K.

## Demo programs

| Program | What it exercises |
| --- | --- |
| `hello.sasm` | strings, `OUTS`, immediate loads |
| `factorial.sasm` | loops, multiply, flags |
| `factorial_recursive.sasm` | CALL/RET, stack, recursion |
| `fibonacci.sasm` | register moves and 16-bit wrapping |
| `memory_sum.sasm` | indexed loads/stores and a memory loop |
| `bubble_sort.sasm` | in-place array sorting and printing |
| `sieve.sasm` | nested loops, composite marking, 46 primes below 200 |
| `reverse_string.sasm` | in-place byte manipulation |
| `bitops.sasm` | AND/OR/XOR/NOT, shifts, rotates |
| `signed_input.sasm` | signed branches and the input stream |
| `advanced.sasm` | indirect calls, carry arithmetic, immediate rotates, `PUSHI` |
| `charout.sasm` | character output and line buffering |
| `rand_time.sasm` | random and clock instructions |
| `loop_bench.sasm` | a 3000-instruction benchmark loop |

Example:

```text
$ python3 tools/sanasm.py programs/sieve.sasm --run
2
3
5
7
11
...
199
```

## Speed

This is deliberately a real interpreter running on top of another
interpreter, so it is slow.  On the development phone:

| Workload | Approx. time |
| --- | --- |
| hello / small programs | 0.6-0.9 s (mostly San startup) |
| 3000-instruction loop benchmark | ~3.3 s |
| sieve of Eratosthenes to 200 (3871 instructions) | ~3.9 s |
| bubble sort of 10 words (665 instructions) | ~1.7 s |
| full 13-case test suite | ~16.4 s |

That is roughly 900-1000 guest instructions per second once the interpreter
is warm.  The point is that the language survives a nontrivial workload, not
that it is fast.  Full details and repeatable commands are in
[docs/benchmarks.md](docs/benchmarks.md).

## San features this emulator had to work around

These are documented in [docs/language-notes.md](docs/language-notes.md).
The important ones:

* San has no array-element assignment.  A memory cell is a one-element array;
  `del(cell, 0)` + `append(cell, value)` mutates it in place.
* San has no `%` and no bitwise operators, so the CPU implements them from
  division and loops.
* A `dec name = ""` statement silently stops parsing the rest of the file,
  because the parser treats the empty string's token value as false.
* String literals cannot contain `()[]{}`; the lexer raises an error.  Most
  printable characters are reconstructed from safe string chunks, parentheses
  and square brackets come from `setstr(())` / `setstr([])`, and curly braces
  are not representable.
* `break` inside a `for` loop escapes to the top level because `visit_ForNode`
  does not catch `BreakException`.
* `pop()` and `insert()` print debugging output, so the emulator avoids them.

## Repository layout

This is the `cpu/` subproject of the San repository.

```text
cpu/
  emulator/cpu.san       the CPU, written in San
  tools/sanasm.py        two-pass assembler + build driver
  tools/run_san.py       dependency-free San runner
  tools/bench.py         benchmark harness
  programs/*.sasm        assembly demos
  tests/run_tests.py     end-to-end tests
  docs/architecture.md   CPU architecture and design
  docs/ISA.md            instruction-set reference
  docs/benchmarks.md     measured timings
  docs/language-notes.md San bugs and workarounds
  README.md              this file
```

`tools/run_san.py` imports `src` from the repository root, so there is no
duplicated copy of the interpreter.  It avoids upstream `main.py`'s
`colorama` dependency.  The generated `.san` files can also be run with
`python3 main.py` from the repository root if `colorama` is installed.
