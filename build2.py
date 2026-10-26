import json, os
from build import F as F1          # v1 build side effect is harmless; v2 overwrites below
OUT = os.environ.get("OUT", "."); D = json.load(open("results.json")); D2 = json.load(open("results_v2.json"))
F = [("Closed forms reproduce the simulator.", "For an ATM option at fair vol, E|ΔΔ| = ΓSσ√Δt·√(2/π) and E[S²Γ] = S/(σ√(2πT)) give hedging-error std ≈ σS√(Δt/8) and expected rebalancing cost ≈ κS√N/π plus entry and unwind. Simulation is within 4% on std for N ≥ 31 rebalances and within 2% on cost for N ≥ 7. Minimising risk aversion × variance + cost gives N* ∝ κ^(-2/3): the simulated tail-optimal N fell from 126 to 63 as costs rose from 10 to 25 bps (theory: ×0.54, grid resolves only ×0.5)."),
("Spread width has an interior optimum.", "With flow elasticity 0.4 per vol point, uninformed profit ∝ h·e^(-a·h) peaks at h = 1/a = 2.5 vol points. The book's mean P&L peaks at 3 points (10.7), versus 6.6 at 1 point and 0.3 at 0.25. Mean/std keeps rising to 4 points (1.71) because flow, and so inventory, shrinks."),
("Adverse selection is a tight-spread problem.", "With 15% informed flow, the mean falls 57% at a 0.25-point half-spread (0.3 vs 0.7) and std rises 15 to 17% at 0.25 to 1 point, but the mean falls only 2% at 2 points. At 2 points the book earns +11.7 from spread, gamma and theta net to +0.3, and hedging costs return 1.5 (13% of spread)."),
("Hedging rule matters most when costs are high.", "At 5 bps all sensible rules are close, though Whalley-Wilmott (γ=2) beats hedging every step on Sharpe (1.42 vs 1.38), tail (-3.4 vs -3.8) and cost (1.5 vs 1.9). At 25 bps WW (γ=0.1) cuts hedging cost 37% versus daily hedging (4.8 vs 7.6), lifts the mean from 4.2 to 6.9 and the tail from -13.4 to -12.0 at 10% higher std. A badly sized fixed band (3 shares) doubles std, so bands must scale with portfolio gamma."),
("Inventory skew behaves like Avellaneda-Stoikov.", "Shifting the reservation vol against vega inventory (strength 2) cuts vega inventory 46% (39 to 21), std 30% (7.9 to 5.5) and the 5% tail from -5.2 to -2.2, for 8% less mean; Mean/std peaks at 1.79 with strength 5. Over-skewing (20) pushes quotes through fair value and loses 13.3 on average, so the optimum is interior."),
("Vol-estimate error is a tail risk more than a mean risk.", "A ±4 point error in fair vol moves mean P&L by only about ±1.5 (8.7 to 11.4), but the 5% tail is -5.2 with no error, -10.5 at -4 points and -7.5 at +4 points. The mean rising with upward bias is unexplained here (hypothesis: the book is net short vega), so do not read it as 'quote high'."),
("Gaps cannot be hedged by rebalancing.", "Adding 4 jumps a year (sd 5%) leaves the mean about unchanged (10.2 to 10.5) but lifts std 41% (7.9 to 11.1) and worsens the tail from -5.2 to -11.6 under daily hedging; WW improves it only to -10.2. Gap risk needs option hedges and limits."),
("Limits.", "Flat vol within each regime (no skew dynamics), one 3-month expiry, no option-on-option vega hedging, stylised informed flow, and flow elasticity, arrival rate and informed share are free parameters, so absolute levels are model-specific. With 2,000 paths the standard error on the book mean is about 0.18, so mean differences under 0.5 are noise.")]
fh = "".join(f'<p class="f"><b>{a}</b>{b}</p>' for a, b in F)
t = open("tpl.html").read()
t = t.replace("--c5:#7a8aa3;", "--c5:#7a8aa3;--c6:#7b4fb8;--c7:#2f8f4e;").replace("--c5:#8d9bb5}", "--c5:#8d9bb5;--c6:#b28bf0;--c7:#5cc983}")
t = t.replace("const f2=x=>", "const COL={edge:'--c1',spread:'--c1',delta:'--c2',gamma:'--c3',theta_carry:'--c4',vega:'--c7',cost:'--c6',resid:'--c5'};const f2=x=>").replace("css(CL[i%5])", "css(COL[a])")
t = t.replace("Short and long ATM calls, 3 months, S=K=100, r=2%. 4,000 paths per scenario.", "3-month options, S=100, r=2%. Single ATM option: 4,000 paths. Six-option book: 2,000 paths.")
t = t.replace('<h2>Hedge less often than you think, but never not at all</h2><p class="lead">What discrete hedging, vol misestimation and transaction costs do to a market maker who sells (or buys) one vol point of edge.</p>',
              '<h2>Spread width sets the edge; hedge rule and inventory skew decide how much you keep</h2><p class="lead">Closed-form theory, a single-option hedging simulator and a six-option market-making book, all with explicit costs and exact P&amp;L attribution.</p>')
