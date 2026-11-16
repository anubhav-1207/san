#!/usr/bin/env python3
"""Run San programs through the C interpreter and check their observable output."""

import io
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scanner import Lexer as PythonLexer  # noqa: E402
from src.parser import Parser as PythonParser  # noqa: E402
from src.interpreter import Evaluator as PythonEvaluator  # noqa: E402


def run_c(source, stdin_text=""):
    with tempfile.NamedTemporaryFile(suffix=".san", delete=False) as handle:
        handle.write(source.encode("utf-8"))
        path = handle.name
    try:
        return subprocess.run(
            [str(ROOT / "san"), path],
            input=stdin_text, capture_output=True, text=True,
            check=False, timeout=20,
        )
    finally:
        Path(path).unlink()


def run_python(source, stdin_text=""):
    stream = io.StringIO()
    error = None
    old_input = sys.stdin
    if stdin_text:
        sys.stdin = io.StringIO(stdin_text)
    try:
        with redirect_stdout(stream):
            ast = PythonParser(PythonLexer(source).tokenise()).parse()
            PythonEvaluator().evaluate(ast)
    except Exception as exc:
        error = type(exc).__name__
    finally:
        sys.stdin = old_input
    return stream.getvalue(), error


def check_fixtures():
    failures = 0
    for path in sorted((ROOT / "tests").glob("*.san")):
        source = path.read_text(encoding="utf-8")
        expected, error = run_python(source)
        proc = run_c(source)
        if error is not None:
            if proc.returncode != 1:
                failures += 1
                print(f"FAIL {path.name}: reference raised {error}, C exited {proc.returncode}")
            else:
                print(f"ok   {path.name} (error: {error})")
            continue
        if proc.stdout != expected or proc.returncode != 0:
            failures += 1
            print(f"FAIL {path.name}")
            print(f"  expected: {expected!r}")
            print(f"  actual:   {proc.stdout!r} (exit {proc.returncode}) {proc.stderr}")
        else:
            print(f"ok   {path.name}")
    return failures


GOLDEN = [
    ('stdout("hello")\nstdout(1 + 2 * 3)', "hello\n7\n", ""),
    ('stdout(7 / 2)\nstdout(7 div 2)\nstdout(-7 div 2)\nstdout(2 ** 10)',
     "3.5\n3\n-4\n1024\n", ""),
    ("dec a = [1, 2, 3]\nstdout(a[1])\nstdout(a[0:2:1])\n"
     "append(a, 4)\nstdout(a)\npop(a, 0)\nstdout(a)\n"
     "insert(a, 1, 9)\nstdout(a)\ndel(a, 0)\nstdout(a)\nstdout(len(a))",
     "2\n[1, 2]\n[1, 2, 3, 4]\n[2, 3, 4]\n[2, 9, 3, 4]\n[9, 3, 4]\n3\n", ""),
    ('dec s = "héllo"\nstdout(len(s))\nstdout(s[1])\nstdout(reverse(s))\n'
     'stdout(strlen(s))\nstdout(emptystr(""))',
     "5\né\nolléh\n5\nTrue\n", ""),
    ('stdout(typeof(1))\nstdout(typeof(1.5))\nstdout(typeof("a"))\n'
     'stdout(typeof(True))\nstdout(typeof([1]))\nstdout(typeof(Null))',
     "int\nfloat\nstr\nbool\narray\nnull\n", ""),
    ("dec x = 1\nfunc f() {\n dec x = 9\n stdout(x)\n}\n"
     "f()\nstdout(x)\nfunc g() {\n flux x = x + 1\n return x\n}\nstdout(g())",
     "9\n1\n2\n", ""),
    ("dec a = [1, 2, 3, 4]\nfor v in a {\n if (v == 3) {\n break\n }\n"
     " stdout(v)\n}", "1\n2\n", ""),
    ("scan(x: int)\nstdout(x + 1)\nscan(b: bool)\nstdout(b)", "6\nTrue\n", "5\ntrue\n"),
    ("use math\nstdout(sin(0))\nstdout(floor(2.9))\nstdout(ceil(2.1))\nstdout(pi())",
     "0.0\n2\n3\n3.141592653589793\n", ""),
    ("func fact(n) {\n if (n <= 1) {\n  return 1\n }\n return n * fact(n - 1)\n}\n"
     "stdout(fact(6))", "720\n", ""),
    ("dec s = \"ab\"\nstdout(s * 3)\nstdout([1, 2] * 2)\n"
     "stdout(True + 1)\nstdout(1 == 1.0)", "ababab\n[1, 2, 1, 2]\n2\nTrue\n", ""),
]

ERRORS = [
    ("stdout(missing)", "#INTRPTR002"),
    ("const x = 1\nflux x = 2", "#INTRPTR003"),
    ("stdout(1 / 0)", "#INTRPTR004"),
    ("dec x = 1\ndec x = 2", "#INTRPTR001"),
    ("stdout(len())", "#INTRPTR007"),
    ("use nope", "#INTRPTR007"),
    ("use math\nstdout(log(0))", "#INTRPTR006"),
    ("stdout(missing())", "#INTRPTR005"),
]


def check_golden():
    failures = 0
    for source, expected, stdin_text in GOLDEN:
        proc = run_c(source, stdin_text)
        if proc.stdout != expected or proc.returncode != 0:
            failures += 1
            print(f"FAIL golden {source!r}")
            print(f"  expected: {expected!r}")
            print(f"  actual:   {proc.stdout!r} (exit {proc.returncode}) {proc.stderr}")
        else:
            print(f"ok   golden {source[:40]!r}")
    for source, code in ERRORS:
        proc = run_c(source)
        if code not in proc.stderr or proc.returncode != 1:
            failures += 1
            print(f"FAIL error {source!r}: expected {code}, got {proc.stderr!r}")
        else:
            print(f"ok   error {code} for {source!r}")
    return failures


if __name__ == "__main__":
    failures = check_fixtures() + check_golden()
    if failures:
        print(f"{failures} interpreter check(s) failed")
        sys.exit(1)
    print("all interpreter checks passed")
