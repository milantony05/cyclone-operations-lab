# RAG design and trade-offs

The prototype ingests 11 provided technical PDFs. A production design must preserve document version, page, access policy and source checksum. Page extraction uses pypdf; insufficient text is audited. OCR, diagram interpretation and table reconstruction are follow-up ingestion stages.

Chunks contain up to 150 whitespace words with 30-word overlap and never cross pages. This preserves citation provenance but can split cross-page procedures. MiniLM supplies normalized embeddings. Exact inner-product FAISS search and BM25 each retrieve candidates; reciprocal rank fusion reranks them. FLAN-T5-small receives two excerpts within a 512-token input budget. A larger context model would improve coverage of multi-step procedures.

Low dense similarity triggers abstention. The application blocks a narrow set of safety-bypass and credential requests. Source content is treated as evidence, not executable instructions. This filter is not a comprehensive safety classifier. Lexical generation support cannot establish entailment or prevent every hallucination. Production needs a tested entailment verifier, adversarial document tests and operator review for safety-critical actions.

For ten times as many documents, deduplicate and hash documents, incrementally rebuild changed chunks, and use a versioned index. Exact search remains practical for a small corpus; benchmark before moving to approximate search or a hosted vector database. Keep document access filters before retrieval.

For 100+ users, separate ingestion workers, retrieval service and generation workers. Reuse shared loaded models, batch requests, queue with bounded capacity, set timeouts and apply backpressure. Cache repeated authorized queries by corpus version. Scale CPU retrieval independently from GPU generation. A small quantized open model and a single batched GPU worker can reduce cost; concurrency and cost claims need load testing.

Monitor recall@k and precision@k on human-labeled page references, abstention accuracy, citation validity, independently assessed answer faithfulness, p50/p95 latency, queue depth and cost per answer. Split evaluation questions from threshold tuning. Avoid reporting lexical overlap as factual accuracy.
