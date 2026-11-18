"""SupeRR Selector S2 - pressure-performance pipeline (single source of truth).
Run:  python3 pipeline.py   (from the code folder; raw data stays in ../../Data Pack, never copied)
Stages: 1 audit/clean -> 2 match state -> 3 win-probability models -> 4 pressure index
        -> 5 context expectations -> 6 player metrics -> 7 scores
"""
import pandas as pd, numpy as np, os, json, re
HERE=os.path.dirname(os.path.abspath(__file__))
PROJECT=os.path.abspath(os.path.join(HERE,'..','..'))        # .../SupeRR_Selector_Season_2
BASE=os.path.dirname(PROJECT)                               # parent folder: holds the confidential raw data and caches
RAW=os.path.join(BASE,'Data Pack')
DASH=os.path.join(PROJECT,'01_Dashboard'); DASH_DATA=os.path.join(DASH,'data'); RESULTS=os.path.join(PROJECT,'02_Analysis','approved_results')
XLSX_DIR=os.path.join(PROJECT,'03_Excel'); PPT_DIR=os.path.join(PROJECT,'04_PowerPoint'); PPT_ASSETS=os.path.join(PPT_DIR,'assets'); REPORT_DIR=os.path.join(PROJECT,'05_Reports')
WORK=os.path.join(BASE,'_private_work')   # kept OUTSIDE the project folder: caches raw-data-derived tables

# ---------------- parameters (every tunable assumption lives here) ----------------
P=dict(pressure_quantile=0.75, stage_floor=0.30,   # high-pressure = top 25% of balls by Pressure Index
       k_shrink=100,             # reliability = n/(n+k) pressure balls
       min_balls=200, min_matches=15,   # eligibility (pressure balls, matches with pressure balls)
       min_inn_balls=6,          # a "pressure innings/spell" needs >= this many pressure balls
       w_bat=dict(rae=0.40,dae=0.20,delta=0.20,cons=0.20),
       w_bowl=dict(rse=0.40,wae=0.20,delta=0.20,cons=0.20),
       include_other=False)      # A-team/emerging tournaments excluded from rankings

def sigmoid(z): return 1/(1+np.exp(-np.clip(z,-30,30)))
def fit_logit(X,y,iters=50,ridge=1e-6):
    b=np.zeros(X.shape[1])
    for _ in range(iters):
        p=sigmoid(X@b); W=p*(1-p)+1e-9
        H=X.T@(X*W[:,None])+ridge*np.eye(X.shape[1]); g=X.T@(y-p)
        step=np.linalg.solve(H,g); b+=step
        if np.abs(step).max()<1e-8: break
    return b
def auc(y,p):
    o=np.argsort(p); r=np.empty(len(p)); r[o]=np.arange(1,len(p)+1)
    n1=y.sum(); n0=len(y)-n1
    return (r[y==1].sum()-n1*(n1+1)/2)/(n1*n0)

def load():
    b=pd.read_csv(os.path.join(RAW,'ball_by_ball.csv'),low_memory=False,keep_default_na=False,na_values=[''])
    m=pd.read_csv(os.path.join(RAW,'matches.csv')); c=pd.read_csv(os.path.join(RAW,'competitions.csv'))
    m=m.merge(c,on='comp_id',how='left')
    m['grp']=np.where(m.comp_name.str.startswith('IPL'),'IPL',np.where(m.match_format=='T20I','T20I','Other'))
    return b,m

