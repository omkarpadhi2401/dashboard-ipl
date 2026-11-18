"""FINAL presentation (10 slides, Rajasthan Royals-inspired palette, illustrations on every slide, transitions + fade-in sequences).
Reads only work/final.pkl. Overwrites 04_PowerPoint/SupeRR_Final_Presentation.pptx (single official version)."""
import pandas as pd, numpy as np, os, pipeline as pl
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, Circle, Wedge, FancyBboxPatch, Polygon
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_TICK_LABEL_POSITION
from lxml import etree
ROOT=pl.PROJECT; OUT=pl.PPT_DIR; IMG=pl.PPT_ASSETS; os.makedirs(IMG,exist_ok=True)
F=pd.read_pickle(os.path.join(pl.WORK,'final.pkl')); B=F['players']['bat'].sort_values('rank'); W=F['players']['bowl'].sort_values('rank'); cv=F['coverage']
HP='#E60693'; HB='#1E73E8'; HN='#141B4D'; HG='#F2F4F8'
PINK=RGBColor(0xE6,0x06,0x93); BLUE=RGBColor(0x1E,0x73,0xE8); NAVY=RGBColor(0x14,0x1B,0x4D); LIGHT=RGBColor(0xF2,0xF4,0xF8); WHITE=RGBColor(255,255,255); GREY=RGBColor(0x55,0x5E,0x75)
VC={'Stable':RGBColor(0x1B,0x7F,0x3B),'Moderate':RGBColor(0xA8,0x62,0x00),'Borderline':RGBColor(0xC6,0x28,0x28)}; VB={'Stable':RGBColor(0xD5,0xF2,0xDC),'Moderate':RGBColor(0xFF,0xEE,0xB8),'Borderline':RGBColor(0xFF,0xD6,0xDB)}

# ---------------- original illustrations (drawn here; no third-party images) ----------------
def canvas(w,h):
    fig=plt.figure(figsize=(w,h)); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,w); ax.set_ylim(0,h); ax.axis('off'); return fig,ax
def save(fig,fn): fig.savefig(os.path.join(IMG,fn),dpi=200,transparent=True); plt.close(fig)
def stumps(ax,x,y,h,col='white',bail=HP):
    for dx in (-0.12,0,0.12): ax.add_patch(Rectangle((x+dx*h*2-0.02*h,y),0.045*h,h,color=col))
    ax.add_patch(Rectangle((x-0.27*h,y+h),0.54*h,0.05*h,color=bail))
def ball(ax,x,y,r,col='#C8102E'):
    ax.add_patch(Circle((x,y),r,color=col)); ax.plot([x-r*0.8,x+r*0.8],[y+r*0.25,y-r*0.25],color='white',lw=1.2,ls=(0,(2,1.5)))
def stadium(fn,night=True):
    fig,ax=canvas(6,7.5); bgc=HN if night else HP
    ax.add_patch(Rectangle((0,0),6,7.5,color=bgc)); ax.add_patch(Circle((4.9,6.6),2.3,color=HP if night else HB,alpha=0.9)); ax.add_patch(Circle((0.3,6.9),1.1,color=HB if night else HN,alpha=0.85))
    for i,(c,a) in enumerate(((HB,0.55),('#3D8BF2',0.5),('white',0.18))): ax.add_patch(Ellipse((3,2.5),7.6-i*0.9,4.6-i*0.55,color=c,alpha=a))
    ax.add_patch(Ellipse((3,2.2),5.2,2.7,color='#2E9E5B')); ax.add_patch(Ellipse((3,2.2),3.4,1.75,fill=False,ec='white',lw=1.2,alpha=0.8))
    ax.add_patch(Polygon([[2.78,1.5],[3.22,1.5],[3.14,2.9],[2.86,2.9]],color='#E9D8A6'))
    stumps(ax,3,2.85,0.28); stumps(ax,3,1.5,0.4); ball(ax,3.35,2.2,0.09)
    for x in (0.7,5.3):
        ax.add_patch(Rectangle((x-0.04,3.6),0.08,2.3,color='white',alpha=0.85)); ax.add_patch(FancyBboxPatch((x-0.45,5.9),0.9,0.5,boxstyle='round,pad=0.03',color='white'))
        for i in range(4):
            for j in range(2): ax.add_patch(Circle((x-0.3+i*0.2,6.03+j*0.24),0.07,color='#FFE66D'))
        ax.add_patch(Polygon([[x-0.4,5.9],[x+0.4,5.9],[3+(x-3)*0.25,2.6]],color='white',alpha=0.07))
    save(fig,fn)
