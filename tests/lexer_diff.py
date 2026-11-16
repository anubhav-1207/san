#!/usr/bin/env python3
"""Differential checks for the C lexer against the Python reference lexer."""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scanner import Lexer as PythonLexer  # noqa: E402

TOKEN_RE = re.compile(r"^Token\(([^ :]+)(?::(.*?))? -> line - (\d+), col - (\d+)\)$")


def normalise(name):
    return "NAME" if name in ("IDENT", "KEYWORD") else name


def python_tokens(source):
    result = []
    for token in PythonLexer(source).tokenise():
        value = "" if token.token_value is None else str(token.token_value)
        result.append((normalise(token.type_), value, token.line))
    return result


def c_tokens(source):
    with tempfile.NamedTemporaryFile(suffix=".san", delete=False) as handle:
        handle.write(source.encode("utf-8"))
        path = handle.name
    try:
        proc = subprocess.run(
            [str(ROOT / "san"), "--tokens", path],
            capture_output=True, text=True, check=False,
        )
    finally:
        Path(path).unlink()

    result = []
    for line in proc.stdout.splitlines():
        if not line.startswith("Token("):
            continue
        match = TOKEN_RE.match(line)
        if match is None:
            raise AssertionError(f"unrecognised token line: {line!r}")
        name, value, line_no, _ = match.groups()
        if name == "NEWLINE":
            continue
        result.append((normalise(name), value or "", int(line_no)))
    return result


SNIPPETS = [
    'stdout("Hello, World!")',
    "dec x = 0\nflux x = x + 1",
    "dec a = [1, 2, 3]\nstdout(a[0])",
    "if (True) {\n  stdout(\"yes\")\n} elif (False) {\n  stdout(\"no\")\n} else {\n  stdout(\"?\")\n}",
    "while (x < 3) {\n  flux x = x + 1\n}",
    "for val in numbers {\n  stdout(val)\n}",
    "func add(a, b) {\n  return a + b\n}",
    "dec a = 7 / 2\nstdout(a ** 2)\nstdout(!a)",
    "stdout(1 == 2)\nstdout(1 != 2)\nstdout(1 >= 2)\nstdout(1 <= 2)",
    "stdout(True && False || True)",
    "stdout('single')\nstdout(\"double\")\nstdout(\"\")",
    "// line comment\nstdout(1) // trailing comment",
    "/* block comment */ stdout(2)",
    "stdout(3);;;;;;\nstdout(4)$#",
    "dec x: int = 5\nstdout(Null)",
    "stdout(1.5)\nstdout(2.)\nstdout(0.25)",
    "stdout(div)\nstdout(try)\nstdout(scan)",
]


def check_tokens():
    cases = []
    for path in sorted((ROOT / "tests").glob("*.san")):
        cases.append((path.name, path.read_text(encoding="utf-8")))
    for path in sorted((ROOT / "examples").glob("*.san")):
        cases.append((path.name, path.read_text(encoding="utf-8")))
    cases.extend((f"snippet {i}", src) for i, src in enumerate(SNIPPETS))

    failures = 0
    for name, source in cases:
        try:
            expected = python_tokens(source)
        except Exception as exc:  # reference lexer rejected it; skip in token diff
            print(f"SKIP {name}: reference lexer raised {type(exc).__name__}")
            continue
        actual = c_tokens(source)
        if expected != actual:
            failures += 1
            print(f"FAIL {name}")
            for index, (want, got) in enumerate(zip(expected, actual)):
                if want != got:
                    print(f"  token {index}: expected {want}, got {got}")
                    break
            if len(expected) != len(actual):
                print(f"  token count: expected {len(expected)}, got {len(actual)}")
        else:
            print(f"ok   {name} ({len(actual)} tokens)")
    return failures


ERROR_CASES = [
    ("stdout(7 % 2)", "#LEX001", "FATAL", "HIGH", "source.fatal", "1:10"),
    ('stdout("unterminated)', "#LEX002", "ERROR", "MEDIUM", "source.recursive", "1:8"),
    ("dec x = 1..2", "#LEX004", "ERROR", "LOW", "source.recursive", "1:9"),
    ("/* never closed", "#LEX005", "ERROR", "LOW", "source.recursive", "1:1"),
]


def check_errors():
    failures = 0
    for source, code, severity, security, class_name, position in ERROR_CASES:
        with tempfile.NamedTemporaryFile(suffix=".san", delete=False) as handle:
            handle.write(source.encode("utf-8"))
            path = handle.name
        try:
            proc = subprocess.run(
                [str(ROOT / "san"), path],
                capture_output=True, text=True, check=False,
            )
        finally:
            Path(path).unlink()

        expected = [
            f"[{severity} | SECURITY: {security}]",
            class_name + "::",
            f"lexer exited with error[{code}]",
            f"line:col {position}",
        ]
        missing = [part for part in expected if part not in proc.stderr]
        if missing or proc.returncode != 1:
            failures += 1
            print(f"FAIL error case {source!r}: missing {missing}, exit {proc.returncode}")
            print(proc.stderr, end="")
        else:
            print(f"ok   error case {code} {position}")
    return failures


def check_block_comment_lines():
    source = "/* block\ncomment */\nstdout(2)"
    with tempfile.NamedTemporaryFile(suffix=".san", delete=False) as handle:
        handle.write(source.encode("utf-8"))
        path = handle.name
    try:
        proc = subprocess.run(
            [str(ROOT / "san"), "--tokens", path],
            capture_output=True, text=True, check=False,
        )
    finally:
        Path(path).unlink()

    tokens = []
    for line in proc.stdout.splitlines():
        match = TOKEN_RE.match(line)
        if match and match.group(1) in ("IDENT", "KEYWORD"):
            tokens.append(match.group(3))
    if tokens != ["3"]:
        print(f"FAIL block comment line tracking: {tokens}")
        return 1
    print("ok   block comment line tracking")
    return 0


def check_multi_error():
    source = "stdout(7 % 2)\nstdout(\"oops)\nstdout(1..2)"
    with tempfile.NamedTemporaryFile(suffix=".san", delete=False) as handle:
        handle.write(source.encode("utf-8"))
        path = handle.name
    try:
        proc = subprocess.run(
            [str(ROOT / "san"), path], capture_output=True, text=True, check=False,
        )
    finally:
        Path(path).unlink()

    lines = proc.stderr.splitlines()
    codes = [re.search(r"error\[#(LEX\d+)\]", line) for line in lines]
    names = [match.group(1) for match in codes if match]
    if names != ["LEX001", "LEX002", "LEX004"]:
        print(f"FAIL multi-error ordering: {names}")
        print(proc.stderr, end="")
        return 1
    print("ok   multi-error collection and ordering")
    return 0


if __name__ == "__main__":
    failures = check_tokens() + check_errors() + check_block_comment_lines() + check_multi_error()
    if failures:
        print(f"{failures} check(s) failed")
        sys.exit(1)
    print("all lexer checks passed")
