"""Builds SupeRR_Pressure_Analytics.xlsx from work/final.pkl. Scores and ranks are live formulas driven by the Parameters sheet."""
import pandas as pd, numpy as np, os, json, pipeline as pl, content as C
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import CellIsRule
ROOT=pl.PROJECT; F=pd.read_pickle(os.path.join(pl.WORK,'final.pkl'))
NAVY='1B2A4A'; PINK='E91E63'; LIGHT='F3F5F9'; INPUT='FFF2CC'
def font(**k): return Font(name='Arial',size=k.pop('size',10),**k)
HF=font(bold=True,color='FFFFFF'); HFILL=PatternFill('solid',fgColor=NAVY); thin=Side(style='thin',color='D0D4DC')
wb=Workbook()
def sheet(name,tab=NAVY):
    ws=wb.create_sheet(name); ws.sheet_properties.tabColor=tab; ws.sheet_view.showGridLines=False; return ws
def title(ws,t,sub=None):
    ws['A1']=t; ws['A1'].font=font(size=16,bold=True,color=NAVY)
    if sub: ws['A2']=sub; ws['A2'].font=font(italic=True,color='555555')
def header(ws,row,cols,start=1,height=32):
    for i,c in enumerate(cols):
        x=ws.cell(row=row,column=start+i,value=c); x.font=HF; x.fill=HFILL; x.alignment=Alignment(wrap_text=True,vertical='center',horizontal='center'); x.border=Border(bottom=thin)
    ws.row_dimensions[row].height=height
def widths(ws,w):
    for i,v in enumerate(w,1): ws.column_dimensions[L(i)].width=v
def table(ws,df,row=4,fmt=None,wrapcols=()):
    header(ws,row,list(df.columns))
    for r,rec in enumerate(df.itertuples(index=False),row+1):
        for c,v in enumerate(rec,1):
            if isinstance(v,(float,np.floating)) and (np.isnan(v) or np.isinf(v)): v=None
            elif isinstance(v,np.generic): v=v.item()
            x=ws.cell(row=r,column=c,value=v); x.font=font()
            if isinstance(v,float): x.number_format=(fmt or {}).get(df.columns[c-1],'0.0')
            if df.columns[c-1] in wrapcols: x.alignment=Alignment(wrap_text=True,vertical='top')
    ws.freeze_panes=ws.cell(row=row+1,column=3); ws.auto_filter.ref=f"A{row}:{L(len(df.columns))}{row+len(df)}"
    return row+len(df)

# ---------------- Parameters ----------------
wp=sheet('Parameters','7F6000'); title(wp,'Model parameters','Yellow cells are the official inputs. Editing them recomputes every score and live rank in the metric sheets (Model Challenge). Official values are listed beside them.')
rows=[('Weight: output vs expected',0.40),('Weight: wickets vs expected',0.20),('Weight: lift vs own normal level',0.20),('Weight: consistency',0.20),('Shrinkage constant k (pressure balls)',100),
      ('Score centre',50),('Score scale (points per z)',15)]
header(wp,4,['Parameter','Value (editable)','Official value','Note'])
notes=['Approved by participant','Approved by participant','Approved by participant','Approved by participant','Reliability = n/(n+k)','Display scale only','Display scale only']
for i,((n,v),nt) in enumerate(zip(rows,notes),5):
    wp.cell(row=i,column=1,value=n).font=font(); c=wp.cell(row=i,column=2,value=v); c.font=font(color='0000FF'); c.fill=PatternFill('solid',fgColor=INPUT)
    wp.cell(row=i,column=3,value=v).font=font(); wp.cell(row=i,column=4,value=nt).font=font(italic=True,color='555555')
wp['A12']='Sum of weights'; wp['B12']='=SUM(B5:B8)'; wp['A12'].font=font(bold=True); wp['B12'].font=font(bold=True)
wp['D12']='Must equal 1.00'; wp['D12'].font=font(italic=True,color='555555')
fixed=[('Pressure threshold - 1st innings (PI, 75th percentile)',F['thr'][1]),('Pressure threshold - chase (PI, 75th percentile)',F['thr'][2]),('Pressure quantile',0.75),('Stage floor in PI',0.30),
       ('Eligibility: minimum pressure balls',200),('Eligibility: minimum matches with pressure balls',15),('Minimum balls for a qualifying pressure innings / spell',6),
       ('Par 1st-innings run rate - IPL',F['par']['IPL']),('Par 1st-innings run rate - T20I',F['par']['T20I']),('WP cross-validated AUC - 1st innings',F['coverage']['auc_inn1_cv']),('WP cross-validated AUC - chase',F['coverage']['auc_inn2_cv']),
       ('Bootstrap resamples (seed 42)',300),('Alternative scenarios',24)]
