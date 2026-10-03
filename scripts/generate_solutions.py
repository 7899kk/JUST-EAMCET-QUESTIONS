"""Generate explanations only for explicitly supported, checked scientific patterns.
Unknown questions are never assigned filler explanations or invented answers.
"""
import json,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def solve(q):
    text=q.get('question') or ''
    m=re.search(r'An ideal gas is cooled from (\d+(?:\.\d+)?)\s*K to (\d+(?:\.\d+)?)\s*K',text,re.I)
    if not m or 'decrease' not in text.lower():return None
    t1,t2=map(float,m.groups())
    if not 0<t2<t1:return None
    ratio=math.sqrt(t2/t1);decrease=100*(1-ratio);match=[]
    for label,value in q['options'].items():
        nums=re.findall(r'\d+(?:\.\d+)?',value or '')
        if len(nums)==1 and '%' in (value or '') and math.isclose(float(nums[0]),decrease,abs_tol=.01):match.append(label)
    if len(match)!=1:return None
    answer=match[0]
    if q['correct_answer'] and q['correct_answer']!=answer:return None
    return {'solution':f'For the same ideal gas, u_rms=√(3RT/M). The molar mass stays constant, so u₂/u₁=√(T₂/T₁)=√({t2:g}/{t1:g})={ratio:.6g}. The fractional decrease is 1−{ratio:.6g}={1-ratio:.6g}; multiplying by 100 gives {decrease:.6g}%. Temperatures are in kelvin. Final answer: {answer}.','eapcet_shortcut':'Use the square root of the temperature ratio; the other constants cancel.','banda_gurthu':'Molecular speed follows √kelvin.','chapter':'States of Matter','topic':'Root-mean-square molecular speed','solution_provenance':{'type':'generated_educational_explanation','method':'checked ideal-gas rms-speed formula; numerical option and existing key agreement required'}}
def main():
    path=ROOT/'database/curated_solutions.json';edits=json.loads(path.read_text()) if path.exists() else [];keys={tuple(e[k] for k in ['year','exam_date','shift','subject','question_number']) for e in edits};count=0
    for q in json.loads((ROOT/'database/questions.json').read_text()):
        selector={k:q[k] for k in ['year','exam_date','shift','subject','question_number']};key=tuple(selector.values())
        if key in keys or q.get('solution'):continue
        fields=solve(q)
        if fields:edits.append(dict(selector,fields=fields));keys.add(key);count+=1
    path.write_text(json.dumps(edits,indent=2,ensure_ascii=False));print(count,'additional explanations generated with a checked supported formula')
if __name__=='__main__':main()
