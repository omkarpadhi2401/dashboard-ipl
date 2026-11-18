# continuation of build_report.py - document bodies
d=newdoc()
d.add_paragraph('Identifying the Most Reliable Players Under Pressure',style='Title')
p=d.add_paragraph('Methodology and Analytical Report  |  Rajasthan Royals SupeRR Selector Season 2, Round 1  |  Individual submission'); p.runs[0].italic=True
d.add_heading('1. Summary',1)
d.add_paragraph(f"This report ranks batters and bowlers by how they perform on high-pressure balls compared with what an average player does in the same situation, and compared with their own normal level. It uses the supplied IPL and T20I ball-by-ball data from {cv['date_min']} to {cv['date_max']}: {cv['deliveries_in_player_analysis']:,} deliveries across {cv['matches_in_pressure_model']-30} matches, of which {cv['high_pressure_deliveries']:,} are classed as high pressure.")
d.add_paragraph('The top three or four names in each list hold up under almost every alternative assumption tested. The lower positions are closer calls and are labelled as such. Every ranking position below comes directly from the model; none was adjusted by hand.')
d.add_heading('Final top 10 batters',2)
tbl(d,['#','Batter','Score','Verdict'],[[int(p['rank']),p['name'],f"{p.score:.1f}",p.verdict] for _,p in B.head(10).iterrows()],[1,6,2,3],size=9,verdict_col=3)
d.add_heading('Final top 10 bowlers',2)
tbl(d,['#','Bowler','Score','Verdict'],[[int(p['rank']),p['name'],f"{p.score:.1f}",p.verdict] for _,p in W.head(10).iterrows()],[1,6,2,3],size=9,verdict_col=3)
d.add_paragraph('Verdict: Stable = in the top 10 in at least 60% of bootstrap resamples and at least 20 of 24 alternative scenarios. Moderate = at least 40% of resamples or at least 15 scenarios. Borderline = neither.')

d.add_heading('2. Objective and data',1)
d.add_paragraph('The task is to build a data-driven system that measures how batters and bowlers perform in high-pressure situations compared with their usual level, and to produce two ordered top-10 lists. The method must work for both batting and bowling and be transparent enough to reproduce.')
d.add_heading('Data audit',2)
tbl(d,['Item','Count'],[['Raw deliveries',f"{cv['raw_deliveries']:,}"],['Matches with ball-by-ball data (of 883 listed)',cv['matches_with_ball_data']],['Super-over deliveries excluded',cv['super_over_deliveries_excluded']],['Matches excluded: no result, abandoned or single innings',cv['matches_single_innings_or_no_result_excluded']],['Matches excluded: rain-revised',cv['matches_rain_revised_excluded']],['Matches in the pressure model',cv['matches_in_pressure_model']],['Deliveries excluded: 30 emerging / A-team matches',f"{cv['other_tournament_deliveries_excluded']:,}"],['Deliveries analysed (IPL + T20I)',f"{cv['deliveries_in_player_analysis']:,}"],['High-pressure deliveries',f"{cv['high_pressure_deliveries']:,}"],['Eligible batters / bowlers',f"{cv['eligible_batters']} / {cv['eligible_bowlers']}"]],[11,4],size=9)
bullets(d,['There are no duplicate deliveries, and every match with ball data appears in the match file.','Wides are not counted as balls faced. Byes and leg-byes are not charged to the bowler. Run-outs are not credited to the bowler.','The bowl_speed field is zero for 38.7% of deliveries and was not used.','Emerging and A-team tournaments were excluded because they are neither IPL nor T20I.'])

d.add_heading('3. Pressure definition',1)
d.add_paragraph('A ball is under pressure when two things are true together: the result of the match is still in doubt, and there is little time left to recover from a mistake. The Pressure Index turns that idea into a number from 0 to 100 for every ball.')
p=d.add_paragraph(); r=p.add_run('Pressure Index = 100 x Balance x (0.30 + 0.70 x Stage)'); r.bold=True
bullets(d,['Balance = 1 - |2 x win probability - 1|. It equals 1 in a 50/50 contest and 0 once the result is settled.','Stage = share of the innings already bowled (legal balls bowled / 120).','Win probability comes from two logistic regressions fitted on this data. The chase model uses required run rate, wickets in hand and balls left. The first-innings model uses run rate against the competition par, wickets lost and stage.','A ball is high pressure if its index is in the top 25% for its innings type (threshold 56.3 in the first innings, 32.9 in chases). Separate thresholds make both innings contribute equally.'])
d.add_paragraph('This combines the factors named in the problem statement (required rate, wickets in hand, balls remaining, stage and closeness) into one measure, and the same balls count as pressure for the batter and the bowler.')
fig(d,'by_over.png',13,'Share of balls classed as high pressure, by over')
d.add_heading('Validation of the pressure model',2)
bullets(d,[f"No data leakage: the win-probability models are cross-fitted in five folds by match, so every ball is scored by a model that never saw the result of its own match.",f"Chase model: out-of-match AUC {cv['auc_inn2_cv']} (0.5 = chance, 1 = perfect).",f"First-innings model: out-of-match AUC {cv['auc_inn1_cv']}. It is well calibrated but weak, so first-innings pressure is mostly 'later overs of an evenly poised innings'.",'Replacing first-innings pressure with a model-free rule (overs 16-20) is one of the 24 robustness scenarios reported in Section 9.'])

