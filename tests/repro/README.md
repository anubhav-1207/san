# San audit repros

Minimal programs used to reproduce the bugs in the San audit.

- **Tested against:** `origin/main` at `c6084ee`
- **Audited baseline:** `7ca7b3f`
- **Tested on:** 2026-11-24

Run a repro from the repository root:

```bash
python main.py tests/repro/<file>.san
```

Every program exits with status `1`, including successful ones, because of **P1-3**. Judge results by stdout/stderr, not `$?`.

`P2-7a` and `P2-7b` read from stdin:

```bash
printf 'False\n' | python main.py tests/repro/p2_7a_scan_bool.san
printf '41\n'    | python main.py tests/repro/p2_7b_scan_int.san
```

## P0

| File | Bug | Expected | Actual at `c6084ee` | Status |
|---|---|---|---|---|
| `p0_2_booleans.san` | P0-2 | `falsy`, `True`, `True` | `falsy`, `True`, `True`, `<class 'bool'>` | Fixed (the last line is P2-6) |

## P1

| File | Bug | Expected | Actual at `c6084ee` | Status |
|---|---|---|---|---|
| `p1_3_exit_status.san` | P1-3 | prints `55`, exit `0` | prints `55`, exit `1` | Still broken |
| `p1_4_short_circuit.san` | P1-4 | `no` | `ZeroDivisionError` | Still broken |
| `p1_5_elif_eager.san` | P1-5 | `if` | `if` | Fixed |
| `p1_6a_multiple_elif.san` | P1-6 | `c` | `TypeError: 'BinaryOpNode' object is not iterable` | Still broken |
| `p1_6b_single_elif.san` | P1-6 | `b` | `TypeError: 'BinaryOpNode' object is not iterable` | Still broken |
| `p1_7a_break_for.san` | P1-7 | `0`, `done` | `0`, `done` | Fixed |
| `p1_7b_break_nested_for.san` | P1-7 | `0`, `iter` ×3, `end` | `0`, `iter` ×3, `end` | Fixed |
| `p1_8_array_assign.san` | P1-8 | `99` | no output, no error | Still broken |
| `p1_9_dynamic_scoping.san` | P1-9 | `1` | `2` | Still broken |
| `p1_10_closures.san` | P1-10 | `7` | `UndefinedVariable: 'secret'` | Still broken |
| `p1_11a_dec_while.san` | P1-11 | `0`, `2`, `4` | `0`, then `AccidentalReassError: 'x'` | Still broken |
| `p1_11b_dec_for.san` | P1-11 | `0`, `2`, `4` | `0`, then `AccidentalReassError: 'x'` | Still broken |
| `p1_12a_extra_args.san` | P1-12 | arity error | `InsufficientFuncArgs` | Fixed for this case |
| `p1_12b_zero_param_extra_args.san` | P1-12 | arity error | `5` | Still broken |
| `p1_13a_undefined_arg.san` | P1-13 | `UndefinedVariable: 'missing'` | `UndefinedVariable: 'missing'` | Fixed for this case |
| `p1_13b_error_arg.san` | P1-13 | `ZeroDivisionError` | `TypeError: InsufficientFuncArgs.__init__() missing 1 required positional argument: 'col'` | Still broken |
| `p1_13c_oob_arg.san` | P1-13 | `OutOfBoundsError` | `TypeError: InsufficientFuncArgs.__init__() missing 1 required positional argument: 'col'` | Still broken |

## P2

