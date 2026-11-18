# continuation of build_ppt_final.py - the ten slides
def datagrid(fn):
    rng=np.random.default_rng(3); fig,ax=canvas(3.6,3.0); ax.add_patch(FancyBboxPatch((0.05,0.05),3.5,2.9,boxstyle='round,pad=0.02,rounding_size=0.2',color=HN))
    cols=['#3A4380','#3A4380','#3A4380',HB,HB,'white',HP]
    for r in range(6):
        for c in range(8): ax.add_patch(Circle((0.45+c*0.39,0.45+r*0.42),0.13,color=cols[rng.integers(0,7)]))
    save(fig,fn)
datagrid('data.png')
def placeholder(s,x,y,w,h,text):
    r=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h)); r.fill.solid(); r.fill.fore_color.rgb=WHITE; r.line.color.rgb=PINK; r.line.width=Pt(1.5); r.line.dash_style=4; r.shadow.inherit=False
    label(r,text,10,PINK,False); return r
LOGO=os.path.exists(os.path.join(IMG,'rr_logo.png'))
PHOTO={'Suryakumar Yadav':'photo_surya.png','Heinrich Klaasen':'photo_klaasen.png','Prabhsimran Singh':'photo_prabhsimran.png','Jasprit Bumrah':'photo_bumrah.png','Krunal Pandya':'photo_krunal.png','Sunil Narine':'photo_narine.png'}
def top3(s,e,x=9.7,y=1.75):
    """Top-three column: participant-supplied photo where one exists, otherwise an initials badge."""
    for i in range(3):
        p_=e.iloc[i]; yy=y+i*1.36; fn=PHOTO.get(p_['name'])
        ring=box(s,x-0.05,yy-0.05,1.3,1.3,PINK,MSO_SHAPE.OVAL)
        if fn and os.path.exists(os.path.join(IMG,fn)): pic(s,fn,x,yy,w=1.2,h=1.2)
        else: c=box(s,x,yy,1.2,1.2,NAVY,MSO_SHAPE.OVAL); label(c,''.join(w[0] for w in p_['name'].split()[:2]),24)
        tx(s,x+1.4,yy+0.1,1.75,0.7,f"#{int(p_['rank'])} {p_['name']}",13,True,NAVY); tx(s,x+1.4,yy+0.75,1.75,0.35,f"Score {p_.score:.1f}",11,False,GREY)
        reg(s,ring)
nS=sum(v=='Stable' for v in list(B.head(10).verdict)+list(W.head(10).verdict)); nM=sum(v=='Moderate' for v in list(B.head(10).verdict)+list(W.head(10).verdict)); nB=20-nS-nM
b1,b2,b3=B.iloc[0],B.iloc[1],B.iloc[2]; w1,w2,w3=W.iloc[0],W.iloc[1],W.iloc[2]

# 1 cover
s=prs.slides.add_slide(BL); s.background.fill.solid(); s.background.fill.fore_color.rgb=WHITE
reg(s,pic(s,'stadium.png',7.333,0,h=7.5)); (pic(s,'rr_logo.png',0.7,0.45,h=1.6) if LOGO else placeholder(s,0.7,0.6,1.7,1.05,'Place official RR logo here'))
reg(s,tx(s,0.7,2.25,6.3,1.5,'SupeRR Selector Season 2',44,True,NAVY,anchor=MSO_ANCHOR.MIDDLE))
reg(s,tx(s,0.7,3.85,6.3,1.2,'Identifying Players Who Perform Under Pressure',26,True,PINK))
tx(s,0.7,5.35,6.3,0.4,'Rajasthan Royals SupeRR Selector  |  Round 1  |  Individual submission',14,False,GREY)
tx(s,0.7,5.85,6.3,0.4,'Omkar Padhi',16,True,NAVY)
s.notes_slide.notes_text_frame.text="Introduce yourself and the project in one line: this project uses IPL and T20I ball-by-ball data to find the batters and bowlers who perform best when the match is on the line."

