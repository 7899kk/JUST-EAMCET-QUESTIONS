import re
from .web import fetch,soup
URLS=['https://www.collegedekho.com/news/ap-eamcet-2023-question-paper-answer-key-40433/','https://www.collegedekho.com/exam/ap-eamcet/previous-year-question-papers','https://www.collegedekho.com/news/ap-eamcet-2021-bpc-agriculture-question-paper-22427/']
def discover():
    items={}
    for u in URLS:
        s=soup(fetch(u))
        for a in s.select('a[href]'):
            v=a['href']
            if not v.startswith('https://static.collegedekho.com/') or not v.endswith('.pdf'):continue
            row=a.find_parent('tr');table=a.find_parent('table');heading=table.find_previous(['h2','h3','h4']) if table else a.find_previous(['h2','h3','h4'])
            label=' '.join(x.get_text(' ',strip=True) for x in [heading,row] if x is not None) or a.get_text(' ',strip=True)
            if not re.search(r'20(?:1[5-9]|2[0-6])',label) or re.search(r'model|sample',label,re.I):continue
            items[v]={'source':'CollegeDekho','source_url':u,'download_url':v,'title':label,'stream':'Agriculture_Pharmacy' if re.search(r'agriculture|BPC|BiPC|medical',label+' '+u,re.I) else 'Engineering'}
    return list(items.values())
