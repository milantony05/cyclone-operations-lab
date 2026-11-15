# Verification report

- Python 3.12 virtual environment: dependencies installed; exact versions in requirements-lock.txt.
- Unit tests: 7 passed, covering event durations, missing-event boundaries, timestamp gaps, duplicate medians, causal lag features, chunk overlap and query filtering.
- Task1 full data run: completed on 377,719 input rows, with all 12 forecasting horizons and required CSVs/plots generated.
- Task2 full corpus run: 11 PDFs ingested into 382 chunks; embedding and generation models loaded locally.
- Four-question RAG smoke evaluation: both answerable questions retrieved the labeled page. One generated an answer and one abstained. Credential request blocked; unrelated question abstained. See Task2/evaluation.csv and example_answers.json. Labels cover one relevant page per answerable question, not exhaustive corpus relevance.
- Presentation: eight-slide final deck and one-slide architecture deck generated. Structural, geometry, font and reimport checks run with the bundled presentation validator. Rendered slides reviewed for layout.
- Clean repository export: 7 tests passed in 0.53 seconds, and both command-line help entry points loaded successfully. This reused the tested virtual environment; it was not a fresh dependency download.
- Submission archive: 52 files, ZIP CRC verification passed, and all required named deliverables are present. The archive includes original inputs; GitHub excludes them.

Limitations: tests are a focused suite, not a coverage claim. Shutdown labels lack ground truth. Root-cause explanations are hypotheses. RAG citation resolution does not prove answer entailment. Native Microsoft PowerPoint behavior and production concurrent-user performance have not been tested.