def prepare(b,m):
    cov={}
    cov['raw_deliveries']=len(b); cov['raw_matches_in_matches_csv']=len(m); cov['matches_with_ball_data']=b.match_id.nunique()
    b=b.sort_values(['match_id','innings','innings_ball_num']).reset_index(drop=True)
    so=b.innings>2; cov['super_over_deliveries_excluded']=int(so.sum()); b=b[~so].copy()
    b=b.merge(m[['match_id','grp','season','win_team_id','first_inn_revised_overs','second_inn_revised_overs','revised_target','knock_out','stage','match_date','comp_name']],on='match_id',how='left')
    b['wide']=b.extras_type.eq('wide'); b['noball']=b.extras_type.isin(['Overstep','other'])
    b['legal']=~(b.wide|b.noball)
    b['tot']=b.runs+b.extras1_runs+b.extras_2_runs
    b['bowl_runs']=b.runs+np.where(b.wide|b.noball,b.extras1_runs,0)       # byes/leg-byes/penalty not charged to bowler
    b['bat_ball']=~b.wide                                                   # balls faced exclude wides
    b['striker_out']=b.is_wicket&(b.dismissed_player_id==b.striker_id)&~b.dismissal_type.isin(['Retire Out'])
    b['bowl_wkt']=b.is_wicket&b.dismissal_type.isin(['Caught','Bowled','LBW','Stump','Hit Wicket'])
    g=b.groupby(['match_id','innings'])
    b['runs_pre']=g.tot.cumsum()-b.tot
    b['wk_pre']=g.is_wicket.cumsum()-b.is_wicket.astype(int)
    b['legal_pre']=g.legal.cumsum()-b.legal.astype(int)
    inn=g.agg(total=('tot','sum'),legal_balls=('legal','sum'),wk=('is_wicket','sum')).reset_index()
    t1=inn[inn.innings==1].set_index('match_id').total
    b['target']=b.match_id.map(t1)+1
    # match eligibility for pressure modelling
    ninn=b.groupby('match_id').innings.nunique()
    has_winner=m.set_index('match_id').win_team_id.notna()
    revised=m.set_index('match_id')[['first_inn_revised_overs','second_inn_revised_overs','revised_target']].notna().any(axis=1)
    mid=pd.Series(b.match_id.unique())
    ok=mid[mid.map(ninn).eq(2)&mid.map(has_winner)&~mid.map(revised)]
    cov['matches_single_innings_or_no_result_excluded']=int((~(mid.map(ninn).eq(2)&mid.map(has_winner))).sum())
    cov['matches_rain_revised_excluded']=int((mid.map(revised)&mid.map(ninn).eq(2)&mid.map(has_winner)).sum())
    cov['matches_in_pressure_model']=len(ok)
    b['model_ok']=b.match_id.isin(set(ok))
    b['bat_win']=(b.batting_team_id==b.win_team_id).astype(int)
    b['balls_rem']=120-b.legal_pre
    b['need']=np.where(b.innings==2,b.target-b.runs_pre,np.nan)
    b['phase']=np.where(b.overid<=6,'Powerplay (1-6)',np.where(b.overid<=15,'Middle (7-15)','Death (16-20)'))
    # par first-innings run rate per group-season (for innings-1 model)
    i1=inn[inn.innings==1].merge(m[['match_id','grp','season']],on='match_id')
    par=6*i1.groupby('grp').total.sum()/i1.groupby('grp').legal_balls.sum()
    b['par_rr']=b.grp.map(par)
    cov['deliveries_in_pressure_model']=int(b.model_ok.sum())
    return b,cov,par

# ---- win probability feature builders (operate on arrays so we can score hypothetical states) ----
def X2(need,balls_rem,wk):
    br=np.maximum(balls_rem,1); rrr=np.minimum(6*need/br,36); f=br/120; wih=10-wk
    return np.column_stack([np.ones(len(rrr)),rrr,wih,f,rrr*f,wih*f,rrr*wih/10])
def X1(runs,legal,wk,par):
    f=legal/120; rr=np.where(legal>=6,6*runs/np.maximum(legal,1),par)-par
    return np.column_stack([np.ones(len(f)),rr,wk,f,rr*f,wk*f])
N2=['intercept','RRR','wkts_in_hand','frac_balls_left','RRR x frac_left','WIH x frac_left','RRR x WIH/10']
N1=['intercept','RR_minus_par','wkts_lost','frac_innings_done','RRdiff x frac_done','wkts x frac_done']

def wp2(beta,need,balls_rem,wk):
    p=sigmoid(X2(need,balls_rem,wk)@beta)
    p=np.where(need<=0,1.0,p); p=np.where((wk>=10)&(need>0),0.0,p); p=np.where((balls_rem<=0)&(need>0),0.0,p)
    return p
def wp1(beta,runs,legal,wk,par): return sigmoid(X1(runs,legal,np.minimum(wk,10),par)@beta)

