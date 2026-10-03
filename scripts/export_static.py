"""Publish the already-collected archive as a self-contained static site."""
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'.static-build'
if DEST.exists():shutil.rmtree(DEST)
DEST.mkdir()
for folder in ['app/frontend','app/data','papers','reports']:
    shutil.copytree(ROOT/folder,DEST/folder)
(DEST/'database').mkdir();shutil.copy2(ROOT/'database/filter_values.json',DEST/'database/filter_values.json');shutil.copy2(ROOT/'index.html',DEST/'index.html');(DEST/'.nojekyll').touch()
print('Static archive:',DEST,'bytes:',sum(f.stat().st_size for f in DEST.rglob('*') if f.is_file()))
