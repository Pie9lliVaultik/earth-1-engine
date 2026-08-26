"""ABC / NPE / NRE estimators for the synthetic twin (prereg A7/A8).

All inference happens in u-space: each theta mapped to [0,1] via its
prior CDF (uniform or log-uniform), so the prior is U(0,1)^6, prior sd
= 1/sqrt(12) per dim, and the false-confidence gate (A8) is a plain
sd comparison. MDN/classifier work in z = logit(u).
"""
import json

import numpy as np

from sbi.theta import NAMES, THETA

PRIOR_SD_U = 1.0 / np.sqrt(12.0)


def to_u(theta_rows):
    u = np.zeros((len(theta_rows), len(NAMES)))
    for j, (name, _, lo, hi, log) in enumerate(THETA):
        v = np.array([t[name] for t in theta_rows], dtype=float)
        u[:, j] = (np.log(v) - np.log(lo)) / (np.log(hi) - np.log(lo)) \
            if log else (v - lo) / (hi - lo)
    return np.clip(u, 1e-6, 1 - 1e-6)


def zscore_fit(S):
    mu, sd = S.mean(0), np.maximum(S.std(0), 1e-12)
    return mu, sd


class ABC:
    name = "abc"

    def fit(self, S, U, mu, sd):
        self.S, self.U, self.mu, self.sd = S, U, mu, sd
        self.k = max(int(0.01 * len(S)), 25)

    def posterior(self, s_obs, n=200, rng=None):
        d = np.linalg.norm((self.S - s_obs) / self.sd, axis=1)
        idx = np.argsort(d)[:self.k]
        rng = rng or np.random.default_rng(0)
        return self.U[rng.choice(idx, size=n, replace=True)]


def _mlp(sizes):
    import torch.nn as nn
    layers = []
    for a, b in zip(sizes[:-2], sizes[1:-1]):
        layers += [nn.Linear(a, b), nn.ReLU()]
    layers.append(nn.Linear(sizes[-2], sizes[-1]))
    return nn.Sequential(*layers)


class NPE:
    """Mixture density network q(z|s), K diagonal Gaussians, z=logit(u)."""
    name = "npe"
    K = 8

    def fit(self, S, U, mu, sd, epochs=300, seed=0):
        import torch
        torch.manual_seed(seed)
        self.mu, self.sd = mu, sd
        X = torch.tensor((S - mu) / sd, dtype=torch.float32)
        Z = torch.tensor(np.log(U / (1 - U)), dtype=torch.float32)
        D = Z.shape[1]
        self.D = D
        self.net = _mlp([X.shape[1], 128, 128, self.K * (1 + 2 * D)])
        opt = torch.optim.Adam(self.net.parameters(), lr=1e-3)
        n = len(X)
        for ep in range(epochs):
            perm = torch.randperm(n)
            for i in range(0, n, 256):
                b = perm[i:i + 256]
                loss = -self._logq(X[b], Z[b]).mean()
                opt.zero_grad(); loss.backward(); opt.step()
        self.net.eval()

    def _params(self, x):
        import torch
        out = self.net(x)
        K, D = self.K, self.D
        logit_pi = out[:, :K]
        m = out[:, K:K + K * D].reshape(-1, K, D)
        ls = torch.clamp(out[:, K + K * D:].reshape(-1, K, D), -7, 3)
        return logit_pi, m, ls

    def _logq(self, x, z):
        import torch
        logit_pi, m, ls = self._params(x)
        lp = -0.5 * (((z[:, None, :] - m) / ls.exp()) ** 2
                     + 2 * ls + np.log(2 * np.pi)).sum(-1)
        return torch.logsumexp(
            torch.log_softmax(logit_pi, -1) + lp, dim=-1)

    def posterior(self, s_obs, n=200, rng=None):
        import torch
        rng = rng or np.random.default_rng(0)
        x = torch.tensor((s_obs - self.mu) / self.sd,
                         dtype=torch.float32)[None, :]
        with torch.no_grad():
            logit_pi, m, ls = self._params(x)
            pi = torch.softmax(logit_pi, -1).numpy()[0]
            m, s = m.numpy()[0], ls.exp().numpy()[0]
        comp = rng.choice(self.K, size=n, p=pi / pi.sum())
        z = m[comp] + rng.standard_normal((n, self.D)) * s[comp]
        return 1.0 / (1.0 + np.exp(-z))


class NRE:
    """Binary classifier ratio r(s,z); posterior by importance-
    resampling a large prior pool."""
    name = "nre"

    def fit(self, S, U, mu, sd, epochs=120, seed=0):
        import torch
        torch.manual_seed(seed)
        self.mu, self.sd = mu, sd
        X = (S - mu) / sd
        Z = np.log(U / (1 - U))
        n = len(X)
        self.net = _mlp([X.shape[1] + Z.shape[1], 128, 128, 1])
        opt = torch.optim.Adam(self.net.parameters(), lr=1e-3)
        rng = np.random.default_rng(seed)
        for ep in range(epochs):
            sh = rng.permutation(n)
            xj = np.concatenate([X, Z], 1)                 # joint
            xm = np.concatenate([X, Z[sh]], 1)             # marginal
            xx = torch.tensor(np.concatenate([xj, xm]), dtype=torch.float32)
            yy = torch.tensor(np.concatenate(
                [np.ones(n), np.zeros(n)]), dtype=torch.float32)
            perm = torch.randperm(2 * n)
            for i in range(0, 2 * n, 512):
                b = perm[i:i + 512]
                out = self.net(xx[b])[:, 0]
                loss = torch.nn.functional.binary_cross_entropy_with_logits(
                    out, yy[b])
                opt.zero_grad(); loss.backward(); opt.step()
        self.net.eval()

    def posterior(self, s_obs, n=200, rng=None, pool=100_000):
        import torch
        rng = rng or np.random.default_rng(0)
        Uq = rng.random((pool, len(NAMES))).clip(1e-6, 1 - 1e-6)
        Zq = np.log(Uq / (1 - Uq))
        x = np.tile((s_obs - self.mu) / self.sd, (pool, 1))
        with torch.no_grad():
            lr = self.net(torch.tensor(
                np.concatenate([x, Zq], 1), dtype=torch.float32))[:, 0].numpy()
        w = np.exp(lr - lr.max()); w /= w.sum()
        return Uq[rng.choice(pool, size=n, p=w)]
