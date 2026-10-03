"""Extract native text, lossless embedded question images, and color-coded keys.
No OCR guesses are promoted to verified question text or official answers.
"""
import hashlib,re
from pathlib import Path
import fitz
SUBJECTS=['Mathematics','Physics','Chemistry','Botany','Zoology']
def parse(path,meta,root):
    doc=fitz.open(path);questions=[];current=None;subject=None;mode='question';option=None
    def finish():
        nonlocal current
        if not current:return
        greens=current.pop('_greens');labels=current.pop('_labels');unlabelled=current.pop('_unlabelled');current.pop('_options_boundary',None)
        if not labels and len(unlabelled)==4:
            for a,asset in zip('ABCD',unlabelled):current['option_images'][a].append(asset)
        elif unlabelled:current['unassigned_images']=unlabelled
        if set(labels)==set('ABCD') and len(greens)==1 and meta['answer_key_status']=='embedded_colored_options':
            current['correct_answer']=greens[0];current['answer_provenance']={'type':meta['answer_key_type'],'method':'single green option label (RGB 0,128,0); four option labels required','source_url':meta['source_url'],'location':'embedded in original PDF','preliminary':meta['answer_key_type']=='official_preliminary' if meta['source'].startswith('APSCHE') else None}
        current['native_text_fragments']='\n'.join(current.pop('_text')).strip() or None
        current['question']=None
        current['extraction_status']='image_preserved' if current['question_images'] else 'native_text_partial'
        questions.append(current);current=None
    for page in doc:
        blocks=page.get_text('dict')['blocks'];events=[]
        for b in blocks:
            if b['type']==0:
                for line in b['lines']:
                    for span in line['spans']:events.append((span['bbox'][1],span['bbox'][0],'text',span))
            elif b['type']==1:events.append((b['bbox'][3],b['bbox'][0],'image',b))
        events.sort(key=lambda e:(round(e[0],1),e[1]))
        for y,x,kind,event in events:
            if kind=='text':
                text=event['text'].strip()
                if not text:continue
                if text in SUBJECTS:subject=text
                match=re.search(r'Question Number\s*:\s*(\d+)\s+Question Id\s*:\s*(\d+)',text)
                if match:
                    finish();n=int(match[1]);mode='question';option=None
                    if subject is None and meta['stream']=='Engineering':subject='Mathematics' if n<=80 else 'Physics' if n<=120 else 'Chemistry'
                    if meta['year']<=2019 and meta['stream']=='Engineering':subject='Mathematics' if n<=80 else 'Physics' if n<=120 else 'Chemistry'
                    elif meta['year']<=2019 and meta['stream']=='Agriculture_Pharmacy':subject='Botany' if n<=40 else 'Zoology' if n<=80 else 'Physics' if n<=120 else 'Chemistry'
                    current={'question_id':f"{meta['paper_id']}_{subject or 'unknown'}_q{n:03d}",'paper_id':meta['paper_id'],'year':meta['year'],'exam_date':meta['exam_date'],'shift':meta['shift'],'stream':meta['stream'],'subject':subject,'question_number':n,'original_question_id':match[2],'question':None,'options':dict.fromkeys('ABCD'),'question_images':[],'option_images':{a:[] for a in 'ABCD'},'correct_answer':None,'answer_provenance':{'type':'unavailable'},'solution':None,'eapcet_shortcut':None,'banda_gurthu':None,'chapter':None,'topic':None,'source_paper':meta['pdf_path'],'source_url':meta['source_url'],'source':meta['source'],'pdf_page':page.number+1,'_greens':[],'_labels':[],'_text':[],'_unlabelled':[],'_options_boundary':{}}
                elif current:
                    if text.startswith('Options'):mode='options';option=None;current['_options_boundary'][page.number]=event['bbox'][1]
                    elif re.fullmatch(r'[1-4]\.',text) and mode=='options':
                        option='ABCD'[int(text[0])-1];current['_labels'].append(option)
                        if event['color']==32768:current['_greens'].append(option)
                    elif not re.match(r'(Correct Marks|Display Question|Question Type|Option Shuffling|Section|Group|Sub-Section|Number of Questions|Maximum|Mandatory|Yes|No|Single Line Question|Vertical|Is Question Mandatory|Option Orientation)',text):
                        if mode=='question':current['_text'].append(text)
                        elif option:current['options'][option]=((current['options'][option] or '')+' '+text).strip()
            elif current:
                w,h=event['width'],event['height'];bbox=fitz.Rect(event['bbox'])
                if w<=20 or h<=20 or (bbox.width>page.rect.width*.94 and bbox.height>page.rect.height*.94):continue
                raw=event['image'];digest=hashlib.sha256(raw).hexdigest()
                asset={'path':meta['pdf_path'],'render_type':'pdf_region','pdf_page':page.number+1,'bbox':list(event['bbox']),'sha256':digest}
                if mode=='question' or event['bbox'][1]<current['_options_boundary'].get(page.number,float('-inf')):current['question_images'].append(asset)
                elif option:current['option_images'][option].append(asset)
                else:current['_unlabelled'].append(asset)
    finish()
    return questions,'\n'.join(p.get_text() for p in doc)
