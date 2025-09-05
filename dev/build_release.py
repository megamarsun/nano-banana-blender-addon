#!/usr/bin/env python3
"""Build a release zip of the add-on without binaries.

The resulting archive contains only the Python source and extension
metadata. Version control information, documentation, and compiled
artifacts are excluded to keep the distribution clean.
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE_NAME = "nano_banana"
PACKAGE_DIR = ROOT / MODULE_NAME
OUTPUT_ZIP = ROOT / f"{MODULE_NAME}.zip"

# Non-binary files to include at the archive root (e.g. manifest, icons).
EXTRA_FILES = [ROOT / "blender_manifest.toml"]


def purge_compiled() -> None:
    """Remove ``__pycache__`` directories and ``*.pyc`` files."""
    for path in ROOT.rglob("__pycache__"):
        shutil.rmtree(path)
    for pyc in ROOT.rglob("*.pyc"):
        pyc.unlink()


def build_zip() -> None:
    """Create a zip archive containing the add-on and extension metadata."""
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for py_file in PACKAGE_DIR.rglob("*.py"):
            zf.write(py_file, py_file.relative_to(ROOT))

        for extra in EXTRA_FILES:
            if extra.exists():
                zf.write(extra, extra.name)


def main() -> None:
    purge_compiled()
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
    build_zip()
    print(f"Created {OUTPUT_ZIP}")


if __name__ == "__main__":
    main()
