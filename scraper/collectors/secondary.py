import re
from urllib.parse import urljoin
from .web import fetch,soup

def discover():
    found=[]
    for year in [2015,2016,2017,2018]:
        u=f'https://upiqpbank.com/ap-eamcet/ap-eamcet-{year}-question-papers/'
        try:
            for a in soup(fetch(u)).select('a[href]'):
                if '.pdf' in a['href'].lower():found.append({'source':'UPI QP Bank','source_url':u,'download_url':a['href'],'title':a.get_text(' ',strip=True),'stream':'Agriculture_Pharmacy' if 'AGRICULTURE' in a['href'] else 'Engineering'})
        except Exception as e:found.append({'source':'UPI QP Bank','source_url':u,'status':'Discovery failed','error':str(e)})
    return found
