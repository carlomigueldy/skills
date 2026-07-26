"""Consumer-facing contract for the orchestra plugin package.

Constants below are deliberately re-declared rather than imported from the
validator: the test independently pins the contract the validator must
enforce, instead of asserting the validator agrees with itself.

The orchestra package (plugins/orchestra/**) does not exist yet at the time
this file is written -- it is being built against this executable spec by
other agents. Most tests here are therefore expected to FAIL until that
content lands; that is the intended workflow (see the approved plan), not a
bug in this test file.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_orchestra.py"
PLUGIN_ROOT = REPO_ROOT / "plugins" / "orchestra"

ROUTER_SKILL = "orchestra"
WORKFLOW_SKILLS = {
    "plan", "design", "spike", "fan-out", "implement", "verify", "review",
    "debug", "triage", "research", "refactor", "migrate", "upgrade",
    "harden", "perf", "cover", "document", "ship",
}
ALL_SKILLS = WORKFLOW_SKILLS | {ROUTER_SKILL}

REQUIRED_SECTIONS = (
    "Required inputs",
    "Lane plan",
    "Delegation contract",
    "Quality gates",
    "Evidence and completion",
    "Hard stops",
    "Deterministic outputs",
    "Failure and recovery",
)
MANDATORY_LITERALS = (
    "ROOT ORCHESTRATOR",
    "Do not implement inline",
    "Maximum delegation depth is two",
    "Evidence, not assertions",
    "sequential fresh-context role-pass",
    "HARD STOP",
    ".orchestra/",
)
LANE_TABLE_HEADER = "| Lane | Role | Tier |"
SHAPES = {
    "fan-out barrier",
    "pipeline",
    "judge panel",
    "loop-until-dry",
    "adversarial verify",
    "staged escalation",
    "sweep",
}
SHAPE_LINE = re.compile(r"(?m)^Shape:\s*(.+?)\s*$")

ROUTER_LITERAL = "returning control is not the end of the run"
WORKFLOW_INDEX_HEADING = "## Workflow index"
SKILL_REFERENCE = re.compile(r"/orchestra:([a-z][a-z0-9-]*)")

RESOURCE = re.compile(r"(?:\.\./)+(?:references|roles|schemas|examples)/[^\s)`]+")

SCHEMA_FILES = ("run.schema.json", "lane.schema.json", "finding.schema.json", "verdict.schema.json")
TIER_ENUM = ["deep", "standard", "fast"]

LANE_FIXTURES = ("parallel-subagents", "sequential-roles", "no-delegation")

MODEL_NAME_POSITIVES = ("grok-4", "claude-opus-4-5", "gpt-5.4", "gemini-3-pro", "Sonnet", "haiku")
MODEL_NAME_NEGATIVES = (
    "Claude Code",
    "Codex CLI",
    "OpenCode",
    "Grok Build",
    "claude-code",
    ".claude-plugin",
    "capability tier: deep",
    "claude-agent-sdk",
    "claude-plugin",
    "codex-plugin",
)


def _mutate_first_tier_enum(node) -> bool:
    """Append a bogus value to the first ``tier.enum`` found, in place.

    Walks the schema the same way ``_find_tier_enums`` reads it, so the
    mutation test stays correct regardless of how deeply the schema authors
    nest the tier enum (e.g. lane.schema.json nests it under
    properties.lanePlan.items.properties.tier, not at the top level).
    """
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "tier" and isinstance(value, dict) and isinstance(value.get("enum"), list):
                value["enum"] = [*value["enum"], "claude-opus-4-5"]
                return True
            if _mutate_first_tier_enum(value):
                return True
    elif isinstance(node, list):
        for item in node:
            if _mutate_first_tier_enum(item):
                return True
    return False


def _find_tier_enums(node):
    """Recursively locate every ``tier: {enum: [...]}`` in a schema document.

    The tier enum is not necessarily at the schema's top level -- e.g.
    lane.schema.json nests it under properties.lanePlan.items.properties.tier
    -- so the search must walk the whole document, not just properties.tier.
    """
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "tier" and isinstance(value, dict) and isinstance(value.get("enum"), list):
                found.append(value["enum"])
            found.extend(_find_tier_enums(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_find_tier_enums(item))
    return found


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_orchestra", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load orchestra validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_repo(temp_dir: str) -> Path:
    root = Path(temp_dir) / "repo"
    shutil.copytree(REPO_ROOT, root, ignore=shutil.ignore_patterns(".git", "dist", ".worktrees"))
    return root


def _load_schema_validator(name: str) -> Draft202012Validator:
    schema = json.loads((PLUGIN_ROOT / "schemas" / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _load_lane_schema_validator() -> Draft202012Validator:
    return _load_schema_validator("lane.schema.json")


def _load_run_schema_validator() -> Draft202012Validator:
    return _load_schema_validator("run.schema.json")


def _load_valid_lane_fixture() -> dict:
    """A real, currently-passing lane document to mutate one field at a time."""
    return json.loads((PLUGIN_ROOT / "examples/lanes/parallel-subagents.json").read_text(encoding="utf-8"))


def _lane_by_id(fixture: dict, lane_id: str) -> dict:
    return next(lane for lane in fixture["lanePlan"] if lane["id"] == lane_id)


def _result_by_id(fixture: dict, lane_id: str) -> dict:
    return next(result for result in fixture["normalizedLaneResults"] if result["laneId"] == lane_id)


def _minimal_valid_run_record() -> dict:
    """A minimal run.schema.json document, built here rather than as a new
    examples/ fixture -- the validator asserts an exact fixture set under
    examples/, and this is a schema-layer test, not a packaging fixture.
    """
    return {
        "schemaVersion": "1.0",
        "runId": "20260101T000000Z-example-run",
        "goal": "Ship the parser migration.",
        "host": "claude-code",
        "capabilities": {"parallelSubagents": True, "childDepth": 1, "isolatedContext": True},
        "tierResolution": {"deep": "high", "standard": "medium", "fast": "low"},
        "scheduler": "sequential-role-pass",
        "delegationDepth": 1,
        "isolation": "intact",
        "reopenCount": 0,
        "lanes": [{"laneId": "inventory", "resolvedTier": "fast", "wave": 0}],
    }


class OrchestraPackageContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    # -- Skill set: exact, bidirectional, bare names ------------------------

    def test_installable_package_contract_is_valid(self) -> None:
        self.assertEqual(self.validator.validate_repository(REPO_ROOT), [])

    def test_skill_set_is_exact_and_bidirectional(self) -> None:
        discovered = {path.parent.name for path in (PLUGIN_ROOT / "skills").glob("*/SKILL.md")}
        self.assertEqual(discovered, ALL_SKILLS)

    def test_missing_workflow_skill_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            shutil.rmtree(root / "plugins/orchestra/skills/fan-out")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("fan-out" in error and "missing" in error for error in errors), errors)

    def test_unexpected_extra_skill_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            stray = root / "plugins/orchestra/skills/docs/SKILL.md"
            stray.parent.mkdir(parents=True, exist_ok=True)
            stray.write_text("---\nname: docs\ndescription: Cut skill, renamed to document.\n---\n", encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("unexpected package skill: docs" in error for error in errors), errors)

    def test_skill_names_are_bare_with_no_stray_orchestra_prefix(self) -> None:
        for path in (PLUGIN_ROOT / "skills").glob("*/SKILL.md"):
            name = path.parent.name
            with self.subTest(skill=name):
                self.assertRegex(name, r"^[a-z0-9][a-z0-9-]*$")
                if name != ROUTER_SKILL:
                    self.assertFalse(name.startswith("orchestra-"), name)

    # -- Frontmatter ----------------------------------------------------------

    def test_frontmatter_is_exactly_two_keys_with_matching_directory_name(self) -> None:
        for path in (PLUGIN_ROOT / "skills").glob("*/SKILL.md"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(skill=path.parent.name):
                match = re.match(r"^---\nname:\s*([^\n]+)\ndescription:\s*([^\n]+)\n---", text)
                self.assertIsNotNone(match, "frontmatter must be exactly name + single-line description")
                self.assertEqual(match.group(1).strip().strip('"'), path.parent.name)

    def test_frontmatter_with_extra_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/skills/plan/SKILL.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace(
                "---\nname: plan\n", "---\nname: plan\nextra-key: not allowed\n", 1
            )
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("plan" in error and "frontmatter" in error for error in errors), errors)

    # -- Required H2 sections, present and in order --------------------------

    def test_workflow_skills_declare_required_sections_in_order(self) -> None:
        for name in WORKFLOW_SKILLS:
            path = PLUGIN_ROOT / "skills" / name / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            with self.subTest(skill=name):
                positions = [text.find(f"## {section}") for section in REQUIRED_SECTIONS]
                self.assertNotIn(-1, positions, positions)
                self.assertEqual(positions, sorted(positions))

    def test_out_of_order_sections_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/skills/verify/SKILL.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace("## Hard stops", "## HARDSTOPTEMP", 1)
            text = text.replace("## Required inputs", "## Hard stops", 1)
            text = text.replace("## HARDSTOPTEMP", "## Required inputs", 1)
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("verify" in error and "in order" in error for error in errors), errors)

    # -- Mandatory literal phrases --------------------------------------------

    def test_workflow_skills_declare_mandatory_literals_and_lane_table(self) -> None:
        for name in WORKFLOW_SKILLS:
            path = PLUGIN_ROOT / "skills" / name / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            with self.subTest(skill=name):
                for phrase in MANDATORY_LITERALS:
                    self.assertIn(phrase, text)
                self.assertIn(LANE_TABLE_HEADER, text)

    def test_missing_mandatory_literal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/skills/implement/SKILL.md"
            text = path.read_text(encoding="utf-8").replace("HARD STOP", "important pause")
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("implement" in error and "HARD STOP" in error for error in errors), errors)

    def test_missing_lane_table_header_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/skills/review/SKILL.md"
            text = path.read_text(encoding="utf-8").replace(LANE_TABLE_HEADER, "| Lane | Owner | Cost |")
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("review" in error and "lane table header" in error for error in errors), errors)

    # -- Shape line ------------------------------------------------------------

    def test_workflow_skills_declare_a_canonical_shape_line(self) -> None:
        for name in WORKFLOW_SKILLS:
            path = PLUGIN_ROOT / "skills" / name / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            with self.subTest(skill=name):
                match = SHAPE_LINE.search(text)
                self.assertIsNotNone(match, "missing 'Shape: <shape>' line")
                self.assertIn(match.group(1), SHAPES)

    def test_non_canonical_shape_line_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/skills/spike/SKILL.md"
            text = SHAPE_LINE.sub("Shape: fan-out + kill gate", path.read_text(encoding="utf-8"), count=1)
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("spike" in error and "Shape line" in error for error in errors), errors)

    # -- Router -----------------------------------------------------------------

    def test_router_declares_the_control_return_invariant(self) -> None:
        text = (PLUGIN_ROOT / "skills" / ROUTER_SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(ROUTER_LITERAL, text)

    def test_router_workflow_index_names_every_workflow_exactly_once(self) -> None:
        text = (PLUGIN_ROOT / "skills" / ROUTER_SKILL / "SKILL.md").read_text(encoding="utf-8")
        start = text.find(WORKFLOW_INDEX_HEADING)
        self.assertNotEqual(start, -1, "router missing Workflow index section")
        next_heading = text.find("\n## ", start + len(WORKFLOW_INDEX_HEADING))
        section = text[start:next_heading] if next_heading != -1 else text[start:]
        counts = Counter(SKILL_REFERENCE.findall(section))
        for name in WORKFLOW_SKILLS:
            self.assertEqual(counts.get(name, 0), 1, f"{name} named {counts.get(name, 0)} times")

    def test_router_never_references_an_unknown_skill(self) -> None:
        text = (PLUGIN_ROOT / "skills" / ROUTER_SKILL / "SKILL.md").read_text(encoding="utf-8")
        refs = set(SKILL_REFERENCE.findall(text))
        self.assertLessEqual(refs, WORKFLOW_SKILLS, refs - WORKFLOW_SKILLS)

    def test_router_workflow_index_missing_a_workflow_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/skills/orchestra/SKILL.md"
            text = path.read_text(encoding="utf-8").replace("/orchestra:ship", "/orchestra:shipx")
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("workflow index missing" in error and "ship" in error for error in errors), errors)

    def test_router_referencing_unknown_skill_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/skills/orchestra/SKILL.md"
            text = path.read_text(encoding="utf-8") + "\n\nSee also /orchestra:docs for prose output.\n"
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("unknown skill" in error and "docs" in error for error in errors), errors)

    # -- Resource links ----------------------------------------------------------

    def test_resource_links_resolve_and_never_escape_the_package(self) -> None:
        package_root = PLUGIN_ROOT.resolve()
        for path in (PLUGIN_ROOT / "skills").glob("*/SKILL.md"):
            text = path.read_text(encoding="utf-8")
            for raw in RESOURCE.findall(text):
                resolved = (path.parent / raw.rstrip(".,")).resolve()
                with self.subTest(skill=path.parent.name, resource=raw):
                    self.assertTrue(resolved.exists(), raw)
                    self.assertTrue(str(resolved).startswith(str(package_root)), raw)

    def test_broken_resource_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/skills/fan-out/SKILL.md"
            text = path.read_text(encoding="utf-8") + "\n\nSee ../../references/does-not-exist.md.\n"
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("missing local resource" in error for error in errors), errors)

    def test_resource_link_that_escapes_the_package_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            # RESOURCE only matches when references|roles|schemas|examples sits
            # immediately after the ../ chain -- a real escaping reference
            # (e.g. into a sibling plugin's own references/) would need an
            # intermediate directory name and so would never match at all, and
            # the repo has no bare top-level references/roles/schemas/examples/
            # to overshoot into by accident. So this decoy is planted
            # deliberately: a resource folder that is a sibling of
            # plugins/orchestra/, not inside it, reachable by a plain ../ chain.
            decoy = root / "plugins/schemas/escaped.json"
            decoy.parent.mkdir(parents=True, exist_ok=True)
            decoy.write_text("{}", encoding="utf-8")
            path = root / "plugins/orchestra/skills/fan-out/SKILL.md"
            text = path.read_text(encoding="utf-8") + "\n\nSee ../../../schemas/escaped.json.\n"
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("escapes the package" in error for error in errors), errors)

    # -- Schemas -----------------------------------------------------------------

    def test_packaged_schemas_parse_declare_required_fields_and_exact_tier_enum(self) -> None:
        found_tier_enum = False
        for name in SCHEMA_FILES:
            path = PLUGIN_ROOT / "schemas" / name
            schema = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)
                self.assertTrue(schema.get("required"), "schema must declare required fields")
            for enum in _find_tier_enums(schema):
                found_tier_enum = True
                self.assertEqual(sorted(enum), sorted(TIER_ENUM))
        self.assertTrue(found_tier_enum, "no packaged schema declares a tier enum")

    def test_invalid_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/schemas/lane.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["type"] = "not-a-real-type"
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("invalid Draft202012 schema" in error for error in errors), errors)

    def test_schema_without_required_fields_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/schemas/finding.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["required"] = []
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("non-empty required" in error for error in errors), errors)

    def test_tier_enum_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/schemas/lane.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(_mutate_first_tier_enum(schema), "fixture schema has no tier enum to mutate")
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("tier enum" in error for error in errors), errors)

    # -- Lane fixtures -------------------------------------------------------------

    def test_lane_fixtures_share_plan_and_results_but_differ_in_dispatch(self) -> None:
        fixtures = {
            name: json.loads((PLUGIN_ROOT / "examples/lanes" / f"{name}.json").read_text(encoding="utf-8"))
            for name in LANE_FIXTURES
        }
        for key in ("lanePlan", "normalizedLaneResults"):
            values = [json.dumps(fixtures[name][key], sort_keys=True) for name in LANE_FIXTURES]
            self.assertEqual(len(set(values)), 1, key)
        dispatches = [json.dumps(fixtures[name]["dispatch"], sort_keys=True) for name in LANE_FIXTURES]
        self.assertEqual(len(set(dispatches)), len(LANE_FIXTURES), "dispatch must differ across all three")

    def test_diverging_lane_plan_fixture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/examples/lanes/no-delegation.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["lanePlan"] = {"diverged": True}
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("lanePlan" in error and "byte-identical" in error for error in errors), errors)

    def test_identical_dispatch_fixture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            target = root / "plugins/orchestra/examples/lanes/sequential-roles.json"
            source = root / "plugins/orchestra/examples/lanes/parallel-subagents.json"
            payload = json.loads(target.read_text(encoding="utf-8"))
            payload["dispatch"] = json.loads(source.read_text(encoding="utf-8"))["dispatch"]
            target.write_text(json.dumps(payload), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("dispatch must differ" in error for error in errors), errors)

    def test_lane_fixtures_validate_cleanly_against_lane_schema(self) -> None:
        """The fixtures don't just agree with each other -- they satisfy the schema.

        check_schema only proves lane.schema.json is well-formed; it never
        instantiates it against a document. This is the missing positive
        check: every conditional invariant in the schema is exercised
        against a real fixture and must accept it.
        """
        validator = _load_lane_schema_validator()
        for name in LANE_FIXTURES:
            payload = json.loads((PLUGIN_ROOT / "examples/lanes" / f"{name}.json").read_text(encoding="utf-8"))
            with self.subTest(fixture=name):
                self.assertEqual(list(validator.iter_errors(payload)), [])

    def test_lane_fixture_schema_violation_is_caught_end_to_end(self) -> None:
        """Prove the validator actually wires the schema check into validate_repository.

        Without this, a fixture could drift out of sync with lane.schema.json
        and CI would stay green -- iter_errors would never run against it.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/examples/lanes/parallel-subagents.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            # Give a write-mode lane an empty ownedPaths: a real, schema-checked
            # violation, not just the fixtures disagreeing with each other.
            lane = next(lane for lane in payload["lanePlan"] if lane["id"] == "implement-parser")
            self.assertEqual(lane["mode"], "write")
            lane["ownedPaths"] = []
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("schema validation" in error for error in errors), errors)

    # -- Packaged-path safety --------------------------------------------------------

    def test_dot_orchestra_is_never_packaged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            stray = root / "plugins/orchestra/.orchestra/current"
            stray.parent.mkdir(parents=True, exist_ok=True)
            stray.write_text("stray-run\n", encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any(".orchestra" in error for error in errors), errors)

    # -- No hardcoded model names: two-layer defense ----------------------------------

    def test_model_name_denylist_matches_known_positives(self) -> None:
        for token in MODEL_NAME_POSITIVES:
            with self.subTest(token=token):
                self.assertTrue(self.validator.find_model_name_violations(token), token)

    def test_model_name_denylist_negative_control_spares_the_plugins_own_host_names(self) -> None:
        """The plugin must be able to talk about its own supported hosts.

        An over-broad denylist that also blocks "Claude Code", "Codex CLI",
        "OpenCode", "Grok Build", or the allowlisted compound tokens is a real
        failure mode -- it would silently make the plugin's own
        host-compatibility documentation impossible to write.
        """
        for token in MODEL_NAME_NEGATIVES:
            with self.subTest(token=token):
                self.assertEqual(self.validator.find_model_name_violations(token), [], token)

    def test_no_hardcoded_model_names_anywhere_in_the_packaged_plugin(self) -> None:
        for path in PLUGIN_ROOT.rglob("*"):
            if path.is_file() and path.suffix in (".md", ".json", ".py"):
                text = path.read_text(encoding="utf-8")
                with self.subTest(path=path.relative_to(PLUGIN_ROOT)):
                    self.assertEqual(self.validator.find_model_name_violations(text), [], path)

    def test_hardcoded_model_name_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/skills/plan/SKILL.md"
            text = path.read_text(encoding="utf-8") + "\n\nUse claude-opus-4-5 for this role.\n"
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("hardcoded model reference" in error for error in errors), errors)

    def test_hardcoded_model_name_in_python_source_is_rejected(self) -> None:
        """Pin .py coverage with a positive control, not just the negative one above.

        install-grok.py is the package's only executable file and the exact
        boundary where an abstract tier (deep/standard/fast) gets mapped onto
        a concrete host setting -- precisely where a hardcoded model id would
        be tempting to write. A denylist that includes .py in its suffix
        filter but is never proven to catch anything there is the same class
        of gap as not scanning .py at all.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/scripts/install-grok.py"
            text = path.read_text(encoding="utf-8") + '\n# TODO: pin to claude-opus-4-5 once stable.\n'
            path.write_text(text, encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("hardcoded model reference" in error for error in errors), errors)

    # -- Registration --------------------------------------------------------------------

    def test_registration_is_complete_across_marketplace_and_release_please(self) -> None:
        marketplace = json.loads((REPO_ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertTrue(any(
            entry.get("name") == "orchestra" and entry.get("source") == "./plugins/orchestra"
            for entry in marketplace.get("plugins", [])
        ))
        release = json.loads((REPO_ROOT / "release-please-config.json").read_text(encoding="utf-8"))
        config = release["packages"]["plugins/orchestra"]
        self.assertEqual(config["release-type"], "simple")
        paths = {item["path"] for item in config["extra-files"]}
        self.assertIn(".claude-plugin/plugin.json", paths)
        self.assertIn(".codex-plugin/plugin.json", paths)
        manifest = json.loads((REPO_ROOT / ".release-please-manifest.json").read_text(encoding="utf-8"))
        version = json.loads((PLUGIN_ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        self.assertEqual(manifest["plugins/orchestra"], version)
        self.assertEqual((PLUGIN_ROOT / "version.txt").read_text(encoding="utf-8").strip(), version)

    def test_missing_codex_extra_file_registration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "release-please-config.json"
            config = json.loads(path.read_text(encoding="utf-8"))
            config["packages"]["plugins/orchestra"]["extra-files"] = [
                item for item in config["packages"]["plugins/orchestra"]["extra-files"]
                if item["path"] != ".codex-plugin/plugin.json"
            ]
            path.write_text(json.dumps(config), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("synchronize .codex-plugin/plugin.json" in error for error in errors), errors)

    def test_conflicting_manifest_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/.codex-plugin/plugin.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["version"] = "9.9.9"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("versions must match" in error for error in errors), errors)

    def test_codex_manifest_has_a_distinct_native_validator(self) -> None:
        self.assertEqual(self.validator.validate_codex_manifest(PLUGIN_ROOT / ".codex-plugin/plugin.json"), [])
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = Path(temp_dir) / "plugin.json"
            data = json.loads((PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
            data.pop("skills")
            manifest.write_text(json.dumps(data), encoding="utf-8")
            errors = self.validator.validate_codex_manifest(manifest)
        self.assertTrue(any("skills" in error for error in errors), errors)


class OrchestraLaneSchemaInvariantTest(unittest.TestCase):
    """Negative controls for lane.schema.json's conditional invariants.

    A conditional invariant with no negative control is indistinguishable
    from a comment: nothing proves the schema actually rejects the case it
    claims to guard against. Each test here mutates one field of a real,
    currently-passing fixture and asserts the schema now rejects it.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = _load_lane_schema_validator()

    def assert_rejected(self, document: dict) -> None:
        errors = list(self.validator.iter_errors(document))
        self.assertTrue(errors, "expected lane.schema.json to reject the mutated document")

    def test_read_only_lane_with_owned_paths_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        lane = _lane_by_id(fixture, "inventory")
        self.assertEqual(lane["mode"], "read_only")
        lane["ownedPaths"] = ["src/should-not-own.ts"]
        self.assert_rejected(fixture)

    def test_write_lane_with_empty_owned_paths_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        lane = _lane_by_id(fixture, "implement-parser")
        self.assertEqual(lane["mode"], "write")
        lane["ownedPaths"] = []
        self.assert_rejected(fixture)

    def test_depth_two_lane_with_non_mechanic_role_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        lane = _lane_by_id(fixture, "migrate-call-sites")
        self.assertEqual(lane["depth"], 2)
        lane["role"] = "builder"
        self.assert_rejected(fixture)

    def test_mechanic_lane_without_parent_lane_id_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        lane = _lane_by_id(fixture, "migrate-call-sites")
        self.assertEqual(lane["role"], "mechanic")
        del lane["parentLaneId"]
        self.assert_rejected(fixture)

    def test_deep_adversary_lane_without_escalation_trigger_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        lane = _lane_by_id(fixture, "falsify")
        self.assertEqual(lane["role"], "adversary")
        lane["tier"] = "deep"
        self.assert_rejected(fixture)

    def test_verified_result_with_empty_evidence_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        result = _result_by_id(fixture, "inventory")
        self.assertEqual(result["status"], "verified")
        result["evidence"] = []
        self.assert_rejected(fixture)

    def test_blocked_result_without_escalation_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        result = _result_by_id(fixture, "inventory")
        result["status"] = "blocked"
        self.assert_rejected(fixture)

    def test_self_execute_dispatch_requires_zero_child_depth(self) -> None:
        """Gap 2: the old check only asserted hoisted was an array -- a type
        it already declared, so it verified nothing. The real invariant is
        that self-execute means the host has no child dispatch at all.
        """
        fixture = _load_valid_lane_fixture()
        fixture["dispatch"]["scheduler"] = "self-execute"
        self.assertEqual(fixture["capabilities"]["childDepth"], 1)
        self.assert_rejected(fixture)


