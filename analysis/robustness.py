"""Robustness / Model Challenge scenarios + match bootstrap. Never changes the official model; reads work/results.pkl."""
import pandas as pd, numpy as np, copy, os, pipeline as pl
WORK=pl.WORK
ASSOC={'United Arab Emirates','Netherlands','Hong Kong','Scotland','Canada','United States Of America','Singapore','Kuwait','Nepal','Oman','Japan'}
def scen(b,P,rule=False,mask=None,hpfun=None,loo=False,wpcol=None):
    b=b.copy()
    bal=b.balance if wpcol is None else 1-np.abs(2*b[wpcol]-1)
    b['PI']=100*bal*(P['stage_floor']+(1-P['stage_floor'])*b.stage)
    base=b.model_ok&(P['include_other']|(b.grp!='Other'))
    if mask is not None: base&=mask
    u=b[base].copy()
    if rule: u['HP']=pl.rule_pressure(u)
    else:
        thr=u.groupby('innings').PI.quantile(P['pressure_quantile']); u['HP']=u.PI>=u.innings.map(thr)
    if hpfun is not None: u['HP']=hpfun(u)
    bm,wm,u=pl.player_tables(u,'HP',P,loo=loo); return pl.score(bm,wm,'HP',P),bm,wm
def main(scheme='weighted'):
    R=pd.read_pickle(os.path.join(WORK,'results.pkl')); b=R['b']; m=R['m']; P0=copy.deepcopy(pl.P)
    wb,_=pl.solve_weights(R['res']['bat'][1]); wl,_=pl.solve_weights(R['res']['bowl'][1])
    VM=dict(w_bat=dict(zip(['rae','dae','delta','cons'],wb)),w_bowl=dict(zip(['rse','wae','delta','cons'],wl)))
    if scheme=='netvalue': P0['scheme']='netvalue'
    if scheme=='varmatch': P0.update(VM)
    assoc=set(m[m.home_team.isin(ASSOC)|m.away_team.isin(ASSOC)].match_id)
    def mod(**k):
        p=copy.deepcopy(P0)
        for a,v in k.items(): p[a]=v
        return p
    S={ 'Official model':(P0,{}),
        'Pressure = top 33% of balls':(mod(pressure_quantile=0.67),{}),
        'Pressure = top 20% of balls':(mod(pressure_quantile=0.80),{}),
        'Stage weight stronger (floor 0)':(mod(stage_floor=0.0),{}),
        'Stage weight weaker (floor 0.5)':(mod(stage_floor=0.5),{}),
        'Rule-based pressure (no WP model)':(P0,dict(rule=True)),
        'Scoring: weighted z 40/20/20/20':(mod(scheme='weighted',w_bat=pl.P['w_bat'],w_bowl=pl.P['w_bowl']),{}),
        'Scoring: net run value 60/20/20':(mod(scheme='netvalue',w_bat=pl.P['w_bat'],w_bowl=pl.P['w_bowl']),{}),
        'Scoring: variance-matched weights':(mod(scheme='weighted',**VM),{}),
        'Shrinkage k=50':(mod(k_shrink=50),{}),
        'Shrinkage k=200':(mod(k_shrink=200),{}),
        'Equal weights 25/25/25/25':(mod(w_bat=dict(rae=.25,dae=.25,delta=.25,cons=.25),w_bowl=dict(rse=.25,wae=.25,delta=.25,cons=.25)),{}),
        'Output-heavy 50/25/0/25 (no delta)':(mod(w_bat=dict(rae=.5,dae=.25,delta=0,cons=.25),w_bowl=dict(rse=.5,wae=.25,delta=0,cons=.25)),{}),
        'Eligibility 150 balls / 12 matches':(mod(min_balls=150,min_matches=12),{}),
        'Eligibility 250 balls / 18 matches':(mod(min_balls=250,min_matches=18),{}),
        'IPL only (100 balls / 8 matches)':(mod(min_balls=100,min_matches=8),dict(mask=b.grp=='IPL')),
        'T20I only (100 balls / 8 matches)':(mod(min_balls=100,min_matches=8),dict(mask=b.grp=='T20I')),
        'Exclude matches involving associate teams':(P0,dict(mask=~b.match_id.isin(assoc))),
        'Inn-1 pressure = overs 16-20 only (no WP model)':(P0,dict(hpfun=lambda u: np.where(u.innings==1,u.overid>=16,u.HP))),
        'Inn-1 pressure = stage only, top 25%':(P0,dict(hpfun=lambda u: np.where(u.innings==1,u.stage>=u[u.innings==1].stage.quantile(.75),u.HP))),
        'Chase pressure only (inn-1 ignored, 100/8)':(mod(min_balls=100,min_matches=8),dict(hpfun=lambda u: u.HP&(u.innings==2))),
        'First-innings pressure only (100/8)':(mod(min_balls=100,min_matches=8),dict(hpfun=lambda u: u.HP&(u.innings==1))),
        'In-sample WP fit (previous version, leaks)':(P0,dict(wpcol='wp_full')),
        'Leakage check: leave-own-out baselines':(P0,dict(loo=True)),
        'Exclude 2022 season':(P0,dict(mask=~b.season.astype(str).str.startswith('2022'))),
        'Exclude 2026 season':(P0,dict(mask=~b.season.astype(str).str.startswith('2026'))),
      }
    out={'bat':{},'bowl':{}}; sc={'bat':{},'bowl':{}}
    for name,(p,kw) in S.items():
        res,bm,wm=scen(b,p,**kw)
        for k in ('bat','bowl'):
            out[k][name]=res[k][1]['rank']; sc[k][name]=res[k][1]['score']
        if name=='Official model': bm0,wm0=bm,wm
    # bootstrap over matches (official model)
    rng=np.random.default_rng(42); mids=np.array(sorted(set(bm0.match_id)|set(wm0.match_id))); B=300
    br={'bat':[], 'bowl':[]}
    for i in range(B):
        w=pd.Series(rng.multinomial(len(mids),np.ones(len(mids))/len(mids)),index=mids)
        res=pl.score(bm0,wm0,'HP',P0,match_w=w)
        for k in ('bat','bowl'): br[k].append(res[k][1]['rank'])
    final={}
    for k in ('bat','bowl'):
        ranks=pd.DataFrame(out[k]); scores=pd.DataFrame(sc[k])
        bt=pd.DataFrame(br[k]).T   # players x B (NaN = not eligible in resample)
        boot=pd.DataFrame({'boot_top10_pct':100*(bt<=10).sum(axis=1)/B,'boot_top20_pct':100*(bt<=20).sum(axis=1)/B,
                           'boot_rank_median':bt.median(axis=1),'boot_rank_p10':bt.quantile(.1,axis=1),'boot_rank_p90':bt.quantile(.9,axis=1)})
        final[k]=dict(ranks=ranks,scores=scores,boot=boot)
    pd.to_pickle(final,os.path.join(WORK,'robust_%s.pkl'%scheme)); return final
if __name__=='__main__':
    import sys; f=main(sys.argv[1] if len(sys.argv)>1 else 'weighted'); R=pd.read_pickle(os.path.join(WORK,'results.pkl')); b=R['b']
    names=pd.concat([b[['striker_id','striker_name']].set_axis(['id','n'],axis=1),b[['bowler_id','bowler_name']].set_axis(['id','n'],axis=1)]).drop_duplicates('id').set_index('id').n
    pd.set_option('display.width',300); pd.set_option('display.max_columns',60)
    for k in ('bat','bowl'):
        r=f[k]['ranks']; o=r.sort_values('Official model').head(20)
        t=pd.DataFrame({'name':o.index.map(names),'off':o['Official model'],'top10_scen':(r.loc[o.index].drop(columns='Official model')<=10).sum(axis=1),
                        'worst':r.loc[o.index].max(axis=1),'missing':r.loc[o.index].isna().sum(axis=1)}).join(f[k]['boot'].round(0))
        print(t.to_string(index=False))
        short=o.copy(); short.columns=[c[:14] for c in short.columns]; short.index=short.index.map(names)
        print(short.fillna(-1).astype(int).to_string())
