#!/usr/bin/env python3
"""Package a plugin as a zip for manual upload to Claude Cowork / Claude Desktop.

The marketplace install path (`/plugin marketplace add carlomigueldy/skills`)
is the normal way to get these plugins. This script exists for the manual
upload flow, where the desktop app wants a single zip and applies stricter
rules to what is inside it than git does.

Two things it handles that a plain `zip -r` does not:

1. **Flat layout.** The uploader expects `.claude-plugin/plugin.json` at the
   root of the archive, not nested under a `<plugin-name>/` directory.

2. **Path sanitization.** The uploader rejects archives containing paths with
   characters that are illegal or reserved on Windows -- most notably `[` and
   `]`, which Next.js dynamic-route directories (`app/[locale]/`) use. Those
   segments are renamed to a `__name__` form and the archive gains a
   `RESTORE-PATHS.md` plus a `restore-paths.sh` that put them back.

Usage:
    scripts/package-plugin.py                      # package saas-launch
    scripts/package-plugin.py <plugin-name>
    scripts/package-plugin.py --output-dir ~/Downloads
    scripts/package-plugin.py --list              # what would be renamed
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
DEFAULT_PLUGIN = "saas-launch"

# Characters the desktop uploader rejects in archive paths. `[` and `]` are
# legal on Windows but the uploader's validator refuses them anyway, which is
# what broke the first saas-launch upload attempt.
ILLEGAL_CHARS = r'<>:"|?*\\[]'
ILLEGAL_RE = re.compile(f"[{re.escape(ILLEGAL_CHARS)}]|[^\x20-\x7e]")

# Never ship these, regardless of what is on disk or tracked in git.
EXCLUDED_DIRS = {".git", "node_modules", ".turbo", "dist", ".next"}
EXCLUDED_FILES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".log"}

RESTORE_SCRIPT = """#!/usr/bin/env bash
# Restores path names that were rewritten so this plugin could be uploaded to
# Claude Cowork / Claude Desktop. Run once, from the plugin root, right after
# copying the template out of the plugin.
set -euo pipefail

cd "$(dirname "$0")"

{commands}
echo "Restored {count} path(s)."
"""


def sanitize_segment(segment: str) -> str:
    """Rewrite one path segment so it survives the uploader's validator."""
    # `[locale]` -> `__locale__` keeps the name readable and reversible.
    bracketed = re.fullmatch(r"\[(.+)\]", segment)
    if bracketed:
        return f"__{bracketed.group(1)}__"
    return ILLEGAL_RE.sub("_", segment)


def sanitize_path(rel_path: str) -> str:
    return "/".join(sanitize_segment(part) for part in rel_path.split("/"))


def rename_root(rel_path: str) -> tuple[str, str] | None:
    """Return the shallowest (original, sanitized) prefix pair that differs.

    Restoring has to happen at the directory level: renaming three files
    individually into `app/[locale]/` fails because that directory does not
    exist yet. Moving `app/__locale__` -> `app/[locale]` once does the whole
    job, and its parent is by definition unchanged.
    """
    parts = rel_path.split("/")
    sanitized = [sanitize_segment(part) for part in parts]
    for i, (original, clean) in enumerate(zip(parts, sanitized)):
        if original != clean:
            return "/".join(parts[: i + 1]), "/".join(sanitized[: i + 1])
    return None


def should_skip(path: Path) -> bool:
    if path.name in EXCLUDED_FILES:
        return True
    return path.suffix in EXCLUDED_SUFFIXES


def collect_files(plugin_dir: Path) -> list[tuple[Path, str]]:
    """Walk the plugin, returning (absolute path, POSIX-relative path) pairs."""
    collected: list[tuple[Path, str]] = []
    for root, dirs, files in os.walk(plugin_dir):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for name in sorted(files):
            path = Path(root) / name
            if should_skip(path):
                continue
            rel = path.relative_to(plugin_dir).as_posix()
            collected.append((path, rel))
    return collected


def read_version(plugin_dir: Path) -> str:
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        sys.exit(
            f"error: {manifest} not found -- is {plugin_dir.name} really a plugin?"
        )
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {manifest} is not valid JSON: {exc}")
    version = data.get("version")
    if not version:
        sys.exit(f"error: {manifest} has no 'version' field.")
    return str(version)


