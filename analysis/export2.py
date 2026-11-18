# continuation of export.py (kept in a second file only for size reasons)
q=copy.deepcopy(P); q['min_balls']=150; q['min_matches']=12; alt=pl.score(R['bm'],R['wm'],'HP',q)
WATCH={}
for k in ('bat','bowl'):
    a=alt[k][1]; a=a[~a.index.isin(OUT[k].index)&(a['rank']<=15)].copy(); a['name']=a.index.map(names)
    WATCH[k]=a[['name','p_balls','p_matches','rae','dae','delta','cons','rank']].rename(columns={'rank':'rank_if_150_12'})
EV={}
for k,idc,opp in (('bat','striker_id','bowling_team_id'),('bowl','bowler_id','batting_team_id')):
    ids=OUT[k][OUT[k]['rank']<=15].index; x=u[u.HP&u[idc].isin(ids)]
    if k=='bat':
        x=x[x.bat_ball]; g=x.groupby([idc,'match_id']).agg(date=('match_date','first'),competition=('comp_name','first'),opp=(opp,'first'),innings=('innings','first'),
            balls=('runs','size'),runs=('runs','sum'),outs=('striker_out','sum'),expected=('e_runs','sum'),fours=('is_four','sum'),sixes=('is_six','sum'),avg_PI=('PI','mean'))
        g['vs_expected']=g.runs-g.expected
    else:
        g=x.groupby([idc,'match_id']).agg(date=('match_date','first'),competition=('comp_name','first'),opp=(opp,'first'),innings=('innings','first'),
            balls=('legal','sum'),runs=('bowl_runs','sum'),wickets=('bowl_wkt','sum'),expected=('e_conc_l','sum'),avg_PI=('PI','mean'))
        g['vs_expected']=g.expected-g.runs
    g['opposition']=g.opp.map(teams); g=g.drop(columns='opp').reset_index().rename(columns={idc:'player_id'})
    g['name']=g.player_id.map(names); g['situation']=np.where(g.innings==1,'1st innings','Chase'); EV[k]=g.sort_values(['player_id','date']).round(2)
TL={}
x=u[u.bat_ball]; lg=x.groupby('band').agg(balls=('runs','size'),runs=('runs','sum')); lg['rate']=100*lg.runs/lg.balls
t=x[x.striker_id.isin(OUT['bat'].index)].groupby(['striker_id','band']).agg(balls=('runs','size'),runs=('runs','sum'),outs=('striker_out','sum')).reset_index()
t['rate']=100*t.runs/t.balls.replace(0,np.nan); t['league_rate']=t.band.map(lg.rate).astype(float); t['name']=t.striker_id.map(names); TL['bat']=t.rename(columns={'striker_id':'player_id'})
lg=u.groupby('band').agg(l=('legal','sum'),r=('bowl_runs','sum')); lg['rate']=6*lg.r/lg.l
t=u[u.bowler_id.isin(OUT['bowl'].index)].groupby(['bowler_id','band']).agg(balls=('legal','sum'),runs=('bowl_runs','sum'),wickets=('bowl_wkt','sum')).reset_index()
t['rate']=6*t.runs/t.balls.replace(0,np.nan); t['league_rate']=t.band.map(lg.rate).astype(float); t['name']=t.bowler_id.map(names); TL['bowl']=t.rename(columns={'bowler_id':'player_id'})
for k in TL: TL[k]['band']=TL[k]['band'].astype(str)
bb,lgx=pl.expectations(u,'HP'); BASE=bb.join(lgx[['e_conc','e_wkt','l']]).reset_index().rename(columns={'n':'bat_balls','l':'legal_balls','HP':'high_pressure'})
x=u[u.legal]; PS=x.groupby(['pace_or_spin','HP']).agg(balls=('legal','sum'),runs=('bowl_runs','sum'),wk=('bowl_wkt','sum')).reset_index(); PS['econ']=6*PS.runs/PS.balls; PS['balls_per_wkt']=PS.balls/PS.wk
cov=dict(R['cov']); cov.update(eligible_batters=len(OUT['bat']),eligible_bowlers=len(OUT['bowl']),batters_with_any_pressure_ball=int(len(R['res']['bat'][0])),bowlers_with_any_pressure_ball=int(len(R['res']['bowl'][0])),
    other_tournament_deliveries_excluded=int((b.model_ok&(b.grp=='Other')).sum()),bowl_speed_zero_pct=round(100*float((b.bowl_speed<=0).mean()),1),
    date_min=str(m.match_date.min()),date_max=str(m.match_date.max()),ipl_matches=int(u[u.grp=='IPL'].match_id.nunique()),t20i_matches=int(u[u.grp=='T20I'].match_id.nunique()),
    hp_inn1=int((u.HP&(u.innings==1)).sum()),hp_inn2=int((u.HP&(u.innings==2)).sum()),auc_inn1_cv=round(R['diag']['cv']['auc1_cv'],3),auc_inn2_cv=round(R['diag']['cv']['auc2_cv'],3))
