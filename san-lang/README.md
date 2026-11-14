# San interpreter (vendored)

This directory is a local copy of the [San programming language](https://github.com/anubhav-1207/san)
interpreter by Anubhav G., used to run `../neural_net.san`.

Upstream San is MIT licensed; see `LICENSE` in this directory.

## Changes from upstream

- `colorama.py`: a tiny stand-in for the `colorama` package, which supplies only
  `Fore` colour constants and `init()`. The real package is not installed and
  this environment has no package index access.
- `src/interpreter.py`: two bug fixes.
  - `Environment.reassign_var` now passes the variable token when recursing to
    the parent scope. Previously `flux` on a global variable from inside a
    function raised `AttributeError`.
  - `Environment.lookup` now passes the token to the parent lookup as well.
- `src/stdlib/native_math.py`: keeps the upstream public names (`sin`, `cos`,
  `exp`, `floor`, `tanh`, `pi`, ...), adds `log`/`log2`/`log10`, and normalises
  argument handling. Upstream had a few incorrect `args[(1,)]` indexes and
  nested argument-count tuples; this copy uses plain `args[0]`, `args[1]` and
  `(n,)`.

Everything else follows the upstream `main` branch.

## Run

```bash
python3 main.py ../neural_net.san
```

`main.py` always exits with status 1, even when the program succeeds.
