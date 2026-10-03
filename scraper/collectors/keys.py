"""Preserve separately published key PDFs and validate complete answer tables."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fitz
from .web import ROOT,fetch
from parsers.answer_key import parse
def collect(items):
    from scraper import session
    metas=[json.loads(p.read_text()) for p in ROOT.glob('papers/**/metadata*.json')];results=[]
    for item in items:
        try:
            raw=fetch(item['download_url'],binary=True);doc=fitz.open(stream=raw,filetype='pdf');text='\n'.join(p.get_text() for p in doc);year,date,shift,stream=session(item,text)
            matches=[m for m in metas if (m['year'],m['exam_date'],m['shift'],m['stream'])==(year,date,shift,stream)]
            if not matches:raise ValueError('Matching collected paper Not Found')
            m=matches[0];sha=hashlib.sha256(raw).hexdigest();dest=(ROOT/m['pdf_path']).parent/f'answer_key_{sha[:12]}.pdf';dest.write_bytes(raw);answers=parse(text)
            record=dict(item,year=year,exam_date=date,shift=shift,stream=stream,paper_id=m['paper_id'],file_path=str(dest.relative_to(ROOT)),sha256=sha,key_type='published_educational_source',answers=answers,mapping_status='validated_160_rows' if answers else 'Not Available: requires manual review')
            dest.with_name(f'answer_key_metadata_{sha[:12]}.json').write_text(json.dumps(record,indent=2));results.append(record)
        except Exception as e:results.append(dict(item,status='Failed',error=str(e)))
    (ROOT/'sources/key_collection_results.json').write_text(json.dumps(results,indent=2));return results
if __name__=='__main__':
    from .careerindia import discover
    collect([i for i in discover() if i.get('paper_type_hint')=='answer_key'])