| File | Bug | Expected | Actual at `c6084ee` | Status |
|---|---|---|---|---|
| `p2_1_string_brackets.san` | P2-1 | `hello (world) [x] {y}` | `hello (world) [x] {y}` | Fixed |
| `p2_2_string_escapes.san` | P2-2 | `a "quoted" word`, then `line1` / `line2` | `UnexpectedTokenError` at `quoted\` | Still broken |
| `p2_3_block_comment.san` | P2-3 | `ok` | `ok` | Fixed |
| `p2_4_typed_const.san` | P2-4 | `5` | `5` | Fixed |
| `p2_5_stdlib_debug_prints.san` | P2-5 | `1` | `[1, 2, 3] 1 9`, `1`, `1` | Still broken |
| `p2_6_typeof.san` | P2-6 | `int` (or a San type value) | `<class 'int'>` | Still broken |
| `p2_7a_scan_bool.san` | P2-7 | `False` for input `False` | `False` | Fixed |
| `p2_7b_scan_int.san` | P2-7 | `42` for input `41` | `42` | Control case |
| `p2_8_array_trailing_comma.san` | P2-8 | length `2`; `a[2]` out of bounds | `2`; `OutOfBoundsError` | Fixed |
| `p2_9_call_trailing_comma.san` | P2-9 | `3` | `InsufficientFuncArgs` (2 expected, 3 got) | Still broken |
| `p2_10a_toplevel_return.san` | P2-10 | San `return outside function` error | raw `src.interpreter.ReturnException: 5` traceback | Still broken |
| `p2_10b_toplevel_break.san` | P2-10 | San `break outside loop` error | raw `src.interpreter.BreakException` traceback | Still broken |
| `p2_11a_native_typeerror.san` | P2-11 | San runtime error | raw `TypeError: object of type 'int' has no len()` traceback | Still broken |
| `p2_11b_slice_step_zero.san` | P2-11 | San runtime error | raw `ValueError: slice step cannot be zero` traceback | Still broken |
| `p2_12_bounds.san` | P2-12 | bounds error with line/column | `OutOfBoundsError` with line/column | Fixed |
| `p2_13_truthiness.san` | P2-13 | `str-falsy`, `arr-falsy` (or documented rule) | `str-truthy`, `arr-truthy` | Still broken |
| `p2_14_const_mutation.san` | P2-14 | `ConstantMutation` | `ConstantMutation` | Fixed |

## P3

| File | Bug | Expected | Actual at `c6084ee` | Status |
|---|---|---|---|---|
| `p3_1_keywords.san` | P3-1 | `dec scantry` works | `UnexpectedTokenError` (`scantry` is a keyword) | Still broken |
| `p3_3_readme_array_assign.san` | P3-3 | `1` | `UndefinedVariable: 'name'` | Still broken |
| `p3_4_readme_iterrange.san` | P3-4 | `0`, `1`, `2` | `UndefinedFunc: 'iterrange'` | Still broken |
| `p3_7_block_scope.san` | P3-7 | tutorial says `temp` is not visible outside the block | `42` | Still broken / contradictory |
| `p3_8_division.san` | P3-8 | tutorial says `3` | `3.3333333333333335` | Still broken |

## Inspection-only checks

These bugs have no standalone `.san` repro.

| Bug | Command | Expected | Actual at `c6084ee` |
|---|---|---|---|
| P1-1 | `python -c "import app"` | imports successfully | imports successfully (with Flask installed) |
| P1-2 | `grep -n "tokenise" app.py` | single-value unpack | `tokens = lexer.tokenise()` |
| P2-15 | `sed -n '479,486p' src/interpreter.py` | `try/finally` restores environment | no `finally` |
| P2-16 | `sed -n '1118,1122p' app.py` | `debug=False`, `127.0.0.1` | `debug=True`, `0.0.0.0` |
| P3-2 | `grep -n "expect(TT_" src/parser.py` | list argument | line 394 uses a string |
| P3-5 | `grep -n -i "statically-scoped\|closure" README.md` | docs match implementation | claims static scoping and closures |
| P3-6 | `grep -n -i "elif" README.md` | docs match implementation | says `elif` is unsupported |
| P3-9 | `grep -n -i "strongly typed\|No type system" README.md` | one consistent story | both claims present |

## Fixed repros

These are included as regression cases:

- `p0_2_booleans.san`
- `p1_5_elif_eager.san`
- `p1_7a_break_for.san`
- `p1_7b_break_nested_for.san`
- `p1_12a_extra_args.san`
- `p1_13a_undefined_arg.san`
- `p2_1_string_brackets.san`
- `p2_3_block_comment.san`
- `p2_4_typed_const.san`
- `p2_7a_scan_bool.san`
- `p2_8_array_trailing_comma.san`
- `p2_12_bounds.san`
- `p2_14_const_mutation.san`
