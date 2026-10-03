"""Discover and preserve actual public AP papers; never fabricate sessions."""
import argparse,concurrent.futures,hashlib,json,re,sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import fitz
from collectors import selfstudys,official,secondary,vedantu,careerindia,collegedekho,byjus
from collectors.web import ROOT,fetch
MONTHS={name.lower():i for i,name in enumerate(['','January','February','March','April','May','June','July','August','September','October','November','December'])};MONTHS.update({k[:3]:v for k,v in list(MONTHS.items()) if k});MONTHS["sept"]=9
def session(paper,text):
    title=paper['title']+' '+paper.get('download_url','')+' '+paper['source_url']
    # Prefer embedded paper identity over directory category (known source typo).
    header=text[:3500]
    match=re.search(r'(\d{1,2})(?:st|nd|rd|th)?[\s_-]*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)[\s_-]*(20\d{2})',header,re.I) or re.search(r'(\d{1,2})(?:st|nd|rd|th)?[\s_-]*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)[\s_-]*(20\d{2})',title,re.I)
    year=int(match[3]) if match else int(re.search(r'20(?:1[5-9]|2[0-6])',title)[0])
    date=f'{year}-{MONTHS[match[2].lower()]:02d}-{int(match[1]):02d}' if match else None
    if not date:
        dm=re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)[-_ ](\d{1,2})[-_ ](20\d{2})',title,re.I)
        if dm:year=int(dm[3]);date=f'{year}-{MONTHS[dm[1].lower()]:02d}-{int(dm[2]):02d}'
    sh=re.search(r'Shift[\s_-]*(1|2)',header,re.I) or re.search(r'Shift[\s_-]*(1|2)',title,re.I)
    shift='Shift_'+sh[1] if sh else 'Shift_1' if re.search(r'forenoon|morning',title,re.I) else 'Shift_2' if re.search(r'afternoon|evening',title,re.I) else None
    stream=('Agriculture_Pharmacy' if re.search(r'AGRICULTURE|BOTANY|ZOOLOGY',header,re.I) else 'Engineering' if re.search(r'ENGINEERING|Mathematics',header,re.I) else paper.get('stream') or 'Not_Identified')
    if stream=='Engineering' and re.search(r'agriculture|bpc',paper['source_url'],re.I) and not re.search(r'ENGINEERING',header,re.I):stream='Agriculture_Pharmacy'
    return year,date,shift,stream

def read_metadata(path):
    try:return json.loads(path.read_text())
    except (ValueError,OSError):return {}

def collect(paper):
    try:
        if 'download_url' not in paper:paper=selfstudys.resolve(paper)
        key=hashlib.sha256(paper['download_url'].encode()).hexdigest()[:16];cached=ROOT/'sources/download_cache'/f'{key}.pdf'
        existing=next((m for m in ROOT.glob('papers/**/metadata*.json') if read_metadata(m).get('download_url')==paper['download_url']),None)
        raw=(ROOT/read_metadata(existing)['pdf_path']).read_bytes() if existing else cached.read_bytes() if cached.exists() else fetch(paper['download_url'],binary=True)
        if not raw.startswith(b'%PDF'):raise ValueError('Download is not a PDF')
        doc=fitz.open(stream=raw,filetype='pdf')
        if not len(doc):raise ValueError('PDF has no pages')
        text='\n'.join(p.get_text() for p in doc)
        year,date,shift,stream=session(paper,text)
        if len(doc)<=4:
            from parsers.answer_key import parse as parse_key
            rows=parse_key(text)
            if rows:
                sm=re.search(r'Session[-\s]*(1|2)',text[:800],re.I)
                if sm:shift='Shift_'+sm[1]
                sha=hashlib.sha256(raw).hexdigest();dest=ROOT/'papers'/str(year)/(date or 'Date_Not_Identified')/(shift or 'Shift_Not_Identified')/stream;dest.mkdir(parents=True,exist_ok=True)
                fp=dest/f'answer_key_{sha[:12]}.pdf';fp.write_bytes(raw)
                record=dict(paper,year=year,exam_date=date,shift=shift,stream=stream,file_path=str(fp.relative_to(ROOT)),sha256=sha,key_type='published_educational_source',answers=rows,mapping_status='validated_160_rows',paper_type='answer_key')
                fp.with_name(f'answer_key_metadata_{sha[:12]}.json').write_text(json.dumps(record,indent=2));return record
        if re.search(r'Telangana|TS EAMCET|TS EAPCET',text[:1000],re.I):raise ValueError('Excluded Telangana paper')
        correction=ROOT/'sources/metadata_corrections.json'
        if correction.exists():
            for c in json.loads(correction.read_text()):
                if c.get('sha256')==hashlib.sha256(raw).hexdigest():
                    year=c.get('year',year);date=c.get('exam_date',date);shift=c.get('shift',shift);stream=c.get('stream',stream)
        if year not in range(2015,2027):raise ValueError('Out-of-range embedded year')
        dest=ROOT/'papers'/str(year)/(date or 'Date_Not_Identified')/(shift or 'Shift_Not_Identified')/stream
        dest.mkdir(parents=True,exist_ok=True)
        sha=hashlib.sha256(raw).hexdigest();file=dest/'question_paper.pdf'
        if file.exists() and hashlib.sha256(file.read_bytes()).hexdigest()!=sha:file=dest/f'question_paper_{key}.pdf'
        file.write_bytes(raw)
        meta=dict(paper,paper_id=f'{year}_{date or "undated"}_{shift or "unidentified"}_{stream}_{sha[:8]}',year=year,exam_date=date,shift=shift,stream=stream,subjects=[s for s in ['Mathematics','Physics','Chemistry','Botany','Zoology'] if s.lower() in text.lower()],paper_type='question_paper',file_name=file.name,pdf_path=str(file.relative_to(ROOT)),sha256=sha,pages=len(doc),metadata_evidence=header_evidence(text),date_verification='embedded PDF' if date and date[:4] in text[:3500] else 'source label' if date else 'Not Identified',answer_key_status='embedded_colored_options' if re.search(r'Options shown in green',text,re.I) else 'Not Found',answer_key_type='official_final' if paper.get('key_version')=='final' else 'official_preliminary' if paper['source'].startswith('APSCHE') else 'published_educational_source' if 'Options shown in green' in text else 'unavailable',extraction_status='pending')
        mfile=dest/('metadata.json' if file.name=='question_paper.pdf' else f'metadata_{key}.json');mfile.write_text(json.dumps(meta,indent=2,ensure_ascii=False));print('Downloaded',year,date,shift,stream,len(raw),flush=True);return meta
    except Exception as e:
        print('FAILED',paper.get('title'),str(e),flush=True);return dict(paper,status='Failed',error=str(e))
def header_evidence(text):return text[:2500]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=3);ap.add_argument('--sources',nargs='+',choices=['selfstudys','official','secondary','vedantu','careerindia','collegedekho','byjus'],default=['selfstudys','official']);args=ap.parse_args()
    found=[]
    for source in [globals()[name] for name in args.sources]:
        try:found+=source.discover()
        except Exception as e:found.append({'source':source.__name__,'status':'Discovery failed','error':str(e)})
    (ROOT/'sources/discovered_papers.json').write_text(json.dumps(found,indent=2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:results=list(ex.map(collect,[p for p in found if 'source_url' in p and p.get('paper_type_hint')!='answer_key']))
    (ROOT/'sources/collection_results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
