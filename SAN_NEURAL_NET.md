# A neural network from scratch in San

This project learns the [San programming language](https://github.com/anubhav-1207/san)
by Anubhav G. and uses it to build a small multilayer perceptron with no ML
library: the forward pass, sigmoid activation, loss, backpropagation and SGD are
all written in San itself.

## Files

| Path | Purpose |
| --- | --- |
| `neural_net.san` | The network: 2 inputs -> 4 hidden sigmoid units -> 1 output, trained on XOR |
| `san-lang/` | A local copy of the San interpreter (MIT), so the program can actually be run here |
| `san-lang/colorama.py` | Tiny local shim: `colorama` is not installed and this machine has no package index |
| `san-lang/src/stdlib/native_math.py` | Same public API as upstream, with normalised argument handling |
| `verification/ref_nn.py` | Independent Python mirror used to verify the San results |

San source is MIT licensed, copyright (c) 2026 Anubhav G. See
`san-lang/LICENSE`. The interpreter is vendored unchanged apart from two small
bug fixes and the stdlib notes above:

- `Environment.reassign_var` passed a string to the parent environment instead
  of the variable token, so `flux` on a global from inside a function crashed.
- `Environment.lookup` had the same token/string mismatch on the parent path.

## Running it

```bash
cd san-lang
python3 main.py ../neural_net.san
```

The interpreter exits with status 1 even on success; that is upstream behaviour
in `main.py`.

## What San is like

San is a dynamically typed, tree-walking interpreted language written in Python.
Its syntax deliberately borrows from C, Python and Rust:

```san
use math

dec count = 0          // mutable binding
const RATE = 0.7       // immutable binding
flux count = count + 1 // explicit reassignment

func square(x) {
    return x * x
}

for i in getrange(0, 5) {
    stdout(square(i))
}
```

Core ideas:

- **Bindings**: `dec` declares, `flux` reassigns, `const` is immutable.
  Re-declaring with `dec` is an error; that matters inside loops (see below).
- **Functions** live in a global function table. Recursion works, but functions
  are not values and are not closures.
- **Arrays** are mutable Python lists; `append`, `pop`, `insert`, `del`, `len`
  are built in. Indexing and slicing (`a[1]`, `a[1:3:1]`, `a[::-1]`) work.
- **Libraries**: `use math`, `use random`, `use time`.
- **Control flow**: `if / elif / else`, `while`, `for x in iterable`, `break`
  (only in `while`), `return`.

### Quirks that shaped the implementation

1. **`/` is floor division.** The interpreter maps `/` to Python `//`. So
   `1 / (1 + exp(-x))` is `0.0`, which silently breaks the usual sigmoid.
   This project writes `sigmoid(x) = (1 + exp(-x)) ** -1` instead, using a
   negative exponent to get a true reciprocal.
2. **No indexed assignment.** `a[0] = 1` does not exist. Arrays are updated by
   rebuilding them (or with `append`). That is why every weight update returns
   a new row/layer instead of mutating one in place.
3. **Loop bodies do not get a new scope.** A `dec` inside a `for` body is
   executed again on the next iteration and raises `AccidentalReassError`.
   All loop temporaries are therefore declared before the loop and updated with
   `flux`.
4. **A `for` defines its loop variable in the current scope and never removes
   it.** Two sequential `for` loops with the same variable in one function
   collide, and genuine nested `for` loops are impossible. The network is split
   into small functions (`train_epoch` -> `train_sample` -> `update_layer` ->
   `new_row`) so that each loop lives in its own call frame.
5. **Strings cannot contain `()[]{}`.** The lexer raises `UnterminatedStringLiteral`
   if it sees a bracket inside a string, so progress messages avoid them.
6. **`getrange`** is the range builtin: `getrange(stop)`, `getrange(start, stop)`
   or `getrange(start, stop, step)`.

These constraints are a good tour of the language: the final program looks like
a tiny autodiff library built out of lists and scalar helpers.

## The network

Architecture: `2 -> 4 -> 1`, sigmoid everywhere, squared error, per-sample
stochastic gradient descent.

Forward pass for layer `l`:

```
z = W_l * a_{l-1} + b_l
a_l = sigmoid(z)
```

Backpropagation:

```
delta_out = (a_out - y) * a_out * (1 - a_out)
delta_l   = (W_{l+1}^T * delta_{l+1}) * a_l * (1 - a_l)
W_l      -= lr * delta_l * a_{l-1}^T
b_l      -= lr * delta_l
```

Weights are initialised from a deterministic sine-based PRNG, so every run
starts from the same point and the output below is reproducible.

Training data is XOR:

| x1 | x2 | y |
| --- | --- | --- |
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

Training uses 4000 epochs of per-sample SGD with learning rate `0.7`. The loss
is printed at epochs 0, 250, 500, 1000, 2000 and 3999, then the four predictions
are printed. The network has 17 parameters: `2*4` weights + 4 biases + `4*1`
weights + 1 bias.

## Result

```text
initial loss 0.2795455150912262
training ...
epoch 0 loss 0.2672638136230254
epoch 250 loss 0.24997839212118897
epoch 500 loss 0.2431558200647843
epoch 1000 loss 0.05486488783406718
epoch 2000 loss 0.0025307431362458273
epoch 3999 loss 0.0006672518616348453
final loss 0.0006672518616348453
XOR predictions:
0 xor 0 = 0.013574990017279734
0 xor 1 = 0.9735807855230741
1 xor 0 = 0.977673001563337
1 xor 1 = 0.03589230195740553
```

With a 0.5 threshold the predictions are `0, 1, 1, 0`. The run takes about 80
seconds on this phone, almost all of it in tree-walking interpreter overhead.

`verification/ref_nn.py` is a line-for-line Python mirror of the same network. It
reproduces the initial loss, every logged loss and all four predictions to
floating-point precision, which checks that the array/backprop plumbing in San
is doing the intended maths.


## Adapting to San

The direct translation of a Python MLP does not run because of quirks 1-4. The
main adaptations are:

- every matrix operation is a helper (`dot`, `matvec`, `addvec`, `get2`) because
  chained indexing such as `w[i][j]` is not parsed;
- every update produces fresh lists (`new_row`, `new_bias`, `update_layer`)
  because array elements cannot be assigned;
- loops are one-per-function, with all temporaries predeclared and reassigned
  with `flux`;
- gradient accumulation is avoided: per-sample SGD only needs the current
  sample's activations.

## Ideas to extend

- Add momentum by storing a velocity layer alongside the weights.
- Swap sigmoid for `tanh` (already in `use math`) and use targets `-1`/`+1`.
- Add a second hidden layer; the generic `forward`/`train_sample` already loop
  over `len(net)`, so only `make_layer` calls and the `hidden_delta` math need
  care.
- Learn a tiny 3-bit function or a small Iris subset using the same helpers.
