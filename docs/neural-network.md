# A neural network from scratch in San

[`examples/neural_network.san`](../examples/neural_network.san) implements a
small feed-forward neural network using only San's own features: arrays,
functions, loops and arithmetic. There is no machine-learning library and no
Python helper code involved when the program runs.

```bash
python main.py examples/neural_network.san
```

## What it learns

The network learns the XOR function:

| input 1 | input 2 | target |
| ------- | ------- | ------ |
| 0       | 0       | 0      |
| 0       | 1       | 1      |
| 1       | 0       | 1      |
| 1       | 1       | 0      |

XOR is the classic "not linearly separable" problem, so a hidden layer is
required. The network is:

```
2 inputs -> 4 hidden neurons -> 1 output
```

All neurons use the sigmoid activation function and training uses mean squared
error with online stochastic gradient descent.

## Parameter layout

San arrays are mutable but do not support indexed assignment, so the network
stores every weight and bias in one flat array and builds a new array for each
gradient-descent step. For `H` hidden neurons the layout is:

```
index 0 .. 2H-1        W1   (H rows of 2 input weights)
index 2H .. 3H-1       b1   (H hidden biases)
index 3H .. 4H-1       W2   (H output weights)
index 4H               b2   (output bias)
```

With `H = 4` that is 17 numbers.

## Forward pass

For hidden neuron `j`:

```
z_j = x1 * W1[j][0] + x2 * W1[j][1] + b1[j]
h_j = sigmoid(z_j)
```

For the output neuron:

```
z   = b2 + sum_j h_j * W2[j]
out = sigmoid(z)
```

`forward()` returns `[h0, h1, h2, h3, out]` so backpropagation can reuse the
hidden activations.

## Backpropagation

With squared error `L = (target - out)^2` and sigmoid output, the output delta
is:

```
output_delta = (target - out) * out * (1 - out)
```

Each hidden neuron receives a share of that error through its outgoing weight:

```
hidden_delta_j = h_j * (1 - h_j) * W2[j] * output_delta
```

The gradients are then:

```
dW1[j][0] = hidden_delta_j * x1
dW1[j][1] = hidden_delta_j * x2
db1[j]    = hidden_delta_j
dW2[j]    = output_delta * h_j
db2       = output_delta
```

Every parameter is updated with `p = p + learning_rate * gradient`.

## Expected output

With the fixed initial weights in the example, 2000 epochs and a learning rate
of `0.9`, the program prints:

```
Training a 2-4-1 network on XOR
epoch 0  loss 0.25037220887041545
epoch 1000  loss 0.004446949926748619

Final loss:
0.0010081701553916016

Predictions: expected -> predicted
0.0 -> 0.02052501559224062
1.0 -> 0.9694257987639759
1.0 -> 0.9680478800375698
0.0 -> 0.040690104511911254

Rounded predictions:
0.0 XOR 0.0 = 0
0.0 XOR 1.0 = 1
1.0 XOR 0.0 = 1
1.0 XOR 1.0 = 0
```

## Verification against a Python reference

The San program was compared with a line-by-line Python port using the same
parameter layout, initial weights, update order, learning rate and epoch
count. Both produce exactly the same floating-point values:

| quantity            | San                       | Python                    |
| ------------------- | ------------------------- | ------------------------- |
| initial loss        | `0.25037220887041545`     | `0.25037220887041545`     |
| loss at epoch 1000  | `0.004446949926748619`    | `0.004446949926748619`    |
| final loss          | `0.0010081701553916016`   | `0.0010081701553916016`   |
| `0 XOR 0`           | `0.02052501559224062`     | `0.02052501559224062`     |
| `0 XOR 1`           | `0.9694257987639759`      | `0.9694257987639759`      |
| `1 XOR 0`           | `0.9680478800375698`      | `0.9680478800375698`      |
| `1 XOR 1`           | `0.040690104511911254`    | `0.040690104511911254`    |

This confirms that the San implementation is numerically correct, not just
"close enough".

## San-specific notes

The example works around three properties of the current interpreter:

1. **`/` is floor division.** `7 / 2` evaluates to `3`, so `sigmoid()` uses a
   small `fdiv(a, b)` helper that computes `a * b ** -1`. This keeps the
   network in floating point without changing the language's operator.
2. **`for` variables live in the enclosing function scope.** A `for` loop
   nested inside another `for` loop cannot be re-entered, because its loop
   variable would be declared twice. `train_epoch()` therefore wraps the
   inner pass over the dataset in its own function call.

3. **Strings cannot contain brackets or parentheses.** The current string
   reader rejects `()`, `[]` and `{}` inside a string literal, so the example
   uses messages such as `"Predictions: expected -> predicted"` instead.
