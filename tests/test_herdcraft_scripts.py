"""Behavior tests for Herdcraft's deterministic run-ledger helpers."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins/herdcraft"


def load_script(filename: str, module_name: str):
    path = PLUGIN_ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HerdcraftScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.init_run = load_script("init-run.py", "herdcraft_init_run")
        cls.validate_run = load_script("validate-run.py", "herdcraft_validate_run")
        cls.summarize_run = load_script("summarize-run.py", "herdcraft_summarize_run")

    def test_initialize_run_creates_a_non_overwriting_durable_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "project"
            repo.mkdir()
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="feature-001",
                objective="Ship the dashboard filter",
                base_revision="abc1234",
                teams=["product", "quality"],
            )

            state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["run_id"], "feature-001")
            self.assertEqual(state["objective"], "Ship the dashboard filter")
            self.assertEqual(state["repo_root"], str(repo.resolve()))
            self.assertEqual(state["base_revision"], "abc1234")
            self.assertEqual(
                [team["team_id"] for team in state["teams"]],
                ["product", "quality"],
            )
            self.assertEqual(
                [team["state"] for team in state["teams"]],
                ["planned", "planned"],
            )
            self.assertEqual(
                state["teams"][0]["team_contract"],
                "teams/product/team-contract.yaml",
            )
            self.assertEqual(
                {path.name for path in (run_dir / "teams").iterdir()},
                {"product", "quality"},
            )
            self.assertEqual(self.validate_run.validate_run(run_dir), [])
            with self.assertRaises(FileExistsError):
                self.init_run.initialize_run(
                    repo_root=repo,
                    run_id="feature-001",
                    objective="Do not overwrite",
                    base_revision="def5678",
                    teams=[],
                )

    def test_initialize_run_rejects_unsafe_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            for value in ("../escape", "Team Name", "", ".hidden"):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    self.init_run.initialize_run(
                        repo_root=repo,
                        run_id=value,
                        objective="x",
                        base_revision="abc1234",
                        teams=[],
                    )

    def test_initialize_run_quotes_repo_root_for_yaml(self) -> None:
        with tempfile.TemporaryDirectory(prefix="herdcraft repo # ") as temp_dir:
            repo = Path(temp_dir)
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="yaml-safe",
                objective="Exercise YAML-safe paths",
                base_revision="abc1234",
                teams=["api"],
            )

            ledger = (run_dir / "teams/api/capability-ledger.yaml").read_text(
                encoding="utf-8"
            )
            self.assertIn(f"repo_root: {json.dumps(str(repo.resolve()))}", ledger)

    def test_initialize_run_rejects_symlink_escape_from_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = root / "repo"
            outside = root / "outside"
            repo.mkdir()
            outside.mkdir()
            (repo / ".orchestration").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "must stay within the repository"):
                self.init_run.initialize_run(
                    repo_root=repo,
                    run_id="escaped",
                    objective="Keep the ledger in-repo",
                    base_revision="abc1234",
                    teams=[],
                )

            self.assertFalse((outside / "runs/escaped").exists())

    def test_validate_run_reports_observable_contract_breaks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "broken-run"
            run_dir.mkdir()
            (run_dir / "run-state.json").write_text(
                json.dumps(
                    {
                        "schema_version": 4,
                        "run_id": "wrong-id",
                        "repo_root": "/tmp/project",
                        "base_revision": "replace-me",
                        "status": "planning",
                        "delivery_profile": "delivery-profile.yaml",
                        "final_report_path": "final-report.md",
                    }
                ),
                encoding="utf-8",
            )

            errors = self.validate_run.validate_run(run_dir)

        self.assertIn("run_id must match the run directory name", errors)
        self.assertIn("base_revision is unresolved", errors)
        self.assertTrue(any("delivery-profile.yaml" in error for error in errors))
        self.assertTrue(any("final-report.md" in error for error in errors))

    def test_validate_run_rejects_run_owned_paths_outside_the_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="contained",
                objective="Keep evidence in the ledger",
                base_revision="abc1234",
                teams=[],
            )
            outside = run_dir.parent / "outside.md"
            outside.write_text("external\n", encoding="utf-8")
            state_path = run_dir / "run-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["delivery_profile"] = "../outside.md"
            state["final_report_path"] = str(outside.resolve())
            state_path.write_text(json.dumps(state), encoding="utf-8")

            errors = self.validate_run.validate_run(run_dir)

        self.assertEqual(
            sum("must stay within the run directory" in error for error in errors),
            2,
            errors,
        )

    def test_validate_run_requires_team_ledger_and_directories_to_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="team-drift",
                objective="Detect team ledger drift",
                base_revision="abc1234",
                teams=["api"],
            )
            state_path = run_dir / "run-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["teams"] = []
            state_path.write_text(json.dumps(state), encoding="utf-8")

            errors = self.validate_run.validate_run(run_dir)

        self.assertIn("team directories and run-state teams must match", errors)

    def test_validate_run_rejects_unresolved_dispatch_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="not-ready",
                objective="Require a real dispatch contract",
                base_revision="abc1234",
                teams=["api"],
            )
            state_path = run_dir / "run-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["status"] = "ready"
            state_path.write_text(json.dumps(state), encoding="utf-8")

            errors = self.validate_run.validate_run(run_dir)

        self.assertIn("product_contract is unresolved before dispatch", errors)
        self.assertTrue(
            any("delivery-profile.yaml contains unresolved placeholders" in e for e in errors),
            errors,
        )
        self.assertTrue(
            any("team api contract contains unresolved placeholders" in e for e in errors),
            errors,
        )

    def test_validate_run_requires_ready_team_state_and_recorded_lead(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="team-readiness",
                objective="Require consistent team readiness",
                base_revision="abc1234",
                teams=["api"],
            )
            (run_dir / "product-contract.md").write_text("approved\n", encoding="utf-8")
            delivery = run_dir / "delivery-profile.yaml"
            delivery.write_text(
                delivery.read_text(encoding="utf-8").replace("replace-me", "resolved"),
                encoding="utf-8",
            )
            contract = run_dir / "teams/api/team-contract.yaml"
            contract.write_text(
                contract.read_text(encoding="utf-8").replace("replace-me", "resolved"),
                encoding="utf-8",
            )
            state_path = run_dir / "run-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.update(
                {
                    "status": "ready",
                    "product_contract": "product-contract.md",
                    "agents": [{"name": "api-lead"}],
                }
            )
            state["teams"][0].update(
                {"lead_agent": "api-lead", "mission": "Own the API"}
            )
            state["workflow_metrics"]["teams_activated"] = 1
            state_path.write_text(json.dumps(state), encoding="utf-8")

            errors = self.validate_run.validate_run(run_dir)

        self.assertIn("teams[0].state must be ready before dispatch", errors)
        self.assertFalse(any("lead_agent must reference" in error for error in errors), errors)

    def test_validate_run_enforces_completed_run_evidence_and_retirement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="premature-close",
                objective="Do not certify unfinished work",
                base_revision="abc1234",
                teams=[],
            )
            state_path = run_dir / "run-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["status"] = "completed"
            state["resources"] = [{"resource_id": "pane-1", "state": "active"}]
            state_path.write_text(json.dumps(state), encoding="utf-8")

            errors = self.validate_run.validate_run(run_dir)

        self.assertIn("completed run must record verification evidence", errors)
        self.assertIn("completed run has resources that are not retired", errors)
        self.assertIn("completed run final report contains unresolved placeholders", errors)

    def test_validate_run_requires_reconstructable_retirement_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="thin-retirement",
                objective="Require retirement evidence",
                base_revision="abc1234",
                teams=[],
            )
            state_path = run_dir / "run-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["status"] = "completed"
            state["resources"] = [{"state": "retired"}]
            state_path.write_text(json.dumps(state), encoding="utf-8")

            errors = self.validate_run.validate_run(run_dir)

        self.assertTrue(
            any("completed run resource entries" in error for error in errors),
            errors,
        )

    def test_validate_run_rejects_malformed_or_failed_completion_evidence(self) -> None:
        cases = (
            ["not evidence"],
            [{"gate": "integration", "result": "passed"}],
            [{"gate": "integration", "result": "failed", "evidence": ["tests"]}],
        )
        for verification in cases:
            with self.subTest(verification=verification), tempfile.TemporaryDirectory() as temp_dir:
                repo = Path(temp_dir)
                run_dir = self.init_run.initialize_run(
                    repo_root=repo,
                    run_id="bad-evidence",
                    objective="Require observed evidence",
                    base_revision="abc1234",
                    teams=[],
                )
                state_path = run_dir / "run-state.json"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                state["status"] = "completed"
                state["verification"] = verification
                state_path.write_text(json.dumps(state), encoding="utf-8")

                errors = self.validate_run.validate_run(run_dir)

            self.assertTrue(
                any("verification entries" in error for error in errors),
                errors,
            )

    def test_validate_run_requires_the_complete_final_report_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="thin-report",
                objective="Require a reconstructable report",
                base_revision="abc1234",
                teams=[],
            )
            (run_dir / "product-contract.md").write_text("approved\n", encoding="utf-8")
            delivery = run_dir / "delivery-profile.yaml"
            delivery.write_text(
                delivery.read_text(encoding="utf-8").replace("replace-me", "resolved"),
                encoding="utf-8",
            )
            (run_dir / "final-report.md").write_text("done\n", encoding="utf-8")
            state_path = run_dir / "run-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.update(
                {
                    "status": "completed",
                    "product_contract": "product-contract.md",
                    "verification": [
                        {
                            "gate": "integration",
                            "result": "passed",
                            "evidence": ["python3 -m unittest: passed"],
                        }
                    ],
                }
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")

            errors = self.validate_run.validate_run(run_dir)

        self.assertIn("completed run final report is missing required sections", errors)

    def test_validate_run_rejects_heading_only_final_report(self) -> None:
        report = "\n\n".join(
            (
                "# Workflow report",
                "## Outcome",
                "## Topology and models",
                "## Delivery evidence",
                "## Delivery profile and capabilities",
                "## Retirement",
                "## Usage telemetry",
                "## Residual risk",
            )
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="heading-only",
                objective="Require substantive reporting",
                base_revision="abc1234",
                teams=[],
            )
            (run_dir / "product-contract.md").write_text("approved\n", encoding="utf-8")
            delivery = run_dir / "delivery-profile.yaml"
            delivery.write_text(
                delivery.read_text(encoding="utf-8").replace("replace-me", "resolved"),
                encoding="utf-8",
            )
            (run_dir / "final-report.md").write_text(report, encoding="utf-8")
            state_path = run_dir / "run-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.update(
                {
                    "status": "completed",
                    "product_contract": "product-contract.md",
                    "verification": [
                        {
                            "gate": "integration",
                            "result": "passed",
                            "evidence": ["tests passed"],
                        }
                    ],
                }
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")

            errors = self.validate_run.validate_run(run_dir)

        self.assertIn("completed run final report is missing substantive fields", errors)

    def test_validate_run_accepts_a_fully_evidenced_completed_run(self) -> None:
        report = """# Workflow report

