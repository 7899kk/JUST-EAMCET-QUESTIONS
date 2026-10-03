"""Report byte/content duplicates; optional prune retains provenance and key changes."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main(prune=False):
    duplicates=json.loads((ROOT/'database/duplicates.json').read_text());history_path=ROOT/'sources/dedup_history.json';history=json.loads(history_path.read_text()) if history_path.exists() else []
    if prune:
        for d in duplicates:
            # Distinct answer versions remain available, even when question IDs match.
            if d.get('answer_differences'):d['pruned']=False;continue
            duplicate=ROOT/d['duplicate'];retained=ROOT/d['retained']
            if duplicate!=retained and retained.exists() and duplicate.exists():
                duplicate.unlink();mp=ROOT/d['metadata_path']
                if mp.exists():mp.unlink()
                text=duplicate.with_name(duplicate.stem+'_text.txt')
                if text.exists():text.unlink()
                d['pruned']=True
            history.append(d)
        unique={json.dumps((d['duplicate'],d['retained'])):d for d in history};history_path.write_text(json.dumps(list(unique.values()),indent=2))
    print(len(duplicates),'duplicate documents;',sum(bool(d.get('pruned')) for d in duplicates),'copies removed')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prune',action='store_true');a=p.parse_args();main(a.prune)