def pressure(b):
    d=b[b.model_ok]
    d2=d[d.innings==2]; d1=d[d.innings==1]
    beta2=fit_logit(X2(d2.need.values,d2.balls_rem.values,d2.wk_pre.values),d2.bat_win.values)
    beta1=fit_logit(X1(d1.runs_pre.values,d1.legal_pre.values,d1.wk_pre.values,d1.par_rr.values),d1.bat_win.values)
    i2=(b.innings==2).values
    need=b.need.fillna(0).values; br=b.balls_rem.values; wk=b.wk_pre.values; runs=b.runs_pre.values; lg=b.legal_pre.values; par=b.par_rr.values
    wp=np.where(i2,wp2(beta2,need,br,wk),wp1(beta1,runs,lg,wk,par))
    six=np.where(i2,wp2(beta2,need-6,br-1,wk),wp1(beta1,runs+6,lg+1,wk,par))
    out=np.where(i2,wp2(beta2,need,br-1,wk+1),wp1(beta1,runs,lg+1,wk+1,par))
    b['wp_full']=wp                                      # in-sample fit (kept only for the leakage comparison)
    # OFFICIAL: 5-fold cross-fitting by match (fold = match_id mod 5): every ball is scored by models that never saw its match
    fold=(b.match_id%5).values; wp=np.full(len(b),np.nan); fold_betas={}
    for f in range(5):
        tr=(b.model_ok.values)&(fold!=f); te=fold==f
        q2=b[tr&i2]; q1=b[tr&~i2]
        f2=fit_logit(X2(q2.need.values,q2.balls_rem.values,q2.wk_pre.values),q2.bat_win.values)
        f1=fit_logit(X1(q1.runs_pre.values,q1.legal_pre.values,q1.wk_pre.values,q1.par_rr.values),q1.bat_win.values)
        fold_betas[f]=dict(inn1=dict(zip(N1,f1.round(5))),inn2=dict(zip(N2,f2.round(5))))
        wp[te]=np.where(i2[te],wp2(f2,need[te],br[te],wk[te]),wp1(f1,runs[te],lg[te],wk[te],par[te]))
    six=np.where(i2,wp2(beta2,need-6,br-1,wk),wp1(beta1,runs+6,lg+1,wk,par)); b['fold']=fold
    b['wp']=wp; b['swing']=100*np.clip(six-out,0,1)    # supplementary: WP swing between a six and a wicket
    b['balance']=1-np.abs(2*wp-1)                      # 1 = 50/50 contest, 0 = result decided
    b['stage']=np.clip(lg/120,0,1)                     # share of the innings already bowled
    b['PI']=100*b.balance*(P['stage_floor']+(1-P['stage_floor'])*b.stage)   # Pressure Index 0-100
    dd=b[b.model_ok]
    cv=dict(auc1_cv=float(auc(dd[dd.innings==1].bat_win.values,dd[dd.innings==1].wp.values)),auc2_cv=float(auc(dd[dd.innings==2].bat_win.values,dd[dd.innings==2].wp.values)),fold_betas=fold_betas)
    diag=dict(cv=cv,beta2=dict(zip(N2,beta2.round(5))),beta1=dict(zip(N1,beta1.round(5))),
              auc2=float(auc(d2.bat_win.values,sigmoid(X2(d2.need.values,d2.balls_rem.values,d2.wk_pre.values)@beta2))),
              auc1=float(auc(d1.bat_win.values,sigmoid(X1(d1.runs_pre.values,d1.legal_pre.values,d1.wk_pre.values,d1.par_rr.values)@beta1))))
    return b,diag,beta1,beta2

def rule_pressure(b):
    """Alternative, model-free definition used only in the Model Challenge panel."""
    rrr=6*b.need/np.maximum(b.balls_rem,1)
    a=(b.innings==2)&(b.balls_rem<=60)&(rrr>=7.5)&(rrr<=15)
    c=(b.innings==1)&(b.overid>=16)
    return (a|c)

def classify(b,q,col='PI'):
    u=b[b.model_ok & (P['include_other']|(b.grp!='Other'))]
    return u.groupby('innings')[col].quantile(q)      # separate threshold per innings so both innings contribute equally

def expectations(u,flag):
    """Context-similarity baseline: average player in same competition group x innings x phase x pressure state."""
    keys=['grp','innings','phase',flag]
    bb=u[u.bat_ball].groupby(keys).agg(e_runs=('runs','mean'),e_out=('striker_out','mean'),n=('runs','size'))
    lg=u.groupby(keys).agg(r=('bowl_runs','sum'),w=('bowl_wkt','sum'),l=('legal','sum'))
    lg['e_conc']=lg.r/lg.l; lg['e_wkt']=lg.w/lg.l
    return bb,lg