# 2 problem
s=slide(2,'The problem we solved','Ordinary statistics do not show who delivers when the game is on the line',
 "Say the question out loud. Explain that averages and strike rates mix easy and difficult situations together, so two players with the same numbers can be very different under pressure. Our job was to separate the two and produce two ranked lists.")
q=reg(s,box(s,0.55,1.8,7.7,1.25,PINK)); label(q,'Which batters and bowlers perform best when the pressure is highest?',20)
reg(s,tx(s,0.6,3.3,7.6,1.8,['Normal statistics blend easy and difficult situations together.','A player can score heavily in comfortable moments and still struggle in tight ones.','We looked for players who hold or raise their level in difficult match situations.'],15,bullet=True,gap=9))
o1=reg(s,box(s,0.55,5.3,3.75,1.35,NAVY)); label(o1,['Objective 1','Top 10 batters under pressure'],17)
o2=reg(s,box(s,4.5,5.3,3.75,1.35,BLUE)); label(o2,['Objective 2','Top 10 bowlers under pressure'],17)
reg(s,pic(s,'pitch.png',8.65,1.75,h=4.95))

# 3 data
s=slide(3,'The data we used',f"IPL and T20I matches, {cv['date_min'][:4]} to {cv['date_max'][:4]}, from the supplied competition data pack",
 "Walk through the four files, then the numbers: about 201 thousand deliveries were supplied; after removing super overs, rain-affected and no-result matches and non-IPL/T20I tournaments, about 188 thousand were analysed, and a quarter of them were classed as high pressure. Then read the flow from left to right.")
for i,(n,l,c) in enumerate([(f"{cv['raw_deliveries']:,}",'deliveries supplied',PINK),(f"{cv['matches_with_ball_data']}",'matches with ball data',BLUE),(f"{cv['deliveries_in_player_analysis']:,}",'IPL + T20I deliveries analysed',NAVY),(f"{cv['high_pressure_deliveries']:,}",'high-pressure deliveries',PINK)]):
    x=0.55+i*2.3; reg(s,box(s,x,1.8,2.15,1.5,LIGHT)); tx(s,x+0.05,1.88,2.05,0.8,n,26,True,c,PP_ALIGN.CENTER,MSO_ANCHOR.MIDDLE); tx(s,x+0.05,2.7,2.05,0.5,l,11,False,GREY,PP_ALIGN.CENTER)
reg(s,pic(s,'data.png',10.2,1.75,h=1.6))
tx(s,0.55,3.55,9,0.4,'Four data sources',15,True,NAVY)
for i,(h_,t_) in enumerate([('Ball-by-ball','every delivery: runs, wickets, extras'),('Matches','date, teams, result, rain revisions'),('Playing XI','who played in each match'),('Competitions and players','IPL or T20I, team and player mapping')]):
    x=0.55+i*3.07; c=reg(s,box(s,x,4.0,2.92,1.05,WHITE)); c.line.color.rgb=BLUE; c.line.width=Pt(1.5); tx(s,x+0.15,4.05,2.65,0.4,h_,14,True,BLUE); tx(s,x+0.15,4.45,2.65,0.55,t_,11,False,GREY)
for i,t_ in enumerate(['Raw cricket data','Data cleaning','Match context','Pressure classification','Player analysis']):
    c=reg(s,box(s,0.55+i*2.45,5.45,2.6,0.95,PINK if i in (0,4) else (BLUE if i%2 else NAVY),MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON)); label(c,t_,12)
tx(s,0.55,6.5,12,0.4,'Excluded with reasons: 38 super-over balls, 25 no-result or one-innings matches, 24 rain-revised matches, 30 emerging / A-team matches.',11,False,GREY,italic=True)

# 4 pressure
s=slide(4,'How we identified pressure','A ball is under pressure when the result is in doubt and time is running out',
 "This is the key idea. Balance asks: is the match close to 50/50? Stage asks: how late is it in the innings? Multiply them and scale to 0-100. A tense last over scores near 100; a one-sided game or the first over scores low. The top 25% of balls in each innings type are our high-pressure balls. Mention that win probability was estimated using models trained on other matches, so a match never grades itself.")
