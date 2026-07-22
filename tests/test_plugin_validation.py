"""Mutation tests for the repository-wide plugin validation interface."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def add_plugin(root: Path, name: str, *, codex: bool = False) -> None:
    package = root / "plugins" / name
    claude_manifest = {
        "name": name,
        "description": f"{name} test plugin",
        "version": "1.2.3",
    }
    write_json(package / ".claude-plugin/plugin.json", claude_manifest)
    if codex:
        write_json(
            package / ".codex-plugin/plugin.json",
            {**claude_manifest, "skills": "./skills/"},
        )
    skill = package / "skills" / f"{name}-skill" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(
        f"---\nname: {name}-skill\ndescription: Test skill\n---\n\n# Test\n",
        encoding="utf-8",
    )
    (package / "version.txt").write_text("1.2.3\n", encoding="utf-8")


def make_repository(root: Path) -> None:
    add_plugin(root, "alpha", codex=True)
    add_plugin(root, "beta")
    write_json(
        root / ".claude-plugin/marketplace.json",
        {
            "name": "test-marketplace",
            "plugins": [
                {"name": "alpha", "source": "./plugins/alpha"},
                {"name": "beta", "source": "./plugins/beta"},
            ],
        },
    )
    write_json(
        root / "release-please-config.json",
        {
            "release-type": "simple",
            "packages": {
                "plugins/alpha": {
                    "release-type": "simple",
                    "component": "alpha",
                    "package-name": "alpha",
                    "extra-files": [
                        {"type": "json", "path": ".claude-plugin/plugin.json"},
                        {"type": "json", "path": ".codex-plugin/plugin.json"},
                    ],
                },
                "plugins/beta": {
                    "release-type": "simple",
                    "component": "beta",
                    "package-name": "beta",
                    "extra-files": [
                        {"type": "json", "path": ".claude-plugin/plugin.json"}
                    ],
                },
            },
        },
    )
    write_json(
        root / ".release-please-manifest.json",
        {"plugins/alpha": "1.2.3", "plugins/beta": "1.2.3"},
    )


class PluginValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        from scripts import validate_plugins

        self.validator = validate_plugins

    def validate_mutation(self, mutate) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            make_repository(root)
            mutate(root)
            return self.validator.validate_repository(root)

    def test_valid_repository_and_plugin_selection_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            make_repository(root)
            self.assertEqual(self.validator.validate_repository(root), [])
            self.assertEqual(
                self.validator.validate_repository(root, plugin_names=["alpha"]), []
            )

    def test_registration_and_version_drift_are_rejected(self) -> None:
        mutations = {
            "missing marketplace registration": lambda root: write_json(
                root / ".claude-plugin/marketplace.json",
                {"name": "test", "plugins": []},
            ),
            "missing release config": lambda root: _delete_release_package(root),
            "missing release manifest": lambda root: write_json(
                root / ".release-please-manifest.json", {"plugins/beta": "1.2.3"}
            ),
            "version.txt drift": lambda root: (
                root / "plugins/alpha/version.txt"
            ).write_text("9.9.9\n", encoding="utf-8"),
            "Claude manifest drift": lambda root: _set_json_value(
                root / "plugins/alpha/.claude-plugin/plugin.json", "version", "9.9.9"
            ),
            "Codex manifest drift": lambda root: _set_json_value(
                root / "plugins/alpha/.codex-plugin/plugin.json", "version", "9.9.9"
            ),
            "missing host extra-file": lambda root: _remove_extra_file(root),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                self.assertTrue(self.validate_mutation(mutate), label)

    def test_orphan_registry_entries_are_rejected_during_full_validation(self) -> None:
        def mutate(root: Path) -> None:
            marketplace_path = root / ".claude-plugin/marketplace.json"
            marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
            marketplace["plugins"].append(
                {"name": "ghost", "source": "./plugins/ghost"}
            )
            write_json(marketplace_path, marketplace)

            release_path = root / "release-please-config.json"
            release = json.loads(release_path.read_text(encoding="utf-8"))
            release["packages"]["plugins/ghost"] = {
                "release-type": "simple",
                "component": "ghost",
                "package-name": "ghost",
                "extra-files": [{"path": ".claude-plugin/plugin.json"}],
            }
            write_json(release_path, release)

            manifest_path = root / ".release-please-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["plugins/ghost"] = "1.0.0"
            write_json(manifest_path, manifest)

        errors = self.validate_mutation(mutate)
        self.assertTrue(any("ghost" in error and "orphan" in error for error in errors), errors)

    def test_duplicate_names_broken_skills_and_unsafe_paths_are_rejected(self) -> None:
        mutations = {
            "duplicate manifest name": lambda root: _set_json_value(
                root / "plugins/beta/.claude-plugin/plugin.json", "name", "alpha"
            ),
            "duplicate marketplace name": lambda root: _set_marketplace_name(root),
            "missing SKILL.md": lambda root: (
                root / "plugins/alpha/skills/alpha-skill/SKILL.md"
            ).unlink(),
            "unsafe packaged directory": lambda root: _write_text(
                root / "plugins/alpha/node_modules/dependency.js", "unsafe\n"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                self.assertTrue(self.validate_mutation(mutate), label)

    def test_archive_path_sanitization_collisions_are_rejected(self) -> None:
        def mutate(root: Path) -> None:
            _write_text(root / "plugins/alpha/templates/[id]/page.txt", "dynamic\n")
            _write_text(root / "plugins/alpha/templates/__id__/page.txt", "literal\n")

        errors = self.validate_mutation(mutate)
        self.assertTrue(any("archive path collision" in error for error in errors), errors)

    def test_windows_unsafe_and_case_colliding_package_paths_are_rejected(self) -> None:
        unsafe_paths = ("CON", "aux.txt", "name.", "name ")
        for relative in unsafe_paths:
            with self.subTest(relative=relative):
                errors = self.validate_mutation(
                    lambda root, relative=relative: _write_text(
                        root / "plugins/alpha/templates" / relative, "unsafe\n"
                    )
                )
                self.assertTrue(any("Windows-unsafe" in error for error in errors), errors)

        def case_collision(root: Path) -> None:
            _write_text(root / "plugins/alpha/templates/A.txt", "upper\n")
            _write_text(root / "plugins/alpha/templates/a.txt", "lower\n")

        errors = self.validate_mutation(case_collision)
        self.assertTrue(any("archive path collision" in error for error in errors), errors)

    def test_packager_generated_restore_files_cannot_be_shadowed(self) -> None:
        def mutate(root: Path) -> None:
            _write_text(root / "plugins/alpha/templates/[id]/page.txt", "dynamic\n")
            _write_text(root / "plugins/alpha/RESTORE-PATHS.md", "shadow\n")

        errors = self.validate_mutation(mutate)
        self.assertTrue(any("generated restore file" in error for error in errors), errors)

    def test_invalid_semver_identifiers_are_rejected(self) -> None:
        for version in ("1.2.3-alpha..1", "1.2.3-01", "1.2.3+build..x", "1.2.3-alpha."):
            with self.subTest(version=version):
                errors = self.validate_mutation(
                    lambda root, version=version: _set_all_versions(root, "alpha", version)
                )
                self.assertTrue(any("semantic" in error for error in errors), errors)

    def test_codex_skills_reference_must_be_safe_and_resolvable(self) -> None:
        for value in ("../outside", "./missing/"):
            with self.subTest(skills=value):
                errors = self.validate_mutation(
                    lambda root, value=value: _set_json_value(
                        root / "plugins/alpha/.codex-plugin/plugin.json",
                        "skills",
                        value,
                    )
                )
                self.assertTrue(errors)

    def test_generated_skill_mirror_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            shutil.copytree(root / "plugins/alpha/skills", root / "skills")
            (root / "skills/.generated").write_text(
                "generated by scripts/sync-skills.py from plugins/alpha/skills "
                "-- edit the source, not this mirror.\n",
                encoding="utf-8",
            )
            (root / "skills/alpha-skill/SKILL.md").write_text(
                "drifted\n", encoding="utf-8"
            )

        errors = self.validate_mutation(mutate)
        self.assertTrue(any("mirror" in error.lower() for error in errors), errors)

    def test_product_foundry_focused_validator_is_composed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            add_plugin(root, "product-foundry")
            write_json(
                root / ".claude-plugin/marketplace.json",
                {
                    "name": "test",
                    "plugins": [
                        {
                            "name": "product-foundry",
                            "source": "./plugins/product-foundry",
                        }
                    ],
                },
            )
            write_json(
                root / "release-please-config.json",
                {
                    "packages": {
                        "plugins/product-foundry": {
                            "release-type": "simple",
                            "extra-files": [
                                {"path": ".claude-plugin/plugin.json"}
                            ],
                        }
                    }
                },
            )
            write_json(
                root / ".release-please-manifest.json",
                {"plugins/product-foundry": "1.2.3"},
            )
            script = root / "scripts/validate_product_foundry.py"
            _write_text(
                script,
                "import sys\nprint('focused sentinel', file=sys.stderr)\nraise SystemExit(1)\n",
            )
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("focused sentinel" in error for error in errors), errors)

    def test_cli_reports_unknown_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            make_repository(root)
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts/validate_plugins.py"),
                    "--repo-root",
                    str(root),
                    "--plugin",
                    "missing",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing", result.stderr)


def _set_json_value(path: Path, key: str, value: object) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[key] = value
    write_json(path, payload)


def _delete_release_package(root: Path) -> None:
    path = root / "release-please-config.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    del payload["packages"]["plugins/alpha"]
    write_json(path, payload)


def _remove_extra_file(root: Path) -> None:
    path = root / "release-please-config.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["packages"]["plugins/alpha"]["extra-files"].pop()
    write_json(path, payload)


def _set_marketplace_name(root: Path) -> None:
    path = root / ".claude-plugin/marketplace.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["plugins"][1]["name"] = "alpha"
    write_json(path, payload)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _set_all_versions(root: Path, plugin: str, version: str) -> None:
    package = root / "plugins" / plugin
    for manifest in (
        package / ".claude-plugin/plugin.json",
        package / ".codex-plugin/plugin.json",
    ):
        if manifest.exists():
            _set_json_value(manifest, "version", version)
    (package / "version.txt").write_text(f"{version}\n", encoding="utf-8")
    release_manifest = root / ".release-please-manifest.json"
    payload = json.loads(release_manifest.read_text(encoding="utf-8"))
    payload[f"plugins/{plugin}"] = version
    write_json(release_manifest, payload)


if __name__ == "__main__":
    unittest.main()
