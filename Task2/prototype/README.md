# Local RAG prototype

From the repository root, install `requirements.txt`, then run:

```sh
python Task2/prototype/rag_prototype.py --docs docs/source-pdfs --rebuild
python Task2/prototype/rag_prototype.py --question "What inspections are required before startup?"
```

The first run downloads `sentence-transformers/all-MiniLM-L6-v2` and `google/flan-t5-small` from Hugging Face. No paid API or API key is required. Model files are cached by Hugging Face. Allow sufficient disk space for PyTorch and the models. CPU execution is supported.

The supplied 11 PDFs produce 382 chunks. Extraction audit records pages with insufficient text and parsing errors. Scanned pages need an OCR preprocessing stage; this prototype explicitly reports them instead of silently claiming coverage. Rebuild after changing documents. Local FAISS index and JSON metadata are reused otherwise.

Responses expose source document, one-based page number and exact retrieved excerpts. A similarity threshold of 0.30 is a heuristic, not a calibrated confidence score. Lexical overlap is only a weak generation check and does not establish entailment. Generated answers require review against excerpts. The small model is chosen for reproducible CPU operation, not production answer quality.

PDFs are versioned in `docs/source-pdfs` for reproducibility. The generated index is excluded. Use `--docs` and `--index-dir` to select other local paths.