d.add_heading('4. Performance measurement',1)
d.add_paragraph('Every pressure ball is compared with what the average player did on the same kind of ball. The comparison cell is competition group (IPL or T20I) x innings x phase (overs 1-6, 7-15, 16-20) x pressure state. This makes a death-overs ball in the IPL comparable only with other death-overs balls in the IPL.')
tbl(d,['Component','Weight','Batters','Bowlers'],[['Output vs expected','40%','Runs above expected per 100 pressure balls (RAE)','Runs saved vs expected per 100 pressure balls (RSE)'],['Wickets vs expected','20%','Dismissals avoided per 100 balls','Wickets above expected per 100 balls'],['Lift vs own normal level','20%','Pressure RAE minus non-pressure RAE','Pressure RSE minus non-pressure RSE'],['Consistency','20%','% of pressure innings (6+ balls) at or above expected runs','% of pressure spells (6+ balls) at or below expected runs']],[3.6,1.5,6,6],size=9)
d.add_heading('Scoring formula',2)
bullets(d,['Shrinkage: each metric is multiplied by n / (n + 100), where n is the number of pressure balls. Small samples are pulled toward the average.','Standardisation: each shrunk metric is converted to a z-score among eligible players, so all four components have mean 0 and standard deviation 1.','Score = 50 + 15 x (0.40 x z-output + 0.20 x z-wickets + 0.20 x z-lift + 0.20 x z-consistency). A score of 50 is the average eligible player.'])
d.add_heading('Are the components comparable?',2)
d.add_paragraph('The z-scores are on the same scale, but they are not independent. Consistency and output correlate at 0.81 for batters and 0.84 for bowlers because both measure runs against expectation. For batters, dismissals and output correlate at -0.22 because faster scorers take more risk. As a result the effective influence of each component differs from its nominal weight.')
fig(d,'weights.png',12,'Nominal weight against the share of score variance each component actually drives')
d.add_paragraph('Two alternatives were tested before the weights were confirmed. Variance-matched weights (nominal 31/33/17/19) give dismissals a true 20% influence but lower the repeatability of the batting score (split-half 0.08 against 0.14). Valuing a wicket at 24 runs and adding it to output makes dismissals 92% of the combined term and produces an unstable ranking (split-half 0.03). The 40/20/20/20 scheme validated best and was retained, with the low effective dismissal influence disclosed.')

d.add_heading('5. Fair comparisons',1)
bullets(d,['Eligibility: at least 200 high-pressure balls and at least 15 matches with pressure balls. This leaves 69 batters and 69 bowlers.','Sample size: the shrinkage factor discounts smaller samples, and each player\'s pressure-ball count is shown beside his ranking.','IPL and T20I: expectations are computed separately for each, so a player is compared with peers in the same competition type. Each player\'s IPL share is published.','Associate-team opposition: these matches are retained because they are part of the supplied data. Each player\'s share of pressure balls against associate teams is disclosed, and a sensitivity run excludes those matches.'])

for kind,e,bat,sec in (('batters',B,True,'6'),('bowlers',W,False,'7')):
    d.add_heading(f'{sec}. Evidence for the top 10 {kind}',1)
    fig(d,'top_bat.png' if bat else 'top_bowl.png',13)
    tbl(d,['#','Player','Score','Verdict','Balls / matches','SR: pressure vs normal' if bat else 'Economy: pressure vs normal','RAE' if bat else 'RSE','Wkts vs exp','Lift','Cons.','1st inn / chase','Scen. of 24','Boot.'],toprows(e,bat),TW,size=7,verdict_col=3)
    d.add_paragraph('RAE / RSE, wickets vs expected and lift are per 100 pressure balls. "1st inn / chase" splits the output figure by innings type. "Scen." is the number of 24 alternative scenarios in which the player stays top-10. "Boot." is the share of 300 match resamples in which he does.').runs[0].font.size=Pt(8)
    d.add_heading('Why each player is selected',2)
    for _,p in e.head(10).iterrows():
        q=d.add_paragraph(); r=q.add_run(f"{int(p['rank'])}. {p['name']} - {p.verdict}. "); r.bold=True; q.add_run(p.justification.split('). ',1)[1])
        extra=f"Context: {p.ipl_pct:.0f}% of his pressure balls were in the IPL and {p.assoc_pct:.1f}% against associate teams. Output by innings type: {f1(p.inn1_vs_exp)} in the first innings ({int(0 if pd.isna(p.inn1_balls) else p.inn1_balls)} balls) and {f1(p.inn2_vs_exp)} in chases ({int(0 if pd.isna(p.inn2_balls) else p.inn2_balls)} balls)."
        x=d.add_paragraph(extra); x.runs[0].font.size=Pt(9); x.runs[0].font.color.rgb=RGBColor(0x55,0x55,0x55)
