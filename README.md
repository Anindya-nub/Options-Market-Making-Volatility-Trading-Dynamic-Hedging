# Options Market Making, Volatility Trading and Dynamic Hedging

## 1. Question
How do discrete hedging, vol-estimation error and transaction costs change the profitability and risk of options market making?

## 2. Models
- **Pricing layer** (`bs.py`, `surface.py`): Black-Scholes with all five Greeks (checked against central differences), vectorised implied-vol inversion (bisection plus Newton, round trip 1e-15), SVI smile fit with calendar and butterfly checks (6 bp recovery error under price noise).
- **Single-option hedging simulator** (`sim.py`): short or long ATM call, one vol point of quoted edge, proportional costs, time, band and Whalley-Wilmott rules, constant-vol and two-state regime worlds, fixed or EWMA hedge vol.
- **Market-making book** (`mm.py`): six OTM options, quotes in vol space around an EWMA fair vol, customer arrivals thinning as spread widens, 15% informed flow, Avellaneda-Stoikov style inventory skew, netted portfolio delta hedging, optional Merton jumps.
- **Attribution**: spread vs model mark, delta slippage, gamma, theta plus cash carry, vega, hedging costs and an exact residual (mean residual below 0.1 in every run reported).

## 3. Theory (ATM, fair vol, r small)
Per rebalance the hedged P&L is ½ΓS²σ²Δt(Z²−1), with variance ½(ΓS²σ²Δt)². Using E[φ(d₁)²] and ∫dt/√(T²−t²) = π/2, Var = σ²S²Δt/8, so std ≈ σS√(Δt/8). With E|ΔΔ| = ΓSσ√Δt·√(2/π) and E[S²Γ] = S/(σ√(2πT)), expected cost ≈ κS√N/π. Minimising (a/2)Var + cost gives N* = (πaσ²ST/(8κ))^(2/3), so N* ∝ κ^(-2/3).

## 4. Findings
1. **Closed forms reproduce the simulator.** For an ATM option at fair vol, E|ΔΔ| = ΓSσ√Δt·√(2/π) and E[S²Γ] = S/(σ√(2πT)) give hedging-error std ≈ σS√(Δt/8) and expected rebalancing cost ≈ κS√N/π plus entry and unwind. Simulation is within 4% on std for N ≥ 31 rebalances and within 2% on cost for N ≥ 7. Minimising risk aversion × variance + cost gives N* ∝ κ^(-2/3): the simulated tail-optimal N fell from 126 to 63 as costs rose from 10 to 25 bps (theory: ×0.54, grid resolves only ×0.5).
2. **Spread width has an interior optimum.** With flow elasticity 0.4 per vol point, uninformed profit ∝ h·e^(-a·h) peaks at h = 1/a = 2.5 vol points. The book's mean P&L peaks at 3 points (10.7), versus 6.6 at 1 point and 0.3 at 0.25. Mean/std keeps rising to 4 points (1.71) because flow, and so inventory, shrinks.
3. **Adverse selection is a tight-spread problem.** With 15% informed flow, the mean falls 57% at a 0.25-point half-spread (0.3 vs 0.7) and std rises 15 to 17% at 0.25 to 1 point, but the mean falls only 2% at 2 points. At 2 points the book earns +11.7 from spread, gamma and theta net to +0.3, and hedging costs return 1.5 (13% of spread).
4. **Hedging rule matters most when costs are high.** At 5 bps all sensible rules are close, though Whalley-Wilmott (γ=2) beats hedging every step on Sharpe (1.42 vs 1.38), tail (-3.4 vs -3.8) and cost (1.5 vs 1.9). At 25 bps WW (γ=0.1) cuts hedging cost 37% versus daily hedging (4.8 vs 7.6), lifts the mean from 4.2 to 6.9 and the tail from -13.4 to -12.0 at 10% higher std. A badly sized fixed band (3 shares) doubles std, so bands must scale with portfolio gamma.
5. **Inventory skew behaves like Avellaneda-Stoikov.** Shifting the reservation vol against vega inventory (strength 2) cuts vega inventory 46% (39 to 21), std 30% (7.9 to 5.5) and the 5% tail from -5.2 to -2.2, for 8% less mean; Mean/std peaks at 1.79 with strength 5. Over-skewing (20) pushes quotes through fair value and loses 13.3 on average, so the optimum is interior.
6. **Vol-estimate error is a tail risk more than a mean risk.** A ±4 point error in fair vol moves mean P&L by only about ±1.5 (8.7 to 11.4), but the 5% tail is -5.2 with no error, -10.5 at -4 points and -7.5 at +4 points. The mean rising with upward bias is unexplained here (hypothesis: the book is net short vega), so do not read it as 'quote high'.
7. **Gaps cannot be hedged by rebalancing.** Adding 4 jumps a year (sd 5%) leaves the mean about unchanged (10.2 to 10.5) but lifts std 41% (7.9 to 11.1) and worsens the tail from -5.2 to -11.6 under daily hedging; WW improves it only to -10.2. Gap risk needs option hedges and limits.
8. **Limits.** Flat vol within each regime (no skew dynamics), one 3-month expiry, no option-on-option vega hedging, stylised informed flow, and flow elasticity, arrival rate and informed share are free parameters, so absolute levels are model-specific. With 2,000 paths the standard error on the book mean is about 0.18, so mean differences under 0.5 are noise.