HPBY=u.groupby(['innings','overid']).HP.mean().unstack(0).round(3)
DIAG={}
rng=np.random.default_rng(7); mids=np.array(sorted(set(R['bm'].match_id)|set(R['wm'].match_id))); qh=copy.deepcopy(P); qh['min_balls']=100; qh['min_matches']=8; qh['k_shrink']=50
acc={k:{c:[] for c in ['z_rae','z_dae','z_delta','z_cons','score_z']} for k in ('bat','bowl')}
for i in range(40):
    h=rng.random(len(mids))<0.5; w1=pd.Series(h.astype(float),index=mids); r1=pl.score(R['bm'],R['wm'],'HP',qh,match_w=w1); r2=pl.score(R['bm'],R['wm'],'HP',qh,match_w=1-w1)
    for k in acc:
        for c in acc[k]:
            j=pd.concat([r1[k][1][c],r2[k][1][c]],axis=1).dropna(); acc[k][c].append(j.corr(method='spearman').iloc[0,1])
for k in ('bat','bowl'):
    z=OUT[k][['z_rae','z_dae','z_delta','z_cons']]; W=np.array([.4,.2,.2,.2]); C=z.cov(ddof=0).values
    DIAG[k]=dict(corr=z.corr().round(2),shares=dict(zip(z.columns,[float(v) for v in (W*(C@W)/(W@C@W)).round(3)])),split_half={c:round(float(np.mean(v)),2) for c,v in acc[k].items()})
SCEN={k:F[k]['ranks'].drop(columns=[DUP]).assign(name=lambda d:d.index.map(names)) for k in ('bat','bowl')}
FINAL=dict(players=OUT,watch=WATCH,evidence=EV,timeline=TL,baselines=BASE,pace_spin=PS,coverage=cov,hp_by_over=HPBY,diag=DIAG,scenarios=SCEN,params=P,wp=R['diag'],thr={int(a):float(c) for a,c in R['thr'].items()},par={a:float(c) for a,c in R['par'].items()})
pd.to_pickle(FINAL,os.path.join(pl.WORK,'final.pkl'))
def recs(df): return json.loads(df.replace([np.inf,-np.inf],np.nan).round(3).to_json(orient='records'))
def dump(n,o): json.dump(o,open(os.path.join(WD,n),'w'),indent=1,default=str)
for k,fn in (('bat','batters.json'),('bowl','bowlers.json')): dump(fn,recs(OUT[k].reset_index().drop(columns=['mw','mt','pos','qual','inn','wicket_value'],errors='ignore')))
dump('top10.json',{k:recs(OUT[k][OUT[k]['rank']<=10].reset_index()[['rank','player_id','name','score','verdict','p_balls','p_matches','boot_top10_pct','scen_top10','scen_total','justification']]) for k in ('bat','bowl')})
dump('near_misses.json',{k:recs(OUT[k][(OUT[k]['rank']>10)&(OUT[k]['rank']<=15)].reset_index()[['rank','player_id','name','score','verdict','p_balls','p_matches','rae','dae','delta','cons','boot_top10_pct','scen_top10','near_miss_reason']]) for k in ('bat','bowl')})
dump('eligibility_watchlist.json',{k:recs(WATCH[k].reset_index().rename(columns={'striker_id':'player_id','bowler_id':'player_id'})) for k in ('bat','bowl')})
dump('evidence.json',{k:recs(EV[k]) for k in ('bat','bowl')})
dump('timeline.json',{k:recs(TL[k]) for k in ('bat','bowl')})
def scj(k):
    s=SCEN[k]; s=s[s['Official model']<=20].sort_values('Official model'); s.index.name='player_id'
    return dict(scenarios=[c for c in s.columns if c!='name'],rows=recs(s.reset_index()))
