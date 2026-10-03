"""Local archive browser and combined-filter full-text search (no cloud services)."""
import argparse,json,mimetypes,sqlite3
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        url=urlsplit(self.path)
        if url.path=='/':
            self.send_response(302);self.send_header('Location','/app/frontend/index.html');self.end_headers();return
        if url.path=='/api/search':
            params=parse_qs(url.query);db=sqlite3.connect(ROOT/'database/search.sqlite');db.row_factory=sqlite3.Row
            sql='SELECT q.* FROM questions q WHERE 1=1';args=[]
            terms=params.get('q',[''])[0].split()
            for term in terms:sql+=' AND q.search_text LIKE ? ESCAPE "\\"';args.append('%'+term.lower().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%')
            for field in ['year','exam_date','shift','subject','chapter','topic','paper_id']:
                val=params.get(field,[''])[0]
                if val:sql+=f' AND q.{field}=?';args.append(val)
            count=db.execute('SELECT COUNT(*) FROM ('+sql+')',args).fetchone()[0];offset=max(0,int(params.get('offset',['0'])[0]));limit=min(100,max(1,int(params.get('limit',['40'])[0])))
            rows=db.execute(sql+' ORDER BY year DESC,exam_date,shift,question_number LIMIT ? OFFSET ?',args+[limit,offset]).fetchall();db.close()
            payload=json.dumps({'total':count,'results':[{k:r[k] for k in r.keys() if k!='search_text'} for r in rows]},ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
        # Do not expose git internals, hidden files, or parent traversal.
        parts=Path(url.path).parts
        if any(p.startswith('.') for p in parts) or '..' in parts:self.send_error(403);return
        super().do_GET()
    def list_directory(self,path):self.send_error(403,'Open the archive browser at /');return None
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);p.add_argument('--host',default='127.0.0.1');a=p.parse_args();print(f'Archive browser: http://{a.host}:{a.port}',flush=True);ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