def build_restore_docs(renames: list[tuple[str, str]]) -> tuple[str, str]:
    """Return (RESTORE-PATHS.md, restore-paths.sh) for the renamed paths."""
    rows = "\n".join(
        f"| `{sanitized}` | `{original}` |" for original, sanitized in renames
    )
    doc = f"""# Restore original paths

This plugin was packaged for **manual upload to Claude Cowork / Claude
Desktop**. The uploader rejects archive paths containing any of
``{ILLEGAL_CHARS}`` or non-ASCII characters, so {len(renames)} path(s) were
renamed before zipping.

**The renamed paths are load-bearing.** Next.js resolves dynamic routes by
the literal `[segment]` directory name -- left as `__segment__`, the route
does not exist and the app 404s. Restore them before running the app.

Run this from the plugin root:

```bash
bash restore-paths.sh
```

Or rename manually:

| Shipped as | Should be |
| --- | --- |
{rows}

Delete this file and `restore-paths.sh` once you have restored the paths;
neither is part of the plugin. The copy of this plugin installed from the
marketplace has the correct names already and needs none of this.
"""

    commands = "\n".join(
        f'mv "{sanitized}" "{original}"' for original, sanitized in renames
    )
    script = RESTORE_SCRIPT.format(commands=commands, count=len(renames))
    return doc, script


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Package a plugin as a zip for manual Claude Cowork upload.",
    )
    parser.add_argument(
        "plugin",
        nargs="?",
        default=DEFAULT_PLUGIN,
        help=f"plugin directory name under plugins/ (default: {DEFAULT_PLUGIN})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "dist"),
        help="where to write the zip (default: <repo>/dist)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="report what would be packaged and renamed, without writing a zip",
    )
    args = parser.parse_args()

    plugin_dir = PLUGINS_DIR / args.plugin
    if not plugin_dir.is_dir():
        available = ", ".join(sorted(p.name for p in PLUGINS_DIR.iterdir() if p.is_dir()))
        sys.exit(f"error: no plugin '{args.plugin}' in plugins/. Available: {available}")

    version = read_version(plugin_dir)
    files = collect_files(plugin_dir)
    if not files:
        sys.exit(f"error: {plugin_dir} contains no packageable files.")

    entries: list[tuple[Path, str]] = []
    rename_set: dict[str, str] = {}
    for path, rel in files:
        arc = sanitize_path(rel)
        if arc != rel:
            root = rename_root(rel)
            assert root is not None  # arc != rel guarantees a differing segment
            rename_set[root[0]] = root[1]
        entries.append((path, arc))

    # Deepest first, so a nested rename runs before its parent moves out
    # from under it.
    renames = sorted(rename_set.items(), key=lambda pair: -pair[0].count("/"))

    # A sanitized name colliding with a real one would silently drop a file.
    seen: dict[str, str] = {}
    for (_, arc), (_, rel) in zip(entries, files):
        if arc in seen:
            sys.exit(
                f"error: '{seen[arc]}' and '{rel}' both sanitize to '{arc}'. "
                "Rename one in the source tree."
            )
        seen[arc] = rel

    if args.list:
        print(f"{args.plugin} v{version}: {len(entries)} file(s)")
        if renames:
            print(f"\n{len(renames)} path(s) would be renamed:")
            for original, sanitized in renames:
                print(f"  {original}\n    -> {sanitized}")
        else:
            print("\nNo paths need renaming.")
        return

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{args.plugin}-{version}-cowork.zip"

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, arc in entries:
            zf.write(path, arc)
        if renames:
            doc, script = build_restore_docs(renames)
            zf.writestr("RESTORE-PATHS.md", doc)
            # 0o755 so the script stays executable once unzipped.
            info = zipfile.ZipInfo("restore-paths.sh")
            info.external_attr = 0o755 << 16
            info.date_time = (1980, 1, 1, 0, 0, 0)
            zf.writestr(info, script)

    # Verify what we actually wrote, rather than trusting the loop above.
    with zipfile.ZipFile(out_path) as zf:
        names = zf.namelist()
        offenders = [n for n in names if ILLEGAL_RE.search(n)]
        if offenders:
            sys.exit(f"error: zip still contains rejected paths: {offenders}")
        if ".claude-plugin/plugin.json" not in names:
            sys.exit("error: zip is missing .claude-plugin/plugin.json at its root.")

    size_kb = out_path.stat().st_size / 1024
    print(f"Wrote {out_path} ({len(names)} files, {size_kb:.0f} KB)")
    if renames:
        print(
            f"Renamed {len(renames)} path(s) for the uploader; "
            "RESTORE-PATHS.md and restore-paths.sh are bundled to reverse it."
        )


if __name__ == "__main__":
    main()
