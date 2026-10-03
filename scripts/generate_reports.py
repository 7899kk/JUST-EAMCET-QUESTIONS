"""Produce candid coverage, missing-data, duplicate and integrity reports."""
import json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path,default=[]):
 p=ROOT/path;return json.loads(p.read_text()) if p.exists() else default
def save(name,lines):(ROOT/'reports'/name).write_text('\n'.join(lines)+'\n')
def main():
 data=read('database/metadata.json');papers=data['papers'];qs=read('database/questions.json');dups=read('database/duplicates.json');verification=read('reports/verification.json',{});counts=collections.Counter(m['source'] for m in data['documents']);keys=list(ROOT.glob('papers/**/answer_key_metadata*.json'))
 generated=sum(q.get('solution_provenance',{}).get('type')=='generated_educational_explanation' for q in qs);text=sum(bool(q['question']) for q in qs);sol=sum(bool(q['solution'] or q.get('solution_images')) for q in qs)
 lines=['# Collection report','', 'Checked on 2026-10-03 UTC. Scope: AP only, Engineering and Agriculture/Pharmacy. This is a collected archive with disclosed gaps, not a claim that every public document or every solution has been found.','',f'- Years checked: 12 (2015–2026)',f'- Canonical paper/session entries: {len(papers)}',f'- Retained question/solution PDF documents: {len(data["documents"])}',f'- Separate answer-key PDF files: {len(keys)}',f'- Indexed question records: {len(qs)}',f'- Records with published/curated searchable question text: {text}',f'- Mapped answers: {sum(bool(q["correct_answer"]) for q in qs)}',f'- Records with a text explanation or preserved published explanation region: {sol}',f'- Newly derived detailed explanations: {generated}',f'- Chapter/topic identified: {sum(bool(q["chapter"]) for q in qs)}','', 'Images and PDF regions are original material, not AI-rewritten questions. Raw publisher glyph extraction is supplementary search text. Null fields mean Not Available/Not Identified.','', '| Year | Checked | Papers | Actual dates discovered | Shifts discovered |','|---|---|---:|---|---|']
 for y in range(2015,2027):
  ps=[m for m in papers if m['year']==y];dates=sorted({m['exam_date'] for m in ps if m['exam_date']});shifts=sorted({m['shift'] for m in ps if m['shift']});lines.append(f'| {y} | checked | {len(ps)} | {", ".join(dates) or "Not Identified"} | {", ".join(shifts) or "Not Identified"} |')
 lines+=['','## Sources actually used','']+[f'- {s}: {n} retained PDF documents' for s,n in sorted(counts.items())]+['- Examsnet: public educational transcriptions and public answer validation; per-question source/evidence retained.','', 'SelfStudys was the first discovery source. Official 2025 final and 2026 preliminary master PDFs were downloaded from APSCHE. Other mirrors remain identified as their actual download sources. Sources/source_urls.json, source_index.csv, discovery/result JSON, HTML snapshots, and fetch_log.jsonl retain research evidence.','', '## Identity and key checks','', 'Original native headers take priority over website categories. The corrected 2018 SelfStudys mislabel is recorded in sources/metadata_corrections.json. Rasterized 2024 headers were read and cross-checked; evidence is in sources/2024_header_verification.json. Final 2025 official keys take priority over preliminary/educational keys. Answer conflicts are recorded in database/answer_conflicts.json.']
 save('collection_report.md',lines)
 missing=['# Missing papers and data','', 'Status: Not Found / Not Available is used explicitly below. An absent record is not evidence that a session never existed. No expected dates or shifts are invented. Public-site blocking and stale links limit this collection.','', '## Years','']+[f'- {y}: checked; '+('papers collected' if any(m['year']==y for m in papers) else 'Status: Not Found') for y in range(2015,2027)]
 missing+=['','## Missing metadata, extraction, answers, solutions','', '| Paper | Missing / incomplete fields |','|---|---|']
 for m in papers:
  qq=[q for q in qs if q['paper_id']==m['paper_id']];issues=[]
  if not m['exam_date']:issues.append('Actual date: Not Identified')
  if not m['shift']:issues.append('Actual shift: Not Identified')
  if len(qq)!=160:issues.append(f'Question boundaries: {len(qq)} indexed; remaining Not Available')
  na=sum(not q['correct_answer'] for q in qq);ns=sum(not(q['solution'] or q.get('solution_images')) for q in qq);nt=sum(not q['question'] for q in qq)
  if na:issues.append(f'{na} answers Not Found')
  if ns:issues.append(f'{ns} detailed solutions Not Available')
  if nt:issues.append(f'{nt} searchable full-text transcriptions Not Available; originals retained')
  if issues:missing.append(f'| {m["paper_id"]} | {"; ".join(issues)} |')
 missing+=['','## Failed discovery/download/transcription attempts','']
 seen=set()
 for fp in sorted((ROOT/'sources').glob('*results.json')):
  obj=json.loads(fp.read_text())
  for item in obj if isinstance(obj,list) else []:
   if item.get('status') in ['Failed','Discovery failed']:
    key=(item.get('source_url') or item.get('download_url'),item.get('question_number'),item.get('error'))
    if key in seen:continue
    seen.add(key);missing.append(f'- Status: Not Found — {key[0]}'+(f' question {key[1]}' if key[1] else '')+f' — {key[2]} ({fp.name})')
 for item in read('sources/year_checks.json'):
  if item['status']!='checked':missing.append(f'- {item["year"]} search-engine attempt failed: {item.get("error")}. Year was separately checked in source archives and collected papers.')
 missing+=['','## Known limitations','', '- 2026 official final answer-key publication: Not Found at the checked final endpoint; available official preliminary keys retained.','- Sakshi returned HTTP 403 at checked AP archive URLs; no papers are claimed from Sakshi. Historical guessed official endpoints returned 404.','- An Examsnet medical link labelled 2024 Shift 4 was excluded: actual session identity could not be verified.','- No independent complete official historical session register was obtained. Missing dates/shifts beyond advertised source leads remain Not Identified.','- Shortcuts, Banda Gurthu, chapter and topic are Not Available/Not Identified unless a reviewed explanation supplies them.','- Published transcriptions can contain formula errors. The original PDF is authoritative; external diagrams in secondary text are flagged.']
 save('missing_papers.md',missing)
 lines=['# Duplicate report','',f'{len(dups)} duplicate document matches recorded. Exact SHA-256 and complete ordered original-question-ID sequences are used. Same session alone is not grounds for deleting a file; distinct key versions and published solution documents are retained.','', '| Match | Retained copy | Duplicate copy | Source | Action |','|---|---|---|---|---|']
 for d in dups:lines.append(f'| {d["kind"]} | {d["retained"]} | {d["duplicate"]} | {d["source_url"]} | {"removed; source preserved" if d.get("pruned") else "retained / pending review"} |')
 lines+=['','Full hashes, content signatures, alternate URLs and answer differences: database/duplicates.json and sources/dedup_history.json.']
 save('duplicate_report.md',lines)
 app=read('reports/application_verification.json',{})
 lines=['# Verification report','',f'Technical integrity: **{verification.get("technical_status","Not run")}**.',f'PDF documents checked: {verification.get("documents_checked",0)}. Question records checked: {verification.get("questions_checked",0)}.', '', 'Checks: original PDF signature/hash, PyMuPDF open/render, metadata presence, allowed year/shift, date/year agreement, source URLs, unique question IDs/numbers, answer provenance, local asset links, PDF region bounds and app data files.','', 'Every year 2015–2026 was individually checked in the collected source/archive results. This is a technical and research check, not certification of exhaustive public coverage or of every source answer.','', f'Application verification: {app.get("status","Not run")}. See application_verification.json for checks.','', '## Errors','',json.dumps(verification.get('errors',[]),indent=2),'','## Items requiring review','']+[f'- {x["paper_id"]}: {x["issue"]}' for x in verification.get('warnings',[])]+['','Full structured results: verification.json. Original prompt/option regions remain accessible even where a reliable text transcription is unavailable.']
 save('verification_report.md',lines)
 print('Reports generated:',len(papers),'papers',len(qs),'records')
if __name__=='__main__':main()
