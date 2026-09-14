"""Write the self-contained GitHub Pages entry point from the site template."""

from __future__ import annotations

from pathlib import Path

import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
import app  # noqa: E402


(PROJECT_DIR / "index.html").write_text(app.HTML, encoding="utf-8")
print("Wrote index.html for static hosting")