t = t.replace('P&amp;L attribution</button></nav>', 'P&amp;L attribution</button><button data-t="s6">Theory vs simulation</button><button data-t="s7">Market-making book</button></nav>')
sec = """<section id="s6"><h2>Closed-form benchmarks match the simulator to within a few percent</h2><p class="lead">ATM, fair vol: hedging-error std ≈ σS√(Δt/8) and expected cost ≈ κS√N/π plus entry and unwind. The asymptotics weaken below about 15 rebalances.</p>
<div class="card"><div class="seg" id="m6"><span>Quantity</span></div><div class="ch"><canvas id="c6"></canvas></div></div><div class="card tbl" id="t6"></div></section>
<section id="s7"><h2>Profit peaks at a 2 to 3 vol-point half-spread; skew and hedge rule shape the tail</h2><p class="lead">Six OTM options on one expiry; customer flow thins as quotes widen (0.4 per vol point); 15% of flow is informed about the vol regime; fair vol is a causal EWMA; 5 bps hedge cost unless stated. Dollars per book.</p>
<div class="card"><div class="seg" id="s7a"><span>Experiment</span></div><div class="seg" id="s7b"><span>Metric</span></div><div class="ch"><canvas id="c7"></canvas></div></div>
<div class="card"><div class="seg" id="s7c"></div><div class="ch"><canvas id="c8"></canvas></div></div></section>"""
t = t.replace("</main>", sec + "</main>")
js = r"""const D2=/*D2*/;const TH=D2.theory;
seg('m6',[['std','Hedging-error std, no costs'],['cost','Hedging cost at 10 bps']],'std',v=>{const a=TH[v+'_theory'],b=TH[v+'_sim'];
mk('c6',{type:'line',data:{labels:TH.N.map(String),datasets:[{label:'Closed form',data:a,borderColor:css('--ink'),backgroundColor:css('--ink'),borderDash:[5,4],tension:.2},{label:'Simulation',data:b,borderColor:css('--c3'),backgroundColor:css('--c3'),showLine:false,pointRadius:5}]},options:{scales:{x:{title:{display:true,text:'Rebalances over the life (N)'}},y:{title:{display:true,text:'$ per option'}}}}});
$('t6').innerHTML='<table><tr><th>N</th><th>Closed form</th><th>Simulation</th><th>Sim / theory</th></tr>'+TH.N.map((n,i)=>`<tr><td>${n}</td><td>${a[i].toFixed(3)}</td><td>${b[i].toFixed(3)}</td><td>${(b[i]/a[i]).toFixed(2)}</td></tr>`).join('')+'</table>'});
let ex='spread',mt='mean',rn=null;const XL={spread:'Half-spread (vol points)',rule:'Hedging rule',bias:'Fair-vol error (vol points)',inv:'Inventory skew strength',jump:'Hedging rule'},ML={mean:'Mean P&L',std:'Std',cvar5:'5% tail mean (CVaR)',sharpe:'Mean / std'},AL2={spread:'Spread vs model mark',delta:'Delta slippage',gamma:'Gamma',theta_carry:'Theta + carry',vega:'Vega',cost:'Hedging costs',resid:'Residual'};
function r7(){const e=D2[ex],names=Object.keys(e.runs);if(!names.includes(rn))rn=names[0];
mk('c7',{type:'bar',data:{labels:e.x,datasets:names.map((nm,i)=>({label:nm,data:e.runs[nm].map(d=>d[mt]),backgroundColor:css(CL[i])}))},options:{scales:{x:{title:{display:true,text:XL[ex]}},y:{title:{display:true,text:ML[mt]+' ($ per book)'}}}}});
mk('c8',{type:'bar',data:{labels:e.x,datasets:Object.keys(AL2).map(a=>({label:AL2[a],data:e.runs[rn].map(d=>d.attr[a]),backgroundColor:css(COL[a])}))},options:{scales:{x:{stacked:true},y:{stacked:true,title:{display:true,text:'Mean P&L by source, run: '+rn}}}}});
const c=$('s7c');c.innerHTML='<span>Attribution for</span>';names.forEach(nm=>{const b=document.createElement('button');b.textContent=nm;if(nm===rn)b.className='on';b.onclick=()=>{rn=nm;r7()};c.appendChild(b)})}
seg('s7a',[['spread','Spread width'],['rule','Hedging rule'],['bias','Vol error'],['inv','Inventory skew'],['jump','Jumps']],'spread',v=>{ex=v;r7()});seg('s7b',Object.entries(ML),'mean',v=>{mt=v;r7()});
"""
t = t.replace("</script></body>", js.replace("/*D2*/", json.dumps(D2, separators=(",", ":"))) + "</script></body>")
t = t.replace("/*DATA*/", json.dumps(D, separators=(",", ":"))).replace("<!--FINDINGS-->", fh)
open(OUT + "/hedging_lab.html", "w").write(t)
def tb(e, run, cols=("mean", "std", "cvar5", "sharpe", "cost")):
    L = D2[e]["runs"][run]; return "| | " + " | ".join(cols) + " |\n|---|" + "---|" * len(cols) + "\n" + "\n".join(f"| {x} | " + " | ".join(f"{d[c]:.2f}" for c in cols) + " |" for x, d in zip(D2[e]["x"], L))