def pitch(fn):
    fig,ax=canvas(4.5,5); ax.add_patch(FancyBboxPatch((0.1,0.1),4.3,4.8,boxstyle='round,pad=0.02,rounding_size=0.25',color='#2E9E5B'))
    ax.add_patch(Polygon([[1.55,0.5],[2.95,0.5],[2.65,4.5],[1.85,4.5]],color='#E9D8A6')); ax.plot([1.6,2.9],[1.1,1.1],color='white',lw=2); ax.plot([1.86,2.64],[4.05,4.05],color='white',lw=1.5)
    stumps(ax,2.25,4.05,0.42); stumps(ax,2.25,0.75,0.75); ball(ax,2.75,2.5,0.16); ax.add_patch(Circle((0.9,4.1),0.55,color=HP,alpha=0.9)); ax.text(0.9,4.1,'?',color='white',fontsize=30,fontweight='bold',ha='center',va='center')
    save(fig,fn)
def gauge(fn):
    fig,ax=canvas(5,3.1)
    for a0,a1,c in ((120,180,'#BFD8FA'),(60,120,HB),(0,60,HP)): ax.add_patch(Wedge((2.5,0.45),2.2,a0,a1,width=0.55,color=c))
    ang=np.deg2rad(28); ax.plot([2.5,2.5+1.75*np.cos(ang)],[0.45,0.45+1.75*np.sin(ang)],color=HN,lw=5,solid_capstyle='round'); ax.add_patch(Circle((2.5,0.45),0.2,color=HN))
    for t,a in (('LOW',150),('MEDIUM',90),('HIGH',30)): ax.text(2.5+1.92*np.cos(np.deg2rad(a)),0.45+1.92*np.sin(np.deg2rad(a)),t,color='white' if a<130 else HN,fontsize=9,fontweight='bold',ha='center',va='center',rotation=a-90)
    ball(ax,4.55,2.75,0.2); save(fig,fn)
def bat(fn):
    fig,ax=canvas(3.2,5); ax.add_patch(FancyBboxPatch((0.1,0.1),3,4.8,boxstyle='round,pad=0.02,rounding_size=0.25',color=HP))
    t=matplotlib.transforms.Affine2D().rotate_deg_around(1.6,2.5,-28)+ax.transData
    ax.add_patch(FancyBboxPatch((1.3,0.8),0.6,2.5,boxstyle='round,pad=0.02,rounding_size=0.12',color='#F4D9A0',transform=t)); ax.add_patch(Rectangle((1.5,3.3),0.2,1.1,color=HN,transform=t))
    ball(ax,2.45,3.9,0.22,'white'); ax.plot([2.45-0.17,2.45+0.17],[3.95,3.85],color=HP,lw=1.3,ls=(0,(2,1.5)))
    for i,(x,y) in enumerate(((0.55,4.3),(0.75,3.9),(0.5,3.5))): ax.plot([x,x+0.45],[y,y],color='white',lw=2.5,alpha=0.7,solid_capstyle='round')
    save(fig,fn)
def bowl(fn):
    fig,ax=canvas(3.2,5); ax.add_patch(FancyBboxPatch((0.1,0.1),3,4.8,boxstyle='round,pad=0.02,rounding_size=0.25',color=HB))
    stumps(ax,1.6,0.7,1.7); ball(ax,1.05,3.55,0.33)
    for r,a in ((0.6,0.6),(0.85,0.4),(1.1,0.22)): ax.add_patch(Wedge((1.05,3.55),r+0.03,20,80,width=0.05,color='white',alpha=a))
    ax.add_patch(Rectangle((1.9,2.42),0.5,0.1,color='white',angle=28)); save(fig,fn)
