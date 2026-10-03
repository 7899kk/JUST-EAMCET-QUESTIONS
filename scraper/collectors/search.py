"""Discovery through public search result pages; results are leads, not proof."""
import json,time
from urllib.parse import urlencode
from .web import fetch,soup,ROOT

def check_years():
    checks=[]
    for year in range(2015,2027):
        u='https://search.brave.com/search?'+urlencode({'q':f'AP EAMCET EAPCET {year} question papers shift PDF engineering agriculture'})
        try:
            s=soup(fetch(u));links=[]
            for a in s.select('a[href]'):
                h=a['href'];t=a.get_text(' ',strip=True)
                if h.startswith('http') and any(x in h for x in ['eamcet','eapcet',f'{year}']) and 'search.brave.com' not in h:links.append({'url':h,'title':t[:300]})
            checks.append({'year':year,'status':'checked','query_url':u,'leads':links,'checked_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
            print(year,len(links),flush=True)
        except Exception as e:checks.append({'year':year,'status':'Search failed','query_url':u,'error':str(e)})
        (ROOT/'sources/year_checks.json').write_text(json.dumps(checks,indent=2))
    return checks
