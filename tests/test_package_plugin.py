"""Contract tests for the manual-upload plugin packager.

`scripts/package-plugin.py` had no coverage before this file. These tests
pin the fix for a CI-breaking bug: the packager's own excluded-directory
list had no entry for `__pycache__` (only `validate_plugins.py`'s separate,
hand-maintained copy did), so a plugin shipping importable Python would
have had interpreter-specific bytecode zipped into its package. Both
scripts now import one shared set from `scripts/package_exclusions.py`
instead of maintaining their own.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from scripts import package_exclusions


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "package-plugin.py"


def load_package_plugin():
    # The hyphen in the filename makes this un-importable by name -- same
    # trick tests/test_sync_skills.py uses for its own hyphenated script.
    spec = importlib.util.spec_from_file_location("package_plugin", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load package-plugin.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_plugin_with_pycache(plugin_dir: Path) -> None:
    write_json(
        plugin_dir / ".claude-plugin/plugin.json",
        {"name": "demo", "description": "demo plugin", "version": "1.0.0"},
    )
    write_text(
        plugin_dir / "skills/demo-skill/SKILL.md",
        "---\nname: demo-skill\ndescription: x\n---\n\n# x\n",
    )
    write_text(plugin_dir / "scripts/demo.py", "print('hello')\n")
    write_text(
        plugin_dir / "scripts/__pycache__/demo.cpython-311.pyc",
        "not real bytecode\n",
    )


def make_codex_only_plugin(plugin_dir: Path) -> None:
    write_json(
        plugin_dir / ".codex-plugin/plugin.json",
        {
            "name": "herdcraft",
            "description": "Codex-only plugin",
            "version": "0.1.0",
            "skills": "./skills/",
        },
    )
    write_text(
        plugin_dir / "skills/herdcraft/SKILL.md",
        "---\nname: herdcraft\ndescription: x\n---\n\n# x\n",
    )


class PackagePluginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_package_plugin()

    def test_excluded_dirs_matches_the_shared_canonical_set(self) -> None:
        """Pins the shared-constant fix: package-plugin.py's EXCLUDED_DIRS
        must come from `package_exclusions`, not a second hand-maintained
        list that can drift the way it already did once (no `__pycache__`
        entry). Not an identity check -- loading this hyphenated script via
        `importlib.util.spec_from_file_location` and importing
        `package_exclusions` via `from scripts import package_exclusions`
        resolve through different `sys.modules` keys (bare name vs.
        `scripts.`-qualified) for the same file, so they're equal, distinct
        objects, not the same object."""
        self.assertEqual(self.module.EXCLUDED_DIRS, package_exclusions.EXCLUDED_DIRS)
        self.assertIn("__pycache__", self.module.EXCLUDED_DIRS)

    def test_collect_files_excludes_pycache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "demo"
            make_plugin_with_pycache(plugin_dir)
            files = self.module.collect_files(plugin_dir)
        relatives = {rel for _, rel in files}
        self.assertIn("scripts/demo.py", relatives)
        self.assertFalse(any("__pycache__" in rel for rel in relatives), relatives)

    def test_built_archive_never_contains_pycache_or_pyc_files(self) -> None:
        """End-to-end: build a real zip (not just `collect_files`) for a
        plugin that has a `__pycache__` directory on disk, and assert
        nothing bytecode-shaped landed in it."""
        with tempfile.TemporaryDirectory() as tmp:
            plugins_dir = Path(tmp) / "plugins"
            plugin_dir = plugins_dir / "demo"
            make_plugin_with_pycache(plugin_dir)
            output_dir = Path(tmp) / "dist"

            with mock.patch.object(self.module, "PLUGINS_DIR", plugins_dir), mock.patch.object(
                sys,
                "argv",
                ["package-plugin.py", "demo", "--output-dir", str(output_dir)],
            ):
                self.module.main()

            zips = list(output_dir.glob("*.zip"))
            self.assertEqual(len(zips), 1, zips)
            with zipfile.ZipFile(zips[0]) as zf:
                names = zf.namelist()

        self.assertIn(".claude-plugin/plugin.json", names)
        self.assertIn("scripts/demo.py", names)
        self.assertFalse(
            any("__pycache__" in name or name.endswith(".pyc") for name in names),
            names,
        )

    def test_codex_only_plugin_builds_a_codex_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugins_dir = Path(tmp) / "plugins"
            plugin_dir = plugins_dir / "herdcraft"
            make_codex_only_plugin(plugin_dir)
            output_dir = Path(tmp) / "dist"

            with mock.patch.object(self.module, "PLUGINS_DIR", plugins_dir), mock.patch.object(
                sys,
                "argv",
                ["package-plugin.py", "herdcraft", "--output-dir", str(output_dir)],
            ):
                self.module.main()

            zips = list(output_dir.glob("herdcraft-0.1.0-codex.zip"))
            self.assertEqual(len(zips), 1, zips)
            with zipfile.ZipFile(zips[0]) as zf:
                names = zf.namelist()

        self.assertIn(".codex-plugin/plugin.json", names)
        self.assertNotIn(".claude-plugin/plugin.json", names)


if __name__ == "__main__":
    unittest.main()
