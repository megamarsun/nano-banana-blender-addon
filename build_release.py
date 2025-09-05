#!/usr/bin/env python3
"""Build a release zip of the nano_banana add-on without binaries.

The resulting archive contains only the Python source inside the
``nano_banana`` package. Version control metadata, documentation, and
compiled artifacts are excluded to keep the distribution clean.
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
SRC_DIR = ROOT / "nano_banana"
OUTPUT_ZIP = ROOT / "nano_banana.zip"

# Additional non-binary files that should be packaged alongside the add-on
# for Blender's extension system (e.g. manifest, icons).
EXTRA_FILES = [ROOT / "blender_manifest.toml"]


def purge_compiled() -> None:
    """Remove ``__pycache__`` directories and ``*.pyc`` files."""
    for path in SRC_DIR.rglob("__pycache__"):
        shutil.rmtree(path)
    for pyc in SRC_DIR.rglob("*.pyc"):
        pyc.unlink()


def build_zip() -> None:
    """Create a zip archive containing the add-on and extension metadata."""
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in SRC_DIR.rglob("*"):
            if file.is_dir():
                continue
            arcname = file.relative_to(ROOT)
            zf.write(file, arcname)

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
