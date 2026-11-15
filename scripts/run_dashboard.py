"""Launch Streamlit from its own folder so its theme config is applied."""
from pathlib import Path
import subprocess
import sys

dashboard = Path(__file__).resolve().parents[1] / "dashboard"
raise SystemExit(subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py"], cwd=dashboard))
