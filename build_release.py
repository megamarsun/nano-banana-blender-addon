#!/usr/bin/env python3
"""Build a release zip of the monkey_banana add-on without binaries.

The resulting archive contains only the Python source inside the
``monkey_banana`` package. Version control metadata, documentation, and
compiled artifacts are excluded to keep the distribution clean.
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
SRC_DIR = ROOT / "monkey_banana"
OUTPUT_ZIP = ROOT / "monkey_banana.zip"


def purge_compiled() -> None:
    """Remove ``__pycache__`` directories and ``*.pyc`` files."""
    for path in SRC_DIR.rglob("__pycache__"):
        shutil.rmtree(path)
    for pyc in SRC_DIR.rglob("*.pyc"):
        pyc.unlink()


def build_zip() -> None:
    """Create a zip archive containing only sources under ``monkey_banana``."""
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in SRC_DIR.rglob("*"):
            if file.is_dir():
                continue
            arcname = file.relative_to(ROOT)
            zf.write(file, arcname)


def main() -> None:
    purge_compiled()
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
    build_zip()
    print(f"Created {OUTPUT_ZIP}")


if __name__ == "__main__":
    main()
