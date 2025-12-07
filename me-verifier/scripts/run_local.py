# scripts/run_local.py
from pathlib import Path
import sys

# añade la raíz del repo al sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from waitress import serve
from api.app import app

if __name__ == "__main__":
    serve(app, host="127.0.0.1", port=5000, threads=2)
