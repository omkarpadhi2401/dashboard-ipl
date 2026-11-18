"""Builds charts, the methodology report (DOCX) and the one-page project work summary (DOCX) from work/final.pkl."""
import pandas as pd, numpy as np, os, pipeline as pl, content as C
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
ROOT=pl.PROJECT; OUT=pl.REPORT_DIR; CH=os.path.join(pl.WORK,'charts'); os.makedirs(CH,exist_ok=True); os.makedirs(OUT,exist_ok=True)
F=pd.read_pickle(os.path.join(pl.WORK,'final.pkl')); B=F['players']['bat'].sort_values('rank'); W=F['players']['bowl'].sort_values('rank'); cv=F['coverage']
NAVY='#1B2A4A'; PINK='#E91E63'; VC={'Stable':'#2E7D32','Moderate':'#F9A825','Borderline':'#C62828'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
def bar_top(e,fn,ttl):
    t=e.head(10).iloc[::-1]; fig,ax=plt.subplots(figsize=(6.6,3.4)); ax.barh(t['name'],t.score,color=[VC[v] for v in t.verdict])
    for y,(s,v) in enumerate(zip(t.score,t.verdict)): ax.text(s+0.3,y,f"{s:.1f}  {v}",va='center',fontsize=8)
    ax.set_xlim(50,max(e.score.head(10))+9); ax.set_xlabel('Pressure Score (50 = average eligible player)'); ax.set_title(ttl,loc='left',fontweight='bold',color=NAVY); fig.tight_layout(); fig.savefig(os.path.join(CH,fn),dpi=180); plt.close(fig)
bar_top(B,'top_bat.png','Top 10 batters under pressure'); bar_top(W,'top_bowl.png','Top 10 bowlers under pressure')
hb=F['hp_by_over']; fig,ax=plt.subplots(figsize=(6.6,3)); ax.plot(hb.index,100*hb[1],marker='o',color=NAVY,label='1st innings'); ax.plot(hb.index,100*hb[2],marker='s',color=PINK,label='Chase')
ax.set_xticks(range(1,21)); ax.set_xlabel('Over'); ax.set_ylabel('% of balls classed high pressure'); ax.legend(frameon=False); ax.set_title('Where high-pressure balls occur',loc='left',fontweight='bold',color=NAVY); fig.tight_layout(); fig.savefig(os.path.join(CH,'by_over.png'),dpi=180); plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(7,3.8))
for ax,e,t in zip(axs,(B,W),('Batters','Bowlers')):
    d=e.head(15).iloc[::-1]; ax.barh([f"{int(r)}. {n}" for r,n in zip(d['rank'],d['name'])],d.boot_top10_pct,color=[VC[v] for v in d.verdict]); ax.axvline(60,ls='--',lw=.8,color='grey'); ax.axvline(40,ls=':',lw=.8,color='grey')
    ax.set_xlim(0,100); ax.set_xlabel('% of 300 resamples in top 10'); ax.set_title(t,loc='left',fontweight='bold',color=NAVY); ax.tick_params(labelsize=7)
fig.tight_layout(); fig.savefig(os.path.join(CH,'bootstrap.png'),dpi=180); plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(7,3.6))
for ax,e,t,lab in zip(axs,(B,W),('Batters: runs above expected /100','Bowlers: runs saved vs expected /100'),('bat','bowl')):
    d=e.head(10).iloc[::-1]; y=np.arange(10); ax.barh(y+0.2,d.inn1_vs_exp,0.4,color=NAVY,label='1st innings'); ax.barh(y-0.2,d.inn2_vs_exp,0.4,color=PINK,label='Chase'); ax.set_yticks(y); ax.set_yticklabels(d['name'],fontsize=7); ax.axvline(0,color='black',lw=.6)
    ax.set_title(t,loc='left',fontweight='bold',color=NAVY,fontsize=9); ax.legend(frameon=False,fontsize=7)