def trophy(fn):
    fig,ax=canvas(6,7.5); ax.add_patch(Rectangle((0,0),6,7.5,color=HP)); ax.add_patch(Circle((5.2,1.0),2.2,color=HB,alpha=0.9)); ax.add_patch(Circle((0.6,6.8),1.5,color=HN,alpha=0.9))
    ax.add_patch(Ellipse((3,2.3),5.4,2.6,color='#2E9E5B')); ax.add_patch(Polygon([[2.75,1.55],[3.25,1.55],[3.15,3.05],[2.85,3.05]],color='#E9D8A6')); stumps(ax,3,3.0,0.3); stumps(ax,3,1.55,0.45)
    for i,(x,h) in enumerate(((1.6,1.0),(2.3,1.7),(3.0,2.5),(3.7,1.4),(4.4,2.1))): ax.add_patch(FancyBboxPatch((x-0.22,4.1),0.44,h,boxstyle='round,pad=0.01,rounding_size=0.08',color='white',alpha=0.95 if i==2 else 0.6))
    ball(ax,3.0,6.95,0.2,'white'); save(fig,fn)
stadium('stadium.png'); pitch('pitch.png'); gauge('gauge.png'); bat('bat.png'); bowl('bowl.png'); trophy('finale.png')

# ---------------- pptx helpers ----------------
prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5); BL=prs.slide_layouts[6]; ANIM={}
def reg(s,sh): ANIM.setdefault(id(s),[]).append(sh.shape_id); return sh
def tx(s,x,y,w,h,text,size=14,bold=False,color=NAVY,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP,italic=False,bullet=False,gap=6):
    tb=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=tb.text_frame; tf.word_wrap=True; tf.vertical_anchor=anchor
    for m in ('margin_left','margin_right','margin_top','margin_bottom'): setattr(tf,m,Inches(0.03))
    for i,t in enumerate(text if isinstance(text,list) else [text]):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.alignment=align; p.space_after=Pt(gap)
        if bullet:
            pPr=p._p.get_or_add_pPr(); pPr.set('marL','228600'); pPr.set('indent','-228600')
            bc=etree.SubElement(pPr,'{http://schemas.openxmlformats.org/drawingml/2006/main}buClr'); sc=etree.SubElement(bc,'{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr'); sc.set('val','E60693')
            bu=etree.SubElement(pPr,'{http://schemas.openxmlformats.org/drawingml/2006/main}buChar'); bu.set('char','•')
        r=p.add_run(); r.text=t; r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=color; r.font.name='Arial'; r.font.italic=italic
    return tb
def box(s,x,y,w,h,fill=LIGHT,shape=MSO_SHAPE.ROUNDED_RECTANGLE,adj=0.08):
    r=s.shapes.add_shape(shape,Inches(x),Inches(y),Inches(w),Inches(h)); r.fill.solid(); r.fill.fore_color.rgb=fill; r.line.fill.background(); r.shadow.inherit=False
    if shape==MSO_SHAPE.ROUNDED_RECTANGLE: r.adjustments[0]=adj
    return r
def label(sh,text,size=14,color=WHITE,bold=True):
    tf=sh.text_frame; tf.word_wrap=True; tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    for i,t in enumerate(text if isinstance(text,list) else [text]):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.alignment=PP_ALIGN.CENTER; r=p.add_run(); r.text=t; r.font.size=Pt(size if i==0 else size-3); r.font.bold=bold if i==0 else False; r.font.color.rgb=color; r.font.name='Arial'
    return sh
def pic(s,fn,x,y,w=None,h=None): return s.shapes.add_picture(os.path.join(IMG,fn),Inches(x),Inches(y),Inches(w) if w else None,Inches(h) if h else None)
def slide(n,title,sub=None,notes=''):
    s=prs.slides.add_slide(BL); f=s.background.fill; f.solid(); f.fore_color.rgb=WHITE
    c=box(s,0.55,0.45,0.62,0.62,PINK,MSO_SHAPE.OVAL); label(c,str(n),16)
    tx(s,1.35,0.36,10.6,0.8,title,30,True,NAVY,anchor=MSO_ANCHOR.MIDDLE)
    if sub: tx(s,1.35,1.12,10.6,0.45,sub,14,False,GREY)
    if os.path.exists(os.path.join(IMG,'rr_logo.png')): pic(s,'rr_logo.png',12.2,0.3,h=0.85)
    tx(s,0.55,7.02,9,0.3,'SupeRR Selector Season 2  |  Performance Under Pressure',10,False,GREY)
    s.notes_slide.notes_text_frame.text=notes; return s
