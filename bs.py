"""Black-Scholes pricing, Greeks and implied volatility (vectorised, continuous dividend yield q)."""
import numpy as np
from scipy.stats import norm

def _d12(S, K, T, r, sig, q=0.0):
    sq = sig * np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sig**2) * T) / sq
    return d1, d1 - sq

def price(S, K, T, r, sig, cp=1, q=0.0):
    """European option price. cp=+1 call, -1 put. T<=0 returns intrinsic."""
    S, K, T, sig = np.broadcast_arrays(*map(np.asarray, (S, K, T, sig)))
    Ts = np.maximum(T, 1e-12)
    d1, d2 = _d12(S, K, Ts, r, np.maximum(sig, 1e-12), q)
    v = cp * (S * np.exp(-q * Ts) * norm.cdf(cp * d1) - K * np.exp(-r * Ts) * norm.cdf(cp * d2))
    return np.where(T > 0, v, np.maximum(cp * (S - K), 0.0))

def greeks(S, K, T, r, sig, cp=1, q=0.0):
    """Delta, Gamma, Vega (per 1.00 vol), Theta (per year), Rho (per 1.00 rate), plus price."""
    d1, d2 = _d12(S, K, T, r, sig, q)
    eq, er, pdf = np.exp(-q * T), np.exp(-r * T), norm.pdf(d1)
    sT = np.sqrt(T)
    delta = cp * eq * norm.cdf(cp * d1)
    gamma = eq * pdf / (S * sig * sT)
    vega = S * eq * pdf * sT
    theta = (-S * eq * pdf * sig / (2 * sT)
             - cp * r * K * er * norm.cdf(cp * d2) + cp * q * S * eq * norm.cdf(cp * d1))
    rho = cp * K * T * er * norm.cdf(cp * d2)
    return dict(price=price(S, K, T, r, sig, cp, q), delta=delta, gamma=gamma, vega=vega, theta=theta, rho=rho)

def implied_vol(p, S, K, T, r, cp=1, q=0.0, lo=1e-4, hi=5.0, tol=1e-10):
    """Vectorised bisection (guaranteed) followed by Newton polish. NaN if price violates no-arbitrage bounds."""
    p, S, K, T = np.broadcast_arrays(*map(lambda x: np.asarray(x, float), (p, S, K, T)))
    lo_, hi_ = np.full(p.shape, lo), np.full(p.shape, hi)
    for _ in range(80):
        mid = 0.5 * (lo_ + hi_)
        up = price(S, K, T, r, mid, cp, q) > p
        hi_ = np.where(up, mid, hi_); lo_ = np.where(up, lo_, mid)
    iv = 0.5 * (lo_ + hi_)
    for _ in range(3):  # Newton polish
        g = greeks(S, K, T, r, np.maximum(iv, 1e-4), cp, q)
        step = (g["price"] - p) / np.maximum(g["vega"], 1e-12)
        iv = np.where(np.abs(g["price"] - p) > tol, iv - step, iv)
    lb = np.maximum(cp * (S * np.exp(-q * T) - K * np.exp(-r * T)), 0)
    ub = S * np.exp(-q * T) if cp == 1 else K * np.exp(-r * T)
    return np.where((p > lb + 1e-12) & (p < ub - 1e-12) & (iv > lo * 1.01) & (iv < hi * 0.99), iv, np.nan)