fb=reg(s,box(s,0.55,1.8,7.3,1.0,PINK)); label(fb,'Pressure Index = 100 x Balance x (0.30 + 0.70 x Stage)',19)
c=reg(s,box(s,0.55,3.0,3.55,1.75,BLUE)); tx(s,0.7,3.05,3.3,0.4,'Balance: is the match close?',15,True,WHITE); tx(s,0.7,3.5,3.3,1.2,['Balance = 1 - 2 x |WP - 0.5|','1 at a 50/50 contest, 0 when decided. WP = win probability.'],12,False,WHITE,gap=4)
c=reg(s,box(s,4.3,3.0,3.55,1.75,NAVY)); tx(s,4.45,3.05,3.3,0.4,'Stage: how late is it?',15,True,WHITE); tx(s,4.45,3.5,3.3,1.2,['Stage = balls bowled in the innings / 120','Later balls count more: mistakes are harder to repair.'],12,False,WHITE,gap=4)
reg(s,tx(s,0.6,4.95,7.3,1.9,['Calculated for every delivery, on a 0-100 scale.','High pressure = top 25% of balls within each innings type.','Win probability comes from models trained on other matches, so no match grades itself.'],14,bullet=True,gap=7))
reg(s,pic(s,'gauge.png',8.35,1.7,w=4.4)); hb=F['hp_by_over']
reg(s,chart(s,8.2,4.35,4.75,2.6,[str(i) for i in hb.index],[('1st innings',list(100*hb[1])),('Chase',list(100*hb[2]))],[BLUE,PINK],kind=XL_CHART_TYPE.COLUMN_CLUSTERED,title='% of balls that are high pressure, by over',size=9))

# 5 evaluation
s=slide(5,'How we evaluated players','Every pressure ball is compared with what an average player did in the same situation',
 "Four questions, four weights. One: did he produce more than an average player would in the same situation? Two: wickets - did the batter protect his, did the bowler take them? Three: is he better under pressure than in his own normal game? Four: does he do it match after match? Small samples are discounted and everything is put on one scale so players are comparable. Only players with 200 pressure balls and 15 matches qualify.")
x=0.55
for wt,nm,col in ((40,'Output',PINK),(20,'Wickets',BLUE),(20,'Lift',NAVY),(20,'Consistency',RGBColor(0x7A,0x86,0xA8))):
    w_=12.2*wt/100; c=reg(s,box(s,x,1.8,w_-0.08,0.7,col,adj=0.2)); label(c,f"{nm}  {wt}%",15); x+=w_
for i,(h_,q_,bt,bw,col) in enumerate([('Output vs expected','Did he produce more than an average player would?','Batters: runs above expected per 100 balls','Bowlers: runs saved per 100 balls',PINK),('Wickets vs expected','Did he win the wicket battle?','Batters: dismissals avoided','Bowlers: extra wickets taken',BLUE),('Lift under pressure','Is he better than his own normal game?','Batters: pressure minus normal scoring','Bowlers: pressure minus normal run-saving',NAVY),('Consistency','Does he do it match after match?','Batters: % of innings beating expectation','Bowlers: % of spells beating expectation',RGBColor(0x7A,0x86,0xA8))]):
    x=0.55+i*3.07; reg(s,box(s,x,2.7,2.92,2.55,LIGHT)); d=box(s,x+0.15,2.85,0.5,0.5,col,MSO_SHAPE.OVAL); label(d,str(i+1),14)
    tx(s,x+0.75,2.85,2.1,0.5,h_,14,True,NAVY,anchor=MSO_ANCHOR.MIDDLE); tx(s,x+0.15,3.45,2.65,0.6,q_,12,False,GREY,italic=True); tx(s,x+0.15,4.1,2.65,1.1,[bt,bw],11.5,False,NAVY,gap=4)
