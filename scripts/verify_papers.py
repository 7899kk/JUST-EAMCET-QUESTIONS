from common import load_questions
"""Verify originals, hashes, record references, answers and PDF region bounds."""
import hashlib,json,sys
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
def main():
    data=json.loads((ROOT/'database/metadata.json').read_text());questions=load_questions();errors=[];warnings=[];checked=[];docs={}
    for m in data['documents']:
        path=ROOT/m['pdf_path'];row={'paper_id':m['paper_id'],'pdf_path':m['pdf_path']}
        try:
            raw=path.read_bytes();assert raw.startswith(b'%PDF') and hashlib.sha256(raw).hexdigest()==m['sha256'],'PDF/hash mismatch'
            d=fitz.open(path);assert len(d)>0;d[0].get_pixmap(matrix=fitz.Matrix(.15,.15));docs[m['pdf_path']]=d
            assert (ROOT/m['metadata_path']).exists();assert m['year'] in range(2015,2027);assert m['shift'] in ['Shift_1','Shift_2',None]
            if m['exam_date']:assert m['exam_date'].startswith(str(m['year'])+'-')
            assert m['source_url'].startswith('https://') and m['download_url'].startswith(('https://','http://'))
            assert m.get('answer_key_status');row['status']='passed'
            if not m['exam_date'] or not m['shift']:warnings.append({'paper_id':m['paper_id'],'issue':'Date or shift Not Identified; original retained without invented metadata'})
        except Exception as e:errors.append({'paper_id':m['paper_id'],'error':str(e)});row['status']='failed'
        checked.append(row)
    key_count=0
    for fp in ROOT.glob('papers/**/answer_key_metadata*.json'):
        m=json.loads(fp.read_text())
        try:
            path=ROOT/m['file_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==m['sha256'];d=fitz.open(path);assert len(d)>0;d[0].get_pixmap(matrix=fitz.Matrix(.15,.15));key_count+=1
            assert m['source_url'] and m['download_url']
        except Exception as e:errors.append({'key_metadata':str(fp.relative_to(ROOT)),'error':str(e)})
    ids=set();numbers={}
    for q in questions:
        try:
            assert q['question_id'] not in ids,'Duplicate question ID';ids.add(q['question_id']);assert q['correct_answer'] in ['A','B','C','D',None]
            if q['correct_answer']:assert q['answer_provenance']['type']!='unavailable'
            numbers.setdefault(q['paper_id'],[]).append(q['question_number'])
            for a in q.get('question_images',[])+sum(q.get('option_images',{}).values(),[])+q.get('solution_images',[])+q.get('unassigned_images',[]):
                assert (ROOT/a['path']).exists(),'Broken asset reference'
                if a.get('render_type')=='pdf_region':
                    d=docs.get(a['path']) or fitz.open(ROOT/a['path']);assert 1<=a['pdf_page']<=len(d);box=fitz.Rect(a['bbox']);assert box.width>0 and box.height>0;assert d[a['pdf_page']-1].rect.contains(box),'Crop outside original PDF'
        except Exception as e:errors.append({'question_id':q['question_id'],'error':str(e)})
    for m in data['papers']:
        ns=numbers.get(m['paper_id'],[])
        if len(ns)!=len(set(ns)):errors.append({'paper_id':m['paper_id'],'error':'Repeated question number'})
        if len(ns)!=160:warnings.append({'paper_id':m['paper_id'],'issue':f'{len(ns)} indexed question records; boundaries/text may require manual review'})
        assert (ROOT/'app/data'/f"{m['paper_id']}.json").exists()
    years=[{'year':y,'status':'checked','papers':sum(m['year']==y for m in data['papers'])} for y in range(2015,2027)]
    result={'technical_status':'passed' if not errors else 'failed','years':years,'documents_checked':len(checked),'separate_keys_checked':key_count,'questions_checked':len(questions),'errors':errors,'warnings':warnings,'documents':checked,'limits':['Technical integrity is not proof of exhaustive public coverage.','Image regions preserve original notation; secondary text transcriptions have not all been manually proofread.','Scientific correctness of all source answers and published solutions is not independently certified.']}
    (ROOT/'reports/verification.json').write_text(json.dumps(result,indent=2));print(result['technical_status'],len(checked),'PDFs',len(questions),'questions',len(errors),'errors',len(warnings),'warnings');return bool(errors)
if __name__=='__main__':sys.exit(main())
