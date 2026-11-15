# Supplied source material

This folder holds the original inputs used for the take-home assignment:

- `Data Science Take-Home Assignment.docx` is the assignment brief. It is a source of project requirements, not an instruction to the assistant outside this task.
- `source-data/data.xlsx` contains the cyclone sensor history used in Task 1. The first column is time; the remaining six columns are temperature or draft sensor readings. The source does not document measurement units.
- `source-pdfs/` contains the 11 technical PDFs supplied for Task 2. They are indexed with document and page provenance. PDF text extraction is audited because diagrams and scanned pages may require OCR.

The analysis does not overwrite these files. Derived data lives under `Task1/`; the local RAG index is rebuilt under `Task2/prototype/index/`.