fb=reg(s,box(s,0.55,5.45,8.3,0.8,NAVY)); label(fb,'Score = 50 + 15 x (0.40 x Z-output + 0.20 x Z-wickets + 0.20 x Z-lift + 0.20 x Z-consistency)',12.5)
e1=reg(s,box(s,9.05,5.45,1.8,0.8,PINK)); label(e1,['200+','pressure balls'],15); e2=reg(s,box(s,10.97,5.45,1.8,0.8,BLUE)); label(e2,['15+','matches'],15)
tx(s,0.55,6.4,12.2,0.5,'Fair comparison: small samples are discounted (n / (n + 100)) and each component is standardised, so 50 = an average eligible player.',12,False,GREY,italic=True)

# 6 batters
s=slide(6,'Final top 10 batters under pressure','Approved ranking, exactly as the model orders it',
 f"Read the top three. {b1['name']} strikes at {b1.p_sr:.0f} under pressure against {b1.np_sr:.0f} normally. Explain 'runs above expected': extra runs per 100 pressure balls compared with an average batter in the same situations. Point at the Verdict column: green is firm, amber reasonable, red uncertain - we show that honestly.")
rows=[[int(p['rank']),p['name'],f"{p.p_sr:.0f}",f"{p.np_sr:.0f}",f1(p.rae),f"{p.cons:.0f}%",p.verdict] for _,p in B.head(10).iterrows()]
reg(s,table(s,0.55,1.75,8.9,4.0,['#','Batter','Pressure strike rate','Normal strike rate','Runs above expected /100','Consistency','Verdict'],rows,[0.5,2.7,1.3,1.3,1.5,1.2,1.3],12,6))
top3(s,B)
reg(s,tx(s,0.6,5.95,12.1,1.0,[f"{b1['name']} leads clearly: {b1.p_sr:.0f} strike rate under pressure, {f1(b1.rae)} runs per 100 balls above expected, on {int(b1.p_balls)} pressure balls.",f"All ten score faster under pressure than in their normal game; {b2['name']} and {b1['name']} are the two firmest picks."],13,bullet=True,gap=5))

# 7 bowlers
s=slide(7,'Final top 10 bowlers under pressure','Approved ranking, exactly as the model orders it',
 f"Read the top three. Explain 'runs saved': runs prevented per 100 pressure balls compared with an average bowler in the same situations. {w1['name']}'s pressure economy looks similar to his normal one, but his pressure overs are mostly at the death where everyone else goes for far more - that is why he saves {w1.rae:.0f} runs per 100 balls.")
rows=[[int(p['rank']),p['name'],f"{p.p_econ:.1f}",f"{p.np_econ:.1f}",f1(p.rae),int(p.p_wk),f"{p.cons:.0f}%",p.verdict] for _,p in W.head(10).iterrows()]
reg(s,table(s,0.55,1.75,8.9,4.0,['#','Bowler','Pressure economy','Normal economy','Runs saved /100','Wickets','Consistency','Verdict'],rows,[0.5,2.5,1.2,1.2,1.3,0.9,1.2,1.3],12,7))
top3(s,W)
reg(s,tx(s,0.6,5.95,12.1,1.0,[f"{w1['name']}, {w2['name']} and {w3['name']} are all classed Stable: they stay in the top 10 under almost every test.",f"{w1['name']} saves {w1.rae:.0f} runs per 100 pressure balls against an average bowler in the same situations, with {int(w1.p_wk)} wickets."],13,bullet=True,gap=5))

# 8 discoveries
s=slide(8,'What did we discover?','Four findings that ordinary statistics would not show',
 "Finding one: pressure in the first innings and pressure in a chase are different jobs - use the chart. Finding two: normal numbers can hide pressure ability. Finding three: sample size matters, and we were strict about it. Finding four: we do not claim every pick is equally certain.")
