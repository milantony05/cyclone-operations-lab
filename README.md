# Cyclone Operations Data Science

Milan Tony's two-part take-home assignment: sensor analysis and local cited RAG.

The project analyzes cyclone sensor history and implements cited question answering over technical PDFs. Source data and downloaded model weights are excluded from Git.

## Execution phases

1. Environment and tests.
2. Data quality, shutdowns, operational states, anomalies, and forecasting.
3. PDF ingestion, retrieval, generation, guardrails, and evaluation.
4. Presentations, reproducibility verification, and submission archive.

## Setup

Use Python 3.12, create a virtual environment, and install `requirements.txt`.
Place the supplied workbook at `data.xlsx` and PDFs in `Task 2 Doc/`.

## Development checks

Run `python -m pytest` from the repository root.

## Run both tasks

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python Task1/task1_analysis.py --data data.xlsx
python -m Task1.enrich_report
python Task2/prototype/rag_prototype.py --docs "Task 2 Doc" --rebuild
python Task2/prototype/rag_prototype.py --question "How often does Linatex recommend internal cyclone inspections?"
python Task2/prototype/evaluate.py
python -m pytest -q
```

Python 3.12 was used. `requirements-lock.txt` records the tested Windows environment; `requirements.txt` lists direct dependencies for other platforms. The first RAG run needs network access to download free models. Subsequent runs can use the cache. The raw workbook and PDFs are supplied separately and excluded from GitHub.

## Results and deliverables

Task1 contains the runnable analysis, CSV outputs, PNG figures, quality audit and methodology README. Task2 contains the prototype, evaluation, design notes and architecture presentation. `Final_Presentation.pptx` summarizes both parts in eight slides. `TEST_REPORT.md` records verification.

Observed data covers January 2017 through August 2020. The conservative shutdown proxy detects 77 events and 5,156.4 hours. One-hour forecast RMSE improves from 22.68 for persistence to 19.48 for gradient boosting. These are retrospective results, with assumptions and limitations explained in Task1/README.md.

The RAG prototype indexes 382 chunks from 11 supplied PDFs and exposes page references. Its small model and heuristic guardrails require source review. The four-question evaluation is a smoke test, not a production quality estimate.

Repository: https://github.com/milantony05/cyclone-data-science