wp['A14']='Fixed settings used upstream in the Python pipeline (changing these requires re-running pipeline.py)'; wp['A14'].font=font(bold=True,color=NAVY)
header(wp,15,['Setting','Value'])
for i,(n,v) in enumerate(fixed,16):
    wp.cell(row=i,column=1,value=n).font=font(); c=wp.cell(row=i,column=2,value=v); c.font=font(); c.number_format='0.000' if isinstance(v,float) else '0'
r0=31; wp.cell(row=r0,column=1,value='Win-probability logistic coefficients by cross-fitting fold (fold = match_id mod 5; a match in fold f is scored with the row for fold f, which was fitted on the other four folds)').font=font(bold=True,color=NAVY)
fb=F['wp']['cv']['fold_betas']; r=r0+1
for inn,lab in (('inn2','Chase model'),('inn1','1st-innings model')):
    keys=list(fb[0][inn].keys()); header(wp,r,[lab+' - fold']+keys)
    for f in range(5):
        wp.cell(row=r+1+f,column=1,value=f).font=font()
        for j,kk in enumerate(keys,2): c=wp.cell(row=r+1+f,column=j,value=float(fb[f][inn][kk])); c.font=font(); c.number_format='0.0000'
    r+=8
widths(wp,[62,18,16,22,18,18,18,18])

