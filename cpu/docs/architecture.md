# SAN-16 CPU architecture

SAN-16 is a 16-bit CPU implemented in San and stored in the `cpu/` folder of
the San repository.  The CPU is a library: `emulator/cpu.san` defines the
machine, and the assembler appends a program image and a `boot()` call to make
a runnable `.san` file.

The goal was not to emulate an existing chip.  It was to find out whether San
can support a real, stateful workload: instruction decoding, indexed memory,
an ALU with flags, stacks, recursion, string handling and I/O.  A custom ISA
kept the instruction set regular and made the whole toolchain small enough to
fit in the repository.

See [ISA.md](ISA.md) for the opcode reference, [benchmarks.md](benchmarks.md)
for measured timings, and [language-notes.md](language-notes.md) for the San
bugs found while building this.

## Machine model

| Property | Value |
| --- | --- |
| Data width | 16 bits |
| Address width | 16 bits |
| Address space | 65,536 words |
| Addressing | word-addressed, addresses wrap modulo 65536 |
| Registers | 16 general purpose, `R0`-`R15` |
| Stack pointer | `R15`, initial value `0x0FFF` |
| Program counter | `PC`, word address |
| Flags | `Z`, `C`, `N`, `V` |
| Instructions | fixed 32 bits, stored as two 16-bit words |
| Reset | `PC = 0`, `R15 = 0x0FFF` |

Memory is word-addressed because the emulator stores a whole machine word in
each San memory cell.  There is no byte-addressing mode and no unaligned
access problem.

## Memory map

| Range | Purpose |
| --- | --- |
| `0x0000` | reset vector; execution begins here |
| `0x0000-0x0FFE` | program and static data |
| `0x0FFF` | initial stack pointer; stack grows downward |
| `0x1000-0xFFFF` | free memory, arrays, strings, heap |

The emulator does not allocate all 65,536 words at boot.  `MEM` grows lazily:
reading an address past the end returns zero, and writing one appends cells up
to that address.  This keeps small programs cheap.

## Instruction format

Every instruction occupies two consecutive memory words:

```text
word 0:  [ opcode: 8 ][ rd: 4 ][ rs: 4 ]
word 1:  [ immediate / address / offset: 16 ]
```

`rd` and `rs` are register numbers.  Instructions without an immediate still
consume word 1, so instruction boundaries are always two words and `PC`
always advances by two.

Example:

```asm
LDI R0, 0x0100
```

```text
word 0 = 0x0300    opcode 3 (LDI), rd = 0, rs = 0
word 1 = 0x0100    immediate
```

Branches store an absolute word address in word 1.  `CALL` pushes the address
of the instruction after the call, which is simply the already-incremented
`PC`.

## San representation of the machine

The CPU state is a set of globals in `emulator/cpu.san`:

```c
dec REGS = []          // 16 one-element arrays
dec MEM = []           // one-element arrays, lazily grown
dec PC = 0
dec FLAG_Z = 0
dec FLAG_C = 0
dec FLAG_N = 0
dec FLAG_V = 0
dec RUNNING = 1
dec OUTBUF = setstr("")
dec INPUT_DATA = []
dec INPUT_POS = 0
```

### Why memory cells are one-element arrays

San has no array-element assignment.  Statements like this are not parsed:

```c
flux MEM[address] = value
```

The emulator therefore stores every memory word as a one-element array:

```text
MEM[address] == [value]
```

A write mutates the inner list in place:

```c
dec cell = MEM[address]
del(cell, 0)
append(cell, value)
```

A read is:

```c
dec cell = MEM[address]
return cell[0]
```

San arrays are Python lists passed by reference, so `cell` aliases the list
inside `MEM`.  The same representation is used for the register file, which is
simply 16 such cells.  Reads and writes stay O(1), but every access pays for
San function calls and list mutation.

### Wrapping and signed values

`u16(x)` normalises a value into `0..65535`.  It has fast paths for values
already in range and for small negatives, and falls back to
`x - floor(x / 65536) * 65536` for larger values.

