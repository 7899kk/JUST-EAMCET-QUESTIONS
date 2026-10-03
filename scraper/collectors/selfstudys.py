import re
from urllib.parse import urljoin
from .web import fetch,soup
BASE='https://www.selfstudys.com'
ARCHIVE=BASE+'/books/ap-eamcet-previous-year-paper'
def discover():
    html=fetch(ARCHIVE); pages={ARCHIVE:html};links={}
    for a in soup(html).select('a[href]'):
        h=urljoin(BASE,a['href'])
        if re.search(r'/year-wise/20(?:1[5-9]|2[0-6])/\d+$',h):pages.setdefault(h,None)
    for u,h in list(pages.items()):
        if h is None:
            try:pages[u]=fetch(u)
            except Exception:continue
        for a in soup(pages[u]).select('a[href]'):
            v=urljoin(BASE,a['href']).replace('/advance-pdf-viewer/','/books/')
            if re.search(r'/year-wise/20(?:1[5-9]|2[0-6])/[^/]+/\d+$',v):links[v]=a.get_text(' ',strip=True) or v.split('/')[-2].replace('-',' ')
    return [{'source':'SelfStudys','source_url':u,'title':t} for u,t in links.items()]
def resolve(paper):
    u=paper['source_url'].replace('/books/','/advance-pdf-viewer/');h=fetch(u)
    links=re.findall(r'https://www\.selfstudys\.com/sitepdfs/[A-Za-z0-9]+',h)
    if not links:raise ValueError('Public PDF URL Not Found')
    return dict(paper,download_url=links[0],viewer_url=u)