fig.tight_layout(); fig.savefig(os.path.join(CH,'innings_split.png'),dpi=180); plt.close(fig)
fig,ax=plt.subplots(figsize=(6.2,2.8)); x=np.arange(4); labs=['Output','Wickets','Lift','Consistency']
ax.bar(x-0.27,[40,20,20,20],0.27,color='#9AA5B8',label='Nominal weight'); ax.bar(x,[100*F['diag']['bat']['shares'][k] for k in ('z_rae','z_dae','z_delta','z_cons')],0.27,color=NAVY,label='Effective - batters'); ax.bar(x+0.27,[100*F['diag']['bowl']['shares'][k] for k in ('z_rae','z_dae','z_delta','z_cons')],0.27,color=PINK,label='Effective - bowlers')
ax.set_xticks(x); ax.set_xticklabels(labs); ax.set_ylabel('% of score'); ax.legend(frameon=False,fontsize=8); ax.set_title('Nominal weights vs effective influence',loc='left',fontweight='bold',color=NAVY); fig.tight_layout(); fig.savefig(os.path.join(CH,'weights.png'),dpi=180); plt.close(fig)

# ---------------- docx helpers ----------------
def newdoc():
    d=Document(); s=d.sections[0]; s.page_width=Cm(21); s.page_height=Cm(29.7); s.left_margin=s.right_margin=Cm(2); s.top_margin=s.bottom_margin=Cm(1.8)
    st=d.styles['Normal']; st.font.name='Arial'; st.font.size=Pt(10); st.element.rPr.rFonts.set(qn('w:eastAsia'),'Arial'); st.paragraph_format.space_after=Pt(6)
    for n,sz in (('Heading 1',15),('Heading 2',12),('Heading 3',10.5),('Title',22)):
        h=d.styles[n]; h.font.name='Arial'; h.font.size=Pt(sz); h.font.bold=True; h.font.color.rgb=RGBColor(0x1B,0x2A,0x4A); h.element.rPr.rFonts.set(qn('w:eastAsia'),'Arial'); h.element.rPr.rFonts.set(qn('w:ascii'),'Arial'); h.element.rPr.rFonts.set(qn('w:hAnsi'),'Arial')
    return d
def shade(cell,hexc):
    tc=cell._tc.get_or_add_tcPr(); sh=OxmlElement('w:shd'); sh.set(qn('w:val'),'clear'); sh.set(qn('w:color'),'auto'); sh.set(qn('w:fill'),hexc); tc.append(sh)
def tbl(d,cols,rows,widths=None,size=8,verdict_col=None):
    t=d.add_table(rows=1,cols=len(cols)); t.style='Table Grid'; t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,c in enumerate(cols):
        ce=t.rows[0].cells[i]; ce.text=''; r=ce.paragraphs[0].add_run(str(c)); r.bold=True; r.font.size=Pt(size); r.font.color.rgb=RGBColor(255,255,255); shade(ce,'1B2A4A')
    for row in rows:
        cs=t.add_row().cells
        for i,v in enumerate(row):
            cs[i].text=''; r=cs[i].paragraphs[0].add_run(str(v)); r.font.size=Pt(size)
            if verdict_col is not None and i==verdict_col: shade(cs[i],{'Stable':'C6EFCE','Moderate':'FFEB9C','Borderline':'FFC7CE'}.get(str(v),'FFFFFF'))
    if widths:
        t.autofit=False
        for i,w in enumerate(widths): t.columns[i].width=Cm(w)
        for row in t.rows:
            for i,w in enumerate(widths): row.cells[i].width=Cm(w)
    d.add_paragraph(); return t
def bullets(d,items):
    for it in items: d.add_paragraph(it,style='List Bullet')
def fig(d,fn,w=15.5,cap=None):
    d.add_picture(os.path.join(CH,fn),width=Cm(w)); d.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER
    if cap: p=d.add_paragraph(cap); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.runs[0].italic=True; p.runs[0].font.size=Pt(8)
f1=lambda v: '' if pd.isna(v) else f"{v:+.1f}"
f0=lambda v: '' if pd.isna(v) else f"{v:+.0f}"
def toprows(e,bat):
    return [[int(p['rank']),p['name'],f"{p.score:.1f}",p.verdict,f"{int(p.p_balls)} / {int(p.p_matches)}",(f"{p.p_sr:.0f} vs {p.np_sr:.0f}" if bat else f"{p.p_econ:.1f} vs {p.np_econ:.1f}"),f1(p.rae),f1(p.dae),f1(p.delta),f"{p.cons:.0f}%",f"{f0(p.inn1_vs_exp)} / {f0(p.inn2_vs_exp)}",f"{int(p.scen_top10)}",f"{p.boot_top10_pct:.0f}%"] for _,p in e.head(10).iterrows()]
TW=[0.6,2.8,1.0,1.5,1.5,1.9,1.15,1.05,1.15,0.95,1.6,0.9,1.0]
exec(open(os.path.join(pl.HERE,'build_report2.py')).read())