d=W.head(10); reg(s,chart(s,0.55,1.75,6.5,5.1,list(d['name']),[('1st innings',list(d.inn1_vs_exp)),('Chase',list(d.inn2_vs_exp))],[BLUE,PINK],title='Bowlers: runs saved per 100 pressure balls',size=10))
nz=B[B['name']=='Mohammad Nawaz'].iloc[0]
finds=[('First innings and chase are different jobs',f"{w1['name']}: {f1(w1.inn1_vs_exp)} in the first innings, {f1(w1.inn2_vs_exp)} in chases. {w2['name']} is the reverse: {f1(w2.inn1_vs_exp)} and {f1(w2.inn2_vs_exp)}."),
       ('Normal statistics can mislead',f"{nz['name']} strikes at {nz.np_sr:.0f} normally but {nz.p_sr:.0f} under pressure."),
       ('Sample size matters','Quinton de Kock qualifies with 201 pressure balls; two strong performers miss out with 196.'),
       ('Not every pick is equally certain',f"{nS} selections are Stable, {nM} Moderate and {nB} Borderline.")]
for i,(h_,t_) in enumerate(finds):
    y=1.75+i*1.3; reg(s,box(s,7.3,y,5.5,1.17,LIGHT)); c=box(s,7.45,y+0.3,0.55,0.55,PINK if i%2==0 else BLUE,MSO_SHAPE.OVAL); label(c,str(i+1),14)
    tx(s,8.15,y+0.08,4.55,0.4,h_,14,True,NAVY); tx(s,8.15,y+0.5,4.55,0.65,t_,11.5,False,GREY)

# 9 reliability
s=slide(9,'How reliable are our results?','We tried to break the ranking before trusting it',
 "Explain bootstrap simply: we re-drew the set of matches 300 times and counted how often each player still made the top 10. We also re-ran the whole model under 24 different reasonable assumptions. Read the three verdict labels. Be open that the lower places are close calls and that pressure performance is a noisy signal.")
for e,x,t in ((B,0.55,'Batters'),(W,4.75,'Bowlers')):
    d=e.head(10); g=chart(s,x,1.7,4.1,3.55,[f"{int(r)}. {n}" for r,n in zip(d['rank'],d['name'])],[('x',list(d.boot_top10_pct))],[BLUE],legend=False,labels=True,vmin=0,vmax=100,title=t+': % of 300 re-draws in the top 10',size=9); reg(s,g)
    for i,v in enumerate(d.verdict): pt=g.chart.plots[0].series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb=VC[v]
for i,(v,t_) in enumerate((('Stable','Strong support across re-draws and alternative assumptions'),('Moderate','Reasonable support, some sensitivity in rank'),('Borderline','Uncertain: sensitive to assumptions or sample size'))):
    x=0.55+i*2.8; c=reg(s,box(s,x,5.4,2.67,1.4,VB[v])); tx(s,x+0.12,5.45,2.45,0.4,f"{v} ({[nS,nM,nB][i]} of 20)",14,True,VC[v]); tx(s,x+0.12,5.87,2.45,0.9,t_,11,False,NAVY)
tx(s,9.15,1.7,3.7,0.4,'Six checks we ran',15,True,NAVY)
for i,t_ in enumerate(['Win probability trained on other matches (cross-fitted)','Bootstrap: 300 re-draws of the matches','24 alternative scenarios re-run','Eligibility thresholds varied','Associate-team matches removed as a test','Leakage check: own balls removed from baseline']):
    y=2.2+i*0.76; c=reg(s,box(s,9.15,y,3.65,0.66,LIGHT)); k=box(s,9.25,y+0.13,0.4,0.4,PINK,MSO_SHAPE.OVAL); label(k,'✓',12); tx(s,9.75,y+0.03,3.0,0.6,t_,11.5,False,NAVY,anchor=MSO_ANCHOR.MIDDLE)
tx(s,9.15,6.8,3.7,0.3,'Lower places are close calls; see report for limits.',10,False,GREY,italic=True)

