"""Compatibility shim for the Nano-Banana Blender add-on.

This file exists so developer tools that assume the legacy add-on layout
(find an ``__init__`` at the repository root) can locate the actual
implementation, which lives in :mod:`nano_banana`.
"""

from nano_banana import bl_info, register, unregister  # noqa: F401
