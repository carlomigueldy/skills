"""Directory names that must never end up inside a packaged plugin.

Single source of truth for `scripts/package-plugin.py` (which must never zip
one of these up) and `scripts/validate_plugins.py` (which checks that a
plugin's package paths are safe to ship). Before this module existed, each
script hand-maintained its own copy of this set, and they drifted: the
packager's list had no entry for `__pycache__`, so it would have shipped
Python bytecode compiled against whatever interpreter happened to run it.
Two lists that have to agree and nothing making them do so is the bug class
this file exists to close -- not just that one instance of it.
"""

from __future__ import annotations

EXCLUDED_DIRS = frozenset(
    {".git", ".next", ".turbo", "__pycache__", "dist", "node_modules"}
)
