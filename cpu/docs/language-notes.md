# San bugs and quirks found by SAN-16

The emulator is intentionally written in ordinary San, with no changes to the
interpreter.  Getting a 16-bit CPU, assembler-generated images, memory,
strings and output through the current implementation exposed a number of
language issues.  They are listed here both as a record and as a small bug
list for the language.

## 1. `dec name = ""` silently truncates the program

This is the most dangerous one because it produces no error.  The `dec` branch
of `Parser.parse_statements` only parses a value when the current token's
`token_value` is truthy:

```python
if self.current_token.token_value:
    var_value_node = self.parse_comp_expr()
    return VarAssignNode(...)
```

An empty string token has `token_value == ""`, so the branch falls through and
returns `None`.  `Parser.parse` stops at the first falsy statement, silently
discarding every statement after it.

Reproduction:

```c
dec x = ""
stdout("this never runs")
```

No output, no error.

Workaround used by the emulator:

```c
dec OUTBUF = setstr("")
```

Suggested fix: test `self.current_token.type_ != TT_EOF` (or always call
`parse_comp_expr`) instead of testing `token_value`.

## 2. String literals cannot contain `()`, `[]` or `{}`

`Lexer.read_strings` raises `UnterminatedStringLiteral` when it encounters any
of these characters while reading a quoted string:

```python
elif self.current_char() in ('(',')','[',']','{','}'):
    raise UnterminatedStringLiteral(self.line, self.col)
```

So `stdout("(hello)")` is a lexer error, and even a string containing a single
`[` cannot be written.  This is why SAN-16 builds printable ASCII from safe
string chunks.

The two bracket pairs that can still be obtained come from Python's `repr`
through `setstr`:

```c
const PARENS = setstr(())     // "()"
const BRACKETS = setstr([])   // "[]"
```

Curly braces cannot be produced at all, so `OUTC 123` and `OUTC 125` currently
print `.`.  Every other printable ASCII code is supported.

Suggested fix: remove the bracket check from `read_strings`; the closing quote
check already handles termination.

## 3. No array-element assignment

There is an `ArrayAssignNode` class in `ast_nodes.py`, but the parser never
constructs it.  Statements such as

```c
flux memory[address] = value
```

are not parsed as an assignment.  Only whole variables can be reassigned, and
`append`/`pop`/`insert`/`del` are the only array mutations exposed.

SAN-16 uses one-element arrays as mutable cells:

```c
dec cell = MEM[address]
del(cell, 0)
append(cell, value)
```

Because Python lists are passed by reference, this mutates the cell in place.
Reading is `dec c = MEM[address]; return c[0]`.  It works, but it means a
memory cell costs a Python list and every access goes through San function
calls.

Suggested fix: parse `lvalue[index] = expr` into `ArrayAssignNode` and have the
interpreter assign into the underlying list.

## 4. `break` inside `for` is not caught

`visit_WhileNode` catches `BreakException`; `visit_ForNode` does not:

```python
for i in iterable:
    ...
    for stmt in statements:
        result = self.evaluate(stmt)
```

A `break` in a `for` body escapes all the way out of the program and is not in
`main.py`'s exception tuple, so it produces a traceback.  The emulator uses
`while` loops whenever a `break` would be natural.

Suggested fix: wrap the loop body in `try: ... except BreakException: break`,
the same way `visit_WhileNode` does.

## 5. `pop()` and `insert()` print debug output

`src/stdlib/native_arrays.py` contains:

```python
def native_pop(args):
    ...
    print(array[index])
    return array.pop(index)

def native_insert(args):
    ...
    print(array, index, element)
    return array.insert(index, element)
```

Any program that uses these functions gets unsolicited output mixed into its
real output.  The emulator avoids both and uses only `append`, `del` and
indexing.  The prints look like leftover debugging and should be removed.

## 6. `const` cannot declare an array

`Parser.parse_statements` explicitly raises `ConstantArrayError` for
`const xs = [1, 2, 3]`.  This is surprising for a language that advertises
immutable bindings.  The emulator uses `dec` for arrays.

## 7. No modulo or bitwise operators

The lexer has symbols for `%`, `&`, `|` and `^`, but the parser only handles
`&&` and `||`.  A single `%` is tokenised and then produces a parse error or
stops the file.  There are no `&`, `|`, `^`, `~`, `<<` or `>>` expression
operators.

SAN-16 implements:

* modulo as `a - floor(a / b) * b`;
* bitwise AND/OR/XOR as 16-iteration loops over the low bit (`mod(x, 2)`,
  `floor(x / 2)`);
* shifts as multiplication/division by powers of two;
* `NOT` as `65535 - x`.

This is correct but slow.  Native `%`, `&`, `|`, `^`, `~`, `<<`, `>>` would
make the CPU several times faster.

## 8. Only one `elif` per `if`

The parser handles a single optional `elif`; a second `elif` is not consumed as
part of the same chain.  The emulator uses nested `if`/`else` blocks or early
`return`s instead.

## 9. `while` does not create a scope

A `dec` executed inside a `while` body is defined in the surrounding scope.  On
the second iteration it raises `AccidentalReassError`.  Loop-local variables
must be declared before the loop and updated with `flux`.  This affects the
emulator's bit-operation loops, memory growth loops and register handling.

## 10. Several math wrappers are broken

Not needed by the CPU, but noticed while reading the stdlib:

* `ceil()` calls `mathfloor` instead of `mathceil`.
* `atan()` calls `mathacos`.
* `copysign`, `power`, `dist` and `remainder` index `args[(1,)]` (a tuple key)
  instead of `args[1]`.
* `ldexp` only reads one argument but calls the two-argument `math.ldexp`.
* `expm1` builds a function from `mathexpm(1,)`.

The emulator only relies on `floor` (math), `randint` (random) and `time`
(time), all of which work.

## 11. Input is statement-only

`scan(x: int)` is a statement, not an expression, and there is no native
`input()`/`read()` function.  A CPU `IN` instruction cannot pause the
instruction loop and read from the terminal.  SAN-16 therefore uses a
preloaded input stream (the assembler's `.input` directive) and returns zero
when it is exhausted.  A native `readint()`/`readline()` would make interactive
I/O possible.

## 12. Useful pieces of the implementation

For anyone extending San after reading this:

* `Environment.reassign_var` walks parent scopes, so `flux` on a global from
  inside a function works (the `global_scope.san` regression test covers it).
* Function environments are fresh per call, so recursion works.
* `return` raises `ReturnException` and is caught by `visit_FuncCallNode`,
  which also makes early returns inside `if`/`while` work.
* Arrays are Python lists, so `append`, `del` and indexing are O(1) (except
  `del` at the front), and arrays passed to functions are shared, not copied.
