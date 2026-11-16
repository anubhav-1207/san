#!/usr/bin/env python3
"""Assembler and runner for the SAN-16 CPU.

Usage:
    python3 tools/sanasm.py programs/hello.sasm
    python3 tools/sanasm.py programs/hello.sasm --run

The assembler emits build/<name>.san, which is the San CPU emulator followed
by the assembled PROGRAM image and a call to boot(PROGRAM, INPUT).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EMULATOR = ROOT / "emulator" / "cpu.san"
RUNNER = ROOT / "tools" / "run_san.py"

# ---------------------------------------------------------------------------
# Instruction table
# ---------------------------------------------------------------------------
# kind is one of: none, reg, reg_reg, reg_imm, branch, load, store, imm,
# halt, dbg
OPS: dict[str, tuple[int, str]] = {
    "NOP": (0, "none"),
    "HALT": (1, "halt"),
    "MOV": (2, "reg_reg"),
    "LDI": (3, "reg_imm"),
    "LD": (4, "load"),
    "ST": (5, "store"),
    "ADD": (6, "reg_reg"),
    "ADDI": (7, "reg_imm"),
    "SUB": (8, "reg_reg"),
    "SUBI": (9, "reg_imm"),
    "MUL": (10, "reg_reg"),
    "MULI": (11, "reg_imm"),
    "DIV": (12, "reg_reg"),
    "DIVI": (13, "reg_imm"),
    "MOD": (14, "reg_reg"),
    "MODI": (15, "reg_imm"),
    "AND": (16, "reg_reg"),
    "ANDI": (17, "reg_imm"),
    "OR": (18, "reg_reg"),
    "ORI": (19, "reg_imm"),
    "XOR": (20, "reg_reg"),
    "XORI": (21, "reg_imm"),
    "NOT": (22, "reg"),
    "SHL": (23, "reg_reg"),
    "SHLI": (24, "reg_imm"),
    "SHR": (25, "reg_reg"),
    "SHRI": (26, "reg_imm"),
    "ROL": (27, "reg_reg"),
    "ROR": (28, "reg_reg"),
    "CMP": (29, "reg_reg"),
    "CMPI": (30, "reg_imm"),
    "TST": (31, "reg_reg"),
    "INC": (32, "reg"),
    "DEC": (33, "reg"),
    "NEG": (34, "reg"),
    "SWAP": (35, "reg_reg"),
    "JMP": (36, "branch"),
    "JZ": (37, "branch"),
    "JNZ": (38, "branch"),
    "JC": (39, "branch"),
    "JNC": (40, "branch"),
    "JN": (41, "branch"),
    "JP": (42, "branch"),
    "JV": (43, "branch"),
    "JNV": (44, "branch"),
    "CALL": (45, "branch"),
    "RET": (46, "none"),
    "PUSH": (47, "reg"),
    "POP": (48, "reg"),
    "OUT": (49, "reg"),
    "OUTI": (50, "imm"),
    "OUTC": (51, "reg"),
    "OUTS": (52, "reg"),
    "OUTH": (53, "reg"),
    "IN": (54, "reg"),
    "RAND": (55, "reg"),
    "TIME": (56, "reg"),
    "CLF": (57, "none"),
    "DIVS": (58, "reg_reg"),
    "MODS": (59, "reg_reg"),
    "SHRS": (60, "reg_reg"),
    "MULH": (61, "reg_reg"),
    "JLE": (62, "branch"),
    "JGT": (63, "branch"),
    "JGE": (64, "branch"),
    "JLT": (65, "branch"),
    "JBE": (66, "branch"),
    "JA": (67, "branch"),
    "JAE": (68, "branch"),
    "JB": (69, "branch"),
    "DBG": (70, "dbg"),
    "JMPR": (71, "reg"),
    "CALLR": (72, "reg"),
    "ADDC": (73, "reg_reg"),
    "SUBC": (74, "reg_reg"),
    "ROLI": (75, "reg_imm"),
    "RORI": (76, "reg_imm"),
    "SHRSI": (77, "reg_imm"),
    "PUSHI": (78, "imm"),
}

ALIASES = {
    "B": "JMP",
    "BRA": "JMP",
    "JSR": "CALL",
    "BSR": "CALL",
    "JEQ": "JZ",
    "BEQ": "JZ",
    "BZ": "JZ",
    "BNE": "JNZ",
    "BNZ": "JNZ",
    "BMI": "JN",
    "BPL": "JP",
    "BLO": "JB",
    "BCS": "JC",
    "BCC": "JNC",
    "BHS": "JAE",
    "BLS": "JBE",
    "BHI": "JA",
    "BLE": "JLE",
    "BGT": "JGT",
    "BGE": "JGE",
    "BLT": "JLT",
}


class AsmError(Exception):
    pass


def strip_comment(line: str) -> str:
    """Remove ; and // comments while respecting quoted strings."""
    out: list[str] = []
    quote = ""
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < len(line):
                out.append(line[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == ";":
            break
        if ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def split_operands(text: str) -> list[str]:
    """Split on commas outside [] and quotes."""
    parts: list[str] = []
    cur: list[str] = []
    depth = 0
    quote = ""
    for ch in text:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "'\"":
            quote = ch
            cur.append(ch)
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    return parts


def unescape_string(text: str) -> list[int]:
    """Turn a quoted assembler string into a list of character codes."""
    if len(text) < 2 or text[0] not in "'\"" or text[-1] != text[0]:
        raise AsmError(f"bad string literal: {text}")
    body = text[1:-1]
    result: list[int] = []
    i = 0
    escapes = {
        "n": 10,
        "r": 13,
        "t": 9,
        "0": 0,
        "\\": 92,
        '"': 34,
        "'": 39,
    }
    while i < len(body):
        ch = body[i]
        if ch == "\\":
            if i + 1 >= len(body):
                raise AsmError("trailing backslash in string")
            nxt = body[i + 1]
            if nxt == "x":
                hexpart = body[i + 2 : i + 4]
                if len(hexpart) != 2 or not re.fullmatch(r"[0-9a-fA-F]{2}", hexpart):
                    raise AsmError("bad \\x escape")
                result.append(int(hexpart, 16))
                i += 4
                continue
            if nxt in escapes:
                result.append(escapes[nxt])
            else:
                result.append(ord(nxt))
            i += 2
            continue
        result.append(ord(ch))
        i += 1
    return result


def parse_reg(text: str) -> int:
    t = text.strip().upper()
    if t == "SP":
        return 15
    m = re.fullmatch(r"R(\d+)", t)
    if not m:
        raise AsmError(f"expected register, got {text!r}")
    n = int(m.group(1))
    if n < 0 or n > 15:
        raise AsmError(f"register out of range: {text!r}")
    return n


def parse_mem(text: str) -> tuple[int, str]:
    """Parse [R2+expr] or [R2-expr]."""
    m = re.fullmatch(r"\[\s*([A-Za-z0-9_]+)\s*(.*?)\s*\]", text)
    if not m:
        raise AsmError(f"bad memory operand: {text!r}")
    reg = parse_reg(m.group(1))
    rest = m.group(2).strip()
    if rest == "":
        return reg, "0"
    if rest[0] not in "+-":
        raise AsmError(f"bad memory offset: {text!r}")
    sign = "" if rest[0] == "+" else "-"
    return reg, sign + rest[1:].strip()


class Assembler:
    def __init__(self) -> None:
        self.symbols: dict[str, int] = {}
        self.items: list[tuple[int, str, Any, int, int]] = []
        self.address = 0
        self.inputs: list[int] = []

    def expr(self, text: str, current: int | None = None) -> int:
        """Evaluate an assembler expression."""
        text = text.strip()
        if not text:
            raise AsmError("empty expression")

        def char_repl(m: re.Match[str]) -> str:
            body = m.group(1)
            if body.startswith("\\"):
                return str(unescape_string("'" + body + "'")[0])
            return str(ord(body))

        text = re.sub(r"'(\\.|[^'])'", char_repl, text)

        def ident_repl(m: re.Match[str]) -> str:
            name = m.group(0)
            if name in self.symbols:
                return str(self.symbols[name])
            raise AsmError(f"unknown symbol: {name}")

        text = re.sub(r"\b[A-Za-z_][A-Za-z0-9_.]*\b", ident_repl, text)
        if current is not None:
            text = text.replace("$", str(current))
        try:
            value = eval(text, {"__builtins__": {}}, {})  # noqa: S307 - local assembler
        except Exception as exc:  # noqa: BLE001
            raise AsmError(f"cannot evaluate expression {text!r}: {exc}") from exc
        return int(value)

    def first_pass(self, lines: list[tuple[int, str]]) -> None:
        for lineno, original in lines:
            line = strip_comment(original).strip()
            if not line:
                continue

            # labels
            while True:
                m = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*)\s*:\s*(.*)$", line)
                if not m:
                    break
                name = m.group(1)
                if name in self.symbols:
                    raise AsmError(f"line {lineno}: duplicate label {name}")
                self.symbols[name] = self.address
                line = m.group(2).strip()
            if not line:
                continue

            low = line.lower()
            if low.startswith(".equ") or low.startswith(".set"):
                body = line.split(None, 1)[1]
                parts = split_operands(body)
                if len(parts) != 2:
                    raise AsmError(f"line {lineno}: .equ needs NAME, value")
                self.symbols[parts[0].strip()] = self.expr(parts[1], self.address)
                continue

            if low.startswith(".org"):
                body = line.split(None, 1)[1]
                self.address = self.expr(body, self.address)
                if self.address < 0 or self.address > 65535:
                    raise AsmError(f"line {lineno}: .org out of range")
                continue

            if low.startswith(".align"):
                body = line.split(None, 1)[1]
                n = self.expr(body, self.address)
                if n <= 0:
                    raise AsmError(f"line {lineno}: bad .align")
                rem = self.address % n
                if rem:
                    self.address += n - rem
                continue

            if low.startswith(".input"):
                body = line.split(None, 1)[1]
                for part in split_operands(body):
                    self.inputs.append(self.expr(part, self.address) & 0xFFFF)
                continue

            if low.startswith(".word"):
                body = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""
                parts = split_operands(body) if body else []
                self.items.append((self.address, "word", parts, lineno, 1))
                self.address += max(0, len(parts))
                continue

            if low.startswith(".fill"):
                body = line.split(None, 1)[1]
                parts = split_operands(body)
                if len(parts) not in (1, 2):
                    raise AsmError(f"line {lineno}: .fill COUNT[, value]")
                count = self.expr(parts[0], self.address)
                value = self.expr(parts[1], self.address) if len(parts) == 2 else 0
                self.items.append((self.address, "fill", (count, value), lineno, count))
                self.address += count
                continue

            if low.startswith(".string") or low.startswith(".asciz") or low.startswith(".cstr"):
                directive = line.split(None, 1)[0].lower()
                body = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""
                codes = unescape_string(body.strip())
                if directive in (".asciz", ".cstr"):
                    codes.append(0)
                self.items.append((self.address, "bytes", codes, lineno, len(codes)))
                self.address += len(codes)
                continue

            # instruction
            mnemonic, _, rest = line.partition(" ")
            mnemonic = mnemonic.upper()
            mnemonic = ALIASES.get(mnemonic, mnemonic)
            if mnemonic not in OPS:
                raise AsmError(f"line {lineno}: unknown instruction {mnemonic!r}")
            self.items.append((self.address, "insn", (mnemonic, rest.strip()), lineno, 2))
            self.address += 2

    def second_pass(self) -> list[int]:
        image: dict[int, int] = {}

        def put(addr: int, value: int) -> None:
            if addr < 0 or addr > 65535:
                raise AsmError(f"address out of range: {addr}")
            image[addr] = value & 0xFFFF

        for addr, kind, payload, lineno, _size in self.items:
            if kind == "word":
                for i, part in enumerate(payload):
                    put(addr + i, self.expr(part, addr + i))
                continue
            if kind == "fill":
                count, value = payload
                v = self.expr(str(value), addr) if isinstance(value, str) else value
                for i in range(count):
                    put(addr + i, v)
                continue
            if kind == "bytes":
                for i, code in enumerate(payload):
                    put(addr + i, code)
                continue

            mnemonic, rest = payload
            opcode, kindname = OPS[mnemonic]
            args = split_operands(rest) if rest else []
            rd = 0
            rs = 0
            imm = 0

            try:
                if kindname == "none":
                    if mnemonic == "HALT":
                        if args:
                            imm = self.expr(args[0], addr)
                    elif args:
                        raise AsmError(f"{mnemonic} takes no operands")
                elif kindname == "halt":
                    imm = self.expr(args[0], addr) if args else 0
                elif kindname == "dbg":
                    if args:
                        raise AsmError("DBG takes no operands")
                elif kindname == "reg":
                    if len(args) != 1:
                        raise AsmError(f"{mnemonic} needs one register")
                    if mnemonic in ("POP", "OUTS", "IN", "RAND", "TIME", "INC", "DEC", "NEG", "NOT"):
                        rd = parse_reg(args[0])
                    else:
                        rs = parse_reg(args[0])
                elif kindname == "reg_reg":
                    if len(args) != 2:
                        raise AsmError(f"{mnemonic} needs two registers")
                    rd = parse_reg(args[0])
                    rs = parse_reg(args[1])
                elif kindname == "reg_imm":
                    if len(args) != 2:
                        raise AsmError(f"{mnemonic} needs REG, IMM")
                    rd = parse_reg(args[0])
                    imm = self.expr(args[1], addr)
                elif kindname == "branch":
                    if len(args) != 1:
                        raise AsmError(f"{mnemonic} needs a target")
                    imm = self.expr(args[0], addr)
                elif kindname == "imm":
                    if len(args) != 1:
                        raise AsmError(f"{mnemonic} needs IMM")
                    imm = self.expr(args[0], addr)
                elif kindname == "load":
                    if len(args) != 2:
                        raise AsmError("LD needs RD, [RS+offset]")
                    rd = parse_reg(args[0])
                    rs, off = parse_mem(args[1])
                    imm = self.expr(off, addr)
                elif kindname == "store":
                    if len(args) != 2:
                        raise AsmError("ST needs [RD+offset], RS")
                    rd, off = parse_mem(args[0])
                    rs = parse_reg(args[1])
                    imm = self.expr(off, addr)
                elif kindname == "halt":
                    imm = self.expr(args[0], addr) if args else 0
                else:
                    raise AsmError(f"internal: bad kind {kindname}")
            except AsmError as exc:
                raise AsmError(f"line {lineno}: {exc}") from exc

            word0 = ((opcode & 0xFF) << 8) | ((rd & 0xF) << 4) | (rs & 0xF)
            put(addr, word0)
            put(addr + 1, imm)

        if not image:
            return []
        top = max(image)
        return [image.get(i, 0) for i in range(top + 1)]

    def assemble(self, source: str) -> tuple[list[int], list[int]]:
        lines = list(enumerate(source.splitlines(), 1))
        self.first_pass(lines)
        image = self.second_pass()
        return image, self.inputs


def san_array(values: list[int], per_line: int = 16) -> str:
    if not values:
        return "[]"
    chunks = []
    for i in range(0, len(values), per_line):
        chunks.append(", ".join(str(v) for v in values[i : i + per_line]))
    return "[\n    " + ",\n    ".join(chunks) + "\n]"


def build(source_path: Path, output: Path, emulator: Path, run: bool, cycles: bool = False) -> Path:
    source = source_path.read_text(encoding="utf-8")
    asm = Assembler()
    image, inputs = asm.assemble(source)
    if not image:
        raise AsmError("program is empty")

    emulator_text = emulator.read_text(encoding="utf-8")
    parts = [
        "// ============================================================",
        f"// Generated by tools/sanasm.py from {source_path.name}",
        "// Do not edit by hand; edit the .sasm source instead.",
        "// ============================================================",
        emulator_text,
        "",
        f"// {len(image)} words of assembled program memory",
        f"dec PROGRAM = {san_array(image)}",
        "",
        f"dec INPUT = {san_array(inputs)}",
        "",
        "dec GUEST_EXIT = boot(PROGRAM, INPUT)",
        "",
    ]
    if cycles:
        parts.extend([
            'stdout("cycles:")',
            "stdout(INSTR_COUNT)",
            "",
        ])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")

    listing = output.with_suffix(".lst")
    listing_lines = [f"; {source_path.name}", "; addr  word   source"]
    for addr, kind, payload, _lineno, _size in asm.items:
        if kind == "insn":
            mnemonic, rest = payload
            w0 = image[addr] if addr < len(image) else 0
            w1 = image[addr + 1] if addr + 1 < len(image) else 0
            listing_lines.append(
                f"{addr:04X}  {w0:04X} {w1:04X}  {mnemonic} {rest}".rstrip()
            )
        elif kind == "word":
            listing_lines.append(f"{addr:04X}  .word      {', '.join(map(str, payload))}")
        elif kind == "bytes":
            listing_lines.append(f"{addr:04X}  .string    {len(payload)} words")
        elif kind == "fill":
            listing_lines.append(f"{addr:04X}  .fill      {payload[0]}")
    listing.write_text("\n".join(listing_lines) + "\n", encoding="utf-8")

    if run:
        print(f"built {output}")
        result = subprocess.run(
            [sys.executable, str(RUNNER), str(output)],
            cwd=str(ROOT),
            check=False,
        )
        print(f"[exit {result.returncode}]")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="SAN-16 assembler")
    parser.add_argument("source", type=Path, help=".sasm source file")
    parser.add_argument("-o", "--output", type=Path, help="output .san file")
    parser.add_argument("--emulator", type=Path, default=EMULATOR)
    parser.add_argument("--run", action="store_true", help="run after building")
    parser.add_argument("--cycles", action="store_true", help="print executed instruction count")
    args = parser.parse_args()

    output = args.output or (ROOT / "build" / (args.source.stem + ".san"))
    try:
        build(args.source, output, args.emulator, args.run, args.cycles)
    except AsmError as exc:
        print(f"asm error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
