"""Public-page fetches with evidence snapshots and bounded timeouts."""
import hashlib,json,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
LOG=ROOT/'sources/fetch_log.jsonl'
def fetch(url,binary=False):
    started=time.time(); status=None
    try:
        r=requests.get(url,timeout=(15,90),headers={'User-Agent':'AP-paper-archive/1.0 (public educational archive)'})
        status=r.status_code;r.raise_for_status()
        if not binary:
            path=ROOT/'sources/snapshots'/f'{hashlib.sha256(url.encode()).hexdigest()[:16]}.html'
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(r.text)
        return r.content if binary else r.text
    finally:
        LOG.parent.mkdir(parents=True,exist_ok=True)
        with LOG.open('a') as f:f.write(json.dumps({'url':url,'http_status':status,'checked_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'elapsed_seconds':round(time.time()-started,2)})+'\n')
def soup(html):return BeautifulSoup(html,'html.parser')
