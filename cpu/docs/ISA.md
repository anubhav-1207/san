# SAN-16 instruction set

SAN-16 has 16-bit registers and 16-bit word-addressed memory.  Every
instruction is two words:

```text
word 0:  [ opcode: 8 ][ rd: 4 ][ rs: 4 ]
word 1:  [ immediate / address / offset: 16 ]
```

`word 1` is ignored by instructions that do not use an immediate.  The
assembler emits both words for every instruction, so instruction addresses are
always even word addresses.

Registers are `R0`-`R15`.  `R15` is the stack pointer (`SP` may be used as an
alias).  Execution starts at address 0 with `R15 = 0x0FFF`.

## Opcode map

`rd` and `rs` show which nibble of word 0 is used.  `imm` is word 1.

### Control

| Op | Mnemonic | Operands | Meaning |
| ---: | --- | --- | --- |
| 0 | `NOP` | | do nothing |
| 1 | `HALT` | `imm` | stop; `imm` becomes the exit code |
| 36 | `JMP` | `addr` | `PC = addr` |
| 37 | `JZ` | `addr` | jump if Z |
| 38 | `JNZ` | `addr` | jump if not Z |
| 39 | `JC` | `addr` | jump if carry/borrow |
| 40 | `JNC` | `addr` | jump if no carry |
| 41 | `JN` | `addr` | jump if negative |
| 42 | `JP` | `addr` | jump if not negative |
| 43 | `JV` | `addr` | jump if signed overflow |
| 44 | `JNV` | `addr` | jump if no signed overflow |
| 45 | `CALL` | `addr` | push return address, `PC = addr` |
| 46 | `RET` | | pop return address into `PC` |
| 47 | `PUSH` | `rs` | push register |
| 48 | `POP` | `rd` | pop into register |
| 71 | `JMPR` | `rs` | indirect jump to `rs` |
| 72 | `CALLR` | `rs` | indirect call to `rs` |
| 78 | `PUSHI` | `imm` | push immediate |

Signed and unsigned conditional branches:

| Op | Mnemonic | Condition |
| ---: | --- | --- |
| 62 | `JLE` | Z or (N != V) |
| 63 | `JGT` | !Z and (N == V) |
| 64 | `JGE` | N == V |
| 65 | `JLT` | N != V |
| 66 | `JBE` | C or Z |
| 67 | `JA` | !C and !Z |
| 68 | `JAE` | !C |
| 69 | `JB` | C |

### Data movement

| Op | Mnemonic | Operands | Meaning |
| ---: | --- | --- | --- |
| 2 | `MOV` | `rd, rs` | `rd = rs` |
| 3 | `LDI` | `rd, imm` | `rd = imm` |
| 4 | `LD` | `rd, [rs+imm]` | `rd = mem[rs + imm]` |
| 5 | `ST` | `[rd+imm], rs` | `mem[rd + imm] = rs` |
| 35 | `SWAP` | `rd, rs` | exchange two registers |

Addresses wrap modulo 65536.

### Arithmetic

| Op | Mnemonic | Operands | Meaning |
| ---: | --- | --- | --- |
| 6 | `ADD` | `rd, rs` | `rd = rd + rs` |
| 7 | `ADDI` | `rd, imm` | `rd = rd + imm` |
| 8 | `SUB` | `rd, rs` | `rd = rd - rs` |
| 9 | `SUBI` | `rd, imm` | `rd = rd - imm` |
| 10 | `MUL` | `rd, rs` | low 16 bits of product |
| 11 | `MULI` | `rd, imm` | low 16 bits of product |
| 12 | `DIV` | `rd, rs` | unsigned division |
| 13 | `DIVI` | `rd, imm` | unsigned division |
| 14 | `MOD` | `rd, rs` | unsigned modulo |
| 15 | `MODI` | `rd, imm` | unsigned modulo |
| 58 | `DIVS` | `rd, rs` | signed division, truncates toward zero |
| 59 | `MODS` | `rd, rs` | signed remainder |
| 61 | `MULH` | `rd, rs` | high 16 bits of product |
| 73 | `ADDC` | `rd, rs` | `rd = rd + rs + C` |
| 74 | `SUBC` | `rd, rs` | `rd = rd - rs - C` |
| 29 | `CMP` | `rd, rs` | set flags from `rd - rs`, do not store |
| 30 | `CMPI` | `rd, imm` | set flags from `rd - imm` |
| 31 | `TST` | `rd, rs` | set flags from `rd & rs` |
| 32 | `INC` | `rd` | `rd = rd + 1` |
| 33 | `DEC` | `rd` | `rd = rd - 1` |
| 34 | `NEG` | `rd` | two's-complement negate |
| 57 | `CLF` | | clear all flags |

Division or modulo by zero stores 0, sets C and V, and leaves Z set.

### Logic and shifts

