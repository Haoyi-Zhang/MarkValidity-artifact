#!/usr/bin/env python3
"""Place the manuscript figures at their actual width, in color and grayscale."""
import argparse
from html import escape
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def argument(text, command):
    m=re.search(r'\\'+re.escape(command)+r'\s*(?:\[[^\]]*\])?\s*\{',text)
    if not m:raise ValueError('missing '+command)
    start=m.end();depth=1
    for i in range(start,len(text)):
        if text[i] in '{}' and text[i-1]!='\\':
            depth += 1 if text[i]=='{' else -1
            if not depth:return text[start:i]
    raise ValueError('unclosed '+command)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--paper',type=Path,required=True)
    a=p.parse_args();root=a.artifact.resolve();paper=a.paper.resolve()
    import fitz
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph
    from reportlab.lib.colors import HexColor
    # Use PDF base fonts so the atlas can be rebuilt from the deliverable alone.
    # The scientific figure assets retain their own embedded fonts; this choice
    # affects only atlas headings and captions.
    atlas_font='Times-Roman';atlas_bold='Times-Bold'
    layout=json.loads((root/'figures/data/manuscript-figure-layout.json').read_text())
    if sha(paper/'acmart.cls')!=layout['class_sha256']:raise ValueError('class changed; remeasure linewidth')
    def expand(path,stack=()):
        path=path.resolve()
        if path in stack:raise ValueError('cyclic TeX input')
        if not path.is_relative_to(paper):raise ValueError('TeX input escapes paper')
        t=re.sub(r'(?<!\\)%[^\n]*','',path.read_text())
        return re.sub(r'\\input\{([^}]+)\}',lambda m:expand(paper/(m.group(1)+('.tex' if not Path(m.group(1)).suffix else '')),stack+(path,)),t)
    source=expand(paper/'main.tex')
    blocks=re.findall(r'\\begin\{figure\}(?:\[[^\]]*\])?(.*?)\\end\{figure\}',source,re.S)
    # Conceptual figures are framed placeholders without an image; the atlas covers drawn figures.
    blocks=[b for b in blocks if re.search(r'\\includegraphics',b)]
    if not blocks:raise ValueError('main article contains no figures')
    atlas=fitz.open();records=[];page_w,page_h=612,720
    total_pages=2*len(blocks)
    for number,block in enumerate(blocks,1):
        name=Path(argument(block,'includegraphics'))
        path=paper/name;figure=fitz.open(path)
        if len(figure)!=1:raise ValueError('each figure source must be a single-page PDF')
        caption=' '.join(argument(block,'caption').split())
        markup=escape(caption)
        markup=re.sub(r'\\texttt\{([^{}]*)\}',r'<font name="Courier">\1</font>',markup)
        for token,value in {'$(P,Q,\\kappa)$':'(P, Q, kappa)',
                            '$Q_0$':'Q<sub>0</sub>','$Q_1$':'Q<sub>1</sub>',
                            '$Q_2$':'Q<sub>2</sub>','$N^2M$':'N<super>2</super>M',
                            '$NF$':'NF','$C$':'C','$J$':'J','$D$':'D','$H$':'H',
                            '$J_L-J_R=1/2$':'J<sub>L</sub> − J<sub>R</sub> = 1/2'}.items():
            markup=markup.replace(token,value)
        markup=markup.replace('\\%','%').replace('~',' ')
        markup=re.sub(r'Equation ?\\eqref\{[^{}]*\}|\\eqref\{[^{}]*\}','the paired envelope',markup)
        markup=re.sub(r'\s*\([^()]*\\ref\{[^{}]*\}[^()]*\)','',markup)
        def inline(m):
            body=m.group(1)
            body=re.sub(r'\\(?:mathrm|mathit)\{([^{}]*)\}',r'\1',body)
            body=re.sub(r'_\{([^{}]*)\}|_(\w)',lambda s:'<sub>'+(s.group(1) or s.group(2))+'</sub>',body)
            return body.replace('\\geq','≥').replace('\\leq','≤').replace('\\,',' ')
        markup=re.sub(r'\$([^$]*)\$',inline,markup)
        if re.search(r'[\\{}$]',markup):raise ValueError('caption needs an explicit math rendering rule: '+caption)
        width=layout['linewidth_bp'];height=figure[0].rect.height*width/figure[0].rect.width
        left=(page_w-width)/2;top=104
        if height>400:raise ValueError('figure too tall at actual manuscript width')
        clipped=[]
        for block_data in figure[0].get_text('dict')['blocks']:
            for line in block_data.get('lines',[]):
                for span in line['spans']:
                    box=fitz.Rect(span['bbox']);r=figure[0].rect
                    if box.x0 < -.4 or box.y0 < -.4 or box.x1>r.width+.4 or box.y1>r.height+.4:
                        clipped.append(span['text'])
        if clipped:raise ValueError('text outside source figure page: '+repr(clipped))
        r=dict(number=number,name=name.stem,label=argument(block,'label'),caption_tex=caption,
               caption_sha256=hashlib.sha256(caption.encode()).hexdigest(),source_pdf_sha256=sha(path),
               source_size_bp=list(figure[0].rect)[2:],display_size_bp=[width,height])
        for mode in ['Color','Grayscale']:
            buf=BytesIO();c=canvas.Canvas(buf,pagesize=(page_w,page_h),invariant=1,pageCompression=1,
                                         initialFontName=atlas_font,initialFontSize=9)
            c.setFillColor(HexColor('#26323C'));c.setFont(atlas_font,9)
            c.drawString(48,page_h-29,'FIGURE ATLAS')
            c.drawRightString(page_w-48,page_h-29,str(len(atlas)+1)+' / '+str(total_pages))
            c.setStrokeColor(HexColor('#BBC4CC'));c.line(48,page_h-40,page_w-48,page_h-40)
            c.setFont(atlas_bold,17);c.drawString(48,page_h-66,f'Figure {number} — {mode}')
            c.setFont(atlas_font,9.5);c.drawString(48,page_h-84,'Manuscript width: 430.00462 TeX points. View or print at 100%.')
            style=ParagraphStyle('caption',fontName=atlas_font,fontSize=10.2,leading=13.4)
            para=Paragraph(f'<b>Figure {number}.</b> '+markup,style)
            _,ch=para.wrap(width,140)
            caption_top=top+height+19
            if caption_top+ch>page_h-94:raise ValueError('caption exceeds atlas page')
            para.drawOn(c,left,page_h-caption_top-ch)
            c.setFont(atlas_font,9);c.setFillColor(HexColor('#55616B'))
            c.drawString(48,55,f'Source: {name.name}')
            c.drawString(48,41,'Precise annotations remain vector text; grayscale is rendered at 300 dpi.')
            c.save();background=fitz.open(stream=buf.getvalue(),filetype='pdf')
            atlas.insert_pdf(background);page=atlas[-1];rect=fitz.Rect(left,top,left+width,top+height)
            if mode=='Color':page.show_pdf_page(rect,figure,0)
            else:
                pix=figure[0].get_pixmap(matrix=fitz.Matrix(width/figure[0].rect.width*300/72,width/figure[0].rect.width*300/72),colorspace=fitz.csGRAY,alpha=False)
                page.insert_image(rect,stream=pix.tobytes('png'))
        records.append(r)
    atlas.set_metadata({'title':'Figure Atlas','author':'','subject':'Manuscript figures at publication width, in color and grayscale'})
    dest=paper/'figure-atlas.pdf';atlas.save(dest,garbage=4,deflate=True,no_new_id=True)
    receipt={'schema':'markvalidity-natural-atlas-v1','status':'PASS','pages':len(atlas),
             'figures':records,'main_tex_sha256':sha(paper/'main.tex'),
             'results_tex_sha256':sha(paper/'figdata/natural-results.tex'),
             'atlas_sha256':sha(dest),'renderer_sha256':sha(Path(__file__)),
             'layout_source_sha256':sha(root/'figures/data/manuscript-figure-layout.json'),
             'grayscale_dpi':300,'text_page_bounds_checked':True}
    (paper/'figure-atlas-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':'PASS','pages':len(atlas),'figures':len(records),'sha256':sha(dest)}))


if __name__=='__main__':main()
