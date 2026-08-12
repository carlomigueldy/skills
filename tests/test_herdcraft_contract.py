"""Committed-tree contract for the Codex-only Herdcraft plugin."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins/herdcraft"


class HerdcraftContractTests(unittest.TestCase):
    def test_focused_validator_accepts_committed_plugin(self) -> None:
        from scripts import validate_herdcraft

        self.assertEqual(validate_herdcraft.validate(REPO_ROOT), [])

    def test_focused_validator_rejects_cross_host_exposure(self) -> None:
        from scripts import validate_herdcraft

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            shutil.copytree(PLUGIN_ROOT, root / "plugins/herdcraft")
            shutil.copytree(REPO_ROOT / ".agents", root / ".agents")
            shutil.copytree(REPO_ROOT / ".claude-plugin", root / ".claude-plugin")
            shutil.copytree(REPO_ROOT / "skills", root / "skills")
            for filename in (
                "release-please-config.json",
                ".release-please-manifest.json",
                "package.json",
            ):
                shutil.copy2(REPO_ROOT / filename, root / filename)
            claude_manifest = root / "plugins/herdcraft/.claude-plugin/plugin.json"
            claude_manifest.parent.mkdir(parents=True)
            claude_manifest.write_text("{}\n", encoding="utf-8")

            errors = validate_herdcraft.validate(root)

        self.assertIn("Herdcraft v1 must not ship a Claude manifest", errors)

    def test_codex_only_manifest_and_version_are_consistent(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "herdcraft")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["interface"]["displayName"], "Herdcraft")
        self.assertEqual(
            (PLUGIN_ROOT / "version.txt").read_text(encoding="utf-8").strip(),
            manifest["version"],
        )
        self.assertFalse((PLUGIN_ROOT / ".claude-plugin/plugin.json").exists())

    def test_complete_v1_surface_is_present(self) -> None:
        required = {
            "README.md",
            "CHANGELOG.md",
            "scripts/init-run.py",
            "scripts/validate-run.py",
            "scripts/summarize-run.py",
            "skills/herdcraft/SKILL.md",
            "skills/herdcraft/agents/openai.yaml",
            "skills/herdcraft/assets/run-state.json",
            "skills/herdcraft/assets/delivery-profile.yaml",
            "skills/herdcraft/assets/capability-ledger.yaml",
            "skills/herdcraft/assets/team-contract.yaml",
            "skills/herdcraft/assets/task-contract.md",
            "skills/herdcraft/assets/team-report.md",
            "skills/herdcraft/assets/final-report.md",
            "skills/herdcraft/references/capabilities-and-delivery.md",
            "skills/herdcraft/references/operating-contract.md",
            "skills/herdcraft/references/specialists.yaml",
            "skills/herdcraft/references/team-operations.md",
        }
        actual = {
            path.relative_to(PLUGIN_ROOT).as_posix()
            for path in PLUGIN_ROOT.rglob("*")
            if path.is_file()
        }
        self.assertTrue(required <= actual, sorted(required - actual))

    def test_skill_resolves_bundled_helpers_from_the_plugin_root(self) -> None:
        skill = (PLUGIN_ROOT / "skills/herdcraft/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "resolve the plugin root three directories above this `SKILL.md`",
            skill,
        )

    def test_external_skill_prerequisites_are_documented_and_fail_closed(self) -> None:
        readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")
        skill = (PLUGIN_ROOT / "skills/herdcraft/SKILL.md").read_text(
            encoding="utf-8"
        )
        for command in (
            "npx skills add ogulcancelik/herdr@herdr",
            "npx skills add vercel-labs/skills@find-skills",
        ):
            self.assertIn(command, readme)
        self.assertIn(
            "Verify the `herdr` and `find-skills` skills are available",
            skill,
        )
        self.assertIn("If either skill is missing, stop", skill)

    def test_codex_marketplace_and_release_please_register_herdcraft(self) -> None:
        marketplace = json.loads(
            (REPO_ROOT / ".agents/plugins/marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        matching = [
            entry for entry in marketplace["plugins"] if entry["name"] == "herdcraft"
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(
            matching[0]["source"],
            {"source": "local", "path": "./plugins/herdcraft"},
        )
        self.assertEqual(
            matching[0]["policy"],
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        )

        release = json.loads(
            (REPO_ROOT / "release-please-config.json").read_text(encoding="utf-8")
        )["packages"]["plugins/herdcraft"]
        self.assertEqual(release["release-type"], "simple")
        self.assertEqual(
            release["extra-files"],
            [
                {
                    "type": "json",
                    "path": ".codex-plugin/plugin.json",
                    "jsonpath": "$.version",
                }
            ],
        )
        released = json.loads(
            (REPO_ROOT / ".release-please-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            released["plugins/herdcraft"],
            (PLUGIN_ROOT / "version.txt").read_text(encoding="utf-8").strip(),
        )

    def test_codex_only_scope_is_not_exposed_through_other_host_registries(self) -> None:
        claude_marketplace = json.loads(
            (REPO_ROOT / ".claude-plugin/marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn(
            "herdcraft", {entry["name"] for entry in claude_marketplace["plugins"]}
        )
        package = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertNotIn("plugins/herdcraft/skills", package["pi"]["skills"])
        marker = (REPO_ROOT / "skills/.generated").read_text(encoding="utf-8")
        self.assertNotIn("plugins/herdcraft/skills", marker)


if __name__ == "__main__":
    unittest.main()
