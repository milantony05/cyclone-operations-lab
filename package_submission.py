"""Build and verify the assignment archive without caches or environment files."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parent
archive=root/'dist'/'Milan_Tony_DataScience.zip'
archive.parent.mkdir(exist_ok=True)
files=[root/n for n in ['README.md','requirements.txt','requirements-lock.txt','package_submission.py']]
for folder in ['Task1','Task2','tests','notebooks','dashboard','docs','.streamlit','presentations','reports']:
    files.extend(p for p in (root/folder).rglob('*') if p.is_file() and not any(part in {'__pycache__','index','.pytest_cache'} for part in p.parts) and not p.name.endswith('.inspect.ndjson'))
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:
        relative=p.relative_to(root)
        if relative==Path('presentations/Final_Presentation.pptx'):
            relative=Path('Final_Presentation.pptx')
        z.write(p,Path('Milan_Tony_DataScience')/relative)
with ZipFile(archive) as z:
    assert z.testzip() is None
    required=['Task1/shutdown_periods.csv','Task1/anomalous_periods.csv','Task1/clusters_summary.csv','Task1/forecasts.csv','Task2/architecture_diagram.pptx','Final_Presentation.pptx','notebooks/task1_analysis.ipynb','notebooks/task2_rag.ipynb','dashboard/app.py','docs/source-data/data.xlsx','reports/TEST_REPORT.md']
    assert all('Milan_Tony_DataScience/'+p in z.namelist() for p in required)
print(f'Verified {archive.name}: {len(files)} files, {archive.stat().st_size:,} bytes')
