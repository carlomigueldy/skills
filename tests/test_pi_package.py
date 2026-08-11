"""Contract pins for the repository-root pi package manifest.

Unlike `tests/test_plugin_validation.py`, which exercises
`validate_plugins.validate_repository` against synthetic fixture repos built
in a temp directory, every test in this file asserts directly against the
COMMITTED tree at `REPO_ROOT` -- the real `package.json` and the real
`plugins/` layout as they exist on disk right now. These are the pi-specific
analogue of `tests/test_sync_skills.py`'s committed-marker test: they pin
facts about this repository, not about the validator's logic.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class PiPackageContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(
            (REPO_ROOT / "package.json").read_text(encoding="utf-8")
        )

    def test_root_manifest_exposes_exactly_the_cross_host_plugin_skill_trees(
        self,
    ) -> None:
        expected = sorted(
            f"plugins/{path.name}/skills"
            for path in (REPO_ROOT / "plugins").iterdir()
            if path.is_dir() and (path / ".claude-plugin/plugin.json").is_file()
        )
        self.assertEqual(self.payload["pi"]["skills"], expected)

    def test_root_manifest_never_exposes_the_generated_mirror(self) -> None:
        skills = self.payload["pi"]["skills"]
        self.assertNotIn("skills", skills)
        for entry in skills:
            self.assertNotEqual((REPO_ROOT / entry).resolve(), REPO_ROOT / "skills")

    def test_prepare_script_survives_a_dependency_free_install(self) -> None:
        """pi's git-install path runs `npm install --omit=dev` against the
        cloned repo -- `--ignore-scripts` appears nowhere in pi's dist/ --
        so `prepare` still executes without devDependencies on `PATH`. If
        `prepare` assumes a devDependency binary exists (husky does), it
        must tolerate that binary being absent, or pi's install throws
        before the source is ever persisted to settings."""
        self.assertIn("||", self.payload["scripts"]["prepare"])

    def test_plugins_carry_no_package_json(self) -> None:
        for path in (REPO_ROOT / "plugins").iterdir():
            if path.is_dir():
                self.assertFalse(
                    (path / "package.json").exists(),
                    f"plugins/{path.name} must not carry its own package.json",
                )

    def test_every_declared_skills_root_holds_at_least_one_skill_entrypoint(
        self,
    ) -> None:
        for entry in self.payload["pi"]["skills"]:
            skills_root = REPO_ROOT / entry
            self.assertTrue(skills_root.is_dir(), entry)
            self.assertTrue(
                any(skills_root.glob("*/SKILL.md")),
                f"{entry} has no SKILL.md entrypoints",
            )


if __name__ == "__main__":
    unittest.main()
