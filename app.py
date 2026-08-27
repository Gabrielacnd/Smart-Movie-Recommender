import importlib.util
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent / "book_recommander"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

SPEC = importlib.util.spec_from_file_location("book_recommander_app", PROJECT_DIR / "app.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError("Nu s-a putut încărca aplicația din subfolderul book_recommander")

MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

app = MODULE.app
