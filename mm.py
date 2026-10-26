"""Options market-making book: vol-space quotes, informed flow, A-S style inventory skew, portfolio delta hedging, exact attribution."""
import numpy as np
from bs import greeks, price
from sim import ewma_vol, summ

INSTR = [(90, -1), (95, -1), (100, -1), (100, 1), (105, 1), (110, 1)]  # OTM puts + ATM/OTM calls, one 3m expiry

def paths(P, n, T, S0, r, sig, seed, jump=None):
    """GBM with optional Merton jumps jump=(lam/yr, mean, sd); drift compensated so E[S_T]=S0 e^{rT}."""
    rng = np.random.default_rng(seed); dt = T / n; sig = np.broadcast_to(sig, (P, n))
    lr = (r - .5 * sig**2) * dt + sig * np.sqrt(dt) * rng.standard_normal((P, n))
    if jump:
        lam, mu, sd = jump
        lr = lr + (rng.random((P, n)) < lam * dt) * rng.normal(mu, sd, (P, n)) - lam * dt * (np.exp(mu + .5 * sd**2) - 1)
    return S0 * np.exp(np.concatenate([np.zeros((P, 1)), np.cumsum(lr, 1)], 1))

def run_book(S, hi, T, r, h, pi, rule, par, kappa, bias=0., g_inv=0., lam=.4, a=.4, seed=0, hl=20, prior=.24):
    """h = half-spread in vol (decimal); pi = informed share of flow (informed buy vol iff regime is high);
    bias = error in our fair-vol estimate; g_inv = inventory skew (reservation vol shifts by -g_inv*1e-4*vega inventory)."""
    P, n1 = S.shape; n = n1 - 1; dt = T / n; K = np.array([k for k, _ in INSTR], float)[None]; cp = np.array([c for _, c in INSTR], float)[None]
    I = K.shape[1]; rng = np.random.default_rng(seed); sh = np.maximum(ewma_vol(S, T, prior, hl_steps=hl) + bias, .05)
    q = np.zeros((P, I)); cash = np.zeros(P); hs = np.zeros(P); trd = np.zeros(P); opts = np.zeros(P); inv = np.zeros(P)
    B = {k: np.zeros(P) for k in ("spread", "delta", "gamma", "theta_carry", "vega", "cost")}
    pa = lam * 252 * dt * np.exp(-a * h * 100)                       # arrivals per step per instrument; tighter quotes -> more flow
    for t in range(n):
        tau = T - t * dt; St = S[:, t][:, None]; sg = sh[:, t][:, None]
        g = greeks(St, K, tau, r, sg, cp); vinv = (q * g["vega"]).sum(1, keepdims=True); qs = sg - g_inv * vinv * 1e-4
        if t < n - 1:
            s_ = g_inv * vinv * 1e-4; f0 = lam * 252 * dt * .5                          # A-S: long vega -> quotes shift down -> more buyers, fewer sellers
            pb = f0 * np.exp(-a * (h - s_) * 100); ps = f0 * np.exp(-a * (h + s_) * 100)
            arr = rng.random((P, I)) < (pb + ps); inf = rng.random((P, I)) < pi
            cb = np.where(inf, hi[:, t][:, None], rng.random((P, I)) < pb / (pb + ps))   # customer buys vol (we sell)?
            px = price(St, K, tau, r, np.where(cb, qs + h, qs - h), cp); sgn = np.where(cb, -1, 1) * arr
            cash += (-sgn * px).sum(1); B["spread"] += (-sgn * (px - g["price"])).sum(1); q = q + sgn; opts += arr.sum(1)
        D = (q * g["delta"]).sum(1); G = (q * g["gamma"]).sum(1); tgt = -D
        if rule == "time": new = tgt if t % par == 0 else hs
        elif rule == "band": new = np.where(np.abs(D + hs) > par, tgt, hs)
        else: new = np.clip(hs, tgt - (1.5 * kappa * S[:, t] * G**2 / par) ** (1 / 3), tgt + (1.5 * kappa * S[:, t] * G**2 / par) ** (1 / 3))
        c = kappa * np.abs(new - hs) * S[:, t]; cash = cash - (new - hs) * S[:, t] - c; B["cost"] -= c; trd += np.abs(new - hs) > 1e-12; hs = new
        dS = S[:, t + 1] - S[:, t]; vi = (q * g["vega"]).sum(1); inv += np.abs(vi) / n
        B["delta"] += (D + hs) * dS; B["gamma"] += .5 * G * dS**2; B["vega"] += vi * (sh[:, t + 1] - sh[:, t])
        B["theta_carry"] += (q * g["theta"]).sum(1) * dt + r * cash * dt; cash = cash * (1 + r * dt)
    ST = S[:, -1]; cash = cash + (q * np.maximum(cp * (ST[:, None] - K), 0)).sum(1) + hs * ST - kappa * np.abs(hs) * ST
    B["cost"] -= kappa * np.abs(hs) * ST; B["total"] = cash; B["resid"] = cash - sum(B[k] for k in ("spread", "delta", "gamma", "theta_carry", "vega", "cost"))
    B["trades"] = trd; B["opts"] = opts; B["inv"] = inv
    return B

def summ2(B):
    d = summ(B); d["sharpe"] = d["mean"] / max(d["std"], 1e-9); d["opts"] = float(B["opts"].mean()); d["inv"] = float(B["inv"].mean())
    d["attr"] = {k: float(B[k].mean()) for k in ("spread", "delta", "gamma", "theta_carry", "vega", "cost", "resid")}
    return d
