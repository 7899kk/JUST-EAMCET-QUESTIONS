"""Read/write the complete question database in manageable JSON partitions."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_questions():
    data=json.loads((ROOT/'database/questions.json').read_text())
    if isinstance(data,list):return data
    if data.get('storage')!='partitioned_json':raise ValueError('Unsupported question database format')
    result=[]
    for part in data['parts']:
        p=ROOT/'database'/part['path'];raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=part['sha256']:raise ValueError('Question partition hash differs: '+part['path'])
        result.extend(json.loads(raw))
    if len(result)!=data['question_count']:raise ValueError('Question partition count differs')
    return result

def save_questions(questions):
    folder=ROOT/'database/questions';folder.mkdir(exist_ok=True);parts=[]
    for old in folder.glob('part_*.json'):old.unlink()
    for i in range(0,len(questions),500):
        path=folder/f'part_{i//500+1:03d}.json';chunk=questions[i:i+500];raw=json.dumps(chunk,ensure_ascii=False,separators=(',',':')).encode();path.write_bytes(raw);parts.append({'path':str(path.relative_to(ROOT/'database')),'question_count':len(chunk),'sha256':hashlib.sha256(raw).hexdigest()})
    (ROOT/'database/questions.json').write_text(json.dumps({'schema_version':3,'storage':'partitioned_json','question_count':len(questions),'note':'All complete question records are in the listed JSON files. scripts/common.py loads and verifies the whole database.','parts':parts},indent=2))
