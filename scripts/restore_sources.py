"""Restore committed source evidence/cache archives for offline rebuilding."""
import tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main(names=None):
    for name in names or ['transcriptions','snapshots','vendor']:
        relative='app/frontend/vendor' if name=='vendor' else 'sources/'+name
        archive=ROOT/(relative+'.tar.gz');target=ROOT/relative
        if not archive.exists() or target.exists():continue
        with tarfile.open(archive) as tar:
            members=tar.getmembers()
            for m in members:
                p=Path(m.name)
                if p.is_absolute() or '..' in p.parts or not m.name.startswith(relative) or not(m.isfile() or m.isdir()):raise ValueError('Unsafe evidence archive member')
            tar.extractall(ROOT,members=members)
        print('Restored source evidence:',name)
if __name__=='__main__':main()
