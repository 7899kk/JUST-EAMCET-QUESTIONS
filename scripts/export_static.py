from common import load_questions
"""Export runnable static data; unused alternative documents link to GitHub originals."""
import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'.static-build'
from restore_sources import main as restore
restore(['vendor'])
if DEST.exists():shutil.rmtree(DEST)
DEST.mkdir()
for folder in ['app/frontend','app/data','reports']:shutil.copytree(ROOT/folder,DEST/folder)
questions=load_questions();catalog=json.loads((ROOT/'app/data/catalog.json').read_text());needed={p['pdf_path'] for p in catalog['papers']}
for q in questions:
    for a in q.get('question_images',[])+sum(q.get('option_images',{}).values(),[])+q.get('solution_images',[])+q.get('unassigned_images',[]):needed.add(a['path'])
for fp in ROOT.glob('papers/**/answer_key_metadata*.json'):needed.add(json.loads(fp.read_text())['file_path'])
for fp in ROOT.glob('papers/**/*.json'):needed.add(str(fp.relative_to(ROOT)))
for path in sorted(needed):
    target=DEST/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,target)
omitted=[]
for p in catalog['papers']:
    for a in p.get('attachments',[]):
        if a['pdf_path'] not in needed:
            path=a['pdf_path'];a['pdf_path']='https://raw.githubusercontent.com/7899kk/JUST-EAMCET-QUESTIONS/main/'+path;omitted.append({'repository_path':path,'hosted_url':a['pdf_path']})
(DEST/'app/data/catalog.json').write_text(json.dumps(catalog,ensure_ascii=False));(DEST/'reports/hosting_manifest.json').write_text(json.dumps({'note':'All originals are committed. Unused alternative source documents use direct GitHub links on the hosted site to respect Pages size limits. Local browsing remains fully offline.','alternate_documents':omitted},indent=2))
(DEST/'database').mkdir();shutil.copy2(ROOT/'database/filter_values.json',DEST/'database/filter_values.json');shutil.copy2(ROOT/'index.html',DEST/'index.html');(DEST/'.nojekyll').touch()
print('Static archive:',DEST,'bytes:',sum(f.stat().st_size for f in DEST.rglob('*') if f.is_file()),'alternative GitHub links:',len(omitted))
