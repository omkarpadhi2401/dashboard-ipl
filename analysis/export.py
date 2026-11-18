"""Builds the single source of truth (work/final.pkl) + dashboard data (01_Dashboard/data) from the approved model. No raw rows are exported."""
import pandas as pd, numpy as np, json, os, copy, warnings, pipeline as pl, robustness as rb
warnings.filterwarnings('ignore')
ROOT=pl.PROJECT; WD=pl.DASH_DATA; os.makedirs(WD,exist_ok=True)
R=pd.read_pickle(os.path.join(pl.WORK,'results.pkl')); F=pd.read_pickle(os.path.join(pl.WORK,'robust_weighted.pkl'))
b=R['b']; u=R['u']; m=R['m']; P=pl.P
names=pd.concat([b[['striker_id','striker_name']].set_axis(['id','n'],axis=1),b[['bowler_id','bowler_name']].set_axis(['id','n'],axis=1)]).drop_duplicates('id').set_index('id').n
teams=pd.read_csv(os.path.join(pl.RAW,'teams.csv')).drop_duplicates('team_id').set_index('team_id').team_name
assoc=set(m[m.home_team.isin(rb.ASSOC)|m.away_team.isin(rb.ASSOC)].match_id)
u['band']=pd.cut(u.PI,[-1,20,40,60,80,101],labels=['0-20','20-40','40-60','60-80','80-100'])
DUP='Scoring: weighted z 40/20/20/20'
def verdict(boot,scen): return 'Stable' if (boot>=60 and scen>=20) else ('Moderate' if (boot>=40 or scen>=15) else 'Borderline')
def pct(s,hi=True):
    r=s.rank(pct=True)*100
    return r if hi else 100-r
OUT={}
for k,t,idc in (('bat',R['bm'],'striker_id'),('bowl',R['wm'],'bowler_id')):
    r,e=R['res'][k]; e=e.copy(); hp=t[t.HP]; x=u[u.HP&(u.bat_ball if k=='bat' else u.legal)]
    g=hp.groupby([idc,'inn']).sum(numeric_only=True)
    if k=='bat': g['x']=100*(g.runs-g.e_runs)/g.balls; g['y']=100*g.runs/g.balls
    else: g['x']=100*(g.e_conc-g.conc)/g.balls; g['y']=6*g.conc/g.balls
    sp=g[['balls','x','y']].unstack('inn'); sp.columns=['inn1_balls','inn2_balls','inn1_vs_exp','inn2_vs_exp','inn1_rate','inn2_rate']
    e=e.join(sp)
    e['assoc_pct']=100*x.match_id.isin(assoc).groupby(x[idc]).mean(); e['ipl_pct']=100*(x.grp=='IPL').groupby(x[idc]).mean()
    rk=F[k]['ranks'].drop(columns=[DUP]); e['scen_top10']=(rk.drop(columns='Official model')<=10).sum(axis=1); e['scen_total']=rk.shape[1]-1
    e['scen_worst']=rk.drop(columns='Official model').max(axis=1); e['scen_ineligible']=rk.drop(columns='Official model').isna().sum(axis=1)
    e=e.join(F[k]['boot'])
    e['verdict']=[verdict(a,c) for a,c in zip(e.boot_top10_pct,e.scen_top10)]
    q=hp[hp.balls>=P['min_inn_balls']]
    if k=='bat':
        e['fail_low_sr_pct']=100*(q.runs/q.balls<1.0).groupby(q[idc]).mean()
        e['fail_cheap_out_pct']=100*((hp.outs>0)&(hp.runs<10)).groupby(hp[idc]).mean()
        e['outs_per100']=100*e.p_outs/e.p_balls
    else:
        e['fail_expensive_pct']=100*(6*q.conc/q.balls>=12).groupby(q[idc]).mean()
        e['fail_wicketless_pct']=100*(q.wk==0).groupby(q[idc]).mean()
    if k=='bat':
        ps=x.groupby([idc,'pace_or_spin']).agg(balls=('runs','size'),runs=('runs','sum'),outs=('striker_out','sum'))
        for ty in ('Pace','Spin'):
            d=ps.xs(ty,level=1); e['vs_%s_balls'%ty.lower()]=d.balls; e['vs_%s_sr'%ty.lower()]=100*d.runs/d.balls; e['vs_%s_outs'%ty.lower()]=d.outs
    else:
        e['bowl_type']=x.groupby(idc).pace_or_spin.agg(lambda s:s.mode().iat[0]); e['bowl_style']=x.groupby(idc).bowling_type.agg(lambda s:s.mode().iat[0])
    e['pc_output']=pct(e.rae); e['pc_wickets']=pct(e.dae); e['pc_lift']=pct(e.delta); e['pc_consistency']=pct(e.cons)
    e['pc_boundary']=pct(e.p_bnd_pct,hi=(k=='bat')); e['pc_dot']=pct(e.p_dot_pct,hi=(k=='bowl'))
    e['name']=e.index.map(names); e.index.name='player_id'
    for c,w in zip(('rae','dae','delta','cons'),(.4,.2,.2,.2)): e['contrib_'+c]=15*w*e['z_'+c]
    OUT[k]=e
