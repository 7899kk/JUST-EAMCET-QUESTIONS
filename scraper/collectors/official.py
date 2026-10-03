import re
from .web import fetch
URL='https://cets.apsche.ap.gov.in/EAPCET/Eapcet/EAPCET_ExamPapers.aspx'
FINAL2025='https://cets.apsche.ap.gov.in/EAPCET25/Eapcet/EAPCET_ExamPapersFinal.aspx'
def discover():
    out=[]
    for url,year,version in [(URL,2026,'preliminary'),(FINAL2025,2025,'final')]:
        html=fetch(url)
        for u in dict.fromkeys(re.findall(r'https://[^\s\'\"]+QPK_[^\s\'\"]+\.pdf',html)):
            day=int(re.search(r'QPK_(\d+)',u)[1]);ag=day>=19 if year==2026 else day in [19,20]
            out.append({'source':'APSCHE (official)','source_url':url,'download_url':u,'title':str(year)+' '+u.rsplit('/',1)[-1],'stream':'Agriculture_Pharmacy' if ag else 'Engineering','key_version':version})
    return out