dump('robustness.json',{k:scj(k) for k in ('bat','bowl')})
dump('baselines.json',recs(BASE)); dump('pace_spin_league.json',recs(PS)); dump('coverage.json',cov)
dump('pressure_by_over.json',recs(HPBY.reset_index().rename(columns={1:'inn1_share',2:'inn2_share'})))
fb={str(f):{i:{a:float(c) for a,c in d.items()} for i,d in v.items()} for f,v in R['diag']['cv']['fold_betas'].items()}
dump('model.json',dict(parameters=P,pressure_thresholds=FINAL['thr'],par_run_rate=FINAL['par'],wp_cv_auc=dict(inn1=cov['auc_inn1_cv'],inn2=cov['auc_inn2_cv']),fold_coefficients=fb,
    wicket_value_runs=dict(bat=float(OUT['bat'].wicket_value.iloc[0]),bowl=float(OUT['bowl'].wicket_value.iloc[0])),
    diagnostics={k:dict(component_correlation=json.loads(DIAG[k]['corr'].to_json()),effective_variance_share=DIAG[k]['shares'],split_half_reliability=DIAG[k]['split_half']) for k in DIAG}))
for k in ('bat','bowl'):
    e=OUT[k]; print(e[e['rank']<=10][['rank','name','score','verdict','scen_top10','boot_top10_pct']].round(1).to_string(index=False)); print(WATCH[k].round(1).to_string())
print(cov); print(DIAG['bat']['shares'],DIAG['bat']['split_half'],DIAG['bowl']['shares'],DIAG['bowl']['split_half'])
import content as C
dump('glossary.json',[dict(zip(['metric','definition','formula','source_columns','sample','limitation'],g)) for g in C.GLOSSARY])
dump('features.json',[dict(zip(['name','purpose','calculation','source_columns','sample','limitation','delivered_in','status'],f)) for f in C.FEATURES])
dump('limitations.json',C.LIMITATIONS); dump('ai_disclosure.json',[dict(heading=h,text=t) for h,t in C.AI_DISCLOSURE])

# ---- one-file copy of the JSON so the dashboard also opens by double-click (file://) ----
import glob
_b={os.path.basename(f):json.load(open(f,encoding='utf-8')) for f in sorted(glob.glob(os.path.join(WD,'*.json')))}
open(os.path.join(WD,'data_bundle.js'),'w',encoding='utf-8').write('// Generated by export.py from the JSON files in this folder (derived results only, no raw data).\nwindow.SUPERR_DATA='+json.dumps(_b,separators=(',',':'))+';\n')
# ---- approved results as CSV (derived, one row per player / per player-match) ----
os.makedirs(pl.RESULTS,exist_ok=True)
_cb=['rank','name','score','verdict','p_balls','p_matches','p_inns','p_runs','p_outs','p_sr','np_sr','rae','dae','delta','cons','reliab','inn1_vs_exp','inn2_vs_exp','ipl_pct','assoc_pct','scen_top10','scen_total','boot_top10_pct','boot_rank_median']
_cw=[c.replace('p_runs','p_conc').replace('p_outs','p_wk').replace('p_sr','p_econ') for c in _cb]
OUT['bat'].sort_values('rank')[_cb].round(3).to_csv(os.path.join(pl.RESULTS,'SupeRR_Final_Batter_Rankings.csv'),index_label='player_id')
OUT['bowl'].sort_values('rank')[_cw].round(3).to_csv(os.path.join(pl.RESULTS,'SupeRR_Final_Bowler_Rankings.csv'),index_label='player_id')
pd.concat([EV['bat'].assign(discipline='batting'),EV['bowl'].assign(discipline='bowling')]).drop(columns=['match_id']).to_csv(os.path.join(pl.RESULTS,'SupeRR_Player_Evidence.csv'),index=False)
print('bundle + approved_results written')
