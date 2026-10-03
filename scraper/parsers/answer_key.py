"""Validate complete native-text answer tables; uncertain rows stay unavailable."""
import re

def parse(text):
    nums=re.findall(r'^\s*(\d+)\s*$',text,re.M)
    for width in [3,2]:
        rows=[]
        if len(nums)%width:continue
        for i in range(0,len(nums),width):
            group=nums[i:i+width];n=int(group[0]);a=int(group[-1]);qid=group[1] if width==3 else None
            if not 1<=n<=160 or not 1<=a<=4 or (qid and len(qid)<6):break
            rows.append({'question_number':n,'correct_answer':'ABCD'[a-1],**({'original_question_id':qid} if qid else {})})
        if len(rows)==160 and len({r['question_number'] for r in rows})==160:return rows
    return []
