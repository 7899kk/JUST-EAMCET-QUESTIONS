# AP EAMCET / AP EAPCET question archive

Original public papers for **2015–2026**, a question database, and a searchable browser. Engineering and Agriculture/Pharmacy papers are included where found. The repository contains the collected PDFs and data: cloning it or using GitHub **Code → Download ZIP** supplies the project. No ChatGPT attachment is needed.

**[Open the hosted browser](https://7899kk.github.io/JUST-EAMCET-QUESTIONS/)** · [Collection report](reports/collection_report.md) · [Missing data](reports/missing_papers.md) · [Verification](reports/verification_report.md)

This is a substantial collected archive, **not certified exhaustive coverage**. Every year was checked individually. Missing dates, shifts, answers, transcriptions and explanations are disclosed in the reports. No replacement questions or sessions are invented. Original PDF content remains authoritative when an educational transcription contains an error.

## Run locally

Python 3.10+ is recommended. From the repository root:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app/server.py --port 8000
```

Open **http://127.0.0.1:8000**. The existing database is ready to use; collection is optional. The local server itself uses only Python's standard library. Internet access is not required to browse collected PDFs, question regions or database search. External provenance links require internet access.

Choose **year → actual date → actual shift → stream/paper → question**. Undated originals appear under “Date Not Identified”; this indicates unresolved metadata, not an invented exam date. Previous/next buttons and the question selector provide navigation. Paper pages offer the original PDF, published solution attachments, separate keys where available, answers and source metadata.

Search uses AND between words, and matches question/option text, metadata, formula text, source and available explanations. Try `2024 physics` or `thermodynamics`. Combine year, date, shift, subject, chapter and topic filters. Chapter/topic filters contain only identified values. Image-only questions are searchable by their metadata and available raw native text, not by every word inside an image. Mathematical transcriptions can contain LaTeX source notation.

## Repository layout

- `papers/YEAR/DATE/SHIFT/STREAM/`: unchanged original PDFs, metadata and supplementary source documents. Unresolved fields use `Date_Not_Identified` / `Shift_Not_Identified`.
- `database/`: questions JSON/CSV, answers, explanations, metadata, SQLite search, duplicate and answer-conflict records.
- `app/frontend/`: browser and bundled PDF.js renderer; `app/data/`: portable catalog/question/search data.
- `sources/`: actual URLs, public-page snapshots, download outcomes, correction evidence and sourced transcription snippets.
- `reports/`: collection, missing-paper, duplicate and verification reports.
- `scraper/`: reusable source collectors and PDF parsers.
- `scripts/`: deterministic database, search, explanation, report and verification tools.

Some master PDFs encode the question and options as images. The database stores **original PDF page and crop coordinates**, and the browser renders those regions locally using bundled PDF.js. This preserves diagrams, Telugu, notation and options without copying or rewriting the original. Secondary text is labelled as a published educational transcription. Native publisher text is supplementary searchable text, not guaranteed complete mathematical text.

## Collect or rebuild

Start with SelfStudys and official APSCHE:

```bash
python scraper/scraper.py --sources selfstudys official --workers 3
```

Additional verified collectors:

```bash
python scraper/scraper.py --sources secondary vedantu careerindia collegedekho byjus --workers 3
python -m scraper.collectors.keys
```

For public Engineering transcriptions, after building the paper catalog:

```bash
cd scraper
python -m collectors.examsnet --workers 3
cd ..
```

Collectors retain successful originals and record failures; source websites may change, block access or remove files. The initial collection's per-source result files remain committed as evidence. Re-running a collector does not guarantee additional papers. Authentication, paywalls and blocked downloads are not bypassed.

Rebuild and verify:

```bash
python scripts/build_database.py
python scripts/detect_duplicates.py
# Optional removal of proven byte/content duplicates; retains URLs and key changes:
python scripts/detect_duplicates.py --prune
python scripts/rebuild.py
```

Or run individual checks:

```bash
python scripts/verify_papers.py
python scripts/generate_reports.py
python scripts/test_app.py
```

Browser testing requires `python -m pip install -r requirements-dev.txt` and `python -m playwright install chromium`, or a system Chromium installation. `test_app.py` starts its own temporary local server.

## Keys, explanations and provenance

Answers distinguish official final, official preliminary, published educational, derived and unavailable provenance. Green-option keys embedded in original master PDFs are extracted only when four option labels and one correct green label can be identified. Separate table keys are validated before mapping; original question IDs are matched when supplied. Conflicting source answers are recorded and do not silently replace the preferred key.

Detailed explanations are generated only for reviewed questions or explicitly supported checked formulas. Published explanation regions are preserved where available. Most questions still need independently reviewed explanations; unavailable fields remain null. Shortcuts and Banda Gurthu are included only where justified. Chapter/topic identification is conservative. Null means Not Available/Not Identified, not “no possible solution exists”.

Each original retains its actual download source, page URL, download URL and SHA-256. Exact-byte and complete original-question-ID duplicates are consolidated while preserving alternate sources. Distinct key versions and useful solution documents remain available. Original publisher documents retain their authorship; the code does not grant a new license over third-party papers.

## Hosting

GitHub Pages serves the same committed data through `.github/workflows/pages.yml`. It uses portable browser search when the Python API is unavailable. To export locally:

```bash
python scripts/export_static.py
python -m http.server 8080 --directory .static-build
```

Open http://127.0.0.1:8080. The repository is the authoritative archive even if hosted deployment is unavailable. All originals are ordinary Git files; no Git LFS or remote-only PDF storage is required.
