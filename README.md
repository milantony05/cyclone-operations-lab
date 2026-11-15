# Cyclone Operations Lab

**A reproducible sensor analysis and cited technical-document Q&A demo.** Milan Tony's data science take-home submission combines an executable notebook, a Python analysis pipeline, an interactive dashboard, a local open-model RAG prototype, and an eight-slide presentation.

![2018 cyclone sensor history with inferred downtime](Task1/plots/full_year.png)

## Start here

| Goal | Open or run |
| --- | --- |
| Explore sensor analysis | `notebooks/task1_analysis.ipynb` |
| Explore PDF retrieval and answers | `notebooks/task2_rag.ipynb` |
| Launch the visual demo | `streamlit run dashboard/app.py` |
| Rebuild sensor outputs | `python Task1/task1_analysis.py` then `python -m Task1.enrich_report` |
| Index the supplied manuals | `python Task2/prototype/rag_prototype.py --rebuild` |
| Ask a cited question | `python Task2/prototype/rag_prototype.py --question "How often does Linatex recommend internal cyclone inspections?"` |
| View the submission story | `presentations/Final_Presentation.pptx` |

## Repository map

```text
docs/                     Assignment brief, original workbook, 11 source PDFs
notebooks/                Executed Task 1 and Task 2 notebooks
dashboard/                Streamlit visual explorer and document Q&A demo
Task1/                    Analysis code, audit, CSVs, case notes, plots
Task2/                    RAG design, prototype, evaluation, diagram
tests/                    Deterministic data and retrieval checks
presentations/            Eight-slide final presentation
reports/                  Verification report
package_submission.py     Builds the submission ZIP
```

Original inputs are versioned in `docs/`. The FAISS index, model weights, virtual environment, and generated ZIP can be rebuilt locally.

## Setup

Use Python 3.12. In PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python Task1/task1_analysis.py
python -m Task1.enrich_report
python Task2/prototype/rag_prototype.py --rebuild
streamlit run dashboard/app.py
```

On macOS/Linux, create the environment with `python3.12 -m venv .venv` and activate with `source .venv/bin/activate`. The first RAG run downloads `sentence-transformers/all-MiniLM-L6-v2` and `google/flan-t5-small`; subsequent runs use the cache. `requirements-lock.txt` records the tested Windows environment.

Open either notebook from the repository root with `jupyter lab notebooks/task1_analysis.ipynb` or `jupyter lab notebooks/task2_rag.ipynb`. The Task 1 script performs full model fitting so its notebook stays responsive during review. The Task 2 notebook walks through PDF ingestion, retrieval, citations, and the smoke evaluation. The dashboard reads the same results and queries the local PDF index.

## Results

The workbook has **377,719 observations** from January 2017 through August 2020. Reindexing exposed **861 missing timestamps**. Error strings are counted separately from downtime. A conservative temperature and draft rule identified **77 shutdown-proxy events totaling 5,156.4 hours**. Six active-operation clusters and 926 state-relative anomaly candidates support investigation, not confirmed fault diagnosis.

For a one-hour forecast on a chronological held-out test, gradient boosting reached **RMSE 19.48** and **MAE 10.90**, versus persistence RMSE 22.68 and MAE 12.48, in native sensor units. `Task1/README.md` details the methods and limitations.

The RAG prototype extracted **382 chunks from 11 PDFs**. It combines MiniLM embeddings, local FAISS search, BM25 and rank fusion, then prompts FLAN-T5-small. Responses expose document names, pages, and excerpts. `Task2/notes.md` covers guardrails, scaling, and evaluation limits.

## Verification and submission

Run `python -m pytest -q` and `python Task2/prototype/evaluate.py`. See [the verification report](reports/TEST_REPORT.md) for measured results. Run `python package_submission.py` to create `dist/Milan_Tony_DataScience.zip` with original inputs and required deliverables. The ZIP places `Final_Presentation.pptx` at its top level as requested by the assignment.

**Interpretation boundary:** no operator labels or maintenance logs were provided. Shutdowns are rule-based proxies; root causes are hypotheses. Retrieved citations show evidence locations, while answer faithfulness still requires review.