def player_tables(u,flag,P,loo=False):
    keys=['grp','innings','phase',flag]
    bb,lg=expectations(u,flag)
    u=u.join(bb[['e_runs','e_out']],on=keys).join(lg[['e_conc','e_wkt']],on=keys)
    if loo:   # leakage check: remove each player's own balls from his own baseline cell
        x=u[u.bat_ball]; ct=x.groupby(keys).agg(R=('runs','sum'),O=('striker_out','sum'),N=('runs','size'))
        pt=x.groupby(keys+['striker_id']).agg(r=('runs','sum'),o=('striker_out','sum'),n=('runs','size')).join(ct,on=keys)
        pt['e_runs']=(pt.R-pt.r)/(pt.N-pt.n); pt['e_out']=(pt.O-pt.o)/(pt.N-pt.n)
        u=u.drop(columns=['e_runs','e_out']).join(pt[['e_runs','e_out']],on=keys+['striker_id'])
        ct=u.groupby(keys).agg(R=('bowl_runs','sum'),W=('bowl_wkt','sum'),L=('legal','sum'))
        pt=u.groupby(keys+['bowler_id']).agg(r=('bowl_runs','sum'),w=('bowl_wkt','sum'),l=('legal','sum')).join(ct,on=keys)
        pt['e_conc']=(pt.R-pt.r)/(pt.L-pt.l); pt['e_wkt']=(pt.W-pt.w)/(pt.L-pt.l)
        u=u.drop(columns=['e_conc','e_wkt']).join(pt[['e_conc','e_wkt']],on=keys+['bowler_id'])
    # ---------- batting: per player-match-pressure aggregates ----------
    x=u[u.bat_ball]
    bm=x.groupby(['striker_id','match_id',flag]).agg(inn=('innings','first'),balls=('runs','size'),runs=('runs','sum'),outs=('striker_out','sum'),
        e_runs=('e_runs','sum'),e_out=('e_out','sum'),fours=('is_four','sum'),sixes=('is_six','sum'),dots=('runs',lambda s:(s==0).sum())).reset_index()
    # ---------- bowling ----------
    u=u.assign(e_conc_l=np.where(u.legal,u.e_conc,0),e_wkt_l=np.where(u.legal,u.e_wkt,0),
               bdot=(u.legal&(u.bowl_runs==0)),bbnd=(u.is_four|u.is_six))
    wm=u.groupby(['bowler_id','match_id',flag]).agg(inn=('innings','first'),balls=('legal','sum'),conc=('bowl_runs','sum'),wk=('bowl_wkt','sum'),
        e_conc=('e_conc_l','sum'),e_wkt=('e_wkt_l','sum'),dots=('bdot','sum'),bnd=('bbnd','sum')).reset_index()
    return bm,wm,u

