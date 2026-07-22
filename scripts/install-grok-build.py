#!/usr/bin/env python3
"""Repo-root helper that runs plugins/grok-build/scripts/install.py.

Example:
    python3 scripts/install-grok-build.py
    python3 scripts/install-grok-build.py --target .grok
    python3 scripts/install-grok-build.py --dry-run
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

INSTALLER = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "grok-build"
    / "scripts"
    / "install.py"
)


def main() -> int:
    if not INSTALLER.is_file():
        print(f"error: installer missing: {INSTALLER}", file=sys.stderr)
        return 1
    return subprocess.call([sys.executable, str(INSTALLER), *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
