"""Rebuild the canonical archive, database, and local/portable app data."""
import csv,hashlib,json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scraper'))
from parsers.master_pdf import parse
from parsers.published_pdf import parse as parse_published

def rank(m):
    return 100 if m.get('answer_key_type')=='official_final' else 90 if m['source'].startswith('APSCHE') else 60 if m['source']=='SelfStudys' else 40 if m['source']=='UPI QP Bank' else 30

def merge_transcriptions(qs,m):
    indexed={q['question_number']:q for q in qs};conflicts=[]
    for fp in sorted((ROOT/'sources/transcriptions'/m['paper_id']).glob('*.json')):
        t=json.loads(fp.read_text());n=t['question_number'];q=indexed.get(n)
        if q is None:
            subject='Mathematics' if n<=80 else 'Physics' if n<=120 else 'Chemistry'
            q={'question_id':f"{m['paper_id']}_{subject}_q{n:03d}",'paper_id':m['paper_id'],'year':m['year'],'exam_date':m['exam_date'],'shift':m['shift'],'stream':m['stream'],'subject':subject,'subject_identification':'published Engineering stream question ordering (80 Mathematics, 40 Physics, 40 Chemistry)','question_number':n,'original_question_id':None,'question':None,'options':dict.fromkeys('ABCD'),'question_images':[],'option_images':{a:[] for a in 'ABCD'},'correct_answer':None,'answer_provenance':{'type':'unavailable'},'solution':None,'eapcet_shortcut':None,'banda_gurthu':None,'chapter':None,'topic':None,'source_paper':m['pdf_path'],'source_url':m['source_url'],'source':m['source'],'pdf_page':None,'extraction_status':'published_transcription'};indexed[n]=q
        if q['correct_answer'] and t.get('published_answer') and q['correct_answer']!=t['published_answer']:
            conflicts.append({'question_id':q['question_id'],'original_answer':q['correct_answer'],'educational_answer':t['published_answer'],'source_url':t['source_url']})
        q.update(question=t['question'],options=t['options'],transcription_source_url=t['source_url'],transcription_evidence=t['evidence_path'],transcription_status='published educational transcription; original PDF remains authoritative',transcription_has_external_diagrams=bool(t.get('image_urls')))
        if not q['correct_answer'] and t.get('published_answer'):q['correct_answer']=t['published_answer'];q['answer_provenance']={'type':'published_educational_source','source_url':t['source_url'],'method':'public validation response'}
        if t.get('solution') and len(t['solution'])>30:q['solution']=t['solution'];q['solution_provenance']={'type':'published_educational_source','source_url':t['source_url']}
    return sorted(indexed.values(),key=lambda q:q['question_number']),conflicts

