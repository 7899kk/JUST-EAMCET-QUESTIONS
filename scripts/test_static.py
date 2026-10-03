"""Verify compressed bundles and GitHub Pages-style repository-prefix hosting."""
import functools,json,shutil,subprocess,sys,tempfile,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 sys.path.insert(0,str(ROOT/'scripts'));import restore_sources
 checks=[];errors=[]
 try:
  with tempfile.TemporaryDirectory() as tmp:
   temp=Path(tmp)
   for rel in ['app/frontend/vendor.tar.gz','sources/transcriptions.tar.gz','sources/snapshots.tar.gz']:
    dest=temp/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest)
   restore_sources.ROOT=temp;restore_sources.main();assert (temp/'app/frontend/vendor/pdf.min.mjs').exists();assert (temp/'app/frontend/vendor/katex/katex.min.js').exists();assert len(list((temp/'sources/transcriptions').glob('*/*.json')))>=9000
  restore_sources.ROOT=ROOT;checks.append('Committed evidence and offline renderer archives restore without network access')
  subprocess.run([sys.executable,str(ROOT/'scripts/export_static.py')],check=True,cwd=ROOT)
  prefix='/JUST-EAMCET-QUESTIONS'
  class Handler(SimpleHTTPRequestHandler):
   def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'.static-build'),**kw)
   def do_GET(self):
    if self.path.startswith(prefix+'/'):self.path=self.path[len(prefix):]
    super().do_GET()
   def log_message(self,*args):pass
  server=ThreadingHTTPServer(('127.0.0.1',8766),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=shutil.which('chromium') or None,args=['--no-sandbox']);page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)));url='http://127.0.0.1:8766'+prefix+'/';page.goto(url);page.wait_for_selector('.year');assert page.locator('.year').count()==12
    catalog=json.loads((ROOT/'app/data/catalog.json').read_text());p=next(p for p in catalog['papers'] if p['year']==2026 and p['exam_date']=='2026-05-12' and p['shift']=='Shift_1');page.goto(url+'app/frontend/index.html#paper='+p['paper_id']);page.wait_for_selector('#qcontent figure canvas',timeout=60000);page.wait_for_selector('#qcontent .katex',timeout=10000)
    checks.append('Repository-prefix routes, original PDF regions and offline mathematical typesetting work')
    page.locator('#query').fill('2026 physics');page.locator('#f_subject').select_option('Physics');page.locator('#searchform').evaluate('(form)=>form.requestSubmit()');page.wait_for_selector('#results .result',timeout=60000);assert 'Physics' in page.locator('#results .result').first.inner_text();checks.append('Full-text search works on a static server with no API')
    (ROOT/'reports/screenshots').mkdir(exist_ok=True);page.locator('#qcontent').screenshot(path=str(ROOT/'reports/screenshots/question.png'));browser.close()
   assert not errors,errors
  finally:server.shutdown();server.server_close()
  result={'status':'passed','checks':checks,'errors':errors}
 except Exception as e:result={'status':'failed','checks':checks,'errors':errors+[str(e)]}
 (ROOT/'reports/static_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));return result['status']!='passed'
if __name__=='__main__':sys.exit(main())
