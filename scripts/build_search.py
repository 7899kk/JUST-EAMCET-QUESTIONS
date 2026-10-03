import json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    db=sqlite3.connect(ROOT/'database/search.sqlite');db.execute('DROP TABLE IF EXISTS questions');db.execute('CREATE TABLE questions(question_id TEXT PRIMARY KEY,paper_id TEXT,year INTEGER,exam_date TEXT,shift TEXT,subject TEXT,chapter TEXT,topic TEXT,question_number INTEGER,question TEXT,source TEXT,extraction_status TEXT,search_text TEXT)')
    qs=json.loads((ROOT/'database/questions.json').read_text())
    cols=['question_id','paper_id','year','exam_date','shift','subject','chapter','topic','question_number','question','source','extraction_status']
    portable=[]
    for q in qs:
        searchable=' '.join(str(q.get(k) or '') for k in ['question','options','year','exam_date','shift','subject','chapter','topic','question_number','source','source_url','solution','eapcet_shortcut','banda_gurthu','searchable_text'])
        db.execute('INSERT INTO questions VALUES('+','.join('?' for _ in range(13))+')',[q.get(k) for k in cols]+[searchable.lower()])
        portable.append({**{k:q.get(k) for k in cols},'search_text':searchable.lower()})
    (ROOT/'database/filter_values.json').write_text(json.dumps({k:sorted({q[k] for q in qs if q.get(k)}) for k in ['chapter','topic']}))
    (ROOT/'app/data/search_index.json').write_text(json.dumps(portable,ensure_ascii=False))
    db.execute('CREATE INDEX combined_filters ON questions(year,exam_date,shift,subject)');db.commit();db.close();print('Search index:',len(qs),'questions')
if __name__=='__main__':main()
