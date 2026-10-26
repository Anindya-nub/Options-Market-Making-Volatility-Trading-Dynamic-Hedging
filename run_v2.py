import json, numpy as np
from scipy.stats import norm
from sim import regime_vols
from mm import paths, run_book, summ2
R = json.load(open("results.json")); out = {}
# ---- A. closed-form benchmarks vs the single-option simulator (ATM, fair vol, r small)
S0, T, r, sig = 100., .25, .02, .20; d1 = (np.log(1) + (r + .5 * sig**2) * T) / (sig * np.sqrt(T)); ks = R["freq"]["ks"]; ex = .01 * 0 + 1e-3
th = {"N": [252 // k for k in ks]}
th["std_theory"] = [sig * S0 * np.sqrt(T / (252 // k) / 8) for k in ks]                  # Var = sig^2 S^2 dt / 8
th["std_sim"] = [R["freq"]["res"]["0"][str(k)]["std"] for k in ks]
kap = 10e-4; edge_ends = kap * S0 * (norm.cdf(d1) + np.exp(r * T) * norm.cdf(d1))       # initial hedge + final unwind
th["cost_theory"] = [kap * S0 * np.sqrt(252 // k) / np.pi + edge_ends for k in ks]       # kappa S sqrt(N)/pi + ends
th["cost_sim"] = [R["freq"]["res"]["10"][str(k)]["cost"] for k in ks]
nst = {b: ks and 252 // max(ks, key=lambda k: R["freq"]["res"][b][str(k)]["cvar5"] if False else 0) for b in ()}
th["nstar_sim"] = {b: 252 // max(ks, key=lambda k: R["freq"]["res"][b][str(k)]["cvar5"]) for b in ("0", "2.5", "5", "10", "25")}
out["theory"] = th
# ---- B. market-making book
P, n, kap = 2000, 126, 5e-4
vols = regime_vols(P, n, T, .15, .30, 6., 6., 11); hi = vols > .22; S = paths(P, n, T, S0, r, vols, 12)
run = lambda **k: summ2(run_book(S, hi, T, r, **{**dict(h=.02, pi=.15, rule="time", par=2, kappa=kap), **k}))
hs_ = [.0025, .005, .01, .02, .03, .04]
out["spread"] = {"x": [f"{h*100:.2g}" for h in hs_], "runs": {f"informed {int(p*100)}%": [run(h=h, pi=p) for h in hs_] for p in (.15, 0.)}}
rules = [("time", 1), ("time", 2), ("time", 8), ("band", 1.), ("band", 3.), ("ww", .1), ("ww", .5), ("ww", 2.)]
lab = lambda a, b: {"time": f"time k={b}", "band": f"band {b}", "ww": f"WW γ={b}"}[a]
out["rule"] = {"x": [lab(a, b) for a, b in rules], "runs": {f"{int(k*1e4)} bps": [run(rule=a, par=b, kappa=k) for a, b in rules] for k in (5e-4, 25e-4)}}
bs_ = [-.04, -.02, 0., .02, .04]; out["bias"] = {"x": [f"{b*100:+.0f}" for b in bs_], "runs": {"time k=2": [run(bias=b) for b in bs_]}}
gi = [0., 2., 5., 10., 20.]; out["inv"] = {"x": [str(g) for g in gi], "runs": {"skew": [run(g_inv=g) for g in gi]}}
Sj = paths(P, n, T, S0, r, vols, 12, jump=(4., -.02, .05)); runj = lambda S_, **k: summ2(run_book(S_, hi, T, r, **{**dict(h=.02, pi=.15, rule="time", par=2, kappa=kap), **k}))
jr = [("time", 2), ("time", 8), ("ww", .5)]
out["jump"] = {"x": [lab(a, b) for a, b in jr], "runs": {nm: [runj(S_, rule=a, par=b) for a, b in jr] for nm, S_ in (("no jumps", S), ("jumps 4/yr, sd 5%", Sj))}}
json.dump(out, open("results_v2.json", "w"))
print("theory N", th["N"]); print("std th", np.round(th["std_theory"], 3)); print("std sim", np.round(th["std_sim"], 3))
print("cost th", np.round(th["cost_theory"], 3)); print("cost sim", np.round(th["cost_sim"], 3)); print("N*", th["nstar_sim"])
f = lambda d: (round(d["mean"], 1), round(d["std"], 1), round(d["cvar5"], 1), round(d["sharpe"], 2), round(d["opts"]), round(d["inv"]), round(d["cost"], 1))
for e in ("spread", "rule", "bias", "inv", "jump"):
    for nm, L in out[e]["runs"].items(): print(e, nm, [(x, f(d)) for x, d in zip(out[e]["x"], L)])
d = out["spread"]["runs"]["informed 15%"][3]["attr"]; print("attr h=2pt", {k: round(v, 1) for k, v in d.items()})