## Outcome
- Run ID/status: complete-run / completed
- Shipped scope: bounded feature

## Topology and models
- Teams activated: none

## Delivery evidence
- Independent verification: integration suite passed

## Delivery profile and capabilities
- Delivery level/constraints: bounded-production

## Retirement
- Final absence verification: no run-owned resources remain

## Usage telemetry
- Token availability: unavailable

## Residual risk
- Residual risks: []
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            run_dir = self.init_run.initialize_run(
                repo_root=repo,
                run_id="complete-run",
                objective="Accept a complete ledger",
                base_revision="abc1234",
                teams=[],
            )
            (run_dir / "product-contract.md").write_text("approved\n", encoding="utf-8")
            delivery = run_dir / "delivery-profile.yaml"
            delivery.write_text(
                delivery.read_text(encoding="utf-8").replace("replace-me", "resolved"),
                encoding="utf-8",
            )
            (run_dir / "final-report.md").write_text(report, encoding="utf-8")
            state_path = run_dir / "run-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.update(
                {
                    "status": "completed",
                    "product_contract": "product-contract.md",
                    "verification": [
                        {
                            "gate": "integration",
                            "result": "passed",
                            "evidence": ["python3 -m unittest: 258 passed"],
                        }
                    ],
                }
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")

            errors = self.validate_run.validate_run(run_dir)

        self.assertEqual(errors, [])

    def test_summary_reports_topology_evidence_and_unavailable_usage(self) -> None:
        summary = self.summarize_run.render_summary(
            {
                "run_id": "feature-001",
                "objective": "Ship the dashboard filter",
                "status": "verified",
                "workflow_metrics": {
                    "teams_activated": 2,
                    "agents_spawned": 5,
                    "dispatch_waves": 2,
                    "peak_concurrency": 3,
                    "retry_count": 1,
                },
                "verification": [{"gate": "integration", "result": "passed"}],
                "risks": ["Sentry MCP unavailable"],
                "usage": {
                    "tokens": {"availability": "unavailable", "total_tokens": None},
                    "context": {"availability": "partial", "per_agent": []},
                },
            }
        )

        self.assertIn("# Herdcraft run feature-001", summary)
        self.assertIn("Agents spawned: 5", summary)
        self.assertIn("integration: passed", summary)
        self.assertIn("Tokens: unavailable", summary)
        self.assertIn("Sentry MCP unavailable", summary)


if __name__ == "__main__":
    unittest.main()