def table(s,x,y,w,h,cols,rows,cw,size=12,vcol=None,top3=True):
    g=s.shapes.add_table(len(rows)+1,len(cols),Inches(x),Inches(y),Inches(w),Inches(h)); t=g.table; tot=sum(cw)
    tblPr=g._element.graphic.graphicData.tbl.tblPr; tblPr.set('bandRow','0'); tblPr.set('firstRow','0')
    for i,c_ in enumerate(cols):
        t.columns[i].width=Inches(w*cw[i]/tot); c=t.cell(0,i); c.fill.solid(); c.fill.fore_color.rgb=NAVY; c.text=''; r=c.text_frame.paragraphs[0].add_run(); r.text=c_; r.font.size=Pt(11); r.font.bold=True; r.font.color.rgb=WHITE; r.font.name='Arial'; c.vertical_anchor=MSO_ANCHOR.MIDDLE; c.margin_left=c.margin_right=Inches(0.06)
    for ri,row in enumerate(rows,1):
        for i,v in enumerate(row):
            c=t.cell(ri,i); c.fill.solid(); c.fill.fore_color.rgb=WHITE if ri%2 else LIGHT; c.text=''; r=c.text_frame.paragraphs[0].add_run(); r.text=str(v); r.font.size=Pt(size); r.font.name='Arial'; r.font.color.rgb=NAVY; r.font.bold=(i==1); c.vertical_anchor=MSO_ANCHOR.MIDDLE
            c.margin_left=c.margin_right=Inches(0.06); c.margin_top=c.margin_bottom=Inches(0.02)
            if top3 and ri<=3 and i==0: c.fill.fore_color.rgb=PINK; r.font.color.rgb=WHITE; r.font.bold=True
            if top3 and ri<=3 and i==1: r.font.color.rgb=BLUE
            if vcol is not None and i==vcol: c.fill.fore_color.rgb=VB[str(v)]; r.font.bold=True; r.font.color.rgb=VC[str(v)]
    for r_ in t.rows: r_.height=Inches(h/(len(rows)+1))
    return g
def chart(s,x,y,w,h,cats,series,cols,kind=XL_CHART_TYPE.BAR_CLUSTERED,legend=True,labels=False,vmin=None,vmax=None,title=None,size=11):
    cd=CategoryChartData(); cd.categories=cats
    for n,v in series: cd.add_series(n,[None if pd.isna(v_) else float(v_) for v_ in v])
    gf=s.shapes.add_chart(kind,Inches(x),Inches(y),Inches(w),Inches(h),cd); ch=gf.chart; ch.font.size=Pt(size); ch.font.name='Arial'; ch.font.color.rgb=GREY; ch.has_legend=legend
    if legend: ch.legend.position=XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout=False
    ch.value_axis.has_major_gridlines=True; ch.value_axis.major_gridlines.format.line.color.rgb=RGBColor(0xDD,0xE1,0xE8); ch.value_axis.format.line.fill.background(); ch.category_axis.format.line.color.rgb=RGBColor(0xC0,0xC6,0xD0)
    for sr,c in zip(ch.plots[0].series,cols): sr.format.fill.solid(); sr.format.fill.fore_color.rgb=c; sr.invert_if_negative=False
    ch.plots[0].gap_width=55
    if kind==XL_CHART_TYPE.BAR_CLUSTERED: ch.category_axis.reverse_order=True; ch.value_axis.tick_label_position=XL_TICK_LABEL_POSITION.HIGH; ch.category_axis.tick_label_position=XL_TICK_LABEL_POSITION.LOW
    if labels: p_=ch.plots[0]; p_.has_data_labels=True; p_.data_labels.number_format='0'; p_.data_labels.number_format_is_linked=False; p_.data_labels.font.size=Pt(10); p_.data_labels.position=XL_LABEL_POSITION.OUTSIDE_END
    if vmin is not None: ch.value_axis.minimum_scale=vmin
    if vmax is not None: ch.value_axis.maximum_scale=vmax
    ch.has_title=bool(title)
    if title: ch.chart_title.text_frame.text=title; r=ch.chart_title.text_frame.paragraphs[0].runs[0]; r.font.size=Pt(12); r.font.bold=True; r.font.color.rgb=NAVY
    return gf
f1=lambda v: f"{v:+.1f}"
exec(open(os.path.join(pl.HERE,'build_ppt_final2.py')).read())