def just_bat(p):
    return (f"{p['name']} is ranked #{int(p['rank'])} (score {p.score:.1f}). On {int(p.p_balls)} high-pressure balls across {int(p.p_matches)} matches he scored {int(p.p_runs)} runs at a strike rate of {p.p_sr:.1f} "
            f"(his non-pressure strike rate is {p.np_sr:.1f}), which is {p.rae:+.1f} runs per 100 balls versus the average batter in the same contexts. "
            f"He was dismissed {int(p.p_outs)} times against {p.e_outs:.1f} expected, and beat expectation in {p.cons:.0f}% of his {int(p.p_inns)} qualifying pressure innings. "
            f"Robustness: top-10 in {int(p.scen_top10)} of {int(p.scen_total)} alternative scenarios and in {p.boot_top10_pct:.0f}% of bootstrap resamples - classified {p.verdict}.")
def just_bowl(p):
    return (f"{p['name']} is ranked #{int(p['rank'])} (score {p.score:.1f}). On {int(p.p_balls)} high-pressure balls across {int(p.p_matches)} matches he conceded {int(p.p_conc)} runs (economy {p.p_econ:.2f}; non-pressure {p.np_econ:.2f}) "
            f"and took {int(p.p_wk)} wickets against {p.e_wk:.1f} expected. That is {p.rae:+.1f} runs saved per 100 balls versus the average bowler in the same contexts, "
            f"and he was at or below expected runs in {p.cons:.0f}% of his {int(p.p_inns)} qualifying pressure spells. "
            f"Robustness: top-10 in {int(p.scen_top10)} of {int(p.scen_total)} alternative scenarios and in {p.boot_top10_pct:.0f}% of bootstrap resamples - classified {p.verdict}.")
LAB=dict(rae='output vs expected',dae='wickets vs expected',delta='lift vs own normal level',cons='consistency')
def near(p,e):
    cut=e[e['rank']==10].iloc[0]; comps={c:p['contrib_'+c]-cut['contrib_'+c] for c in LAB}
    worst=min(comps,key=comps.get); best=max(comps,key=comps.get)
    return (f"Rank #{int(p['rank'])}, {cut.score-p.score:.1f} score points behind #10 ({cut['name']}). Largest shortfall versus #10: {LAB[worst]} ({comps[worst]:+.1f} points); "
            f"best relative component: {LAB[best]} ({comps[best]:+.1f}). Top-10 in {int(p.scen_top10)} of {int(p.scen_total)} scenarios, {p.boot_top10_pct:.0f}% of bootstrap resamples.")
for k,fn in (('bat',just_bat),('bowl',just_bowl)):
    e=OUT[k]; e['justification']=[fn(p) if p['rank']<=10 else '' for _,p in e.iterrows()]
    e['near_miss_reason']=[near(p,e) if 10<p['rank']<=15 else '' for _,p in e.iterrows()]
exec(open(os.path.join(pl.HERE,'export2.py')).read())
