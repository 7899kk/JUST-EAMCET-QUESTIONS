import re
from .web import fetch,soup
URL='https://byjus.com/jee/ap-eamcet-question-paper/'
def discover():
    return [{'source':"BYJU'S",'source_url':URL,'download_url':a['href'],'title':a.get_text(' ',strip=True)+' '+a['href'].rsplit('/',1)[-1]} for a in soup(fetch(URL)).select('a[href]') if a['href'].endswith('.pdf') and re.search(r'AP[-_]EAMCET',a['href'],re.I)]
