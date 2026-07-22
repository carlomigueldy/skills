"""Contract tests for the repository-level plugin operations harness."""

from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = REPO_ROOT / "docs" / "agent-harness"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class AgentHarnessContractTest(unittest.TestCase):
    def test_root_instructions_define_the_repository_governance_contract(self) -> None:
        text = read(REPO_ROOT / "AGENTS.md").lower()

        for phrase in (
            "plugins/",
            "skills/",
            "generated",
            "explicit authorization",
            "human identity",
            "conventional commits",
            "verification",
            "docs/agent-harness/",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_claude_imports_canonical_policy_and_routes_only_host_specific_behavior(self) -> None:
        text = read(REPO_ROOT / "CLAUDE.md")

        self.assertIn("@AGENTS.md", text)
        self.assertIn("docs/agent-harness/", text)
        self.assertNotIn("Conventional Commits", text)

    def test_roles_have_explicit_ownership_and_collaboration_limits(self) -> None:
        text = read(HARNESS_ROOT / "roles.md").lower()

        for phrase in (
            "sol",
            "never implements",
            "terra",
            "primary writer",
            "luna",
            "deterministic",
            "maximum delegation depth is two",
            "one writer per path",
            "non-overlapping edits",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_lifecycle_orders_design_implementation_sweeps_and_independent_review(self) -> None:
        text = read(HARNESS_ROOT / "lifecycle.md").lower()
        expected_steps = (
            "inventory and baseline",
            "sol design",
            "non-overlapping assignment",
            "terra implementation",
            "luna sweep",
            "terra remediation",
            "isolated red-team",
            "remediation and full verification",
            "sol final review",
        )

        positions = [text.index(step) for step in expected_steps]
        self.assertEqual(positions, sorted(positions))

    def test_all_five_modes_define_their_required_operating_contracts(self) -> None:
        text = read(HARNESS_ROOT / "modes.md").lower()

        required_by_mode = {
            "maintain": ("preserve behavior", "drift", "compatibility"),
            "create": ("atomically", "manifests", "marketplace", "packaging"),
            "refine": ("reproduce", "smallest interface", "regression coverage"),
            "test": ("read-only", "separately authorized"),
            "red-team": ("policy overrides", "host fallbacks", "fail-open"),
        }
        for mode, phrases in required_by_mode.items():
            with self.subTest(mode=mode):
                section = text.split(f"## {mode}", 1)[1].split("\n## ", 1)[0]
                for phrase in phrases:
                    self.assertIn(phrase, section)

    def test_red_team_records_are_complete_and_block_unsafe_approval(self) -> None:
        text = read(HARNESS_ROOT / "red-team.md").lower()

        for field in (
            "id",
            "severity",
            "precondition/attack",
            "evidence",
            "impact",
            "remediation",
            "retest result",
        ):
            with self.subTest(field=field):
                self.assertIn(field, text)
        self.assertIn("unresolved high or critical findings", text)
        self.assertIn("sol cannot approve", text)


if __name__ == "__main__":
    unittest.main()
