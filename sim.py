"""Delta-hedging simulator with explicit proportional costs, three hedging rules, and exact P&L attribution."""
import numpy as np
from bs import greeks, price

def gbm_paths(P, n, T, S0, r, sig_path, seed):
    """sig_path: (P,n) realised vol per step (or scalar). Returns (P,n+1) prices, drift = r."""
    rng = np.random.default_rng(seed); dt = T / n
    sig = np.broadcast_to(np.asarray(sig_path, float), (P, n))
    z = rng.standard_normal((P, n))
    lr = (r - 0.5 * sig**2) * dt + sig * np.sqrt(dt) * z
    return S0 * np.exp(np.concatenate([np.zeros((P, 1)), np.cumsum(lr, 1)], 1))

def regime_vols(P, n, T, lo, hi, lam_up, lam_dn, seed):
    """Two-state Markov vol regime; start from stationary distribution. Returns (P,n) vols."""
    rng = np.random.default_rng(seed); dt = T / n
    st = (rng.random(P) < lam_up / (lam_up + lam_dn)).astype(int); out = np.empty((P, n))
    for t in range(n):
        out[:, t] = np.where(st == 1, hi, lo)
        flip = rng.random(P) < np.where(st == 1, lam_dn, lam_up) * dt
        st = np.where(flip, 1 - st, st)
    return out

def ewma_vol(S, T, prior, hl_steps=40, floor=0.05):
    """Causal EWMA vol estimate, sigma_hat[:,t] uses returns up to t. Initialised at `prior`."""
    P, n1 = S.shape; n = n1 - 1; dt = T / n; lam = 0.5 ** (1 / hl_steps)
    r2 = np.diff(np.log(S), axis=1) ** 2 / dt; v = np.full(P, prior**2); out = np.empty((P, n1)); out[:, 0] = prior
    for t in range(n):
        v = lam * v + (1 - lam) * r2[:, t]; out[:, t + 1] = np.sqrt(v)
    return np.maximum(out, floor)

def hedge(S, K, T, r, sig_h, quote_iv, side, kappa, rule, param=None, cp=1):
    """
    side=-1 short option (market maker sells at quote_iv), +1 long. sig_h: (P,n+1) hedge/model vol (known at t).
    rule: 'time' (param = rebalance every k steps) | 'band' (param = |delta error| band) |
          'ww' (Whalley-Wilmott band, param = risk aversion gamma; width ~ (1.5*kappa*S*Gamma^2/gamma)^(1/3)).
    kappa = proportional cost per unit notional traded. Cash-settled; terminal hedge unwound at cost kappa.
    """
    P, n1 = S.shape; n = n1 - 1; dt = T / n; s = side
    P0 = float(price(S[0, 0], K, T, r, quote_iv, cp))
    held = np.zeros(P); cash = np.zeros(P); trades = np.zeros(P)
    B = {k: np.zeros(P) for k in ("edge", "delta", "gamma", "theta_carry", "vega", "cost")}
    for t in range(n):
        tau = T - t * dt; St = S[:, t]; g = greeks(St, K, tau, r, sig_h[:, t], cp)
        D, G = g["delta"], g["gamma"]
        if t == 0:
            B["edge"] = s * (g["price"] - P0); cash = -s * P0 * np.ones(P); new = D.copy()
        elif rule == "time":
            new = D if t % param == 0 else held
        elif rule == "band":
            new = np.where(np.abs(D - held) > param, D, held)
        else:
            H = (1.5 * kappa * St * G**2 / param) ** (1 / 3) if kappa > 0 else 0.0
            new = np.clip(held, D - H, D + H)
        dsh = -s * (new - held); c = kappa * np.abs(dsh) * St          # shares traded (hedge = -side*delta)
        cash = cash - dsh * St - c; trades += (np.abs(dsh) > 1e-12); B["cost"] -= c; held = new
        dS = S[:, t + 1] - St
        B["delta"] += s * (D - held) * dS                             # unhedged delta slippage
        B["gamma"] += s * 0.5 * G * dS**2
        B["vega"] += s * g["vega"] * (sig_h[:, t + 1] - sig_h[:, t])
        B["theta_carry"] += s * g["theta"] * dt + r * cash * dt       # theta + funding on cash
        cash = cash * (1 + r * dt)
    ST = S[:, -1]; close = kappa * np.abs(held) * ST; B["cost"] -= close
    total = cash + (-s * held) * ST - close + s * np.maximum(cp * (ST - K), 0)
    B["resid"] = total - sum(B.values())
    B["total"] = total; B["trades"] = trades
    return B

def summ(B):
    x = B["total"]; q = np.sort(x)[: max(1, int(0.05 * len(x)))]
    return dict(mean=float(x.mean()), std=float(x.std()), cvar5=float(q.mean()), cost=float(-B["cost"].mean()), trades=float(B["trades"].mean()))