# ---------------- metric sheets with live formulas ----------------
def metric_sheet(kind):
    e=F['players'][kind].sort_values('rank').copy(); n=len(e); ws=sheet('Batter_Metrics' if kind=='bat' else 'Bowler_Metrics','1F4E79')
    title(ws,('Batter' if kind=='bat' else 'Bowler')+' pressure metrics - all %d eligible players'%n,'Blue = values computed by pipeline.py from the data pack. Black = live Excel formulas (see Formula_Glossary). Live rank reacts to the Parameters sheet; Official rank is the approved ranking.')
    bat=kind=='bat'
    cols=['Official rank','Player','Pressure balls','Matches','Qualifying innings' if bat else 'Qualifying spells','Innings >= expected' if bat else 'Spells <= expected',
          'Pressure runs' if bat else 'Runs conceded','Expected runs','Dismissals' if bat else 'Wickets','Expected dismissals' if bat else 'Expected wickets',
          'Non-pressure RAE /100' if bat else 'Non-pressure RSE /100','Pressure SR' if bat else 'Pressure economy','Non-pressure SR' if bat else 'Non-pressure economy',
          'RAE /100' if bat else 'RSE /100','Wickets vs exp /100','Lift','Consistency %','Reliability','Shrunk output','Shrunk wickets','Shrunk lift','Shrunk consistency',
          'z output','z wickets','z lift','z consistency','Pressure Score (live)','Live rank','Matches official?','Verdict','Scenarios top-10 (of 24)','Bootstrap top-10 %','Bootstrap median rank',
          '1st-inn balls','1st-inn vs exp /100','Chase balls','Chase vs exp /100','IPL share %','Associate share %','Clutch contribution %']
    header(ws,4,cols,height=44); a,z=5,4+n
    R=lambda col: f"${col}${a}:${col}${z}"
    for i,(pid,p) in enumerate(e.iterrows()):
        r=a+i; pos=int(round(p.cons*p.p_inns/100))
        vals=[int(p['rank']),p['name'],int(p.p_balls),int(p.p_matches),int(p.p_inns),pos,int(p.p_runs if bat else p.p_conc),float(p.e_runs if bat else p.e_conc),int(p.p_outs if bat else p.p_wk),float(p.e_outs if bat else p.e_wk),float(p.np_rae)]
        for c,v in enumerate(vals,1):
            x=ws.cell(row=r,column=c,value=v); x.font=font(color='0000FF' if c>2 else '000000',bold=(c==2))
            if isinstance(v,float): x.number_format='0.00'
        fm={12:(f"=100*G{r}/C{r}" if bat else f"=6*G{r}/C{r}"),13:float(p.np_sr if bat else p.np_econ),
            14:(f"=100*(G{r}-H{r})/C{r}" if bat else f"=100*(H{r}-G{r})/C{r}"),15:(f"=100*(J{r}-I{r})/C{r}" if bat else f"=100*(I{r}-J{r})/C{r}"),
            16:f"=N{r}-K{r}",17:f"=100*F{r}/E{r}",18:f"=C{r}/(C{r}+Parameters!$B$9)",19:f"=N{r}*R{r}",20:f"=O{r}*R{r}",21:f"=P{r}*R{r}",
            22:f"=AVERAGE({R('Q')})+(Q{r}-AVERAGE({R('Q')}))*R{r}",
            23:f"=(S{r}-AVERAGE({R('S')}))/STDEVP({R('S')})",24:f"=(T{r}-AVERAGE({R('T')}))/STDEVP({R('T')})",25:f"=(U{r}-AVERAGE({R('U')}))/STDEVP({R('U')})",26:f"=(V{r}-AVERAGE({R('V')}))/STDEVP({R('V')})",
            27:f"=Parameters!$B$10+Parameters!$B$11*(Parameters!$B$5*W{r}+Parameters!$B$6*X{r}+Parameters!$B$7*Y{r}+Parameters!$B$8*Z{r})",
            28:f"=RANK(AA{r},{R('AA')})",29:f'=IF(AB{r}=A{r},"Yes","Changed")',30:p.verdict,31:int(p.scen_top10),32:float(p.boot_top10_pct),33:float(p.boot_rank_median),
            34:p.inn1_balls,35:p.inn1_vs_exp,36:p.inn2_balls,37:p.inn2_vs_exp,38:float(p.ipl_pct),39:float(p.assoc_pct),40:float(p.clutch_pct)}
        for c,v in fm.items():
            if isinstance(v,(float,np.floating)) and np.isnan(v): v=None
            elif isinstance(v,np.generic): v=v.item()
            x=ws.cell(row=r,column=c,value=v); x.font=font(color='0000FF' if (not isinstance(v,str) or not v.startswith('=')) and c not in (30,) else '000000')
            x.number_format={18:'0.000',23:'0.00',24:'0.00',25:'0.00',26:'0.00',28:'0',31:'0',34:'0',36:'0'}.get(c,'0.0')
        ws.cell(row=r,column=27).font=font(bold=True)
    ws.freeze_panes='C5'; ws.auto_filter.ref=f"A4:{L(len(cols))}{z}"; widths(ws,[9,24]+[11]*38)
    ws.conditional_formatting.add(f"AC{a}:AC{z}",CellIsRule(operator='equal',formula=['"Changed"'],fill=PatternFill('solid',fgColor='FFC7CE')))
    return ws,n
wbat,nb=metric_sheet('bat'); wbow,nw=metric_sheet('bowl')

