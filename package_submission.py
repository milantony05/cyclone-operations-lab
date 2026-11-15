"""Package the project in the assignment's required submission layout."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT / "Milan_Tony_DataScience.zip"
DESTINATION.parent.mkdir(exist_ok=True)

files = [ROOT / name for name in ("README.md", "requirements.txt", "package_submission.py")]
for folder in ("1_sensor_analysis", "2_document_qa", "dashboard", "docs", "tests"):
    files.extend(
        path for path in (ROOT / folder).rglob("*")
        if path.is_file()
        and not any(part in {"__pycache__", "index", ".pytest_cache"} for part in path.parts)
        and not path.name.endswith(".inspect.ndjson")
    )

with ZipFile(DESTINATION, "w", ZIP_DEFLATED, compresslevel=6) as archive:
    for path in files:
        relative = path.relative_to(ROOT)
        archive.write(path, Path("Milan_Tony_DataScience") / relative)
        if relative.parts[0] == "1_sensor_analysis":
            archive.write(path, Path("Milan_Tony_DataScience", "Task1", *relative.parts[1:]))
        elif relative.parts[0] == "2_document_qa":
            archive.write(path, Path("Milan_Tony_DataScience", "Task2", *relative.parts[1:]))
        elif relative == Path("docs/Final_Presentation.pptx"):
            archive.write(path, Path("Milan_Tony_DataScience", "Final_Presentation.pptx"))

with ZipFile(DESTINATION) as archive:
    assert archive.testzip() is None
    names = set(archive.namelist())
    required = (
        "Final_Presentation.pptx",
        "Task1/task1_analysis.py",
        "Task1/shutdown_periods.csv",
        "Task1/anomalous_periods.csv",
        "Task1/clusters_summary.csv",
        "Task1/forecasts.csv",
        "Task2/architecture_diagram.pptx",
        "Task2/prototype/rag_prototype.py",
        "1_sensor_analysis/1_sensor_analysis.ipynb",
        "2_document_qa/2_document_qa.ipynb",
        "dashboard/app.py",
        "dashboard/.streamlit/config.toml",
        "docs/data.xlsx",
    )
    assert all(f"Milan_Tony_DataScience/{name}" in names for name in required)

print(f"Verified {DESTINATION}: {len(files)} files, {DESTINATION.stat().st_size:,} bytes")