### Spread sweep, informed share 15%, half-spread in vol points
| | mean | std | cvar5 | sharpe | cost |
|---|---|---|---|---|---|
| 0.25 | 0.34 | 11.68 | -24.37 | 0.03 | 2.39 |
| 0.5 | 2.87 | 10.79 | -19.71 | 0.27 | 2.24 |
| 1 | 6.65 | 9.87 | -13.67 | 0.67 | 1.97 |
| 2 | 10.24 | 7.91 | -5.17 | 1.30 | 1.52 |
| 3 | 10.73 | 6.62 | -2.38 | 1.62 | 1.17 |
| 4 | 9.61 | 5.60 | -1.33 | 1.71 | 0.89 |

### Hedging rules at 25 bps
| | mean | std | cvar5 | sharpe | cost |
|---|---|---|---|---|---|
| time k=1 | 1.96 | 7.62 | -15.15 | 0.26 | 9.71 |
| time k=2 | 4.16 | 8.21 | -13.39 | 0.51 | 7.59 |
| time k=8 | 7.40 | 12.45 | -21.12 | 0.59 | 4.35 |
| band 1.0 | 6.62 | 9.34 | -13.93 | 0.71 | 5.18 |
| band 3.0 | 9.36 | 17.52 | -31.77 | 0.53 | 2.64 |
| WW γ=0.1 | 6.94 | 9.01 | -11.98 | 0.77 | 4.79 |
| WW γ=0.5 | 5.91 | 8.12 | -10.97 | 0.73 | 5.80 |
| WW γ=2.0 | 5.04 | 7.74 | -11.12 | 0.65 | 6.65 |

## 5. Talking points for interviews
- Gamma/theta: the book earns theta and pays realised variance, so hedging only changes the dispersion of that difference, not its mean.
- Hedging error shrinks as 1/√N while cost grows as √N, so the optimal N scales as κ^(-2/3).
- Wider spreads earn more per trade but thin flow (h* = 1/a), and informed flow is what punishes tight quotes.
- Inventory skew buys Sharpe at the cost of mean, with an interior optimum and a failure mode when over-applied.

## 6. Reproduce
`python run_experiments.py && python run_v2.py && OUT=. python build2.py` (needs numpy, scipy). Not done: Heston/SABR worlds with minimum-variance delta, vega-hedging with other expiries, skew dynamics.
