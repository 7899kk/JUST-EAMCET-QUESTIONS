"""Index numbered questions and published explanations as original PDF regions.
Math text from custom fonts remains searchable raw text, never a complete transcription.
"""
import re
from collections import Counter
import fitz

def parse(path,meta,root):
    doc=fitz.open(path);candidates=[]
    for p in doc:
        for b in p.get_text('dict')['blocks']:
            if b['type']!=0:continue
            for line in b['lines']:
                text=''.join(s['text'] for s in line['spans']).strip();match=re.match(r'^(\d{1,3})\.(?:\s+|$)(.*)',text) or re.match(r'^(\d{1,3})\s+([A-Z].*)',text)
                if match and 1<=int(match[1])<=160 and line['bbox'][0]<p.rect.width*.3:
                    candidates.append({'n':int(match[1]),'page':p.number,'bbox':line['bbox'],'text':text})
    candidates.sort(key=lambda c:(c['page'],c['bbox'][1],c['bbox'][0]))
    # Accept only runs of consecutive labels to reject isolated formula numbers.
    accepted=[]
    columns=Counter(round(c['bbox'][0]/4)*4 for c in candidates);dominant={x for x,count in columns.items() if count>=max(columns.values(),default=1)*.35}
    for i,c in enumerate(candidates):
        adjacent=(i+1<len(candidates) and candidates[i+1]['n']==c['n']+1) or (i>0 and candidates[i-1]['n']==c['n']-1)
        if adjacent or any(abs(c['bbox'][0]-x)<=5 for x in dominant):accepted.append(c)
    questions={};text='\n'.join(p.get_text() for p in doc)
    for i,c in enumerate(accepted):
        end=accepted[i+1] if i+1<len(accepted) else {'page':len(doc)-1,'bbox':[0,doc[-1].rect.height-25,0,0]}
        regions=[];raw=[];sol_regions=[]
        for pi in range(c['page'],end['page']+1):
            page=doc[pi];top=max(0,c['bbox'][1]-3) if pi==c['page'] else 36;bottom=end['bbox'][1]-3 if pi==end['page'] else page.rect.height-25
            if bottom-top<8:continue
            clip=fitz.Rect(15,top,page.rect.width-15,bottom);content=page.get_text(clip=clip);raw.append(content)
            region={'path':meta['pdf_path'],'render_type':'pdf_region','pdf_page':pi+1,'bbox':list(clip)};regions.append(region)
            # Published Sol/HINT starts are evidence; preserve the actual region, not garbled glyphs.
            hits=page.search_for('Sol:',clip=clip)+page.search_for('Sol :',clip=clip)+page.search_for('HINT:',clip=clip)
            if hits:
                sr=dict(region,bbox=[15,min(h.y0 for h in hits)-2,page.rect.width-15,bottom]);sol_regions.append(sr)
        if not regions:continue
        n=c['n'];scope=meta.get('subject_scope')
        subject=scope or ('Mathematics' if n<=80 else 'Physics' if n<=120 else 'Chemistry') if meta['stream']=='Engineering' else ('Botany' if n<=40 else 'Zoology' if n<=80 else 'Physics' if n<=120 else 'Chemistry')
        if n in questions:
            if re.search(r'Solutions|Solution|Answers',text,re.I):questions[n].setdefault('solution_images',[]).extend(regions);questions[n]['solution_provenance']={'type':'published_educational_source','source_url':meta['source_url'],'pdf_path':meta['pdf_path']}
            continue
        q={'question_id':f"{meta['paper_id']}_{subject}_q{n:03d}",'paper_id':meta['paper_id'],'year':meta['year'],'exam_date':meta['exam_date'],'shift':meta['shift'],'stream':meta['stream'],'subject':subject,'question_number':n,'original_question_id':None,'question':None,'options':dict.fromkeys('ABCD'),'question_images':regions,'option_images':{a:[] for a in 'ABCD'},'options_embedded_in_question_image':True,'correct_answer':None,'answer_provenance':{'type':'unavailable'},'solution':None,'solution_images':sol_regions,'eapcet_shortcut':None,'banda_gurthu':None,'chapter':None,'topic':None,'source_paper':meta['pdf_path'],'source_url':meta['source_url'],'source':meta['source'],'pdf_page':c['page']+1,'searchable_text':'\n'.join(raw),'extraction_status':'original_question_region_with_partial_native_text'}
        keys=re.findall(r'(?:KEY|Key|Ans)\s*:\s*([1-4])\b','\n'.join(raw))
        if len(keys)==1:q['correct_answer']='ABCD'[int(keys[0])-1];q['answer_provenance']={'type':'published_educational_source','method':'explicit KEY/Ans label in same question region','source_url':meta['source_url'],'pdf_path':meta['pdf_path']}
        if sol_regions:q['solution_provenance']={'type':'published_educational_source','source_url':meta['source_url'],'pdf_path':meta['pdf_path']}
        questions[n]=q
    return sorted(questions.values(),key=lambda q:q['question_number']),text
