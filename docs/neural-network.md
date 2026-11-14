# A neural network from scratch in San

[`examples/neural_network.san`](../examples/neural_network.san) implements a
generic feed-forward neural network using only San's own features: arrays,
functions, loops and arithmetic. There is no machine-learning library and no
Python helper code involved when the program runs.

```bash
python main.py examples/neural_network.san
```

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
`1.5`, the program prints:

```
Training a 3-4-1 network on 3-bit parity
epoch 0  loss 0.7057617798042103
epoch 200  loss 0.510129100987375
epoch 400  loss 0.3083891970349758
epoch 600  loss 0.3020205439315524

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

The run takes about 40 seconds in the current tree-walking interpreter.

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

This confirms that the San implementation is numerically correct, not just
"close enough".

## San-specific notes

The example works around several properties of the current interpreter:

1. **`/` is floor division.** `7 / 2` evaluates to `3`, so `sigmoid()` uses a
   small `fdiv(a, b)` helper that computes `a * b ** -1`. This keeps the
   network in floating point without changing the language's operator.
2. **`for` variables live in the enclosing function scope.** A `for` loop
   nested inside another `for` loop cannot be re-entered, because its loop
   variable would be declared twice. `train_epoch()` therefore wraps the
   inner pass over the dataset in its own function call.
3. **Strings cannot contain brackets or parentheses.** The current string
   reader rejects `()`, `[]` and `{}` inside a string literal, so the example
   uses messages without them.
4. **An empty string cannot be used as a `dec` initialiser.** The parser
   treats the empty token as "no value", so `layer_string()` starts from the
   first layer size instead of `""`.

`use math` now also exposes `log()`, which is used for the binary
cross-entropy loss.
