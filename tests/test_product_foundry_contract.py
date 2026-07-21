"""Consumer-facing contract for the product-foundry plugin package."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_product_foundry.py"
PLUGIN_ROOT = REPO_ROOT / "plugins" / "product-foundry"

PUBLIC_SKILLS = {"product-foundry", "implement-prd"}
PHASE_SKILLS = {
    "foundry-intake",
    "foundry-research",
    "foundry-company-strategy",
    "foundry-mvp",
    "foundry-low-fidelity",
    "foundry-brand",
    "foundry-architecture",
    "foundry-agent-harness",
    "foundry-prd",
    "foundry-high-fidelity",
    "foundry-go-to-market",
    "foundry-readiness",
    "foundry-handoff",
}
PHASE_SECTIONS = {
    "Required inputs",
    "Deterministic outputs",
    "Completion criteria",
    "Invalidation rules",
    "Participation gate",
    "Approval gate",
}
DECISION_METADATA = {"rationale", "evidence", "assumptions", "confidence", "risks", "revisit conditions"}
PROTOTYPE_STATES = {"loading", "empty", "error", "permission", "success", "validation"}
ADAPTER_FIXTURES = ("claude", "codex-structured", "plain-fallback")


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_product_foundry", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load product-foundry validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProductFoundryPackageContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_installable_package_contract_is_valid(self) -> None:
        self.assertEqual(self.validator.validate_repository(REPO_ROOT), [])

    def test_both_hosts_discover_the_same_public_and_phase_skills(self) -> None:
        expected = PUBLIC_SKILLS | PHASE_SKILLS
        discovered = {
            path.parent.name
            for path in (PLUGIN_ROOT / "skills").glob("*/SKILL.md")
        }
        self.assertEqual(discovered, expected)

        for manifest_name in (".claude-plugin", ".codex-plugin"):
            manifest = json.loads(
                (PLUGIN_ROOT / manifest_name / "plugin.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["name"], "product-foundry")
        codex_manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(codex_manifest["skills"], "./skills/")

    def test_generated_examples_match_the_handoff_schema_contract(self) -> None:
        examples = sorted((PLUGIN_ROOT / "examples").glob("*/implementation-manifest.json"))
        self.assertEqual([path.parent.name for path in examples], ["advanced-custom", "lean", "standard"])
        for example in examples:
            payload = json.loads(example.read_text(encoding="utf-8"))
            self.assertEqual(self.validator.validate_manifest(payload), [], example)

    def test_manifest_requirements_are_unique_traceable_and_testable(self) -> None:
        for example in (PLUGIN_ROOT / "examples").glob("*/implementation-manifest.json"):
            payload = json.loads(example.read_text(encoding="utf-8"))
            self.assertTrue(payload["requirements"], example)
            self.assertEqual(self.validator.validate_manifest(payload), [], example)
        invalid = json.loads((PLUGIN_ROOT / "examples/standard/implementation-manifest.json").read_text(encoding="utf-8"))
        invalid["requirements"].append(dict(invalid["requirements"][0]))
        self.assertTrue(any("duplicate requirement id" in error for error in self.validator.validate_manifest(invalid)))
        invalid = json.loads((PLUGIN_ROOT / "examples/standard/implementation-manifest.json").read_text(encoding="utf-8"))
        invalid["requirements"][0]["traceability"] = {"evidence": [], "assumptions": []}
        self.assertTrue(any("traceability" in error for error in self.validator.validate_manifest(invalid)))

    def test_packaged_json_schemas_execute_and_required_contract_mutations_fail(self) -> None:
        self.assertEqual(self.validator.validate_repository(REPO_ROOT), [])
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            shutil.copytree(REPO_ROOT, root, ignore=shutil.ignore_patterns(".git", "dist", ".worktrees"))
            path = root / "plugins/product-foundry/schemas/implementation-manifest.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["required"].remove("requirements")
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("schema contract" in error and "requirements" in error for error in errors), errors)
        manifest = json.loads((PLUGIN_ROOT / "examples/standard/implementation-manifest.json").read_text(encoding="utf-8"))
        manifest["inputFingerprints"]["docs/product/prd.md"] = None
        self.assertTrue(any("inputFingerprints" in error for error in self.validator.validate_manifest(manifest)))
        manifest = json.loads((PLUGIN_ROOT / "examples/standard/implementation-manifest.json").read_text(encoding="utf-8"))
        manifest["reconciliation"]["partialTasks"] = ["TASK-404"]
        self.assertTrue(any("unknown implementation task id" in error for error in self.validator.validate_manifest(manifest)))

    def test_every_phase_has_independent_participation_and_uniform_contract_sections(self) -> None:
        for phase in PHASE_SKILLS:
            text = (PLUGIN_ROOT / "skills" / phase / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(phase=phase):
                for section in PHASE_SECTIONS:
                    self.assertIn(f"## {section}", text)
                self.assertIn("Interview me", text)
                self.assertIn("Decide for me", text)
                for field in DECISION_METADATA:
                    self.assertIn(field, text)

    def test_decision_schema_uses_exact_modes_and_delegation_metadata(self) -> None:
        schema = json.loads((PLUGIN_ROOT / "schemas/decision.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["mode"]["enum"], ["Interview me", "Decide for me"])
        required = set(schema["required"])
        self.assertTrue({"rationale", "evidence", "assumptions", "confidence", "risks", "revisitConditions"} <= required)

    def test_phase_contract_violation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            shutil.copytree(REPO_ROOT, root, ignore=shutil.ignore_patterns(".git", "dist", ".worktrees"))
            path = root / "plugins/product-foundry/skills/foundry-mvp/SKILL.md"
            path.write_text(path.read_text(encoding="utf-8").replace("## Approval gate", "## Gate"), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("foundry-mvp" in error and "Approval gate" in error for error in errors), errors)

    def test_roster_requires_find_skills_fail_closed_recovery(self) -> None:
        text = (PLUGIN_ROOT / "skills/implement-prd/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("find-skills", text)
        self.assertIn("fail closed", text)
        self.assertIn("installation", text)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            shutil.copytree(REPO_ROOT, root, ignore=shutil.ignore_patterns(".git", "dist", ".worktrees"))
            path = root / "plugins/product-foundry/skills/implement-prd/SKILL.md"
            path.write_text(path.read_text(encoding="utf-8").replace("fail closed", "continue"), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("find-skills fail-closed" in error for error in errors), errors)

    def test_fresh_resume_contract_preserves_verification_and_reconciles_state(self) -> None:
        required = {"inputFingerprints", "unresolvedBlockers", "reconciliation", "changedInputInvalidation"}
        for example in (PLUGIN_ROOT / "examples").glob("*/implementation-manifest.json"):
            payload = json.loads(example.read_text(encoding="utf-8"))
            self.assertTrue(required <= payload.keys(), example)
            self.assertEqual(self.validator.validate_manifest(payload), [], example)
        task_state = json.loads((PLUGIN_ROOT / "templates/docs/task-state.json").read_text(encoding="utf-8"))
        self.assertEqual(self.validator.validate_task_state(task_state), [])
        invalid = json.loads(json.dumps(task_state))
        invalid["tasks"][0].pop("verificationEvidence")
        self.assertTrue(any("verificationEvidence" in error for error in self.validator.validate_task_state(invalid)))
        verified_without_evidence = json.loads(json.dumps(task_state))
        verified_without_evidence["tasks"][0]["status"] = "verified"
        self.assertTrue(any("verified task" in error for error in self.validator.validate_task_state(verified_without_evidence)))
        manifest = json.loads((PLUGIN_ROOT / "examples/standard/implementation-manifest.json").read_text(encoding="utf-8"))
        manifest.pop("inputFingerprints")
        self.assertTrue(any("inputFingerprints" in error for error in self.validator.validate_manifest(manifest)))

    def test_task_state_uses_typed_fingerprints_and_resolvable_reconciliation_ids(self) -> None:
        task_state = json.loads((PLUGIN_ROOT / "templates/docs/task-state.json").read_text(encoding="utf-8"))
        task_state["tasks"][0]["inputFingerprints"] = None
        self.assertTrue(any("inputFingerprints" in error for error in self.validator.validate_task_state(task_state)))
        task_state = json.loads((PLUGIN_ROOT / "templates/docs/task-state.json").read_text(encoding="utf-8"))
        task_state["tasks"][0]["inputFingerprints"] = "docs/implementation-manifest.json"
        self.assertTrue(any("inputFingerprints" in error for error in self.validator.validate_task_state(task_state)))
        task_state = json.loads((PLUGIN_ROOT / "templates/docs/task-state.json").read_text(encoding="utf-8"))
        task_state["reconciliation"]["partialTasks"] = ["TASK-404"]
        self.assertTrue(any("unknown task id" in error for error in self.validator.validate_task_state(task_state)))
        task_state = json.loads((PLUGIN_ROOT / "templates/docs/task-state.json").read_text(encoding="utf-8"))
        task_state["tasks"].append(dict(task_state["tasks"][0]))
        self.assertTrue(any("duplicate task id" in error for error in self.validator.validate_task_state(task_state)))
        task_state = json.loads((PLUGIN_ROOT / "templates/docs/task-state.json").read_text(encoding="utf-8"))
        task_state["tasks"][0]["status"] = "verified"
        task_state["tasks"][0]["verificationEvidence"] = ["tests passed"]
        self.assertTrue(any("must be preserved" in error for error in self.validator.validate_task_state(task_state)))

    def test_agent_roster_enforces_ownership_tools_and_delegation_depth(self) -> None:
        roster = json.loads((PLUGIN_ROOT / "templates/docs/agent-roster.json").read_text(encoding="utf-8"))
        self.assertEqual(self.validator.validate_agent_roster(roster), [])
        without_tools = json.loads(json.dumps(roster))
        without_tools["agents"][0].pop("tools")
        self.assertTrue(any("tools" in error for error in self.validator.validate_agent_roster(without_tools)))
        deep_without_reason = json.loads(json.dumps(roster))
        deep_without_reason["delegationDepth"] = 3
        self.assertTrue(any("deeperDelegationJustification" in error for error in self.validator.validate_agent_roster(deep_without_reason)))

    def test_agent_roster_schema_rejects_deep_delegation_without_justification(self) -> None:
        schema = json.loads((PLUGIN_ROOT / "schemas/agent-roster.schema.json").read_text(encoding="utf-8"))
        roster = json.loads((PLUGIN_ROOT / "templates/docs/agent-roster.json").read_text(encoding="utf-8"))
        roster["delegationDepth"] = 3
        errors = list(Draft202012Validator(schema).iter_errors(roster))
        self.assertTrue(any("deeperDelegationJustification" in error.message for error in errors), errors)

    def test_prototype_skills_fail_closed_with_shared_policy_recovery(self) -> None:
        for name in ("foundry-low-fidelity", "foundry-high-fidelity"):
            text = (PLUGIN_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=name):
                for phrase in ("../../references/policies.md", "fail closed", "installation", "recovery guidance"):
                    self.assertIn(phrase, text)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            shutil.copytree(REPO_ROOT, root, ignore=shutil.ignore_patterns(".git", "dist", ".worktrees"))
            path = root / "plugins/product-foundry/skills/foundry-high-fidelity/SKILL.md"
            path.write_text(path.read_text(encoding="utf-8").replace("../../references/policies.md", "../../references/missing.md"), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("foundry-high-fidelity" in error and "frontend-design fail-closed" in error for error in errors), errors)

    def test_platform_adapter_fixtures_normalize_to_one_answer_contract(self) -> None:
        adapter = (PLUGIN_ROOT / "references/platform-adapter.md").read_text(encoding="utf-8")
        for phrase in ("runtime", "stable id", "recommended", "consequence", "one question", "wait", "silence", "same shape"):
            self.assertIn(phrase, adapter)
        normalized = []
        for name in ADAPTER_FIXTURES:
            payload = json.loads((PLUGIN_ROOT / "examples/adapters" / f"{name}.json").read_text(encoding="utf-8"))
            normalized.append(payload["normalizedAnswer"])
        self.assertEqual(normalized, [normalized[0]] * len(normalized))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            shutil.copytree(REPO_ROOT, root, ignore=shutil.ignore_patterns(".git", "dist", ".worktrees"))
            path = root / "plugins/product-foundry/examples/adapters/codex-structured.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["question"]["options"][0].pop("consequence")
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("consequence" in error and "codex-structured" in error for error in errors), errors)

    def test_prototypes_cover_all_interactive_states_and_accessibility_basics(self) -> None:
        for name in ("low-fidelity", "high-fidelity"):
            path = PLUGIN_ROOT / "templates/prototypes" / name / "index.html"
            text = path.read_text(encoding="utf-8")
            with self.subTest(prototype=name):
                for state in PROTOTYPE_STATES:
                    self.assertIn(f'data-state="{state}"', text)
                self.assertIn("aria-live", text)
                self.assertIn("addEventListener", text)
                self.assertIn("<button", text)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            shutil.copytree(REPO_ROOT, root, ignore=shutil.ignore_patterns(".git", "dist", ".worktrees"))
            path = root / "plugins/product-foundry/templates/prototypes/high-fidelity/index.html"
            path.write_text(path.read_text(encoding="utf-8").replace('data-state="permission"', ""), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("permission" in error and "high-fidelity" in error for error in errors), errors)

    def test_codex_manifest_has_a_distinct_native_validator(self) -> None:
        self.assertEqual(self.validator.validate_codex_manifest(PLUGIN_ROOT / ".codex-plugin/plugin.json"), [])
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = Path(temp_dir) / "plugin.json"
            data = json.loads((PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
            data.pop("skills")
            manifest.write_text(json.dumps(data), encoding="utf-8")
            errors = self.validator.validate_codex_manifest(manifest)
        self.assertTrue(any("skills" in error for error in errors), errors)

    def test_release_please_uses_simple_versioning_with_matching_version_txt(self) -> None:
        release = json.loads((REPO_ROOT / "release-please-config.json").read_text(encoding="utf-8"))
        config = release["packages"]["plugins/product-foundry"]
        self.assertEqual(config["release-type"], "simple")
        manifest = json.loads((PLUGIN_ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual((PLUGIN_ROOT / "version.txt").read_text(encoding="utf-8").strip(), manifest["version"])

    def test_missing_required_phase_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            shutil.copytree(REPO_ROOT, root, ignore=shutil.ignore_patterns(".git", "dist", ".worktrees"))
            (root / "plugins/product-foundry/skills/foundry-prd/SKILL.md").unlink()
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("foundry-prd" in error for error in errors), errors)

    def test_conflicting_manifest_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            shutil.copytree(REPO_ROOT, root, ignore=shutil.ignore_patterns(".git", "dist", ".worktrees"))
            path = root / "plugins/product-foundry/.codex-plugin/plugin.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["version"] = "9.9.9"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("versions must match" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
