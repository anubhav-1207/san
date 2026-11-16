#!/usr/bin/env python3
"""Compare the C parser's canonical AST with the Python reference parser."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scanner import Lexer as PythonLexer  # noqa: E402
from src.parser import Parser as PythonParser  # noqa: E402


def quote(value):
    return json.dumps(str(value), ensure_ascii=True)


def token_value(token):
    return "" if token is None or token.token_value is None else str(token.token_value)


def canonical_list(nodes):
    return "[" + " ".join(canonical(node) for node in nodes) + "]"


def canonical(node):
    if node is None:
        return "-"
    name = node.__class__.__name__

    if name == "ProgramNode":
        return f"(Program {canonical_list(node.statements)})"
    if name == "NumberNode":
        return f"(Number {quote(node.number)})"
    if name == "BooleanLiteral":
        return f"(Bool {'True' if node.value else 'False'})"
    if name == "StringLiteral":
        return f"(String {quote(node.value)})"
    if name == "NullLiteral":
        return "(Null)"
    if name == "UnaryOpNode":
        return f"(Unary {quote(node.op)} {canonical(node.value)})"
    if name == "BinaryOpNode":
        return f"(Binary {quote(token_value(node.op))} {canonical(node.left)} {canonical(node.right)})"
    if name == "VarAssignNode":
        kind = "const" if node.is_const else "dec"
        return f"(VarAssign {quote(token_value(node.var_name_token))} {kind} {canonical(node.value_node)})"
    if name == "VarReassignNode":
        return f"(VarReassign {quote(token_value(node.var_name_token))} {canonical(node.value_node)})"
    if name == "VarAccessNode":
        return f"(VarAccess {quote(token_value(node.var_name_token))})"
    if name == "ArrayLiteralNode":
        return f"(Array {canonical_list(node.elements)})"
    if name == "IndexingNode":
        return f"(Index {quote(token_value(node.array))} {canonical(node.start_index)})"
    if name == "SlicingNode":
        return (f"(Slice {quote(token_value(node.array))} {canonical(node.start_index)} "
                f"{canonical(node.end_index)} {canonical(node.steps)})")
    if name == "TupleLiteralNode":
        return f"(Tuple {canonical_list(node.elements)})"
    if name == "FuncCallNode":
        return f"(Call {quote(token_value(node.func_name))} {canonical_list(node.func_args)})"
    if name == "FuncDefNode":
        params = " ".join(quote(token_value(p)) for p in node.func_params)
        return f'(FuncDef {quote(token_value(node.func_name))} ({params}) {canonical_list(node.func_body)})'
    if name == "ReturnNode":
        return f"(Return {canonical(node.value)})"
    if name == "BreakNode":
        return "(Break)"
    if name == "IfNode":
        elifs = []
        if node.elif_condition is not None:
            elifs.append(f"(Elif {canonical(node.elif_condition)} {canonical_list(node.elif_body or [])})")
        else_body = canonical_list(node.else_body) if node.else_body else "[]"
        return (f"(If {canonical(node.if_condition)} {canonical_list(node.if_body)} "
                f"[{' '.join(elifs)}] {else_body})")
    if name == "WhileNode":
        return f"(While {canonical(node.condition)} {canonical_list(node.while_body)})"
    if name == "ForNode":
        variable = canonical(node.variable).removeprefix("(VarAccess ").removesuffix(")")
        return (f"(For {variable} {canonical(node.iterable)} "
                f"{canonical_list(node.statements)})")
    if name == "ScanNode":
        return f"(Scan {quote(token_value(node.variable))} {quote(node.type_)})"
    if name == "UseNode":
        return f"(Use {quote(token_value(node.library))})"
    raise AssertionError(f"unhandled AST node: {name}")


SNIPPETS = [
    'dec x = 1 + 2 * 3 ** 4',
    'dec y: int = 5\nconst z: float = 2.5',
    'dec a = [1, 2, 3]\nstdout(a[0])\nstdout(a[1:2:1])',
    'dec t = (1, 2, 3)\nstdout(t)',
    'dec n = 0\nflux n = n + 1',
    'if (True) {\n stdout(1)\n} elif (False) {\n stdout(2)\n} else {\n stdout(3)\n}',
    'while (x < 3) {\n flux x = x + 1\n}',
    'func add(a, b) {\n return a + b\n}',
    'for v in items {\n stdout(v)\n}',
    'stdout(!True)\nstdout(-5)\nstdout(+3)',
    'scan(value: int)\nuse math',
    'stdout(Null)',
    'dec s = "hi"\nstdout(s[0])',
]


def c_ast(source):
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

    lines = [line for line in proc.stdout.splitlines() if not line.startswith("Token(")]
    if not lines:
        raise AssertionError(f"no AST from C parser; stderr: {proc.stderr}")
    return " ".join(line.strip() for line in lines)


def check():
    cases = []
    for path in sorted((ROOT / "tests").glob("*.san")):
        cases.append((path.name, path.read_text(encoding="utf-8")))
    for path in sorted((ROOT / "examples").glob("*.san")):
        cases.append((path.name, path.read_text(encoding="utf-8")))
    cases.extend((f"snippet {i}", src) for i, src in enumerate(SNIPPETS))

    failures = 0
    for name, source in cases:
        try:
            expected = canonical(PythonParser(PythonLexer(source).tokenise()).parse())
        except Exception as exc:
            print(f"SKIP {name}: reference parser raised {type(exc).__name__}")
            continue
        actual = c_ast(source)
        if expected != actual:
            failures += 1
            print(f"FAIL {name}")
            print(f"  expected: {expected}")
            print(f"  actual:   {actual}")
        else:
            print(f"ok   {name}")
    return failures


def run_c(source):
    with tempfile.NamedTemporaryFile(suffix=".san", delete=False) as handle:
        handle.write(source.encode("utf-8"))
        path = handle.name
    try:
        return subprocess.run(
            [str(ROOT / "san"), "--tokens", path],
            capture_output=True, text=True, check=False,
        )
    finally:
        Path(path).unlink()


C_ONLY = [
    ("const z: float = 2.5", 0, None, '(VarAssign "z" const (Number "2.5"))'),
    ("stdout(1 div 2)", 0, None, '(Binary "div" (Number "1") (Number "2"))'),
    ("dec x = )\nstdout(1)", 1, "#PAR001", '(Call "stdout" [(Number "1")])'),
    ("if (a) {\n}", 1, "#PAR002", None),
    ("func f() {\n}", 1, "#PAR003", None),
    ("const a = [1, 2]", 1, "#PAR003", None),
]


def check_c_only():
    failures = 0
    for source, expected_status, code, fragment in C_ONLY:
        proc = run_c(source)
        problems = []
        if proc.returncode != expected_status:
            problems.append(f"exit {proc.returncode}, expected {expected_status}")
        if code is not None and code not in proc.stderr:
            problems.append(f"missing {code}")
        if fragment is not None and fragment not in proc.stdout:
            problems.append(f"missing AST fragment {fragment}")
        if code is not None:
            if "parser exited with error" not in proc.stderr:
                problems.append("missing phase text")
            if "source.fatal" not in proc.stderr and "source.recursive" not in proc.stderr:
                problems.append("missing source class")
        if problems:
            failures += 1
            print(f"FAIL C-only case {source!r}: {', '.join(problems)}")
            print(proc.stderr, end="")
        else:
            print(f"ok   C-only case {source!r}")
    return failures


def check_elif_chain():
    source = ("if (a) {\n stdout(1)\n} elif (b) {\n stdout(2)\n} "
              "elif (c) {\n stdout(3)\n} else {\n stdout(4)\n}")
    proc = run_c(source)
    if proc.stdout.count("(Elif ") != 2 or proc.returncode != 0:
        print(f"FAIL elif chain: {proc.stdout.strip()} / {proc.stderr}")
        return 1
    print("ok   multiple elif branches")
    return 0


if __name__ == "__main__":
    failures = check() + check_c_only() + check_elif_chain()
    if failures:
        print("parser checks failed")
        sys.exit(1)
    print("all parser checks passed")
