# continuation of build_excel.py
def para_sheet(name,ttl,sub,items,tab='548235',w=(34,120)):
    ws=sheet(name,tab); title(ws,ttl,sub); r=4
    for h,t in items:
        a=ws.cell(row=r,column=1,value=h); a.font=font(bold=True,color=NAVY); a.alignment=Alignment(vertical='top',wrap_text=True)
        b_=ws.cell(row=r,column=2,value=t); b_.font=font(); b_.alignment=Alignment(wrap_text=True,vertical='top'); ws.row_dimensions[r].height=max(18,15*(len(str(t))//115+1)); r+=1
    widths(ws,list(w)); return ws
# Evidence
for k,nm in (('bat','Evidence_Batters'),('bowl','Evidence_Bowlers')):
    ev=F['evidence'][k].copy(); rk=F['players'][k]['rank']; ev['rank']=ev.player_id.map(rk).astype(int); ev=ev.sort_values(['rank','date'])
    if k=='bat': ev=ev[['rank','name','date','competition','opposition','situation','balls','runs','outs','fours','sixes','expected','vs_expected','avg_PI']]; ev.columns=['Official rank','Player','Date','Competition','Opposition','Situation','Pressure balls','Runs','Dismissed','Fours','Sixes','Expected runs','Runs vs expected','Average Pressure Index']
    else: ev=ev[['rank','name','date','competition','opposition','situation','balls','runs','wickets','expected','vs_expected','avg_PI']]; ev.columns=['Official rank','Player','Date','Competition','Opposition','Situation','Legal pressure balls','Runs conceded','Wickets','Expected runs','Runs saved vs expected','Average Pressure Index']
    ws=sheet(nm,'1F4E79'); title(ws,'Match-by-match pressure evidence - top 10 and near misses (ranks 1-15)','One row per player per match, high-pressure balls only. Derived aggregates; no raw ball-by-ball rows are reproduced. Use the filter on Player.')
    table(ws,ev); widths(ws,[9,22,12,40,22,12,10,10,10,10,10,11,12,12])
# Robustness
for k,nm in (('bat','Robustness_Batters'),('bowl','Robustness_Bowlers')):
    s=F['scenarios'][k]; p=F['players'][k]; s=s[s['Official model']<=20].sort_values('Official model')
    df=pd.DataFrame({'Official rank':s['Official model'].astype(int),'Player':s['name'],'Verdict':p.loc[s.index,'verdict'],'Scenarios top-10 (of 24)':p.loc[s.index,'scen_top10'].astype(int),'Scenarios ineligible':p.loc[s.index,'scen_ineligible'].astype(int),
        'Worst rank':p.loc[s.index,'scen_worst'],'Bootstrap top-10 %':p.loc[s.index,'boot_top10_pct'],'Bootstrap top-20 %':p.loc[s.index,'boot_top20_pct'],'Bootstrap median rank':p.loc[s.index,'boot_rank_median'],'Bootstrap 10th pct rank':p.loc[s.index,'boot_rank_p10'],'Bootstrap 90th pct rank':p.loc[s.index,'boot_rank_p90']})
    for c in s.columns:
        if c not in ('Official model','name'): df[c]=s[c]
    ws=sheet(nm,'C00000'); title(ws,'Robustness and Model Challenge - rank of the official top 20 under each alternative assumption','Blank = player not eligible in that scenario (sample falls below the threshold). Supplementary analysis: none of these scenarios alters the official ranking.')
    table(ws,df,fmt={c:'0' for c in df.columns if c not in ('Bootstrap top-10 %','Bootstrap top-20 %')}); widths(ws,[9,22,11]+[12]*40); ws.row_dimensions[4].height=70
    for v,col in (('Stable','C6EFCE'),('Moderate','FFEB9C'),('Borderline','FFC7CE')): ws.conditional_formatting.add(f'C5:C{4+len(df)}',CellIsRule(operator='equal',formula=[f'"{v}"'],fill=PatternFill('solid',fgColor=col)))
# Near miss
ws=sheet('Near_Miss','C00000'); title(ws,'Alternative candidates and near misses','Ranks 11-15 in the official model, and players excluded only by the eligibility rule.'); r=4
for k,lab in (('bat','Batters'),('bowl','Bowlers')):
    p=F['players'][k]; nmx=p[(p['rank']>10)&(p['rank']<=15)].sort_values('rank')
    df=pd.DataFrame({'Official rank':nmx['rank'].astype(int),'Player':nmx['name'],'Score':nmx.score,'Verdict':nmx.verdict,'Pressure balls':nmx.p_balls.astype(int),'Matches':nmx.p_matches.astype(int),'Output vs exp /100':nmx.rae,'Wickets vs exp /100':nmx.dae,'Lift':nmx.delta,'Consistency %':nmx.cons,'Bootstrap top-10 %':nmx.boot_top10_pct,'Scenarios top-10 (of 24)':nmx.scen_top10.astype(int),'Why he missed':nmx.near_miss_reason})
    ws.cell(row=r,column=1,value=lab+' - ranks 11 to 15').font=font(bold=True,size=12,color=PINK); header(ws,r+1,list(df.columns))
    for i,rec in enumerate(df.itertuples(index=False),r+2):
        for c,v in enumerate(rec,1):
            if isinstance(v,np.generic): v=v.item()
            x=ws.cell(row=i,column=c,value=v); x.font=font(); x.number_format='0.0' if isinstance(v,float) else '0'
            if c==13: x.alignment=Alignment(wrap_text=True,vertical='top'); ws.row_dimensions[i].height=48
    r+=len(df)+4
    w=F['watch'][k]; ws.cell(row=r,column=1,value=lab+' - eligibility watch-list (below 200 balls or 15 matches; rank shown is from a 150-ball / 12-match re-run and is NOT official)').font=font(bold=True,color=NAVY)
    header(ws,r+1,['Rank if 150/12','Player','Pressure balls','Matches','Output vs exp /100','Wickets vs exp /100','Lift','Consistency %'])
    for i,(pid,q) in enumerate(w.iterrows(),r+2):
        for c,v in enumerate([int(q.rank_if_150_12),q['name'],int(q.p_balls),int(q.p_matches),float(q.rae),float(q.dae),float(q.delta),float(q.cons)],1):
            x=ws.cell(row=i,column=c,value=v); x.font=font(); x.number_format='0.0' if isinstance(v,float) else '0'
    r+=len(w)+4
widths(ws,[10,22,9,11,10,9,11,11,9,11,11,11,95])
# Supplementary
for k,nm in (('bat','Supplementary_Batters'),('bowl','Supplementary_Bowlers')):
    p=F['players'][k].sort_values('rank'); bat=k=='bat'
    base={'Official rank':p['rank'].astype(int),'Player':p['name'],'Clutch contribution %':p.clutch_pct,'Boundary %':p.p_bnd_pct,'Dot-ball %':p.p_dot_pct}
    if bat: base.update({'Dismissals per 100 balls':p.outs_per100,'Pressure innings under a run a ball %':p.fail_low_sr_pct,'Pressure innings out for < 10 %':p.fail_cheap_out_pct,'Balls vs pace':p.vs_pace_balls,'SR vs pace':p.vs_pace_sr,'Outs vs pace':p.vs_pace_outs,'Balls vs spin':p.vs_spin_balls,'SR vs spin':p.vs_spin_sr,'Outs vs spin':p.vs_spin_outs,
        'Pace/spin sample flag':np.where((p.vs_pace_balls<60)|(p.vs_spin_balls<60),'Low sample (<60 balls on one side)','OK')})
    else: base.update({'Bowling type':p.bowl_type,'Bowling style':p.bowl_style,'Spells at 12+ per over %':p.fail_expensive_pct,'Wicketless spells %':p.fail_wicketless_pct})
    base.update({'Percentile: output':p.pc_output,'Percentile: wickets':p.pc_wickets,'Percentile: lift':p.pc_lift,'Percentile: consistency':p.pc_consistency,'Percentile: boundary':p.pc_boundary,'Percentile: dot ball':p.pc_dot})
    df=pd.DataFrame(base); tl=F['timeline'][k]
    for band in ['0-20','20-40','40-60','60-80','80-100']:
        t=tl[tl.band==band].set_index('player_id'); df[f'PI {band}: balls']=t.balls.reindex(p.index).values; df[f'PI {band}: '+('SR' if bat else 'economy')]=t.rate.reindex(p.index).values
    ws=sheet(nm,'7030A0'); title(ws,'Supplementary exploratory analysis - '+('batters' if bat else 'bowlers'),'NOT part of the official score. Clutch contribution, failure analysis, pace/spin split, radar percentiles (0-100, higher = better) and the Pressure Response Timeline by Pressure Index band.')
    table(ws,df,fmt={c:'0' for c in df.columns if 'balls' in c.lower() or 'Outs' in c}); widths(ws,[9,22]+[12]*40); ws.row_dimensions[4].height=58
# Baselines
bs=F['baselines'].copy(); bs.columns=['Competition group','Innings','Phase','High pressure?','Expected runs per ball (batter)','Expected dismissal rate per ball','Balls faced in cell','Expected runs conceded per legal ball','Expected wickets per legal ball','Legal balls in cell']
ws=sheet('Baselines','548235'); title(ws,'Match Context Similarity - expected performance by context cell','Every ball is compared with the average for its cell. These 24 cells are the baseline for RAE, RSE and wickets vs expected.')
table(ws,bs,fmt={c:'0.0000' for c in bs.columns}); widths(ws,[16,9,18,12,16,16,12,16,16,12])
lg=F['pace_spin'].copy(); lg.columns=['Bowling type','High pressure?','Legal balls','Runs conceded','Wickets','Economy','Balls per wicket']
r=8+len(bs); ws.cell(row=r,column=1,value='League reference: pace vs spin').font=font(bold=True,color=NAVY); header(ws,r+1,list(lg.columns))
for i,rec in enumerate(lg.itertuples(index=False),r+2):
    for c,v in enumerate(rec,1):
        if isinstance(v,np.generic): v=v.item()
        x=ws.cell(row=i,column=c,value=v); x.font=font(); x.number_format='0.00' if isinstance(v,float) else '#,##0'
hb=F['hp_by_over'].reset_index(); r+=len(lg)+5; ws.cell(row=r,column=1,value='Share of balls classed as high pressure, by over').font=font(bold=True,color=NAVY); header(ws,r+1,['Over','1st innings','Chase'])
for i,rec in enumerate(hb.itertuples(index=False),r+2):
    for c,v in enumerate(rec,1):
        x=ws.cell(row=i,column=c,value=float(v) if c>1 else int(v)); x.font=font(); x.number_format='0.0%' if c>1 else '0'
# Data audit
cv=F['coverage']; ws=sheet('Data_Audit','548235'); title(ws,'Data audit and coverage','What was supplied, what was used, and what was excluded and why.')
aud=[('Raw deliveries in ball_by_ball.csv',cv['raw_deliveries'],'No duplicate deliveries (match, innings, ball number is unique).'),('Matches in matches.csv',cv['raw_matches_in_matches_csv'],'16 abandoned matches have no ball-by-ball rows.'),('Matches with ball-by-ball data',cv['matches_with_ball_data'],'Every one of them is present in matches.csv.'),
 ('Super-over deliveries excluded',cv['super_over_deliveries_excluded'],'Innings 3 and 4.'),('Matches excluded: no result, abandoned or single innings',cv['matches_single_innings_or_no_result_excluded'],'No winner or no second innings, so pressure cannot be modelled.'),
 ('Matches excluded: rain-revised overs or target',cv['matches_rain_revised_excluded'],'Revised targets break the 120-ball assumption.'),('Matches in the pressure model',cv['matches_in_pressure_model'],'Two innings, a winner, no revision.'),('Deliveries in the pressure model',cv['deliveries_in_pressure_model'],''),
 ('Deliveries excluded: emerging / A-team tournaments',cv['other_tournament_deliveries_excluded'],'Neither IPL nor T20I (30 matches).'),('Deliveries in player analysis (IPL + T20I)',cv['deliveries_in_player_analysis'],'%d IPL matches and %d T20I matches.'%(cv['ipl_matches'],cv['t20i_matches'])),
 ('High-pressure deliveries',cv['high_pressure_deliveries'],'Top 25%% within each innings type: %d first-innings, %d chase.'%(cv['hp_inn1'],cv['hp_inn2'])),('Batters with at least one pressure ball',cv['batters_with_any_pressure_ball'],''),('Eligible batters (>= 200 pressure balls, >= 15 matches)',cv['eligible_batters'],''),
 ('Bowlers with at least one pressure ball',cv['bowlers_with_any_pressure_ball'],''),('Eligible bowlers (>= 200 pressure balls, >= 15 matches)',cv['eligible_bowlers'],''),('Date range',cv['date_min']+' to '+cv['date_max'],''),('bowl_speed recorded as 0 (% of deliveries)',cv['bowl_speed_zero_pct'],'Field not used.')]
header(ws,4,['Item','Value','Note'])
for i,(a_,v,n_) in enumerate(aud,5):
    ws.cell(row=i,column=1,value=a_).font=font(); x=ws.cell(row=i,column=2,value=v); x.font=font(bold=True); x.number_format='#,##0' if isinstance(v,int) else '0.0'; x.alignment=Alignment(horizontal='right'); ws.cell(row=i,column=3,value=n_).font=font(color='555555')
r=7+len(aud); ws.cell(row=r,column=1,value='Scoring conventions').font=font(bold=True,color=NAVY)
for i,t in enumerate(['Legal ball: extras_type is not wide, Overstep or other (no-ball).','Balls faced by a batter: every delivery except wides.','Runs charged to a bowler: runs off the bat + wides + no-balls. Byes, leg-byes and penalty runs are not charged.','Bowler wickets: Caught, Bowled, LBW, Stump, Hit Wicket. Run-outs, retired out and obstructing the field are not credited.','Batter dismissals: is_wicket and dismissed_player_id equals striker_id (retired out excluded).','Target for a chase: first-innings total + 1.'],r+1): ws.cell(row=i,column=1,value=t).font=font()
widths(ws,[62,22,80])
# Diagnostics
ws=sheet('Diagnostics','C00000'); title(ws,'Score diagnostics - are the components comparable?','Each z-score has mean 0 and standard deviation 1 among eligible players. They are correlated, so effective influence differs from the nominal weights.'); r=4
for k,lab in (('bat','Batters'),('bowl','Bowlers')):
    dg=F['diag'][k]; names_=['Output','Wickets','Lift','Consistency']; ws.cell(row=r,column=1,value=lab).font=font(bold=True,size=12,color=PINK); header(ws,r+1,['Component','Nominal weight','Effective share of score variance','Split-half reliability']+['Corr with '+n for n in names_])
    for i,(zc,nm_,w_) in enumerate(zip(['z_rae','z_dae','z_delta','z_cons'],names_,[.4,.2,.2,.2])):
        vals=[nm_,w_,dg['shares'][zc],dg['split_half'][zc]]+[float(v) for v in dg['corr'].loc[zc].values]
        for c,v in enumerate(vals,1): x=ws.cell(row=r+2+i,column=c,value=v); x.font=font(); x.number_format='0%' if c in (2,3) else '0.00'
    ws.cell(row=r+6,column=1,value='Composite score').font=font(bold=True); x=ws.cell(row=r+6,column=4,value=dg['split_half']['score_z']); x.font=font(bold=True); x.number_format='0.00'; r+=9
ws.cell(row=r,column=1,value='Split-half reliability: matches are split at random into two halves 40 times (seed 7); the Spearman correlation between the two halves is averaged. Half-samples use 100 balls / 8 matches and k = 50.').font=font(italic=True,color='555555')
widths(ws,[22,16,18,16,16,16,16,18])
# Glossary / features / AI / README
ws=sheet('Formula_Glossary','548235'); title(ws,'Formula glossary','Definition, formula, source columns, sample and limitation for every metric.')
table(ws,pd.DataFrame(C.GLOSSARY,columns=['Metric','Plain-English definition','Formula','Source columns','Sample / eligibility','Limitation']),wrapcols=('Metric','Plain-English definition','Formula','Source columns','Sample / eligibility','Limitation')); widths(ws,[26,40,62,40,30,44])
for i in range(5,5+len(C.GLOSSARY)): ws.row_dimensions[i].height=88
ws.freeze_panes='B5'
ws=sheet('Feature_Register','548235'); title(ws,'Feature register','Purpose, calculation, source columns, sample size, limitations and output for each additional feature. "Core" items feed the official ranking; "Supplementary" items never do.')
cols=['Feature','Purpose','Calculation','Source columns','Sample','Limitation','Delivered in','Core or supplementary']; table(ws,pd.DataFrame(C.FEATURES,columns=cols),wrapcols=cols); widths(ws,[28,36,56,30,34,36,36,16])
for i in range(5,5+len(C.FEATURES)): ws.row_dimensions[i].height=80
ws.freeze_panes='B5'
para_sheet('AI_Disclosure','AI Assistance and Independent Decision-Making','Required disclosure under the competition rules.',C.AI_DISCLOSURE)
para_sheet('Limitations','Limitations and uncertainty','Read these before relying on any individual ranking position.',[(str(i+1),t) for i,t in enumerate(C.LIMITATIONS)],w=(6,150))
rd=para_sheet('README',C.PROJECT,'Individual submission - Excel workbook. Single source of truth: the approved official model (cross-fitted, 40/20/20/20, 200 balls / 15 matches).',[
 ('Dashboard','Final top 10 batters and bowlers, plus a player explorer (choose a player in the yellow cells).'),('Top10_Batters / Top10_Bowlers','The approved ranked lists with evidence and a written justification for each player.'),
 ('Batter_Metrics / Bowler_Metrics','All eligible players. Blue values come from the data pack via pipeline.py; black cells are live formulas that rebuild the score and rank.'),('Parameters','Weights and shrinkage constant (editable for the Model Challenge), thresholds, eligibility, win-probability coefficients.'),
 ('Evidence_*','Match-by-match pressure record for ranks 1-15.'),('Robustness_*','24 alternative scenarios and 300 bootstrap resamples for the top 20.'),('Near_Miss','Ranks 11-15 and the eligibility watch-list.'),('Supplementary_*','Exploratory features that are not part of the score.'),
 ('Baselines','Context cells used for expected performance; pace/spin and by-over reference tables.'),('Data_Audit','Coverage and exclusions.'),('Diagnostics','Component correlations, effective weights, reliability.'),('Formula_Glossary / Feature_Register','Definitions and documentation.'),('AI_Disclosure / Limitations','Required disclosure and honest caveats.'),
 ('Colour code','Blue text = input values; black = formulas; yellow fill = cells you may edit.'),('Confidentiality','This workbook contains derived results only. The raw competition data pack is not included and must not be shared.')],w=(34,120))
del wb['Sheet']
order=['README','Dashboard','Top10_Batters','Top10_Bowlers','Batter_Metrics','Bowler_Metrics','Parameters','Evidence_Batters','Evidence_Bowlers','Robustness_Batters','Robustness_Bowlers','Near_Miss','Supplementary_Batters','Supplementary_Bowlers','Baselines','Diagnostics','Data_Audit','Formula_Glossary','Feature_Register','Limitations','AI_Disclosure']
wb._sheets=[wb[n] for n in order]; wb.active=1; wb.calculation.fullCalcOnLoad=True
out=pl.XLSX_DIR; os.makedirs(out,exist_ok=True); wb.save(os.path.join(out,'SupeRR_Pressure_Analytics.xlsx')); print('saved',len(wb.sheetnames),'sheets')
