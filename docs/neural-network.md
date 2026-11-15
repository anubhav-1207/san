# A neural network from scratch in San

[`examples/neural_network.san`](../examples/neural_network.san) implements a
generic feed-forward neural network using only San's own features: arrays,
functions, loops and arithmetic. There is no machine-learning library and no
Python helper code involved when the program runs.

```bash
python main.py examples/neural_network.san
```

A line-by-line Python port used for the benchmark lives in
[`benchmarks/neural_network.py`](../benchmarks/neural_network.py). It keeps the
same parameter layout, operation order, floating-point arithmetic and output;
it deliberately does not use NumPy or vectorisation.

## What it learns

The default task is **3-bit parity**. The output is `1` when the input has an
odd number of `1` bits, otherwise `0`:

| input        | target |
| ------------ | ------ |
| `0 0 0`      | 0      |
| `0 0 1`      | 1      |
| `0 1 0`      | 1      |
| `0 1 1`      | 0      |
| `1 0 0`      | 1      |
| `1 0 1`      | 0      |
| `1 1 0`      | 0      |
| `1 1 1`      | 1      |

Parity is not linearly separable, so the network needs at least one hidden
layer. The default architecture is:

```
3 inputs -> 4 hidden neurons -> 1 output
```

`LAYERS` at the top of the file controls the shape. Any valid stack works, for
example `[3, 6, 4, 1]` for two hidden layers.

## Training

- Activation: sigmoid, implemented with a numerically stable branch so large
  negative inputs cannot overflow `exp()`.
- Loss: binary cross-entropy.
- Optimiser: online stochastic gradient descent.
- Initialisation: a small deterministic linear congruential generator, so
  every run starts from the same weights and is reproducible.
- Default schedule: 800 epochs at a learning rate of `1.5`.

## Parameter layout

San arrays are mutable but do not support indexed assignment, so the network
stores every weight and bias in one flat array and builds a new array for each
gradient-descent step.

For each layer `l` the layout is:

```
W[l]   LAYERS[l] * LAYERS[l+1] values
b[l]   LAYERS[l+1] values
```

`W_OFFSET[l]` and `B_OFFSET[l]` are computed once at startup. The default
`3 -> 4 -> 1` network therefore has `3*4 + 4 + 4*1 + 1 = 21` parameters.

## Forward pass

For layer `l`, output neuron `j`:

```
z_j = b[l][j] + sum_k W[l][j][k] * input[k]
a_j = sigmoid(z_j)
```

`forward()` returns the full activation stack `[input, hidden..., output]`, so
backpropagation can reuse every layer's activations.

## Backpropagation

With sigmoid output and binary cross-entropy, the output delta is simply:

```
delta_out = target - output
```

Each earlier layer receives its share of the error through the next layer's
weights:

```
delta_l[j] = a_l[j] * (1 - a_l[j]) * sum_k W[l+1][k][j] * delta_{l+1}[k]
```

The gradients are:

```
dW[l][j][k] = delta_{l+1}[j] * a_l[k]
db[l][j]    = delta_{l+1}[j]
```

Every parameter is updated with `p = p + learning_rate * gradient`.

## Expected output

With the default shape, initialisation, 800 epochs and a learning rate of
`1.5`, the complete output has 755 lines and 26,394 bytes. The excerpt below
shows selected epoch lines and the final result:

```
Training a 3-4-1 network on 3-bit parity
epoch 0  loss 0.7057617798042103
...
epoch 200  loss 0.510129100987375
...
epoch 400  loss 0.3083891970349758
...
epoch 600  loss 0.3020205439315524
...
epoch 799  loss 0.007401892402777487

Final loss:
0.007401892402777487
Accuracy:
1.0

Predictions: inputs -> target / output
0.0 0.0 0.0 -> 0.0 / 5.871305824594899e-07
0.0 0.0 1.0 -> 1.0 / 0.9979841514064582
0.0 1.0 0.0 -> 1.0 / 0.9972902158584702
0.0 1.0 1.0 -> 0.0 / 0.011335047437190627
1.0 0.0 0.0 -> 1.0 / 0.9982704625019749
1.0 0.0 1.0 -> 0.0 / 0.013579269875749757
1.0 1.0 0.0 -> 0.0 / 0.002838903725969887
1.0 1.0 1.0 -> 1.0 / 0.9754687633129521

Rounded predictions:
0.0 0.0 0.0 -> 0
0.0 0.0 1.0 -> 1
0.0 1.0 0.0 -> 1
0.0 1.0 1.0 -> 0
1.0 0.0 0.0 -> 1
1.0 0.0 1.0 -> 0
1.0 1.0 0.0 -> 0
1.0 1.0 1.0 -> 1
```