fig(d,'innings_split.png',15.5,'Output versus expected, split by first-innings and chase pressure')
d.add_paragraph('First-innings and chase performance are kept visible because some players differ sharply between them. Jasprit Bumrah is far stronger on first-innings pressure, Krunal Pandya on chase pressure, and Pat Cummins and Lockie Ferguson are below expectation on first-innings pressure.')

d.add_heading('8. Near misses and alternative candidates',1)
for e,lab in ((B,'Batters'),(W,'Bowlers')):
    d.add_heading(lab+': ranks 11 to 15',2)
    for _,p in e[(e['rank']>10)&(e['rank']<=15)].iterrows():
        q=d.add_paragraph(style='List Bullet'); r=q.add_run(p['name']+' - '); r.bold=True; q.add_run(f"{int(p.p_balls)} pressure balls, score {p.score:.1f}. "+p.near_miss_reason)
d.add_heading('Eligibility watch-list',2)
d.add_paragraph('These players are excluded only because they have fewer than 200 pressure balls or 15 matches. The rank shown is where they would sit if the threshold were 150 balls and 12 matches. It is not an official rank.')
rows=[]
for k,lab in (('bat','Batter'),('bowl','Bowler')):
    for _,q in F['watch'][k].iterrows(): rows.append([lab,q['name'],int(q.p_balls),int(q.p_matches),f1(q.rae),f"{q.cons:.0f}%",int(q.rank_if_150_12)])
tbl(d,['Type','Player','Pressure balls','Matches','Output vs exp /100','Consistency','Rank if 150 / 12'],rows,[2,5,2.3,2,3,2.3,2.6],size=9)
d.add_paragraph('Abrar Ahmed against Ravindra Jadeja: Abrar has top-10 quality figures (economy 6.5, +31.0 runs saved per 100 balls, 80% consistency) but only 196 pressure balls, none in the IPL and 19.4% against associate teams, so he is ineligible. Jadeja has a large sample (358 balls, 36 matches) but mid-table results and ranks 17th.')

d.add_heading('9. Reliability and robustness',1)
fig(d,'bootstrap.png',15.5,'Share of 300 match resamples in which each player finishes in the top 10 (dashed line 60%, dotted line 40%)')
d.add_heading('What was tested',2)
bullets(d,['24 alternative scenarios: pressure threshold (top 20% and top 33%), stage weighting, a rule-based pressure definition with no model, three scoring schemes, shrinkage constants, eligibility thresholds, IPL only, T20I only, excluding associate matches, alternative first-innings definitions, chase-only and first-innings-only pressure, the in-sample (leaky) fit, leave-own-out baselines, and dropping the 2022 or 2026 season.','A match-level bootstrap with 300 resamples (seed 42).','Split-half reliability: matches are split at random into two halves 40 times and the two sets of scores are compared.'])
d.add_heading('What it shows',2)
bullets(d,['Firm selections: Suryakumar Yadav and Heinrich Klaasen among batters; Jasprit Bumrah, Krunal Pandya and Sunil Narine among bowlers.','Borderline selections: Quinton de Kock, Rohit Sharma and Mohammad Nawaz among batters; Pat Cummins and Lockie Ferguson among bowlers. Kuldeep Yadav, ranked 11th, is top-10 in 16 of 24 scenarios and is a more robust candidate than the two bowlers directly above him, but the model order was kept.','Excluding associate matches keeps nine of ten batters (Mohammad Nawaz falls from 9th to 16th and Josh Inglis enters) and nine of ten bowlers (Lockie Ferguson falls to 11th and Kuldeep Yadav enters).','Leakage: removing each player\'s own balls from his baseline leaves the ranking unchanged (rank correlation 1.00). Cross-fitting the win-probability model changed 1.7% of pressure flags; it is the official version.',f"Repeatability is modest: split-half correlation is {F['diag']['bat']['split_half']['score_z']} for batters and {F['diag']['bowl']['split_half']['score_z']} for bowlers. Output is the most repeatable component (0.32-0.33) and lift the least (0.08-0.10)."])
d.add_paragraph('The full scenario-by-scenario rank table for the top 20 is in the Robustness sheets of the Excel workbook.')

