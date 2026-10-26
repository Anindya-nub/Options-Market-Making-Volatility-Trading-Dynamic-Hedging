"""Synthetic quote surface (SVI ground truth) -> price noise -> implied-vol recovery -> SVI fit + arbitrage checks."""
import numpy as np
from scipy.optimize import least_squares
from bs import price, implied_vol

def svi_w(k, a, b, rho, m, s):
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + s ** 2))

TRUE = {  # total-variance params per maturity (years): equity-like skew, flattening with T
    0.0833: (0.0008, 0.060, -0.70, 0.00, 0.10), 0.25: (0.0030, 0.080, -0.65, 0.00, 0.14),
    0.5: (0.0070, 0.090, -0.60, 0.00, 0.18), 1.0: (0.0160, 0.100, -0.55, 0.00, 0.24)}

def make_quotes(S=100., r=0.02, noise=0.002, seed=0):
    """OTM quotes (puts below forward, calls above) with additive price noise (cents-level tick error)."""
    rng = np.random.default_rng(seed); rows = []
    for T, p in TRUE.items():
        F = S * np.exp(r * T)
        for K in np.linspace(75, 125, 21):
            k = np.log(K / F); iv = np.sqrt(svi_w(k, *p) / T); cp = 1 if K >= F else -1
            px = float(price(S, K, T, r, iv, cp)) + rng.normal(0, noise)
            rows.append((T, K, cp, iv, max(px, 1e-4)))
    return np.array(rows)

def recover(q, S=100., r=0.02):
    T, K, cp = q[:, 0], q[:, 1], q[:, 2]
    iv = np.array([implied_vol(q[i, 4], S, K[i], T[i], r, int(cp[i])) for i in range(len(q))]).ravel()
    return iv

def fit_svi(k, w):
    f = lambda x: svi_w(k, *x) - w
    best = least_squares(f, [w.min() * .8, .08, -.5, 0., .15], bounds=([-1, 1e-4, -.99, -.5, 1e-3], [1, 2, .99, .5, 1]))
    return best.x

def no_arb(params_by_T, kgrid=np.linspace(-.5, .5, 401)):
    Ts = sorted(params_by_T); W = np.array([svi_w(kgrid, *params_by_T[T]) for T in Ts])
    cal = bool(np.all(np.diff(W, axis=0) >= -1e-9))  # calendar: total variance nondecreasing in T
    fly = []
    for T in Ts:  # butterfly: Gatheral g(k) >= 0
        a, b, rho, m, s = params_by_T[T]; w = svi_w(kgrid, *params_by_T[T])
        w1 = b * (rho + (kgrid - m) / np.sqrt((kgrid - m) ** 2 + s ** 2)); w2 = b * s ** 2 / ((kgrid - m) ** 2 + s ** 2) ** 1.5
        g = (1 - kgrid * w1 / (2 * w)) ** 2 - w1 ** 2 / 4 * (1 / w + .25) + w2 / 2
        fly.append(bool(g.min() >= -1e-9))
    return cal, fly