md = f"""# Options Market Making, Volatility Trading and Dynamic Hedging

## 1. Question
How do discrete hedging, vol-estimation error and transaction costs change the profitability and risk of options market making?

## 2. Models
- **Pricing layer** (`bs.py`, `surface.py`): Black-Scholes with all five Greeks (checked against central differences), vectorised implied-vol inversion (bisection plus Newton, round trip 1e-15), SVI smile fit with calendar and butterfly checks (6 bp recovery error under price noise).
- **Single-option hedging simulator** (`sim.py`): short or long ATM call, one vol point of quoted edge, proportional costs, time, band and Whalley-Wilmott rules, constant-vol and two-state regime worlds, fixed or EWMA hedge vol.
- **Market-making book** (`mm.py`): six OTM options, quotes in vol space around an EWMA fair vol, customer arrivals thinning as spread widens, 15% informed flow, Avellaneda-Stoikov style inventory skew, netted portfolio delta hedging, optional Merton jumps.
- **Attribution**: spread vs model mark, delta slippage, gamma, theta plus cash carry, vega, hedging costs and an exact residual (below 0.1 in all runs reported).

## 3. Theory (ATM, fair vol, r small)
Per rebalance the hedged P&L is ½ΓS²σ²Δt(Z²−1), with variance ½(ΓS²σ²Δt)². Using E[φ(d₁)²] and ∫dt/√(T²−t²) = π/2, Var = σ²S²Δt/8, so std ≈ σS√(Δt/8). With E|ΔΔ| = ΓSσ√Δt·√(2/π) and E[S²Γ] = S/(σ√(2πT)), expected cost ≈ κS√N/π. Minimising (a/2)Var + cost gives N* = (πaσ²ST/(8κ))^(2/3), so N* ∝ κ^(-2/3).

## 4. Findings
""" + "\n".join(f"{i+1}. **{a}** {b}" for i, (a, b) in enumerate(F)) + f"""

### Spread sweep, informed share 15%, half-spread in vol points
{tb("spread", "informed 15%")}

### Hedging rules at 25 bps
{tb("rule", "25 bps")}

## 5. Talking points for interviews
- Gamma/theta: the book earns theta and pays realised variance, so hedging only changes the dispersion of that difference, not its mean.
- Hedging error shrinks as 1/√N while cost grows as √N, so the optimal N scales as κ^(-2/3).
- Wider spreads earn more per trade but thin flow (h* = 1/a), and informed flow is what punishes tight quotes.
- Inventory skew buys Sharpe at the cost of mean, with an interior optimum and a failure mode when over-applied.

## 6. Reproduce
`python run_experiments.py && python run_v2.py && OUT=. python build2.py` (needs numpy, scipy). Not done: Heston/SABR worlds with minimum-variance delta, vega-hedging with other expiries, skew dynamics.
"""
open(OUT + "/REPORT.md", "w").write(md)