The current interpreter actually prints 729 epoch lines, not four. The progress
test is written as `epoch - (epoch / 200) * 200 == 0`, and `/` is ordinary
floating-point division in the current tree, so a few values fail the exact
zero test because of rounding (71 of the 800 epochs in this run). This is an
output-frequency quirk, not a training difference: the loss values at epochs
0, 200, 400 and 600 match the original reference exactly. The complete output
is in [`benchmarks/results/san.out`](../benchmarks/results/san.out).

On the benchmark phone (ARM Cortex-A53), a full 800-epoch run takes roughly
52–70 seconds depending on thermal state and background load. The Python port
takes about 0.55–0.76 seconds. See the benchmark below.

## Verification against a Python reference

The San program was compared with a line-by-line Python port using the same
layer sizes, parameter layout, initialisation, update order, learning rate and
epoch count. Both produce exactly the same floating-point values:

| quantity            | San                     | Python                  |
| ------------------- | ----------------------- | ----------------------- |
| initial loss        | `0.7057617798042103`    | `0.7057617798042103`    |
| loss at epoch 200   | `0.510129100987375`     | `0.510129100987375`     |
| loss at epoch 400   | `0.3083891970349758`    | `0.3083891970349758`    |
| loss at epoch 600   | `0.3020205439315524`    | `0.3020205439315524`    |
| final loss          | `0.007401892402777487`  | `0.007401892402777487`  |
| accuracy            | `1.0`                   | `1.0`                   |
| `0 0 0`             | `5.871305824594899e-07` | `5.871305824594899e-07` |
| `0 1 1`             | `0.011335047437190627`  | `0.011335047437190627`  |
| `1 1 1`             | `0.9754687633129521`    | `0.9754687633129521`    |

The entire stdout is identical as well: 26,394 bytes, 755 lines, SHA-256
`33bc31d62b239e0358a115ec3ca7c0a72ea947c566c7137467b88604e899adeb`.
Every timed San and Python run produced the same hash. This confirms that the
port is behaviourally equivalent, not just "close enough".

## Benchmark: San vs. Python

The benchmark compares the unchanged San example with the equivalent Python
port. The Python port is intentionally a line-by-line translation: it keeps
the flat parameter array, the same loop order, the same `fdiv()` helper and
the same float operations. It is not an idiomatic NumPy implementation, so the
result measures the languages running the same algorithm rather than the best
possible Python algorithm.

Raw data and full outputs are in
[`benchmarks/results/`](../benchmarks/results/).

### Environment and method

- **Host:** Linux aarch64, ARM Cortex-A53, 8 cores, about 3.7 GB RAM,
  Python 3.12.3.
- **San:** upstream commit `7ca7b3f`. The checkout needed a local one-line
  `Token = Tokens` import shim to start; it does not change runtime behaviour.
- **Processes:** each program ran as a fresh child process. Wall time came
  from the parent, CPU time and page faults from `wait4()`, and peak RSS from
  the kernel's `VmHWM` high-water mark in `/proc/<pid>/status`, sampled after
  `exec`.
- **Runs:** 3 San runs and 5 Python runs for the detailed measurement; one San
  run and the median of 3 Python runs for each scaling point.
- **Output:** both programs were redirected to a file. San's `main.py` exits
  with status `1` even on success, so the harness validates the captured output
  instead of trusting the exit status.
- **Variance:** the phone is shared and thermally throttled. San wall time
  varied from 51.7 s to 70.4 s across the session, so medians and ranges are
  more meaningful than a single number.

### Correctness

| metric                | result                                      |
| --------------------- | ------------------------------------------- |
| stdout                | byte-identical                              |
| lines                 | 755                                         |
| epoch lines           | 729                                         |
| bytes                 | 26,394                                      |
| SHA-256               | `33bc31d62b239e0358a115ec3ca7c0a72ea947c566c7137467b88604e899adeb` |
| final loss            | `0.007401892402777487`                      |
| accuracy              | `1.0`                                       |
| deterministic         | yes, every run produced the same hash       |

### Wall time

One detailed run, taken while the phone was relatively hot:

| target             | runs | median  | mean    | range            | CPU time        | peak RSS  |
| ------------------ | ---: | ------: | ------: | ---------------- | --------------: | --------: |
| San, 800 epochs    | 3    | 69.50 s | 69.32 s | 68.07–70.39 s    | 68.25 s (98.5%) | 11.64 MiB |
| Python port, 800   | 5    | 0.652 s | 0.621 s | 0.559–0.672 s    | 0.527 s (84.8%) | 9.08 MiB  |

That set gives a full-process speedup of about **106× by median** (112× by
mean). Across all repeated full runs in the session, San ranged from 51.7 s to
70.4 s (median 57.6 s) and Python from 0.548 s to 0.758 s (median 0.619 s):
about **93× by median** and **96× by mean** end-to-end.

