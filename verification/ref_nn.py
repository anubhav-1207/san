"""Pure-Python mirror of neural_net.san, used to cross-check the San output."""
import math

rng_state = 0.123456789


def rand01():
    global rng_state
    rng_state += 0.6180339887498949
    v = math.sin(rng_state * 12.9898) * 43758.5453
    return v - math.floor(v)


def make_layer(n_in, n_out):
    W = []
    b = []
    for _ in range(n_out):
        W.append([(rand01() - 0.5) for _ in range(n_in)])
        b.append(rand01() - 0.5)
    return [W, b]


def sigmoid(x):
    return (1.0 + math.exp(-x)) ** -1


def forward(net, x):
    acts = [x]
    a = x
    for W, b in net:
        a = [sigmoid(sum(w * xi for w, xi in zip(row, a)) + bi) for row, bi in zip(W, b)]
        acts.append(a)
    return acts


def train_sample(net, x, y, lr):
    acts = forward(net, x)
    delta = [(acts[-1][i] - y[i]) * acts[-1][i] * (1 - acts[-1][i]) for i in range(len(y))]
    new_layers = []
    for l in range(len(net) - 1, -1, -1):
        W, b = net[l]
        a_prev = acts[l]
        new_W = [[W[i][j] - lr * delta[i] * a_prev[j] for j in range(len(W[i]))] for i in range(len(W))]
        new_b = [b[i] - lr * delta[i] for i in range(len(b))]
        new_layers.append([new_W, new_b])
        if l > 0:
            delta = [sum(delta[j] * W[j][i] for j in range(len(delta))) * a_prev[i] * (1 - a_prev[i])
                     for i in range(len(a_prev))]
    return new_layers[::-1]


def train_epoch(net, data, lr):
    for sample in data:
        net = train_sample(net, sample[:2], [sample[2]], lr)
    return net


def loss(net, data):
    total = 0.0
    for sample in data:
        out = forward(net, sample[:2])[-1]
        total += sum((out[i] - [sample[2]][i]) ** 2 for i in range(1))
    return total * len(data) ** -1


data = [[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0]]
net = [make_layer(2, 4), make_layer(4, 1)]
print("initial", loss(net, data))
for epoch in range(4000):
    net = train_epoch(net, data, 0.7)
    if epoch in (0, 250, 500, 1000, 2000, 3999):
        print("epoch", epoch, "loss", loss(net, data))
for x in ([0, 0], [0, 1], [1, 0], [1, 1]):
    print(x, forward(net, x)[-1][0], forward(net, x)[-1][0] >= 0.5)