`s16(x)` interprets a 16-bit value as two's complement:

```c
if (x >= 32768) {
    return x - 65536
}
return x
```

### Bitwise operations

San has no `%`, `&`, `|`, `^`, `~`, `<<` or `>>` operators.  The CPU therefore
implements bitwise operations in software.  AND/OR/XOR loop over 16 bits:

```c
while (i < 16) {
    xd = mod(x, 2)
    yd = mod(y, 2)
    ...
    x = floor(x / 2)
    y = floor(y / 2)
    bit = bit * 2
    i = i + 1
}
```

Modulo is `a - floor(a / b) * b`.  Shifts are multiplication or division by
powers of two.  Rotates combine a left and right shift.  `NOT` is `65535 - x`.

This is correct but much slower than native operators would be.

## Flags

| Flag | Set when |
| --- | --- |
| `Z` | the result is zero |
| `C` | addition carries out of bit 15, or unsigned subtraction borrows |
| `N` | bit 15 of the result is set |
| `V` | signed two's-complement addition/subtraction overflows |

Arithmetic and logic instructions update all four flags.  `CMP`/`CMPI`
calculate flags from `a - b` without storing the result.  `TST` calculates
flags from `a & b`.

Signed branches use `N` and `V`:

```text
JLT  = N != V
JGE  = N == V
JLE  = Z or N != V
JGT  = !Z and N == V
```

Unsigned branches use `C` and `Z`:

```text
JB   = C
JAE  = !C
JBE  = C or Z
JA   = !C and !Z
```

## Execution cycle

`run()` repeatedly calls `step()` while `RUNNING` is set.  One `step()` is:

1. Fetch `w0 = MEM[PC]` and `w1 = MEM[PC+1]`.
2. Advance `PC` by two, wrapping at 65536.
3. Decode the opcode and register fields.
4. Dispatch to the instruction implementation.
5. Execute it, writing registers/memory and updating flags.
6. Return to `run()`, which increments `INSTR_COUNT`.

Decoding uses division rather than bit operations:

```c
op   = floor(w0 / 256)
rest = w0 - op * 256
rd   = floor(rest / 16)
rs   = rest - rd * 16
```

The hottest instructions (`LDI`, `MOV`, `ADD`, `SUB`, branches, `INC`, `DEC`,
loads and stores) are placed first in the dispatch chain and have their
register/memory access inlined.  The remaining instructions are checked after
them.  This was a measurable improvement over a strictly numerical dispatch
order.

## ALU and instruction groups

The ISA is documented in detail in [ISA.md](ISA.md).  The main groups are:

- data movement: `MOV`, `LDI`, `LD`, `ST`, `SWAP`
- arithmetic: `ADD`, `SUB`, `MUL`, `DIV`, `MOD`, signed variants, `MULH`,
  `ADDC`, `SUBC`
- logic: `AND`, `OR`, `XOR`, `NOT`, `TST`
- shifts and rotates: logical, arithmetic, immediate and register forms
- comparison: `CMP`, `CMPI`, `TST`
- control: `JMP`, eleven conditional branches, `CALL`, `RET`, `JMPR`,
  `CALLR`
- stack: `PUSH`, `POP`, `PUSHI`
- I/O: `OUT`, `OUTI`, `OUTC`, `OUTS`, `OUTH`, `IN`, `RAND`, `TIME`
- debug: `DBG`

Division or modulo by zero stores zero, sets `C` and `V`, and sets `Z`.

## Stack and calling convention

There is no fixed ABI, but the demos use:

- arguments in `R0`, `R1`, ...;
- return value in `R0`;
- `CALL`/`RET` for return addresses;
- `PUSH`/`POP` to save temporaries across calls.

`CALL` decrements `R15` and writes the return address into memory.  `RET`
reads `MEM[R15]` into `PC` and increments `R15`.  Because the stack starts at
`0x0FFF`, the first push allocates memory up to that address.  There is no
stack-overflow or empty-stack detection.

## Output and input

Output goes through `OUTBUF`:

- `OUTC` appends a character to the buffer;
- `OUTS` walks a NUL-terminated string in memory and emits each word;
- a newline flushes the buffer with `stdout`;
- `OUT`, `OUTI` and `OUTH` flush pending text first, then print their own line;
- `HALT` flushes anything left.

San string literals cannot contain `()[]{}`, so the printable character table
is built from safe string chunks.  Parentheses and square brackets come from:

```c
const PARENS = setstr(())     // "()"
const BRACKETS = setstr([])   // "[]"
```

Curly braces cannot be constructed, so character codes 123 and 125 print `.`.

Input is non-interactive.  The assembler's `.input` directive preloads a word
stream, and `IN` consumes it; when it is exhausted, `IN` returns zero.  This is
because `scan` is a statement in San and there is no native expression-level
input function.

## Assembler and build pipeline

`tools/sanasm.py` is a two-pass assembler:

1. Pass 1 walks the source, tracks the current address, records labels and
   constants, and computes the size of every instruction/data item.
2. Pass 2 emits encoded words, resolving labels and expressions.

It writes:

```text
build/<name>.san    CPU source + program image + boot call
build/<name>.lst    address/word listing
```

The generated file is literally:

```c
// emulator/cpu.san contents
dec PROGRAM = [ ... ]
dec INPUT = [ ... ]
dec GUEST_EXIT = boot(PROGRAM, INPUT)
```

This keeps the emulator itself pure San.  The only Python is the assembler,
the runner and the test/benchmark harness.

## Boot sequence

`boot(program, input)`:

1. resets `REGS`, `MEM`, output buffer and flags;
2. creates 16 one-element register cells;
3. sets `R15 = 0x0FFF`;
4. copies the program image into memory with `mem_write`;
5. resets `PC`, `RUNNING`, input position and instruction count;
6. runs until `HALT` or an invalid opcode.

An invalid opcode prints a diagnostic, sets the exit code to 255 and stops.

## Performance model

The emulator is an interpreter running inside an interpreter.  A guest
instruction costs many San AST evaluations, several San function calls, list
mutations for registers and memory, and, for bitwise work, a loop over 16 bits.
The measured throughput is about **1,000 guest instructions per second** on
the development phone, with roughly 0.6 seconds of startup for each fresh
process.

The dominant costs are:

1. San's tree-walking dispatch (`evaluate` does a `getattr` per node).
2. One-element-array register/memory cells with `del` + `append`.
3. Software bitwise operations and modulo.
4. Function-call overhead for `reg_get`, `reg_set`, `mem_read`, `mem_write`,
   `u16`, `flags_add`, `flags_sub`.

Measured numbers and the exact commands are in
[benchmarks.md](benchmarks.md).

## Limits and possible extensions

Current limits:

- word-addressed memory only; no byte load/store
- no interrupts, traps or MMU
- no stack-overflow detection
- non-interactive input only
- character output cannot produce `{` or `}`
- no built-in debugger beyond `DBG`
- no step limit; an infinite guest loop runs forever

The biggest language-side improvements would be:

1. real array-element assignment, allowing flat `REGS`/`MEM` arrays;
2. native `%`, `&`, `|`, `^`, `~`, `<<`, `>>`;
3. a native expression-level `read()` for interactive `IN`;
4. fixing the empty-string `dec` parser bug and the string-literal bracket
   check.

Machine-side extensions that would fit the current design:

- byte-addressable `LDB`/`STB`
- interrupt/trap vectors
- a programmable timer
- a step limit and breakpoints
- an assembler-level macro system
- a small monitor/debugger written in San

## File map

```text
cpu/
  emulator/cpu.san       CPU implementation
  tools/sanasm.py        assembler and build driver
  tools/run_san.py       dependency-free San runner
  tools/bench.py         benchmark harness
  programs/*.sasm        assembly demos
  tests/run_tests.py     end-to-end tests
  docs/ISA.md            opcode reference
  docs/architecture.md   this document
  docs/benchmarks.md     measured timings
  docs/language-notes.md San bugs and workarounds
  README.md              quick start and overview
```
