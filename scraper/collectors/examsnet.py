"""Public educational transcriptions; retain source snippets and key conflicts.
Transcriptions remain secondary to the original PDF. No hidden APIs or login.
"""
import argparse,concurrent.futures,copy,hashlib,json,re,time
from datetime import datetime
from urllib.parse import urljoin
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from .web import ROOT,fetch,soup
ARCHIVE='https://www.examsnet.com/exams/ap-eapcet-previous-question-papers-online'
def plain_math(tag):
    if tag is None:return None
    tag=copy.copy(tag)
    for node in list(tag.select('.katex')):
        a=node.select_one('annotation[encoding="application/x-tex"]')
        if a:node.replace_with('$'+a.get_text()+'$')
    for node in tag.select('script,style,input'):node.decompose()
    for br in tag.select('br'):br.replace_with('\n')
    return tag.get_text(' ',strip=True)
def discover():
    h=fetch(ARCHIVE);out=[]
    for a in soup(h).select('a[href]'):
        u=urljoin(ARCHIVE,a['href'])
        if '/test/ap-eapcet-' not in u:continue
        m=re.search(r'(\d{1,2})(?:th|st|nd|rd)?-(\w+)-(20\d{2})-shift-(\d)',u)
        if not m:continue
        date=datetime.strptime(f'{m[1]} {m[2][:3]} {m[3]}','%d %b %Y').strftime('%Y-%m-%d')
        out.append({'exam_date':date,'year':int(m[3]),'shift':'Shift_'+m[4],'source_url':u})
    (ROOT/'sources/examsnet_sessions.json').write_text(json.dumps(out,indent=2));return out

def collect_question(job):
    pid,url,n,answer=job;target=ROOT/'sources/transcriptions'/pid/f'q{n:03d}.json';target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():return json.loads(target.read_text())
    try:
        time.sleep(.15)
        r=requests.post(url,data={'answerid':str('ABCD'.index(answer)) if answer else '0'},timeout=(15,45));r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
        header=s.select_one('#question');match=re.search(r'Question\s*:\s*(\d+)\s+of\s+(\d+)',plain_math(header) or '')
        if not match or int(match[1])!=n:raise ValueError('Question number did not match requested page')
        q=s.select_one('#imagewrap');options=s.select('#answers li label > span');script=next((x.get_text() for x in s.select('script') if x.get_text().startswith('function v(){')),'');am=re.search(r'var c=\["([0-3])"\]',script);source_answer='ABCD'[int(am[1])] if am else None
        solution=s.select_one('#answerstatus');text=plain_math(q);opts={a:plain_math(v) for a,v in zip('ABCD',options)}
        if not text or len(opts)!=4:raise ValueError('Incomplete public transcription')
        # Some questions use diagrams instead of text. Keep source URL and do not claim completeness.
        images=[urljoin(url,i.get('src','')) for i in (q.select('img') if q else [])]
        data={'paper_id':pid,'question_number':n,'source_url':url,'question':text,'options':opts,'published_answer':source_answer,'original_answer':answer,'answer_agreement':source_answer==answer if answer and source_answer else None,'solution':plain_math(solution),'image_urls':images,'status':'downloaded','retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
        evidence='\n'.join(str(t) for t in [header,q,s.select_one('#answers'),solution] if t is not None)+'\n<!-- '+script+' -->'
        (target.with_suffix('.html')).write_text(evidence);data['evidence_path']=str(target.with_suffix('.html').relative_to(ROOT));target.write_text(json.dumps(data,ensure_ascii=False));return data
    except Exception as e:return {'paper_id':pid,'question_number':n,'source_url':url,'status':'Failed','error':str(e)}
def main(workers=3,years=None):
    sessions=discover();metadata=json.loads((ROOT/'database/metadata.json').read_text());questions=json.loads((ROOT/'database/questions.json').read_text());by={}
    for q in questions:by.setdefault(q['paper_id'],{})[q['question_number']]=q
    jobs=[]
    for session in sessions:
        if years and session['year'] not in years:continue
        matches=[p for p in metadata['papers'] if (p['exam_date'],p['shift'])==(session['exam_date'],session['shift']) and p['stream'] in ['Engineering','Not_Identified']]
        if len(matches)!=1:continue
        p=matches[0]
        for n in range(1,161):jobs.append((p['paper_id'],session['source_url']+'/'+str(n),n,by.get(p['paper_id'],{}).get(n,{}).get('correct_answer')))
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for i,r in enumerate(ex.map(collect_question,jobs),1):
            results.append(r)
            if i%40==0:print('Transcriptions',i,'/',len(jobs),'failed',sum(x['status']=='Failed' for x in results),flush=True)
    (ROOT/'sources/transcription_results.json').write_text(json.dumps([{k:v for k,v in r.items() if k not in ['question','options','solution']} for r in results],indent=2));print('Completed',len(results),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=3);p.add_argument('--years',type=int,nargs='*');a=p.parse_args();main(a.workers,a.years)
