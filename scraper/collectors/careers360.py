import json,re,concurrent.futures,hashlib
from urllib.parse import urljoin
import fitz
from .web import ROOT,fetch,soup
URL='https://engineering.careers360.com/articles/ap-eamcet-sample-papers'
def collect_keys():
    html=fetch(URL);urls=list(dict.fromkeys(urljoin(URL,a['href']) for a in soup(html).select('a[href]') if '.pdf' in a['href'] and re.search(r'answer-key',a['href'],re.I) and 'user/register' not in a['href'] and 'capture-any-product' not in a['href']))
    metas=[(p,json.loads(p.read_text())) for p in ROOT.glob('papers/**/metadata*.json')];results=[]
    def one(u):
        try:
            raw=fetch(u,binary=True)
            if not raw.startswith(b'%PDF'):raise ValueError('Not a PDF')
            d=fitz.open(stream=raw,filetype='pdf');text='\n'.join(p.get_text() for p in d);yr=re.search(r'20(?:19|20)',text) or re.search(r'20(?:19|20)',u);year=int(yr[0])
            match=re.search(r'(\d{1,2})(?:st|nd|rd|th)?[ -]*(Sep|Sept|September|April|Apr)[ -]*(20\d{2})',text,re.I)
            if match:date=f'{int(match[3])}-{9 if match[2].lower().startswith("sep") else 4:02d}-{int(match[1]):02d}'
            else:
                m=re.search(r'(?:Date[: ]*)?(\d{2})-(\d{2})-(20\d{2})',text)
                if not m:raise ValueError('Key date Not Identified')
                date=f'{m[3]}-{m[2]}-{m[1]}'
            sh=re.search(r'(?:Session|Shift)[- :]*(1|2)',text,re.I);shift='Shift_'+sh[1] if sh else 'Shift_1' if re.search(r'morning|forenoon',u,re.I) else 'Shift_2' if re.search(r'afternoon',u,re.I) else None
            if not shift:raise ValueError('Key shift Not Identified')
            matches=[(p,m) for p,m in metas if (m['year'],m['exam_date'],m['shift'],m['stream'])==(year,date,shift,'Engineering')]
            if not matches:raise ValueError('Matching paper Not Found')
            path,m=matches[0];dest=path.parent/'answer_key.pdf';dest.write_bytes(raw)
            # 2020 tables contain qnumber, original qID, option; 2019 tables qnumber, option.
            nums=re.findall(r'^\s*(\d+)\s*$',text,re.M);triples=[];pairs=[]
            if year==2020:
                for i in range(0,len(nums)-2,3):
                    n,qid,a=nums[i:i+3]
                    if 1<=int(n)<=160 and len(qid)>=6 and 1<=int(a)<=4:triples.append({'question_number':int(n),'original_question_id':qid,'correct_answer':'ABCD'[int(a)-1]})
            else:
                for i in range(0,len(nums)-1,2):
                    n,a=nums[i:i+2]
                    if 1<=int(n)<=160 and 1<=int(a)<=4:pairs.append({'question_number':int(n),'correct_answer':'ABCD'[int(a)-1]})
            mapping=triples or pairs
            if len(mapping)!=160 or len({x['question_number'] for x in mapping})!=160:raise ValueError(f'Answer table validation failed ({len(mapping)} rows); original PDF retained')
            key={'paper_id':m['paper_id'],'year':year,'exam_date':date,'shift':shift,'source':'Careers360','source_url':URL,'download_url':u,'file_path':str(dest.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'key_type':'published_educational_source','document_description':'AP EAMCET Engineering preliminary key','answers':mapping}
            (path.parent/'answer_key_metadata.json').write_text(json.dumps(key,indent=2));print('Key',date,shift,160,flush=True);return key
        except Exception as e:return {'source':'Careers360','source_url':URL,'download_url':u,'status':'Failed','error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:results=list(ex.map(one,urls))
    (ROOT/'sources/separate_key_results.json').write_text(json.dumps(results,indent=2));return results
if __name__=='__main__':collect_keys()
