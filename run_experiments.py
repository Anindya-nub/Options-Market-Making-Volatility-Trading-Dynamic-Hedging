import json, numpy as np
from bs import price, greeks, implied_vol
from surface import make_quotes, recover, fit_svi, svi_w, no_arb, TRUE
from sim import *
S0, K, T, r, n, P = 100., 100., 0.25, 0.02, 252, 4000
out = {}
# ---- 1. Greeks sanity (finite differences) + IV round trip
g = greeks(S0, K, T, r, .2); h = 1e-4
fd = dict(delta=(price(S0+h,K,T,r,.2)-price(S0-h,K,T,r,.2))/(2*h), gamma=(price(S0+.01,K,T,r,.2)-2*price(S0,K,T,r,.2)+price(S0-.01,K,T,r,.2))/1e-4,
          vega=(price(S0,K,T,r,.2+h)-price(S0,K,T,r,.2-h))/(2*h), theta=-(price(S0,K,T+h,r,.2)-price(S0,K,T-h,r,.2))/(2*h), rho=(price(S0,K,T,r+h,.2)-price(S0,K,T,r-h,.2))/(2*h))
out["greeks"] = {k: [float(g[k]), float(fd[k])] for k in fd}
ivs = np.linspace(.05, 1.5, 200); rt = implied_vol(price(S0, 130, .5, r, ivs), S0, 130, .5, r)
out["iv_roundtrip_maxerr"] = float(np.nanmax(np.abs(rt - ivs)))
# ---- 2. Surface
q = make_quotes(); iv = recover(q); F = S0*np.exp(r*q[:,0]); k = np.log(q[:,1]/F)
fits = {}; surf = {}
for T_ in TRUE:
    m = (q[:,0]==T_)&~np.isnan(iv); fits[T_] = fit_svi(k[m], iv[m]**2*T_)
    surf[T_] = dict(K=q[m,1].tolist(), iv=iv[m].tolist(), true=q[m,3].tolist(), fit=(np.sqrt(svi_w(k[m],*fits[T_])/T_)).tolist())
cal, fly = no_arb(fits)
out["surface"] = {str(t): v for t, v in surf.items()}
out["surface_stats"] = dict(rmse_iv_vs_true=float(np.sqrt(np.nanmean((iv-q[:,3])**2))), rmse_fit_vs_true=float(np.sqrt(np.mean([(np.array(v["fit"])-np.array(v["true"]))**2 for v in surf.values()][0]))),
                            calendar_ok=cal, butterfly_ok=fly, n_failed=int(np.isnan(iv).sum()))
# ---- 3. Constant-vol hedging frequency x cost (short ATM call, quote = real + 1 vol pt edge)
sr = .20; S = gbm_paths(P, n, T, S0, r, sr, 1); shv = np.full((P, n+1), sr)
ks = [1, 2, 4, 8, 16, 32, 63, 126, 252]; e1 = {}
for bps in [0, 2.5, 5, 10, 25]:
    e1[bps] = {k_: summ(hedge(S, K, T, r, shv, sr+.01, -1, bps/1e4, "time", k_)) for k_ in ks}
out["freq"] = {"ks": ks, "res": {str(b): {str(k_): v for k_, v in d.items()} for b, d in e1.items()}}
# long side at 10bps
out["freq_long"] = {str(k_): summ(hedge(S, K, T, r, shv, sr-.01, +1, 10/1e4, "time", k_)) for k_ in ks}
# ---- 4. Vol misestimation: hedge vol vs realised 20%
hv = [.10, .14, .17, .20, .23, .26, .30]; e2 = {}
for h_ in hv:
    sh = np.full((P, n+1), h_)
    e2[str(h_)] = {sd: summ(hedge(S, K, T, r, sh, sr+.01 if sd < 0 else sr-.01, sd, 5/1e4, "time", 4)) for sd in (-1, 1)}
    e2[str(h_)] = {"short": e2[str(h_)][-1], "long": e2[str(h_)][1]}
out["misvol"] = e2
# ---- 5. Regimes vs constant, fixed vs EWMA vol, three rules, attribution
lo, hi, lam = .15, .30, 6.; sq = .24; kap = 5/1e4; out["regime"] = {}
Sg = gbm_paths(P, n, T, S0, r, .24, 2)
Sr = gbm_paths(P, n, T, S0, r, regime_vols(P, n, T, lo, hi, lam, lam, 3), 4)
for name, Sx in (("constant", Sg), ("regime", Sr)):
    for vm in ("fixed", "ewma"):
        sh = np.full((P, n+1), sq) if vm == "fixed" else ewma_vol(Sx, T, sq)
        for rule, par in (("time", 4), ("time", 16), ("band", .05), ("ww", 1.)):
            B = hedge(Sx, K, T, r, sh, sq+.01, -1, kap, rule, par)
            d = summ(B); d["attr"] = {k_: float(B[k_].mean()) for k_ in ("edge","delta","gamma","theta_carry","vega","cost","resid")}
            d["attr_sd"] = {k_: float(B[k_].std()) for k_ in ("delta","gamma","theta_carry","vega","cost","resid")}
            out["regime"][f"{name}|{vm}|{rule}{par}"] = d
# ---- 6. Cost-optimal strategy map: cvar5 over rule x bps (constant vol)
out["rules_cost"] = {}
for bps in [2.5, 10, 25]:
    kp = bps/1e4; sh = shv
    out["rules_cost"][str(bps)] = {f"{rl}{pr}": summ(hedge(S, K, T, r, sh, sr+.01, -1, kp, rl, pr)) for rl, pr in
        [("time",1),("time",4),("time",16),("time",63),("band",.02),("band",.05),("band",.10),("ww",.5),("ww",1.),("ww",2.)]}
json.dump(out, open("results.json", "w"))
print(json.dumps({k: out[k] for k in ("greeks","iv_roundtrip_maxerr","surface_stats")}, indent=0)[:1500])
for b in ["0","10","25"]:
    print("bps",b, {k_: (round(v["mean"],3), round(v["std"],3), round(v["cost"],3), round(v["cvar5"],2)) for k_, v in out["freq"]["res"][b].items()})
print("misvol", {h_: (round(v["short"]["mean"],2), round(v["short"]["std"],2), round(v["long"]["mean"],2)) for h_, v in out["misvol"].items()})
for k_, v in out["regime"].items(): print(k_, round(v["mean"],3), round(v["std"],3), round(v["cvar5"],2), round(v["cost"],3), round(v["trades"],1), {a: round(b,2) for a, b in v["attr"].items()})
for b, d in out["rules_cost"].items(): print("rules", b, {k_: (round(v["mean"],2), round(v["std"],2), round(v["cvar5"],2)) for k_, v in d.items()})