# ---------------- Top 10 sheets (formula-linked to metric sheets by official rank) ----------------
def top10(kind):
    bat=kind=='bat'; src='Batter_Metrics' if bat else 'Bowler_Metrics'; n=nb if bat else nw; e=F['players'][kind].sort_values('rank')
    ws=sheet('Top10_Batters' if bat else 'Top10_Bowlers',PINK); title(ws,'FINAL TOP 10 '+('BATTERS' if bat else 'BOWLERS')+' UNDER PRESSURE','Approved ranking (official model, cross-fitted). Values are pulled from %s by official rank.'%src)
    cols=[('Rank',None),('Player','B'),('Pressure Score','AA'),('Verdict','AD'),('Pressure balls','C'),('Matches','D'),('Pressure SR' if bat else 'Pressure economy','L'),('Non-pressure SR' if bat else 'Non-pressure economy','M'),
          ('RAE /100' if bat else 'RSE /100','N'),('Wickets vs exp /100','O'),('Lift','P'),('Consistency %','Q'),('1st-inn vs exp','AI'),('Chase vs exp','AK'),('Scenarios top-10 (of 24)','AE'),('Bootstrap top-10 %','AF'),('Associate share %','AM')]
    header(ws,4,[c for c,_ in cols]+['Evidence-based justification'],height=40)
    for i in range(10):
        r=5+i; ws.cell(row=r,column=1,value=i+1).font=font(bold=True,size=12,color=PINK)
        for c,(nm,col) in enumerate(cols[1:],2):
            x=ws.cell(row=r,column=c,value=f"=INDEX({src}!${col}$5:${col}${4+n},MATCH($A{r},{src}!$A$5:$A${4+n},0))"); x.font=font(bold=(c==2)); x.number_format='0.0' if c not in (5,6,15) else '0'
        j=ws.cell(row=r,column=len(cols)+1,value=e.iloc[i].justification); j.font=font(size=9); j.alignment=Alignment(wrap_text=True,vertical='top'); ws.row_dimensions[r].height=92
        for c in range(1,len(cols)+1): ws.cell(row=r,column=c).alignment=Alignment(vertical='center',horizontal='center' if c!=2 else 'left')
    widths(ws,[6,22,10,11,9,8,10,10,9,9,8,10,9,9,10,10,10,90]); ws.freeze_panes='C5'
    for v,col in (('Stable','C6EFCE'),('Moderate','FFEB9C'),('Borderline','FFC7CE')): ws.conditional_formatting.add('D5:D14',CellIsRule(operator='equal',formula=[f'"{v}"'],fill=PatternFill('solid',fgColor=col)))
    ch=BarChart(); ch.type='bar'; ch.style=10; ch.title='Pressure Score - top 10'; ch.add_data(Reference(ws,min_col=3,min_row=4,max_row=14),titles_from_data=True); ch.set_categories(Reference(ws,min_col=2,min_row=5,max_row=14))
    ch.y_axis.scaling.min=50; ch.x_axis.scaling.orientation='maxMin'; ch.legend=None; ch.roundedCorners=False; ch.x_axis.delete=False; ch.y_axis.delete=False; ch.title.overlay=False; ch.height=9; ch.width=18
    ws.add_chart(ch,'B17'); return ws
top10('bat'); top10('bowl')

# ---------------- Dashboard ----------------
d=sheet('Dashboard',PINK); title(d,C.PROJECT,'Individual submission. Official cross-fitted model, 40/20/20/20 weights, eligibility 200 pressure balls and 15 matches.')
d['A4']='TOP 10 BATTERS'; d['G4']='TOP 10 BOWLERS'
for c in ('A4','G4'): d[c].font=font(bold=True,size=12,color=PINK)
header(d,5,['Rank','Batter','Score','Verdict','Bootstrap %'],start=1,height=26); header(d,5,['Rank','Bowler','Score','Verdict','Bootstrap %'],start=7,height=26)
for i in range(10):
    r=6+i
    for st,sh in ((1,'Top10_Batters'),(7,'Top10_Bowlers')):
        d.cell(row=r,column=st,value=i+1).font=font(bold=True)
        for j,col in enumerate(('B','C','D','P'),1):
            x=d.cell(row=r,column=st+j,value=f"={sh}!{col}{5+i}"); x.font=font(bold=(j==1)); x.number_format='0.0'
for rng in ('D6:D15','J6:J15'):
    for v,col in (('Stable','C6EFCE'),('Moderate','FFEB9C'),('Borderline','FFC7CE')): d.conditional_formatting.add(rng,CellIsRule(operator='equal',formula=[f'"{v}"'],fill=PatternFill('solid',fgColor=col)))
d['A18']='PLAYER EXPLORER - choose any eligible player from the yellow cells'; d['A18'].font=font(bold=True,size=12,color=NAVY)
d['A19']='Batter'; d['B19']=F['players']['bat'].sort_values('rank').iloc[0]['name']; d['G19']='Bowler'; d['H19']=F['players']['bowl'].sort_values('rank').iloc[0]['name']
for c in ('B19','H19'): d[c].fill=PatternFill('solid',fgColor=INPUT); d[c].font=font(bold=True,color='0000FF')
for cell,src,n in (('B19','Batter_Metrics',nb),('H19','Bowler_Metrics',nw)):
    dv=DataValidation(type='list',formula1=f"={src}!$B$5:$B${4+n}",allow_blank=False); d.add_data_validation(dv); dv.add(d[cell])
