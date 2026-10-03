import json,re,concurrent.futures
from urllib.parse import urljoin
from .web import fetch,soup,ROOT
BASE='https://www.vedantu.com'
def page(url):
    try:
        h=fetch(url);s=soup(h);sc=s.select_one('#__NEXT_DATA__');links=[];pdfs=[]
        if sc:
            j=json.loads(sc.get_text());cp=j.get('props',{}).get('pageProps',{}).get('initialState',{}).get('seo',{}).get('categoryPage',{});pdfs=cp.get('downloadableLinks') or []
        for a in s.select('a[href]'):
            u=urljoin(BASE,a['href'])
            if re.search(r'/exams/ap-eamcet-(?:maths-|physics-|chemistry-|biology-)?question-paper-(?:online-)?20(?:1[5-9]|2[0-6])',u):links.append(u)
        return url,links,[{'source':'Vedantu','source_url':url,'download_url':p,'title':(s.title.get_text() if s.title else url.rsplit('/',1)[-1]),'subject_scope':next((x.title() if x!='maths' else 'Mathematics' for x in ['maths','physics','chemistry','biology'] if f'-{x}-' in url),None),'stream':'Agriculture_Pharmacy' if '-biology-' in url else 'Engineering'} for p in pdfs if isinstance(p,str) and p.endswith('.pdf')]
    except Exception as e:return url,[],[{'source':'Vedantu','source_url':url,'status':'Discovery failed','error':str(e)}]
def discover():
    queue=[BASE+'/exams/ap-eamcet-question-paper']+[BASE+f'/exams/ap-eamcet-question-paper-{y}' for y in [2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026]];seen=set();papers=[];rounds=0
    while queue and rounds<4:
        urls=[u for u in dict.fromkeys(queue) if u not in seen];seen.update(urls);queue=[];rounds+=1
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            for u,links,found in ex.map(page,urls):queue+=links;papers+=found
        print('Vedantu discovered pages',len(seen),'PDFs',len(papers),flush=True)
    (ROOT/'sources/vedantu_discovered.json').write_text(json.dumps(papers,indent=2));return papers
