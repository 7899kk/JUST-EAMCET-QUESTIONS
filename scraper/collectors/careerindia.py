import re
from urllib.parse import urljoin
from .web import fetch,soup,ROOT
URL='https://www.careerindia.com/exam/ap-eamcet-eapcet-question-papers-e21.html'
def discover():
    result=[]
    for a in soup(fetch(URL)).select('a[href]'):
        t=a.get_text(' ',strip=True);u=urljoin(URL,a['href'])
        if not u.endswith('.pdf') or not re.search(r'20(?:1[5-9]|2[0-6])',t):continue
        stream='Agriculture_Pharmacy' if re.search(r'agriculture|medical',t,re.I) else 'Engineering'
        result.append({'source':'CareerIndia','source_url':URL,'download_url':u,'title':t,'stream':stream,'paper_type_hint':'answer_key' if 'Answer Key' in t and 'Question Paper' not in t else 'question_paper'})
    return result