| Op | Mnemonic | Operands | Meaning |
| ---: | --- | --- | --- |
| 16 | `AND` | `rd, rs` | bitwise and |
| 17 | `ANDI` | `rd, imm` | bitwise and immediate |
| 18 | `OR` | `rd, rs` | bitwise or |
| 19 | `ORI` | `rd, imm` | bitwise or immediate |
| 20 | `XOR` | `rd, rs` | bitwise xor |
| 21 | `XORI` | `rd, imm` | bitwise xor immediate |
| 22 | `NOT` | `rd` | bitwise complement |
| 23 | `SHL` | `rd, rs` | shift left by low 4 bits of `rs` |
| 24 | `SHLI` | `rd, imm` | shift left immediate |
| 25 | `SHR` | `rd, rs` | logical shift right |
| 26 | `SHRI` | `rd, imm` | logical shift right immediate |
| 27 | `ROL` | `rd, rs` | rotate left |
| 28 | `ROR` | `rd, rs` | rotate right |
| 60 | `SHRS` | `rd, rs` | arithmetic shift right |
| 75 | `ROLI` | `rd, imm` | rotate left immediate |
| 76 | `RORI` | `rd, imm` | rotate right immediate |
| 77 | `SHRSI` | `rd, imm` | arithmetic shift right immediate |

Shift counts of 16 or more produce zero (or all sign bits for `SHRS`).
Rotates use the count modulo 16.

### I/O and debug

| Op | Mnemonic | Operands | Meaning |
| ---: | --- | --- | --- |
| 49 | `OUT` | `rs` | print unsigned decimal + newline |
| 50 | `OUTI` | `imm` | print immediate in decimal + newline |
| 51 | `OUTC` | `rs` | print character code in `rs` |
| 52 | `OUTS` | `rd` | print NUL-terminated word string at address `rd` |
| 53 | `OUTH` | `rs` | print `0xNNNN` + newline |
| 54 | `IN` | `rd` | read next word from the input stream, or 0 |
| 55 | `RAND` | `rd` | random word 0..65535 |
| 56 | `TIME` | `rd` | low 16 bits of Unix time |
| 70 | `DBG` | | dump PC, flags and registers |

Character output is line-buffered.  A newline character flushes the buffer.
`OUT`/`OUTI`/`OUTH` flush any pending text first.

## Flags

| Flag | Meaning |
| --- | --- |
| Z | result is zero |
| C | addition carried out of bit 15, or unsigned subtraction borrowed |
| N | bit 15 of the result |
| V | signed two's-complement overflow |

Arithmetic and logic instructions set all four flags.  `CMP`/`CMPI` set flags
without writing a register.  Branches only read flags.

## Assembler

`tools/sanasm.py` is a two-pass assembler.

```asm
; comment (also //)
.equ LIMIT, 200
.org 0x0000
start:
        LDI R0, message
        OUTS R0
        HALT

.org 0x0200
message:
        .asciz "Hello!\n"
```

Supported directives:

| Directive | Meaning |
| --- | --- |
| `.org expr` | set the current word address |
| `.equ NAME, expr` | define a constant (must appear before use) |
| `.align n` | align to a multiple of `n` words |
| `.word v1, v2, ...` | emit words |
| `.fill count[, value]` | emit repeated words |
| `.string "..."` | emit characters with no terminator |
| `.asciz "..."` / `.cstr "..."` | emit characters plus a NUL word |
| `.input v1, v2, ...` | preload the `IN` stream |

Expressions support decimal, `0x` hex, `0b` binary, `'A'` character
literals, labels, `.equ` names, `$` (current address), and the usual
`+ - * / % << >> & | ^ ~` operators.

Convenience aliases include `B`/`BRA` for `JMP`, `JSR`/`BSR` for `CALL`,
`BEQ`/`BZ` for `JZ`, `BNE`/`BNZ` for `JNZ`, `BLT` for `JLT`, `BLE` for
`JLE`, `BGT` for `JGT`, `BGE` for `JGE`, `BLO`/`BCS` for `JB`/`JC`,
`BHS` for `JAE`, `BLS` for `JBE`, `BHI` for `JA`, `BMI` for `JN`, and
`BPL` for `JP`.

## Calling convention

There is no hard-wired ABI, but the demos use:

* arguments in `R0`, `R1`, ...;
* return value in `R0`;
* `CALL`/`RET` for the return address;
* `PUSH`/`POP` for saving registers around a call.

`CALL` pushes the address of the instruction after the call and jumps.  `RET`
pops that address.  The stack lives below `0x0FFF` and grows downward.

## Example: multiply by repeated addition

```asm
        .org 0
        LDI R0, 7          ; a
        LDI R1, 6          ; b
        LDI R2, 0          ; result
loop:
        CMPI R1, 0
        JZ   done
        ADD  R2, R0
        DEC  R1
        JMP  loop
done:
        OUT  R2            ; 42
        HALT
```