items_b=[('Official rank','A'),('Pressure Score','AA'),('Verdict','AD'),('Pressure balls','C'),('Matches','D'),('Pressure strike rate','L'),('Non-pressure strike rate','M'),('Runs above expected /100','N'),('Wickets vs expected /100','O'),('Lift vs own normal','P'),('Consistency %','Q'),('Reliability','R'),('1st-innings vs expected /100','AI'),('Chase vs expected /100','AK'),('Scenarios top-10 (of 24)','AE'),('Bootstrap top-10 %','AF'),('Associate share %','AM'),('Clutch contribution %','AN')]
items_w=[(a.replace('strike rate','economy').replace('Runs above expected','Runs saved vs expected'),b) for a,b in items_b]
for i,((lb,cb),(lw,cw)) in enumerate(zip(items_b,items_w)):
    r=20+i; d.cell(row=r,column=1,value=lb).font=font(); d.cell(row=r,column=7,value=lw).font=font()
    x=d.cell(row=r,column=2,value=f"=INDEX(Batter_Metrics!${cb}$5:${cb}${4+nb},MATCH($B$19,Batter_Metrics!$B$5:$B${4+nb},0))"); x.font=font(bold=True); x.number_format='0.0'; x.alignment=Alignment(horizontal='left')
    x=d.cell(row=r,column=8,value=f"=INDEX(Bowler_Metrics!${cw}$5:${cw}${4+nw},MATCH($H$19,Bowler_Metrics!$B$5:$B${4+nw},0))"); x.font=font(bold=True); x.number_format='0.0'; x.alignment=Alignment(horizontal='left')
cv=F['coverage']; d['A40']='DATA COVERAGE'; d['A40'].font=font(bold=True,size=12,color=NAVY)
for i,(k,v) in enumerate([('Raw deliveries',cv['raw_deliveries']),('Deliveries analysed (IPL + T20I)',cv['deliveries_in_player_analysis']),('High-pressure deliveries',cv['high_pressure_deliveries']),('Matches in pressure model',cv['matches_in_pressure_model']),('Eligible batters / bowlers',f"{cv['eligible_batters']} / {cv['eligible_bowlers']}")]):
    d.cell(row=41+i,column=1,value=k).font=font(); x=d.cell(row=41+i,column=2,value=v); x.font=font(bold=True); x.number_format='#,##0'; x.alignment=Alignment(horizontal='left')
d['G40']='HOW TO READ THE VERDICT'; d['G40'].font=font(bold=True,size=12,color=NAVY)
for i,t in enumerate(['Stable: bootstrap top-10 >= 60% and top-10 in >= 20 of 24 scenarios','Moderate: bootstrap >= 40% or >= 15 scenarios','Borderline: anything else - the place is not statistically firm','See Robustness sheets and the Limitations in the methodology report']): d.cell(row=41+i,column=7,value=t).font=font()
widths(d,[30,24,9,12,12,3,30,24,9,12,12])
ch=BarChart(); ch.type='bar'; ch.style=10; ch.title='Batters - Pressure Score'; ch.add_data(Reference(d,min_col=3,min_row=5,max_row=15),titles_from_data=True); ch.set_categories(Reference(d,min_col=2,min_row=6,max_row=15)); ch.legend=None; ch.y_axis.scaling.min=50; ch.x_axis.scaling.orientation='maxMin'
ch.roundedCorners=False; ch.x_axis.delete=False; ch.y_axis.delete=False; ch.title.overlay=False; ch.height=8; ch.width=13; d.add_chart(ch,'M4')
ch=BarChart(); ch.type='bar'; ch.style=10; ch.title='Bowlers - Pressure Score'; ch.add_data(Reference(d,min_col=9,min_row=5,max_row=15),titles_from_data=True); ch.set_categories(Reference(d,min_col=8,min_row=6,max_row=15)); ch.legend=None; ch.y_axis.scaling.min=50; ch.x_axis.scaling.orientation='maxMin'
ch.roundedCorners=False; ch.x_axis.delete=False; ch.y_axis.delete=False; ch.title.overlay=False; ch.height=8; ch.width=13; d.add_chart(ch,'M21')
exec(open(os.path.join(pl.HERE,'build_excel2.py')).read())
