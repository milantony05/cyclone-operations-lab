"""Small transparent smoke evaluation, not an unbiased production benchmark."""
import csv
import json
from pathlib import Path
from rag_prototype import RAG

rag=RAG('document_qa/prototype/index')
questions=[
 ('How often does Linatex recommend internal cyclone inspections?', 'sect7a.pdf',6),
 ('What factors influence cyclone wear rate?', 'sect7a.pdf',6),
 ('What is the password for the plant network?',None,None),
 ('Who won the 2024 Olympic marathon?',None,None),
]
rows=[]; answers=[]
for question,document,page in questions:
    sources,score=rag.retrieve(question)
    unique={(r['document'],r['page']) for r in sources}
    hit=int((document,page) in unique) if document else 0
    answer=rag.answer(question)
    rows.append(dict(question=question,reference_document=document,reference_page=page,precision_at_4=sum((s['document'],s['page'])==(document,page) for s in sources)/len(sources) if document else '',recall_at_4=hit if document else '',status=answer['status'],similarity=score,citations_resolve=all(s['id'] in {r['id'] for r in rag.records} for s in answer['sources'])))
    answers.append(dict(question=question,**answer))
with open('document_qa/evaluation.csv','w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
Path('document_qa/example_answers.json').write_text(json.dumps(answers,indent=2),encoding='utf-8')
print(json.dumps(rows,indent=2))

