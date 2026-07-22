#!/usr/bin/env python3
"""Install grok-ultracode artifacts into a Grok config directory.

Default target is ~/.grok (user-level). Use --target .grok for a project
checkout, or any other directory with the same layout Grok discovers.

Usage:
    python3 plugins/grok-ultracode/scripts/install.py
    python3 plugins/grok-ultracode/scripts/install.py --target .grok
    python3 plugins/grok-ultracode/scripts/install.py --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = Path.home() / ".grok"

SKILL_NAME = "ultracode"
WORKFLOW_NAME = "ship-feature.rhai"
PERSONA_NAMES = ("architect", "implementer", "reviewer", "sweeper")
ROLE_NAMES = ("architect", "implementer", "reviewer", "sweeper")


def copy_tree(src: Path, dest: Path, *, dry_run: bool) -> None:
    if dry_run:
        print(f"  would copy tree  {src} -> {dest}")
        return
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    print(f"  copied tree      {src.name}/ -> {dest}")


def copy_file(src: Path, dest: Path, *, dry_run: bool) -> None:
    if dry_run:
        print(f"  would copy file  {src} -> {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"  copied file      {src.name} -> {dest}")


def install(target: Path, *, dry_run: bool) -> int:
    skill_src = PLUGIN_ROOT / "skills" / SKILL_NAME
    workflow_src = PLUGIN_ROOT / "workflows" / WORKFLOW_NAME
    personas_src = PLUGIN_ROOT / "personas"
    roles_src = PLUGIN_ROOT / "roles"

    missing = [
        path
        for path in (skill_src, workflow_src, personas_src, roles_src)
        if not path.exists()
    ]
    if missing:
        for path in missing:
            print(f"error: missing package source: {path}", file=sys.stderr)
        return 1

    print(f"Installing grok-ultracode → {target}" + (" (dry-run)" if dry_run else ""))
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    copy_tree(skill_src, target / "skills" / SKILL_NAME, dry_run=dry_run)
    copy_file(workflow_src, target / "workflows" / WORKFLOW_NAME, dry_run=dry_run)

    for name in PERSONA_NAMES:
        src = personas_src / f"{name}.toml"
        if not src.is_file():
            print(f"error: missing persona: {src}", file=sys.stderr)
            return 1
        copy_file(src, target / "personas" / f"{name}.toml", dry_run=dry_run)

    for name in ROLE_NAMES:
        src = roles_src / f"{name}.toml"
        if not src.is_file():
            print(f"error: missing role: {src}", file=sys.stderr)
            return 1
        copy_file(src, target / "roles" / f"{name}.toml", dry_run=dry_run)

    print("Done.")
    if not dry_run:
        print("Restart Grok Build (or open a new session) to reload skills/workflows.")
        print("Try: /ultracode <feature description>")
        print('  or: /workflow ship-feature target="..."')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install grok-ultracode skill, workflow, personas, and roles for Grok Build.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"Grok config root (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print planned copies without writing files",
    )
    args = parser.parse_args()
    target = args.target.expanduser().resolve()
    return install(target, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