def score(bm,wm,flag,P,kind_weights=None,match_w=None):
    """Aggregate player-match rows into metrics + composite score. match_w: optional bootstrap weights per match."""
    out={}
    for kind,t,idc in (('bat',bm,'striker_id'),('bowl',wm,'bowler_id')):
        t=t.copy()
        if match_w is not None:
            w=t.match_id.map(match_w).fillna(0).values
            num=[c for c in t.columns if c not in (idc,'match_id',flag,'inn')]
            t[num]=t[num].mul(w,axis=0); t['mw']=w
        else: t['mw']=1.0
        if kind=='bat':
            t['pos']=((t.runs>=t.e_runs)&(t.balls>=P['min_inn_balls']*t.mw)&(t.mw>0))*t.mw
        else:
            t['pos']=((t.conc<=t.e_conc)&(t.balls>=P['min_inn_balls']*t.mw)&(t.mw>0))*t.mw
        t['qual']=((t.balls>=P['min_inn_balls']*t.mw)&(t.mw>0))*t.mw
        t['mt']=(t.balls>0)*t.mw
        a=t.groupby([idc,flag]).sum(numeric_only=True).drop(columns=['match_id'],errors='ignore')
        hp=a.xs(True,level=flag); lp=a.xs(False,level=flag).reindex(hp.index).fillna(0)
        r=pd.DataFrame(index=hp.index)
        r['p_balls']=hp.balls; r['p_matches']=hp.mt; r['np_balls']=lp.balls
        if kind=='bat':
            r['p_runs']=hp.runs; r['p_outs']=hp.outs; r['p_sr']=100*hp.runs/hp.balls; r['np_sr']=100*lp.runs/lp.balls.replace(0,np.nan)
            r['p_avg']=hp.runs/hp.outs.replace(0,np.nan); r['p_bnd_pct']=100*(hp.fours+hp.sixes)/hp.balls; r['p_dot_pct']=100*hp.dots/hp.balls
            r['e_runs']=hp.e_runs; r['e_outs']=hp.e_out
            r['rae']=100*(hp.runs-hp.e_runs)/hp.balls; r['dae']=100*(hp.e_out-hp.outs)/hp.balls
            r['np_rae']=100*(lp.runs-lp.e_runs)/lp.balls.replace(0,np.nan)
            r['clutch_pct']=100*hp.runs/(hp.runs+lp.runs)
            prim,sec=('rae','dae'); W=P['w_bat']
        else:
            r['p_conc']=hp.conc; r['p_wk']=hp.wk; r['p_econ']=6*hp.conc/hp.balls; r['np_econ']=6*lp.conc/lp.balls.replace(0,np.nan)
            r['p_sr']=hp.balls/hp.wk.replace(0,np.nan); r['p_dot_pct']=100*hp.dots/hp.balls; r['p_bnd_pct']=100*hp.bnd/hp.balls
            r['e_conc']=hp.e_conc; r['e_wk']=hp.e_wkt
            r['rae']=100*(hp.e_conc-hp.conc)/hp.balls; r['dae']=100*(hp.wk-hp.e_wkt)/hp.balls   # runs saved / wickets above expected
            r['np_rae']=100*(lp.e_conc-lp.conc)/lp.balls.replace(0,np.nan)
            r['clutch_pct']=100*hp.wk/(hp.wk+lp.wk).replace(0,np.nan)
            W=dict(rae=P['w_bowl']['rse'],dae=P['w_bowl']['wae'],delta=P['w_bowl']['delta'],cons=P['w_bowl']['cons'])
        r['delta']=r.rae-r.np_rae.fillna(0)
        r['p_inns']=hp.qual; r['cons']=100*hp.pos/hp.qual.replace(0,np.nan)
        r['reliab']=r.p_balls/(r.p_balls+P['k_shrink'])
        r['eligible']=(r.p_balls>=P['min_balls'])&(r.p_matches>=P['min_matches'])
        e=r[r.eligible].copy()
        cmean=e.cons.mean()
        for c in ('rae','dae','delta'): e['s_'+c]=e[c]*e.reliab          # shrink toward 0 (= average player in same contexts)
        e['s_cons']=cmean+(e.cons-cmean)*e.reliab
        for c in ('rae','dae','delta','cons'):
            s=e['s_'+c]; e['z_'+c]=(s-s.mean())/s.std(ddof=0)
        V=(hp.runs.sum()/hp.outs.sum()) if kind=='bat' else (hp.conc.sum()/hp.wk.sum())   # runs per wicket on pressure balls (all players)
        e['wicket_value']=V; e['net']=e.rae+V*e.dae                          # net run value per 100 pressure balls
        e['s_net']=e.net*e.reliab; e['z_net']=(e.s_net-e.s_net.mean())/e.s_net.std(ddof=0)
        if P.get('scheme','weighted')=='netvalue':
            e['score_z']=(W['rae']+W['dae'])*e.z_net+W['delta']*e.z_delta+W['cons']*e.z_cons
        else:
            e['score_z']=sum(W[c]*e['z_'+c] for c in ('rae','dae','delta','cons'))
        e['score']=50+15*e.score_z                                          # display scale; 50 = average eligible player
        e=e.sort_values('score_z',ascending=False); e['rank']=np.arange(1,len(e)+1)
        out[kind]=(r,e)
    return out

def run(P=P,verbose=True):
    b,m=load(); b,cov,par=prepare(b,m); b,diag,beta1,beta2=pressure(b)
    thr=classify(b,P['pressure_quantile']); b['HP']=b.PI>=b.innings.map(thr)
    u=b[b.model_ok&(P['include_other']|(b.grp!='Other'))].copy()
    cov['deliveries_in_player_analysis']=len(u); cov['high_pressure_deliveries']=int(u.HP.sum()); cov['pressure_threshold_PI_inn1']=float(thr[1]); cov['pressure_threshold_PI_inn2']=float(thr[2])
    bm,wm,u=player_tables(u,'HP',P); res=score(bm,wm,'HP',P)
    return dict(b=b,u=u,m=m,cov=cov,diag=diag,par=par,bm=bm,wm=wm,res=res,thr=thr,beta1=beta1,beta2=beta2)

if __name__=='__main__':
    R=run(); pd.to_pickle(R,os.path.join(WORK,'results.pkl'))
    print(json.dumps(R['cov'],indent=1)); print(R['diag'])

def solve_weights(e,target=(0.4,0.2,0.2,0.2),iters=500):
    """Find nominal weights whose EFFECTIVE variance shares equal the target shares (accounts for component correlation)."""
    z=e[['z_rae','z_dae','z_delta','z_cons']].values; C=np.cov(z.T,ddof=0); w=np.array(target,float); t=np.array(target)
    for _ in range(iters):
        sh=w*(C@w)/(w@C@w); w=w*(t/np.maximum(sh,1e-3))**0.5; w=w/w.sum()
    return w, w*(C@w)/(w@C@w)
