"""Exercise actual navigation, question rendering and combined search in Chromium."""
import json,os,shutil,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 proc=subprocess.Popen([sys.executable,str(ROOT/'app/server.py'),'--port','8765'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);checks=[];errors=[]
 try:
  for _ in range(40):
   try:urllib.request.urlopen('http://127.0.0.1:8765/app/data/catalog.json',timeout=1);break
   except Exception:time.sleep(.1)
  catalog=json.loads((ROOT/'app/data/catalog.json').read_text())
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=shutil.which('chromium') or None,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8765/');page.wait_for_selector('.year');assert page.locator('.year').count()==12
   for year in range(2015,2027):
    page.locator(f'.year[data-year="{year}"]').click();page.wait_for_function('(y)=>location.hash=="#year="+y',arg=year);assert page.locator('#browse .card').count()>0
   checks.append('All 12 year buttons and real date cards work')
   for p in catalog['papers']:
    for route in [f"#year={p['year']}&date={p['exam_date'] or 'unknown'}",f"#year={p['year']}&date={p['exam_date'] or 'unknown'}&shift={p['shift'] or 'unknown'}"]:
     page.goto('http://127.0.0.1:8765/app/frontend/index.html'+route);page.wait_for_selector('#browse .card')
    for path in [p['pdf_path'],p['metadata_path'],f"app/data/{p['paper_id']}.json"]:
     response=page.request.head('http://127.0.0.1:8765/'+path);assert response.status==200,(path,response.status)
   checks.append(f"All actual date/shift routes and {len(catalog['papers'])} canonical PDF/metadata/question links work")
   p=next(p for p in catalog['papers'] if p['year']==2026 and p['exam_date']=='2026-05-12' and p['shift']=='Shift_1');page.goto('http://127.0.0.1:8765/app/frontend/index.html#paper='+p['paper_id']);page.wait_for_selector('#qcontent .question');page.wait_for_selector('#qcontent figure canvas',timeout=60000);assert 'Question 1' in page.locator('#qcontent').inner_text();page.locator('#next').click();page.wait_for_function('()=>document.querySelector("#qcontent h3").textContent=="Question 2"');page.locator('#prev').click();page.wait_for_function('()=>document.querySelector("#qcontent h3").textContent=="Question 1"');page.locator('#viewanswers').click();assert page.locator('#answerlist a').count()==160
   checks.append('Original PDF-region rendering, question next/previous and 160-answer navigation work')
   page.locator('#query').fill('2026 physics');page.locator('#f_year').select_option('2026');page.locator('#f_subject').select_option('Physics');page.locator('#f_exam_date').select_option('2026-05-12');page.locator('#f_shift').select_option('Shift_1');page.locator('#searchform').evaluate('(form)=>form.requestSubmit()');page.wait_for_selector('#results .result');assert '2026' in page.locator('#results .result').first.inner_text() and 'Physics' in page.locator('#results .result').first.inner_text()
   page.locator('#query').fill('');page.locator('#f_subject').select_option('Mathematics');page.locator('#f_chapter').select_option('Functions');page.locator('#f_topic').select_option('Greatest integer function');page.locator('#searchform').evaluate('(form)=>form.requestSubmit()');page.wait_for_function('()=>document.querySelector("#results").textContent.includes("matching questions")&&!document.querySelector("#results").textContent.includes("Searching")');assert page.locator('#results .result').count()>0
   checks.append('Full-text year/subject search and combined year/subject/chapter/topic filters work')
   page.route('**/api/search?*',lambda route:route.fulfill(status=404,body='static mode'));page.locator('#reset').click();page.locator('#query').fill('2026 physics');page.locator('#searchform').evaluate('(form)=>form.requestSubmit()');page.wait_for_selector('#results .result',timeout=60000);checks.append('Portable JSON search works when the Python API is unavailable')
   (ROOT/'reports/screenshots').mkdir(exist_ok=True);page.goto('http://127.0.0.1:8765/');page.wait_for_selector('.year');page.screenshot(path=str(ROOT/'reports/screenshots/home.png'),full_page=True);browser.close()
  assert not errors,errors
  result={'status':'passed','checks':checks,'errors':errors}
 except Exception as e:
  result={'status':'failed','checks':checks,'errors':errors+[str(e)]}
 finally:proc.terminate();proc.wait()
 (ROOT/'reports/application_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));return result['status']!='passed'
if __name__=='__main__':sys.exit(main())