d.add_heading('10. Supplementary features',1)
d.add_paragraph('The following analyses support the selections but never feed the official score. Their full outputs are in the Excel workbook and the website data.')
tbl(d,['Feature','What it shows','Status'],[[f[0],f[2],f[7]] for f in C.FEATURES],[4.2,10.3,2.6],size=8)

d.add_heading('11. Limitations and assumptions',1); bullets(d,C.LIMITATIONS)
d.add_heading('12. AI Assistance and Independent Decision-Making',1)
for h,t in C.AI_DISCLOSURE:
    q=d.add_paragraph(); r=q.add_run(h+'. '); r.bold=True; q.add_run(t)
d.add_heading('13. Reproducibility',1)
bullets(d,['pipeline.py: audit, match state, cross-fitted win probability, Pressure Index, context baselines, player metrics and scores.','robustness.py: the 24 scenarios and the bootstrap.','export.py: the consolidated result set used by every deliverable.','All parameters are listed in the Parameters sheet of the workbook, where the score and rank are also rebuilt with live Excel formulas and match the Python output for all 138 eligible players.'])
d.add_heading('Appendix: formula glossary',1)
tbl(d,['Metric','Definition','Formula'],[[g[0],g[1],g[2]] for g in C.GLOSSARY],[3.6,5.5,8],size=8)
d.save(os.path.join(OUT,'SupeRR_Methodology_Report.docx'))

# ---------------- one-page project work summary ----------------
s=newdoc(); s.sections[0].top_margin=s.sections[0].bottom_margin=Cm(1.3); s.styles['Normal'].font.size=Pt(9); s.styles['Normal'].paragraph_format.space_after=Pt(3)
s.add_heading('Project Work Summary - Most Reliable Players Under Pressure',1)
p=s.add_paragraph('SupeRR Selector Season 2, Round 1  |  Individual submission'); p.runs[0].italic=True
def sec(t,items):
    h=s.add_heading(t,3)
    for it in items: q=s.add_paragraph(it,style='List Bullet'); q.paragraph_format.space_after=Pt(1)
sec('What was done',[f"Audited {cv['raw_deliveries']:,} deliveries from 867 matches; analysed {cv['deliveries_in_player_analysis']:,} IPL and T20I deliveries after documented exclusions.",'Defined pressure as Balance x Stage: the match is undecided and time is running out. The top 25% of balls per innings type are high pressure (47,038 balls).','Scored every eligible player on four components against the average player in the same context: output (40%), wickets (20%), lift over own normal level (20%) and consistency (20%).','Tested the ranking with 24 alternative scenarios, 300 bootstrap resamples, leakage checks and split-half reliability.'])
sec('How it was done',['Python pipeline with fixed seeds; win-probability models cross-fitted by match to avoid leakage.','Small samples discounted by n / (n + 100); eligibility set at 200 pressure balls and 15 matches.','Excel workbook rebuilds every score with live formulas and reproduces the Python ranking exactly.'])
t=s.add_table(rows=11,cols=4); t.style='Table Grid'
for i,h in enumerate(['#','Top 10 batters (verdict)','#','Top 10 bowlers (verdict)']):
    c=t.rows[0].cells[i]; c.text=''; r=c.paragraphs[0].add_run(h); r.bold=True; r.font.size=Pt(8.5); r.font.color.rgb=RGBColor(255,255,255); shade(c,'1B2A4A')
for i in range(10):
    pb=B.iloc[i]; pw=W.iloc[i]
    for j,v in enumerate([i+1,f"{pb['name']} ({pb.verdict})",i+1,f"{pw['name']} ({pw.verdict})"]):
        c=t.rows[i+1].cells[j]; c.text=''; c.paragraphs[0].add_run(str(v)).font.size=Pt(8.5); c.paragraphs[0].paragraph_format.space_after=Pt(0)
t.autofit=False
for i,w in enumerate([0.8,7.7,0.8,7.7]): t.columns[i].width=Cm(w)
for row in t.rows:
    for i,w in enumerate([0.8,7.7,0.8,7.7]): row.cells[i].width=Cm(w)
sec('Honest caveats',['Only the top three or four in each list are statistically firm; lower positions are close calls.','Pressure performance is weakly repeatable (split-half 0.14 batters, 0.23 bowlers).','No adjustment for opposition strength; three players sit within five balls of the eligibility line.'])
sec('AI assistance and my decisions',['An AI assistant (Claude) wrote and ran the analysis code and drafted the files from the computed results.','I reviewed the evidence at each stage and decided the pressure definition, the weights, the 200 / 15 eligibility, the cross-fitted model, the treatment of associate matches, and accepted the lists in model order with no manual changes.'])
sec('Deliverables',['Excel workbook (21 sheets), methodology report, presentation, website data folder and website build instructions - all from one result set.'])
s.save(os.path.join(OUT,'SupeRR_Project_Summary.docx')); print('docs saved')