The end-to-end figure includes interpreter startup. The marginal training cost
is better estimated by the scaling fit below: **62.38 ms/epoch for San versus
0.448 ms/epoch for Python, a ratio of about 139×**.

### Scaling with epoch count

Each row is a separate copy of both programs with only the `EPOCHS` constant
changed. All outputs remained byte-identical.

| epochs | San wall | Python wall | full speedup | output identical |
| -----: | -------: | ----------: | -----------: | :--------------- |
|     50 |  4.857 s |     0.223 s |        21.7× | yes              |
|    100 |  8.414 s |     0.208 s |        40.4× | yes              |
|    200 | 14.214 s |     0.307 s |        46.3× | yes              |
|    400 | 27.807 s |     0.375 s |        74.2× | yes              |
|    800 | 51.628 s |     0.548 s |        94.2× | yes              |

Least-squares fit of wall time against epoch count:

| language | intercept | marginal cost | R²      |
| -------- | --------: | ------------: | ------: |
| San      |   2.045 s | 62.38 ms/epoch | 0.9993 |
| Python   |   0.194 s |  0.448 ms/epoch | 0.9795 |

The fixed overhead explains why the speedup grows with the epoch count: at 50
epochs it is only about 22×, while the marginal training ratio is about 139×.
At 800 epochs the San run is long enough that the fixed startup is a small
fraction of the total.

Throughput, using the marginal costs and the default 8 samples per epoch and
21 parameters per sample:

| metric                    | San       | Python    | ratio |
| ------------------------- | --------: | --------: | ----: |
| epochs/s                  |     16.0  |    2,232  | 139×  |
| samples/s                 |      128  |   17,853  | 139×  |
| parameter updates/s       |    2,693  |  374,916  | 139×  |

### Memory

| metric                         | San      | Python   |
| ------------------------------ | -------: | -------: |
| peak RSS (`VmHWM`)             | 11.64 MiB | 9.08 MiB |
| empty-program baseline         | 11.00 MiB | 7.80 MiB |
| incremental program memory     |  0.64 MiB | 1.29 MiB |

Peak RSS includes CPython in both cases. The San process is about 2.5 MiB
larger at its peak because it carries the San scanner, parser and evaluator;
the Python process is smaller in absolute terms but its compiled script and
runtime objects add about 1.3 MiB over an empty Python process. The network
itself is tiny (21 parameters and a few activations), so memory is not a
differentiator at this scale. A much larger network would be needed to expose
the cost of San's flat-array rebuild strategy.

`ru_maxrss` was not used for the comparison because a forked child can inherit
the parent's pre-`exec` high-water mark. Sampling `VmHWM` after `exec` gives
the memory of the target process itself.

### Code size and static structure

Counted with [`benchmarks/code_stats.py`](../benchmarks/code_stats.py):

| metric             | San    | Python | San / Python |
| ------------------ | -----: | -----: | -----------: |
| physical lines     |    394 |    319 |        1.24× |
| code lines         |    291 |    252 |        1.15× |
| comment lines      |     65 |     13 |            — |
| docstring lines    |      0 |      7 |            — |
| blank lines        |     38 |     54 |            — |
| functions          |     14 |     14 |        1.00× |
| bytes              | 11,635 |  8,335 |        1.40× |
| tokens             |  1,864 |  1,632 |        1.14× |
| loops              |     24 |     24 |        1.00× |
| `if` statements    |      9 |      9 |        1.00× |
| call sites         |     72 |     72 |        1.00× |

The algorithm has exactly the same shape in both files: 14 functions, 24
loops, 9 conditionals and 72 call sites. San needs about **15.5% more code
lines** and **39.6% more bytes**, mostly for explicit declarations, flat-array
bookkeeping and workaround helpers rather than extra computation. San also has
far more comments (65 lines, 16.5% of the file) than the Python port (13
comments plus a 7-line module docstring).

The custom San AST has 922 nodes; Python's standard AST has 2,026. Those
figures are not directly comparable because Python's AST includes context and
operator nodes that San's tree does not model separately.

### Abstraction

Abstraction is the least mechanical metric in this benchmark. The table below
is a qualitative feature comparison; the 1–5 scores are a rubric, not a
measurement.

| capability                     | San                         | Python                         |
| ------------------------------ | --------------------------- | ------------------------------ |
| Data structures                | arrays/tuples only          | lists, dicts, classes          |
| Indexed assignment             | no                          | yes                            |
| Block-local declarations       | no                          | yes                            |
| First-class functions/closures | no                          | yes                            |
| Exceptions / `try`             | no (`try` is reserved)      | yes                            |
| Modules and packages           | `use math` only             | standard library and PyPI      |
| Native `%` and bitwise ops     | no                          | yes                            |
| Numeric/array libraries        | no                          | NumPy, SciPy, PyTorch, ...     |
| Typing and tooling             | annotations ignored; minimal | optional typing, pdb, cProfile |
| Operator overloading           | no                          | yes                            |