def main():
    records=[]
    for mp in ROOT.glob('papers/**/metadata*.json'):
        m=json.loads(mp.read_text());m['metadata_path']=str(mp.relative_to(ROOT));records.append(m)
    records.sort(key=lambda m:(-rank(m),m['pdf_path']))
    all_docs=[];hashes={};signatures={};duplicate_records=[];groups={};answer_conflicts=[]
    for m in records:
        sha=m['sha256']
        if sha in hashes:
            kept=hashes[sha];kept.setdefault('additional_sources',[]).append({'source':m['source'],'source_url':m['source_url'],'download_url':m['download_url'],'sha256':sha})
            duplicate_records.append({'kind':'identical_file','sha256':sha,'retained':kept['pdf_path'],'duplicate':m['pdf_path'],'source_url':m['source_url'],'metadata_path':m['metadata_path']});continue
        qs,text=parse(ROOT/m['pdf_path'],m,ROOT)
        if not qs and len(text.strip())>500:qs,text=parse_published(ROOT/m['pdf_path'],m,ROOT)
        ids=[q['original_question_id'] for q in qs]
        signature=hashlib.sha256('|'.join(ids).encode()).hexdigest() if ids and all(ids) else None
        # Equal complete original IDs identify the same paper across source compression/watermarks.
        if signature and signature in signatures and len(qs)==len(signatures[signature][1]):
            kept,kqs=signatures[signature];kept.setdefault('additional_sources',[]).append({'source':m['source'],'source_url':m['source_url'],'download_url':m['download_url'],'sha256':sha,'content_signature':signature})
            diffs=[{'question_number':q['question_number'],'retained_answer':k['correct_answer'],'alternate_answer':q['correct_answer']} for k,q in zip(kqs,qs) if k['correct_answer']!=q['correct_answer']]
            duplicate_records.append({'kind':'same_original_question_ids','sha256':sha,'content_signature':signature,'retained':kept['pdf_path'],'duplicate':m['pdf_path'],'source_url':m['source_url'],'metadata_path':m['metadata_path'],'answer_differences':diffs});continue
        if signature:signatures[signature]=(m,qs)
        hashes[sha]=m;m['question_count']=len(qs);m['answers_mapped']=sum(q['correct_answer'] is not None for q in qs);m['content_signature']=signature;m['extraction_status']='original_regions_and_native_text' if qs else 'question_boundaries_not_identified';m['subjects']=sorted({q['subject'] for q in qs if q['subject']})
        m['text_path']=str(Path(m['pdf_path']).parent/(Path(m['pdf_path']).stem+'_text.txt'));(ROOT/m['text_path']).write_text(text)
        session=(m['year'],m['exam_date'],m['shift'],m['stream'])
        groups.setdefault(session,[]).append((m,qs));all_docs.append(m);print(m['paper_id'],len(qs),m['answers_mapped'],flush=True)
    papers=[];questions=[]
    for session,docs in sorted(groups.items(),key=lambda x:str(x[0])):
        # Prefer a combined paper; subject PDFs remain accessible as sourced attachments.
        primary=next(((m,qs) for m,qs in docs if not m.get('subject_scope') and qs),next(((m,qs) for m,qs in docs if not m.get('subject_scope')),docs[0]));m,qs=primary
        # Move transcripts between retained copies only for the same confirmed session.
        for alt,aqs in docs:
            source_dir=ROOT/'sources/transcriptions'/alt['paper_id'];target=ROOT/'sources/transcriptions'/m['paper_id']
            if source_dir.exists() and source_dir!=target:
                target.mkdir(parents=True,exist_ok=True)
                for fp in source_dir.glob('*.json'):
                    tf=target/fp.name
                    if not tf.exists():tf.write_text(fp.read_text())
        qs,conflicts=merge_transcriptions(qs,m);answer_conflicts+=conflicts
        # Supply subject-only questions where a combined original is not available.
        if not qs:
            merged={}
            for alt,aqs in docs:
                for q in aqs:
                    n=q['question_number']
                    if alt.get('subject_scope') and n<=40 and alt['subject_scope'] in ['Physics','Chemistry']:n+=80 if alt['subject_scope']=='Physics' else 120;q['question_number']=n
                    q['paper_id']=m['paper_id'];q['question_id']=f"{m['paper_id']}_{q['subject']}_q{n:03d}";merged.setdefault(n,q)
            qs=sorted(merged.values(),key=lambda q:q['question_number'])
        # Merge reliable published solution regions from matching subject documents.
        qlookup={q['question_number']:q for q in qs}
        for alt,aqs in docs:
            if alt is m:continue
            for aq in aqs:
                n=aq['question_number']
                if alt.get('subject_scope') in ['Physics','Chemistry'] and n<=40:n+=80 if alt['subject_scope']=='Physics' else 120
                target=qlookup.get(n)
                if target and aq.get('solution_images'):
                    target.setdefault('solution_images',[]).extend(aq['solution_images']);target['solution_provenance']=aq.get('solution_provenance')
        m['attachments']=[{'pdf_path':alt['pdf_path'],'source':alt['source'],'source_url':alt['source_url'],'download_url':alt['download_url'],'subject':alt.get('subject_scope'),'pages':alt['pages'],'description':'Additional published question/solution document','metadata_path':alt['metadata_path']} for alt,aqs in docs if alt is not m]
        m['question_count']=len(qs);m['answers_mapped']=sum(q['correct_answer'] is not None for q in qs);m['subjects']=sorted({q['subject'] for q in qs if q['subject']});m['extraction_status']='indexed' if qs else 'question_boundaries_not_identified'
        keys=[fp for fp in ROOT.glob('papers/**/answer_key_metadata*.json') if all(json.loads(fp.read_text()).get(k)==m.get(k) for k in ['year','exam_date','shift','stream'])]
        if keys:
            m['separate_answer_keys']=[json.loads(fp.read_text()) for fp in keys]
            key=json.loads(keys[0].read_text());mapping={a['question_number']:a for a in key['answers']};m['answer_key_pdf']=key['file_path'];m['separate_answer_key_source']=key['source_url']
            for q in qs:
                row=mapping.get(q['question_number'])
                if row and (not row.get('original_question_id') or row['original_question_id']==q.get('original_question_id')):
                    if q['correct_answer'] and q['correct_answer']!=row['correct_answer']:answer_conflicts.append({'question_id':q['question_id'],'original_answer':q['correct_answer'],'separate_key_answer':row['correct_answer'],'source_url':key['download_url']})
                    elif not q['correct_answer']:q['correct_answer']=row['correct_answer'];q['answer_provenance']={'type':key['key_type'],'method':'separate PDF table, matched original question ID where supplied','source_url':key['source_url'],'download_url':key['download_url'],'file_path':key['file_path']}
            m['answers_mapped']=sum(q['correct_answer'] is not None for q in qs);m['answer_key_status']='separate_pdf_and_embedded' if m['answer_key_status']!='Not Found' else 'separate_pdf';m['answer_key_type']=m['answer_key_type'] if m['answer_key_type']!='unavailable' else key['key_type']
        papers.append(m);questions+=qs
    curated=ROOT/'database/curated_solutions.json'
    if curated.exists():
        for edit in json.loads(curated.read_text()):
            matches=[q for q in questions if all(q.get(k)==edit[k] for k in ['year','exam_date','shift','subject','question_number'])]
            if len(matches)==1:matches[0].update(edit['fields'])
    for m in all_docs:
        m['additional_sources']=list({(s['source'],s['source_url'],s['download_url']):s for s in m.get('additional_sources',[])}.values())
        (ROOT/m['metadata_path']).write_text(json.dumps(m,indent=2,ensure_ascii=False))
    (ROOT/'app/data/catalog.json').write_text(json.dumps({'schema_version':2,'years':list(range(2015,2027)),'papers':papers},ensure_ascii=False))
    by_paper={m['paper_id']:[] for m in papers}
    for q in questions:by_paper[q['paper_id']].append(q)
    for old in (ROOT/'app/data').glob('*_*.json'):old.unlink()
    for pid,qs in by_paper.items():(ROOT/'app/data'/f'{pid}.json').write_text(json.dumps(qs,ensure_ascii=False))
    for name,obj in [('questions',questions),('answers',[{'question_id':q['question_id'],'correct_answer':q['correct_answer'],'provenance':q['answer_provenance']} for q in questions]),('solutions',[{'question_id':q['question_id'],'solution':q['solution'],'solution_images':q.get('solution_images',[]),'provenance':q.get('solution_provenance'),'eapcet_shortcut':q['eapcet_shortcut'],'banda_gurthu':q['banda_gurthu']} for q in questions if q['solution'] or q.get('solution_images')]),('metadata',{'schema_version':2,'years':list(range(2015,2027)),'papers':papers,'documents':all_docs,'question_count':len(questions)}),('duplicates',duplicate_records+(json.loads((ROOT/'sources/dedup_history.json').read_text()) if (ROOT/'sources/dedup_history.json').exists() else [])),('answer_conflicts',answer_conflicts)]:
        (ROOT/'database'/f'{name}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2 if name!='questions' else None))
    fields=['question_id','year','exam_date','shift','subject','question_number','question','options','correct_answer','solution','eapcet_shortcut','banda_gurthu','chapter','topic','source_paper','source_url','extraction_status']
    with (ROOT/'database/questions.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
        for q in questions:w.writerow({k:json.dumps(q[k],ensure_ascii=False) if isinstance(q[k],(dict,list)) else q[k] for k in fields})
    urls=[{'paper_id':m['paper_id'],'source':m['source'],'source_url':m['source_url'],'download_url':m['download_url'],'pdf_path':m['pdf_path'],'additional_sources':m.get('additional_sources',[]),'attachments':m.get('attachments',[])} for m in papers]
    (ROOT/'sources/source_urls.json').write_text(json.dumps(urls,indent=2))
    with (ROOT/'sources/source_index.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['paper_id','source','source_url','download_url','pdf_path'],extrasaction='ignore');w.writeheader();w.writerows(urls)
if __name__=='__main__':main()
