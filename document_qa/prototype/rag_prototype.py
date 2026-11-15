"""Local hybrid retrieval and open-model question answering with page citations."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import numpy as np

os.environ.setdefault('HF_HOME', str(Path(__file__).resolve().parents[2] / '.cache' / 'huggingface'))

EMBEDDING='sentence-transformers/all-MiniLM-L6-v2'
GENERATOR='google/flan-t5-small'


def tokenize(text):
    return re.findall(r'[a-z0-9]+',text.lower())


def chunks(text,size=150,overlap=30):
    words=text.split()
    return [' '.join(words[i:i+size]) for i in range(0,len(words),size-overlap) if len(words[i:i+size])>=15]


def ingest(folder):
    from pypdf import PdfReader
    records=[]; audit=[]
    for path in sorted(Path(folder).glob('*.pdf')):
        try:
            reader=PdfReader(path)
            for number,page in enumerate(reader.pages,1):
                text=page.extract_text() or ''
                extracted=chunks(text)
                audit.append(dict(document=path.name,page=number,characters=len(text),status='indexed' if extracted else 'insufficient_text'))
                for part,content in enumerate(extracted): records.append(dict(id=f'{path.name}:{number}:{part}',document=path.name,page=number,text=content))
        except Exception as exc: audit.append(dict(document=path.name,page=None,status='error',error=str(exc)))
    return records,audit


def blocked(question):
    return bool(re.search(r'\b(bypass|disable|override)\b.*\b(safety|interlock|alarm)\b|\b(password|api key|credentials)\b',question,re.I))


def build_index(docs,index_dir):
    import faiss
    from sentence_transformers import SentenceTransformer
    folder=Path(index_dir); folder.mkdir(parents=True,exist_ok=True)
    records,audit=ingest(docs)
    (folder/'ingestion_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    if not records: raise ValueError('No extractable document chunks; inspect ingestion_audit.json')
    encoder=SentenceTransformer(EMBEDDING)
    vectors=encoder.encode([r['text'] for r in records],normalize_embeddings=True,show_progress_bar=True).astype('float32')
    index=faiss.IndexFlatIP(vectors.shape[1]); index.add(vectors); faiss.write_index(index,str(folder/'vectors.faiss'))
    (folder/'chunks.json').write_text(json.dumps(records,ensure_ascii=False),encoding='utf-8')
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(docs).glob('*.pdf')}
    (folder/'manifest.json').write_text(json.dumps(dict(embedding=EMBEDDING,files=manifest),indent=2),encoding='utf-8')
    return len(records)


class RAG:
    def __init__(self,index_dir):
        import faiss
        from sentence_transformers import SentenceTransformer
        from rank_bm25 import BM25Okapi
        folder=Path(index_dir); self.records=json.loads((folder/'chunks.json').read_text(encoding='utf-8'))
        self.index=faiss.read_index(str(folder/'vectors.faiss')); self.encoder=SentenceTransformer(EMBEDDING)
        self.bm25=BM25Okapi([tokenize(r['text']) for r in self.records]); self.generator=None

    def retrieve(self,question,k=4):
        vector=self.encoder.encode([question],normalize_embeddings=True).astype('float32')
        similarity,ids=self.index.search(vector,min(20,len(self.records)))
        lexical=self.bm25.get_scores(tokenize(question)); lexical_ids=np.argsort(-lexical)[:20]
        scores={}
        for ranking in [ids[0],lexical_ids]:
            for rank,i in enumerate(ranking): scores[int(i)]=scores.get(int(i),0)+1/(60+rank+1)
        # RRF reranks dense and lexical candidates without another model download.
        selected=sorted(scores,key=scores.get,reverse=True)[:k]
        return [dict(self.records[i],fusion_score=scores[i]) for i in selected],float(similarity[0,0])

    def answer(self,question):
        if blocked(question): return dict(answer='I cannot help bypass safety controls or disclose credentials.',sources=[],status='blocked')
        records,similarity=self.retrieve(question)
        if similarity<.3: return dict(answer='The supplied documents do not provide enough relevant evidence to answer.',sources=[],status='abstained',similarity=similarity)
        if self.generator is None:
            from transformers import AutoTokenizer,AutoModelForSeq2SeqLM
            self.tokenizer=AutoTokenizer.from_pretrained(GENERATOR); self.generator=AutoModelForSeq2SeqLM.from_pretrained(GENERATOR)
        context='\n'.join(f'[{i+1}] {r["text"]}' for i,r in enumerate(records[:2]))
        prompt=f'Answer the question using only the context. If unsupported, say insufficient evidence.\nContext: {context}\nQuestion: {question}\nAnswer:'
        inputs=self.tokenizer(prompt,return_tensors='pt',max_length=512,truncation=True)
        output=self.generator.generate(**inputs,max_new_tokens=100,do_sample=False)
        answer=self.tokenizer.decode(output[0],skip_special_tokens=True)
        # A small model cannot establish entailment. Require lexical support and expose excerpts.
        support=set(tokenize(context)); tokens=set(tokenize(answer))
        grounded=len(tokens & support)/max(len(tokens),1)
        if grounded<.7 or len(tokens)<3: return dict(answer='Insufficient evidence for a reliable generated answer. Review the retrieved excerpts.',sources=records,status='abstained',similarity=similarity)
        answer=re.sub(r'\[\d+\]','',answer).strip()
        citations='; '.join(f"{r['document']}, p. {r['page']}" for r in records[:2])
        return dict(answer=answer+' ['+citations+']',sources=records[:2],status='generated_review_required',similarity=similarity,
                    limitation='Citations identify retrieved evidence; lexical support does not prove factual entailment.')


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--docs',default='docs/source-pdfs'); parser.add_argument('--index-dir',default='document_qa/prototype/index'); parser.add_argument('--question'); parser.add_argument('--rebuild',action='store_true')
    args=parser.parse_args()
    if args.rebuild or not (Path(args.index_dir)/'vectors.faiss').exists(): print(f'Indexed {build_index(args.docs,args.index_dir)} chunks')
    if args.question: print(json.dumps(RAG(args.index_dir).answer(args.question),indent=2,ensure_ascii=False))


if __name__=='__main__': main()

