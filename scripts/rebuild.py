"""Rebuild all deterministic outputs from committed originals and provenance."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for script in ['build_database.py','generate_solutions.py','build_database.py','build_search.py','verify_papers.py','generate_reports.py']:
    subprocess.run([sys.executable,str(ROOT/'scripts'/script)],check=True,cwd=ROOT)