# 10 conclusion
s=prs.slides.add_slide(BL); s.background.fill.solid(); s.background.fill.fore_color.rgb=WHITE
reg(s,pic(s,'finale.png',0,0,h=7.5)); (pic(s,'rr_logo.png',11.75,0.4,h=1.35) if LOGO else placeholder(s,11.0,0.5,1.7,1.05,'Place official RR logo here'))
reg(s,tx(s,6.6,0.55,4.3,0.9,'Conclusion',34,True,NAVY,anchor=MSO_ANCHOR.MIDDLE))
reg(s,tx(s,6.6,1.75,6.1,3.2,['We built a transparent, repeatable way to measure performance on the highest-pressure balls of a match.','It adds information that averages and strike rates cannot: who holds or raises their level when the result is in doubt.',f"The selected players beat an average player in the same situations, led by {b1['name']} and {w1['name']}.",'Used with scouting and coaching judgement, it can support selection and auction decisions; it does not replace them.'],15,bullet=True,gap=10))
q=reg(s,box(s,6.6,5.15,6.1,1.0,PINK)); label(q,'"Beyond the Numbers. Performance Under Pressure."',19)
tx(s,6.6,6.35,6.1,0.8,'Tools: Python and an AI assistant supported data processing, coding and visualisation. The methodology choices and final player selections were reviewed and approved by the participant.',10,False,GREY,italic=True)
s.notes_slide.notes_text_frame.text="Close with what the method adds and how it should be used: as evidence alongside cricket judgement, not a guarantee. If asked about AI: tools helped with data processing, coding and visuals; you reviewed the evidence and made the decisions on the method and the final lists. End on the tagline."

# ---------------- transitions + fade-in sequences ----------------
NS='http://schemas.openxmlformats.org/presentationml/2006/main'
def timing(ids):
    n=[2];
    def nid(): n[0]+=1; return n[0]
    pars=''
    for i,sid in enumerate(ids):
        a,b_,c_,d_=nid(),nid(),nid(),nid()
        pars+=f'<p:par><p:cTn id="{a}" fill="hold"><p:stCondLst><p:cond delay="{i*350}"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="{b_}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="afterEffect"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:set><p:cBhvr><p:cTn id="{c_}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set><p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{d_}" dur="400"/><p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>'
    return (f'<p:timing xmlns:p="{NS}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
            f'<p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>{pars}</p:childTnLst></p:cTn></p:par>'
            '</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')
N=len(prs.slides)
for i,sl in enumerate(prs.slides):
    edge=i in (0,N-1); kind='<p:fade/>' if edge else '<p:push dir="l"/>'; spd='slow' if edge else 'med'
    tr=etree.fromstring('<p:transition xmlns:p="%s" spd="%s">%s</p:transition>'%(NS,spd,kind))
    anchor=sl._element.find('{%s}clrMapOvr'%NS); anchor=anchor if anchor is not None else sl._element.find('{%s}cSld'%NS); anchor.addnext(tr)
    ids=ANIM.get(id(sl),[])
    if ids: tr.addnext(etree.fromstring(timing(ids)))
fn='SupeRR_Final_Presentation.pptx'
try: prs.save(os.path.join(OUT,fn))
except PermissionError:
    raise SystemExit('The presentation is open in PowerPoint. Close it and run this script again (no second copy is written).')
print(fn); print('final ppt saved',N,'slides; animated shapes',sum(len(v) for v in ANIM.values()))

os.makedirs(os.path.join(OUT,'speaker_notes'),exist_ok=True)
with open(os.path.join(OUT,'speaker_notes','SupeRR_Speaker_Notes.md'),'w',encoding='utf-8') as _f:
    _f.write('# Speaker notes - SupeRR_Final_Presentation.pptx\n\nThe same notes are in the Notes pane of each slide.\n')
    for _i,_s in enumerate(prs.slides,1):
        _t=next((sh.text_frame.text for sh in _s.shapes if sh.has_text_frame and sh.text_frame.text.strip() and not sh.text_frame.text.strip().isdigit()),'')
        _f.write(f"\n## Slide {_i}: {_t.splitlines()[0] if _t else ''}\n\n{_s.notes_slide.notes_text_frame.text}\n")