class OrchestraRunSchemaInvariantTest(unittest.TestCase):
    """Negative controls for run.schema.json's conditional invariants."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = _load_run_schema_validator()

    def assert_rejected(self, document: dict) -> None:
        errors = list(self.validator.iter_errors(document))
        self.assertTrue(errors, "expected run.schema.json to reject the mutated document")

    def test_minimal_valid_run_record_validates_cleanly(self) -> None:
        self.assertEqual(list(self.validator.iter_errors(_minimal_valid_run_record())), [])

    def test_deep_delegation_without_justification_is_rejected(self) -> None:
        record = _minimal_valid_run_record()
        record["delegationDepth"] = 3
        self.assert_rejected(record)

    def test_degraded_isolation_without_verdict_cap_is_rejected(self) -> None:
        record = _minimal_valid_run_record()
        record["isolation"] = "degraded"
        self.assert_rejected(record)

    def test_reopen_count_over_the_cap_is_rejected(self) -> None:
        record = _minimal_valid_run_record()
        record["reopenCount"] = 4
        self.assert_rejected(record)

    def test_parallel_subagents_scheduler_requires_the_capability_flag(self) -> None:
        record = _minimal_valid_run_record()
        record["scheduler"] = "parallel-subagents"
        record["capabilities"]["parallelSubagents"] = False
        self.assert_rejected(record)


if __name__ == "__main__":
    unittest.main()
