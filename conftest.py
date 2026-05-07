import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent
for path in (ROOT, ROOT / "VetClinic" / "API", ROOT / "VetClinic" / "GUI"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