The San program has to manage several things manually: it stores all 21
parameters in a flat array because it cannot assign to an array element, builds
a new array after every sample, and uses the `fdiv(a, b)` helper for real
division. It also declares loop temporaries before the loops because a `dec`
inside a loop body is evaluated in the enclosing function scope. The
`train_epoch()` wrapper was written for an older `for`-scoping limitation; on
the current interpreter nested `for` loops work, but the wrapper is harmless
and keeps the original operation order.

Rubric (1 = manual bookkeeping, 5 = direct expression):

| dimension              | San  | Python port | Python + NumPy |
| ---------------------- | ---: | ----------: | -------------: |
| Data modelling         |    2 |           3 |              5 |
| Control flow           |    2 |           4 |              4 |
| Functional reuse       |    1 |           4 |              4 |
| Error handling         |    1 |           4 |              4 |
| Numeric/array expressiveness | 1 |        2 |              5 |
| Modularity/ecosystem   |    1 |           5 |              5 |
| Typing/tooling         |    1 |           4 |              4 |
| **Mean**               | **1.29** | **3.71** | **4.43** |

The Python port's 3.71 is not a claim that Python is only slightly more
abstract than San. The port deliberately mirrors the San structure to make the
comparison fair. An idiomatic NumPy implementation would be much shorter and
would score near the ceiling, but it would not be bit-identical and is not
used for the correctness benchmark.

### Other observations

- **CPU:** both programs are single-threaded. San used about 98.5% of one core
  during the timed run; Python used about 85% including startup and I/O.
- **Front end:** lexing plus parsing the San file took 51.9 ms (lexing alone
  38.7 ms). Python's `compile()` took 20.2 ms and `ast.parse()` 16.6 ms in the
  same session. San's empty-process baseline was about 0.5 s versus about
  0.15 s for Python, so San pays roughly 0.35 s more before training starts.
- **Startup share:** for the 800-epoch workload, San's empty-process startup is
  about 1% of total wall time; Python's is about 20–25%. This is why the
  full-process speedup is lower than the marginal per-epoch speedup.
- **Determinism:** the LCG and fixed operation order make both programs
  deterministic. All timed runs produced the same 755-line output.
- **Energy:** not measured; the phone does not expose a stable per-process
  energy counter.

### Caveats

1. The benchmark runs on a phone, not a quiet benchmark machine. Thermal
   throttling and background Android processes caused a roughly 35% spread in
   San wall time. The medians and the scaling slope are more trustworthy than
   any single run.
2. The San checkout at `7ca7b3f` does not import without a local `Token =
   Tokens` shim. The shim only repairs an import; it does not change the
   interpreter's semantics.
3. The current San example prints 729 epoch lines because of the floating-point
   progress test described above. The Python port reproduces that behaviour
   exactly. Fixing the progress test would reduce output size and a small
   amount of I/O time, but would change behaviour, so it was not changed for
   this benchmark.
4. The Python port is deliberately non-idiomatic. It is the right comparison
   for "same algorithm, different language", but it is not the shortest or
   fastest Python program that solves the problem.
5. Peak RSS includes the CPython runtime for both programs. The incremental
   columns subtract a matching empty-program baseline, but allocator and
   interpreter startup noise still affect the last 0.1 MiB or so.

### Reproducing

From the repository root:

```bash
# Detailed time/memory benchmark (3 San runs, 5 Python runs by default).
python benchmarks/benchmark.py --san-repo /path/to/san

# Epoch-count scaling and linear fit.
python benchmarks/scaling.py --san-repo /path/to/san

# Line/token/AST statistics.
python benchmarks/code_stats.py --san-repo /path/to/san

# Run only the Python port.
python benchmarks/neural_network.py
```

`SAN_REPO=/path/to/san` can be used instead of `--san-repo`. The San checkout
must contain `main.py` and the `colorama` dependency, and the current tree
needs the `Token = Tokens` import shim described in the project's San audit
notes. Results are written to `benchmarks/results/`.

## San-specific notes

The example works around several properties of the current interpreter:

1. **`/` is floating-point division in the current tree.** The comment at the
   top of the example says floor division (`7 / 2 == 3`), but the current
   interpreter evaluates `7 / 2` as `3.5`. `fdiv(a, b)` computes
   `a * b ** -1` explicitly and keeps the network's operation order fixed; it
   is still used even though `/` is now float division. The stale comment also
   explains the 729-line epoch output: the progress test uses `/`, so the
   exact-zero test is not a reliable "every 200 epochs" test.
2. **Loop scoping is only partly block-local.** Nested `for` loops work in the
   current interpreter, contrary to the older note in the example. However, a
   `dec` in
