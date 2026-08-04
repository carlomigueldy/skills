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

import contextlib
import importlib.util
import io
import json
import re
import shutil
import sys
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
# Run fixtures are a directory, not a pinned list. The lane fixtures are an
# exact triple because their whole point is that one lane plan dispatches three
# different ways; run records only have to be individually valid, so the
# contract here is that the directory is non-empty and covers both chain
# shapes (see test_run_fixtures_cover_the_chain_of_one_and_the_chained_shape).
RUN_FIXTURE_DIR = PLUGIN_ROOT / "examples/runs"

# ownedPaths entries that declare no checkable territory. Every one of these
# carries nothing but whitespace, separators and dots, so it names no path at
# all -- and each used to normalize to zero path segments, which is what made
# G7 silently unenforceable: a lane with no segments intersects nothing, so a
# lane claiming the whole repository conflicted with no lane at all and the
# plan read as G7-clean. They also hollowed out lane.schema.json's
# `mode: write -> ownedPaths minItems 1` conditional, since `minLength: 1`
# alone let `[" "]` satisfy "a write lane owns at least one path".
DEGENERATE_OWNED_PATHS = (".", "/", " ", "./", "//", "./.", "\t\n ", "   ")
# The other direction: ordinary declarations the tightened rule must not
# swallow. `./src/parser/` and `.github/workflows/validate.yml` are the
# load-bearing pair -- both begin with a dot, and a rule keyed off a leading
# dot rather than off the absence of any meaningful character would lose them.
REAL_OWNED_PATHS = (
    "src/parser/",
    "src/parser/callers.ts",
    "src/parser.ts",
    "src/parser-utils/index.ts",
    "./src/parser/",
    ".github/workflows/validate.yml",
    "Makefile",
)
# Other spellings of the same territory. Every one of these was schema-clean
# and produced NO G7 error when two write lanes shared a wave, because the old
# rule asked only for one character that was not whitespace, a slash or a dot,
# and then split on "/" -- a splitter, not a path normalizer.
#
# `src/..`, `docs/..` and `x/../..` ARE the repository root under POSIX
# resolution; kept as literal ".." segments they intersect nothing, which is
# the degenerate-path hole reopened under a new spelling. The rest fork one
# path into two owners that never collide: a backslash is not a separator, a
# space beside a separator survives into the segment, and a zero-width
# character is not `\s` in Python, so it was neither stripped nor rejected --
# an INVISIBLE character silently splitting one territory in two. A trailing
# newline is here too, for the same reason the anchored patterns had to stop
# using `$`.
NON_RELATIVE_OWNED_PATHS = (
    "src/..",
    "docs/..",
    "x/../..",
    "src/../lib",
    "src/./lib",
    "..",
    "../src",
    "src\\lib",
    "src/ lib",
    "src /lib",
    " src/lib",
    "src/lib ",
    "src\tlib",
    "src/lib\n",
    "src/lib​",
    "​src/lib",
    "/src/lib",
    "src//lib",
    "src/lib//",
    "src/lib/.",
    "src/lib/..",
)

# Packaged-schema bodies that are valid JSON and are not a document. `load_json`
# parses each without complaint, so a caller that skipped a non-object without
# reporting it voided the entire schema layer: no required-key check, no
# check_schema, and no fixture ever instantiated against it. `null` is the
# sharpest of the four, because json.loads maps it onto the exact value
# load_json returns on failure.
NON_OBJECT_SCHEMA_BODIES = ("[]", "null", '"nope"', "17")

MODEL_NAME_POSITIVES = ("grok-4", "claude-opus-4-5", "gpt-5.4", "gemini-3-pro", "Sonnet", "haiku")
MODEL_NAME_NEGATIVES = (
    "Claude Code",
    "Codex CLI",
    "OpenCode",
    "pi",
    "PI_CODING_AGENT",
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


def run_validator_cli(module, root: Path) -> tuple[int, str]:
    """Drive the command, not just the library, and return (exit code, stdout).

    `validate_repository` returning a non-empty list and the command reporting
    failure are two different facts, and the second is the only one CI reads.
    A fail-open that leaves the list empty prints "validation passed" and exits
    0, so the assertions that matter are on this side of `main`.
    """
    captured = io.StringIO()
    argv = sys.argv
    sys.argv = ["validate_orchestra.py", str(root)]
    try:
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(io.StringIO()):
            code = module.main()
    finally:
        sys.argv = argv
    return code, captured.getvalue()


def _set_path(document: dict, dotted: str, value) -> None:
    """Assign through a dotted path, so a nested field can be named in a table."""
    node = document
    keys = dotted.split(".")
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = value


def _schema_patterns(node) -> list[str]:
    """Every ``pattern`` string anywhere in a schema document.

    Walks rather than reads fixed locations, so `propertyNames.pattern` and any
    pattern added later are covered without the audit having to be extended.
    """
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "pattern" and isinstance(value, str):
                found.append(value)
            found.extend(_schema_patterns(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_schema_patterns(item))
    return found


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


def _wave_of(fixture: dict, lane_id: str) -> int:
    return next(wave["wave"] for wave in fixture["dispatch"]["waves"] if lane_id in wave["laneIds"])


def _reschedule_lane(fixture: dict, lane_id: str, target_wave: int) -> None:
    """Move one lane into an existing wave, leaving the rest of the plan alone.

    G7 is scoped to a wave, so every one-writer-per-path test needs to put two
    lanes into the same wave without disturbing the dependency ordering the
    identity checks enforce alongside it -- otherwise the expected G7 error
    arrives mixed with a wave-ordering error and proves much less.

    A wave the move empties is dropped rather than left behind: `laneIds` is
    `minItems: 1`, so an empty wave is a schema violation, and each test here
    asserts the mutated document still satisfies the schema in order to show
    the gap G7 fills is real. Wave numbers carry their own `wave` field and
    need not be contiguous, so removing one renumbers nothing.
    """
    for wave in fixture["dispatch"]["waves"]:
        wave["laneIds"] = [item for item in wave["laneIds"] if item != lane_id]
    destination = next(
        wave for wave in fixture["dispatch"]["waves"] if wave["wave"] == target_wave
    )
    destination["laneIds"].append(lane_id)
    fixture["dispatch"]["waves"] = [
        wave for wave in fixture["dispatch"]["waves"] if wave["laneIds"]
    ]


def _minimal_valid_run_record() -> dict:
    """The smallest document run.schema.json accepts, built here rather than
    shipped under examples/ -- this is a schema-layer probe to mutate one
    field at a time, not a packaging fixture. The real fixtures live in
    examples/runs/ and are exercised end to end separately.

    ``chain`` is required, and once it is present the schema's conditional
    makes every lanes[] entry carry ``workflow`` and ``chainPosition`` too, so
    the floor is a chain of one whose single lane names that one link. It is
    also internally consistent with the cross-field invariants: the lane's
    (workflow, chainPosition) resolves to a declared link and chain positions
    are unique, so ``validate_run_record`` returns [] for it as well.

    Keep it at that floor. Many tests below mutate one field of this record
    and assert the result is rejected; incidental structure added here is
    structure one of those assertions can come to depend on by accident.
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
        "reopenCount": {},
        "chain": [{"chainPosition": 1, "workflow": "plan"}],
        "lanes": [
            {
                "laneId": "inventory",
                "workflow": "plan",
                "chainPosition": 1,
                "resolvedTier": "fast",
                "wave": 0,
            }
        ],
    }


def _minimal_valid_finding() -> dict:
    """The smallest document finding.schema.json accepts.

    Built here rather than shipped under examples/ for the same reason as
    `_minimal_valid_run_record`: this is a schema-layer probe to mutate one
    field at a time, not a packaging fixture. `status: open` is the floor --
    `fixed` drags in a passing post-remediation retest and `accepted`/`wontfix`
    drag in a humanDecision, and incidental structure is structure an
    assertion can come to depend on by accident.
    """
    return {
        "id": "F-001",
        "severity": "high",
        "status": "open",
        "precondition": "The parser is built with the migration flag on.",
        "evidence": ["01-verify/falsify/report.md"],
        "impact": "Call sites silently drop the trailing token.",
        "remediation": "Emit the token before returning.",
        "retest": {"result": "not_run"},
    }


def _minimal_valid_verdict() -> dict:
    """The smallest document verdict.schema.json accepts.

    `request_changes` is the floor: `approve` requires gateRunEvidence and
    either zero unresolved high/critical findings or a humanException.
    """
    return {
        "id": "V-001",
        "verdict": "request_changes",
        "rationale": "One high finding is still open.",
        "unresolvedHighOrCritical": 1,
        "isolation": "intact",
        "evidence": ["01-verify/adjudicate/report.md"],
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

    def test_an_invalid_lane_schema_is_reported_exactly_once(self) -> None:
        """One rule, one enforcement.

        lane.schema.json was loaded and check_schema'd twice per run -- once
        by the packaged-schema pass and again by the fixture pass that
        instantiates it -- so every schema-level failure arrived in the log
        twice and doubled the noise in the CI output a reader is trying to
        diagnose from.

        Counting rather than `any(...)` is the whole point of this test.
        `test_invalid_schema_is_rejected` above passes at one copy, at two,
        and at ten, so it cannot tell the doubling apart from the fix -- and,
        far more importantly, it would also pass at zero. A de-duplication
        that removed the surviving caller instead of the duplicate one is a
        fail-open, and much worse than the noise it removed.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/schemas/lane.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["type"] = "not-a-real-type"
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        reported = [
            error for error in errors
            if "invalid Draft202012 schema" in error and "lane.schema.json" in error
        ]
        self.assertEqual(len(reported), 1, errors)

    def test_an_invalid_run_schema_is_reported_exactly_once(self) -> None:
        """The symmetric half: run.schema.json was read and checked by the
        packaged-schema pass and again by the run-fixture pass."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/schemas/run.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["type"] = "not-a-real-type"
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        reported = [
            error for error in errors
            if "invalid Draft202012 schema" in error and "run.schema.json" in error
        ]
        self.assertEqual(len(reported), 1, errors)

    def test_an_unreadable_packaged_schema_is_reported_exactly_once(self) -> None:
        """The same de-duplication has to hold one stage earlier.

        A schema that fails to parse never reaches `check_schema` at all, so
        it is `load_json` that used to run twice over it. Both fixture passes
        now receive an already-parsed schema instead of re-reading the file,
        and a schema that failed to load arrives as nothing to instantiate.

        What this pins is that the LOAD FAILURE is reported once. What it must
        not be read as saying is that the fixture pass then goes quiet: an
        earlier revision drew that conclusion and skipped in silence, which is
        how a single unreadable schema came to void the entire schema layer at
        exit 0. The pass reports its own distinct failure -- that it could not
        run -- and `test_a_non_object_schema_leaves_the_fixture_pass_audibly_unrun`
        pins that half. Both are true at once precisely because they are
        different messages.
        """
        for schema_name in ("lane.schema.json", "run.schema.json"):
            with self.subTest(schema=schema_name):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = copy_repo(temp_dir)
                    path = root / "plugins/orchestra/schemas" / schema_name
                    path.write_text("{ not json", encoding="utf-8")
                    errors = self.validator.validate_repository(root)
                reported = [
                    error for error in errors
                    if "invalid JSON" in error and schema_name in error
                ]
                self.assertEqual(len(reported), 1, errors)

    def test_a_packaged_schema_that_is_valid_json_but_not_an_object_fails_closed(self) -> None:
        """The fail-open the de-duplication introduced, closed at every point.

        `load_json` reports only what it could not PARSE, so `[]`, `null`, a
        bare string and a number all came back as a clean parse of a value that
        is not a schema -- and were skipped without a word. The required-key
        check never ran, `check_schema` never ran, the schema never entered the
        returned mapping, and both fixture passes then received nothing and
        skipped in silence. One such file voided the whole schema layer while
        the command printed "validation passed" and exited 0:

            echo '[]' > plugins/orchestra/schemas/run.schema.json
            python scripts/validate_orchestra.py .   ->   exit 0

        Every schema file and every non-object body, because the defect is in
        the shared load path, not in one file. Asserting on `main` as well as
        on the error list is deliberate: an empty list IS the success report,
        so a check that only counted errors could not distinguish "clean" from
        "voided".
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            for schema_name in SCHEMA_FILES:
                path = root / "plugins/orchestra/schemas" / schema_name
                original = path.read_text(encoding="utf-8")
                for body in NON_OBJECT_SCHEMA_BODIES:
                    with self.subTest(schema=schema_name, body=body):
                        path.write_text(body, encoding="utf-8")
                        try:
                            errors = self.validator.validate_repository(root)
                            code, stdout = run_validator_cli(self.validator, root)
                        finally:
                            path.write_text(original, encoding="utf-8")
                        self.assertNotEqual(errors, [], f"{schema_name} = {body}")
                        self.assertTrue(
                            any(
                                schema_name in error and "must contain a JSON object" in error
                                for error in errors
                            ),
                            errors,
                        )
                        self.assertEqual(code, 1, stdout)
                        self.assertNotIn("validation passed", stdout)

    def test_a_non_object_schema_leaves_the_fixture_pass_audibly_unrun(self) -> None:
        """Skipping is not the same as being silent about skipping.

        A fixture validator handed nothing has already had the load failure
        reported for it, so repeating that failure would double the log -- but
        saying nothing at all is what let the whole schema layer evaporate
        without a trace. That the schema is broken and that no fixture was
        checked against it are two separate facts, and the second one is the
        only signal that the invariants went unenforced.
        """
        for schema_name in ("lane.schema.json", "run.schema.json"):
            with self.subTest(schema=schema_name):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = copy_repo(temp_dir)
                    path = root / "plugins/orchestra/schemas" / schema_name
                    path.write_text("[]", encoding="utf-8")
                    errors = self.validator.validate_repository(root)
                self.assertTrue(
                    any(
                        schema_name in error and "were not validated" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_no_packaged_json_document_can_be_voided_by_being_valid_non_object_json(self) -> None:
        """The same fail-open, everywhere else it was hiding in the load path.

        `load_json` reports what it could not parse, so every caller that
        answered a non-object by skipping had the identical hole as the schema
        pass, and each one silently voided a different layer:

        * a lane fixture holding `[]` left `fixtures` under three, which
          returned from the whole lane pass -- byte-identical check, schema
          instantiation and identity checks all skipped at once;
        * a run fixture holding `null` was indistinguishable from a load
          failure and was stepped over;
        * a plugin manifest holding `[]` gave `_validate_manifests` no version,
          so there was no name check, no semver check, and nothing left to
          mismatch its sibling manifest against.

        Each of these reported ZERO errors and exited 0 before the fix.
        """
        targets = (
            "plugins/orchestra/examples/lanes/no-delegation.json",
            "plugins/orchestra/examples/runs/chained.json",
            "plugins/orchestra/.claude-plugin/plugin.json",
            "plugins/orchestra/.codex-plugin/plugin.json",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            for target in targets:
                path = root / target
                original = path.read_text(encoding="utf-8")
                for body in NON_OBJECT_SCHEMA_BODIES:
                    with self.subTest(target=target, body=body):
                        path.write_text(body, encoding="utf-8")
                        try:
                            errors = self.validator.validate_repository(root)
                            code, stdout = run_validator_cli(self.validator, root)
                        finally:
                            path.write_text(original, encoding="utf-8")
                        self.assertTrue(
                            any(
                                path.name in error and "must contain a JSON object" in error
                                for error in errors
                            ),
                            errors,
                        )
                        self.assertEqual(code, 1, stdout)
                        self.assertNotIn("validation passed", stdout)

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

    def test_workflow_added_to_the_enum_without_the_reopen_key_pattern_is_rejected(self) -> None:
        """reopenCount keys name a ledger directory, so the pattern's
        workflow segment and $defs/workflow must not drift apart.

        The pattern spells the 18 workflow names out inline so a host that
        holds only run.schema.json still fails closed on a bogus key. That
        duplication is the point, and this is the check that keeps the two
        copies honest: adding a workflow to the enum and forgetting the
        pattern must be a build failure, not a silently unenforceable key.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/schemas/run.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["$defs"]["workflow"]["enum"].append("deploy")
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("reopenCount key pattern rejects workflow" in error for error in errors), errors)

    def test_reopen_key_pattern_that_accepts_any_workflow_is_rejected(self) -> None:
        """The other drift direction: a pattern loose enough to accept a
        workflow the enum never declared enforces nothing.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/schemas/run.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["properties"]["reopenCount"]["propertyNames"]["pattern"] = "^0[1-6]-[a-z-]+/[a-z0-9-]+$"
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("accepts unknown workflow" in error for error in errors), errors)

    def test_workflow_dropped_from_the_enum_while_the_pattern_keeps_it_is_rejected(self) -> None:
        """The drift direction forward probing can never see.

        Probing the enum only proves the pattern is not too narrow. A pattern
        that still accepts a workflow the enum has since dropped keeps
        `01-document/<lane>` a legal reopen key for a workflow that no longer
        exists, and every forward probe still passes while it does. Only
        comparing the two duplicated lists as sets catches it.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/schemas/run.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            enum = schema["$defs"]["workflow"]["enum"]
            self.assertIn("document", enum)
            schema["$defs"]["workflow"]["enum"] = [name for name in enum if name != "document"]
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(
            any("reopenCount key pattern accepts unknown workflow 'document'" in error for error in errors),
            errors,
        )

    def test_reopen_key_pattern_without_one_literal_alternation_group_is_rejected(self) -> None:
        """Comparing the pattern against the enum as sets is only possible
        while the pattern states its workflows literally, so a pattern the
        extraction cannot read must fail closed rather than skip the check.

        This mutation is deliberately still correct in behavior -- it splits
        the eighteen names across two groups, so it accepts every declared
        workflow and rejects every bogus one and both probe loops stay silent.
        That is exactly what makes it the case a behavioral check alone waves
        through.
        """
        first = "cover|debug|design|document|fan-out|harden|implement|migrate|perf"
        second = "plan|refactor|research|review|ship|spike|triage|upgrade|verify"
        tail = r"/[a-z0-9][a-z0-9-]*(?![\s\S])"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/schemas/run.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                set(first.split("|")) | set(second.split("|")),
                set(schema["$defs"]["workflow"]["enum"]),
                "the split must stay behaviorally identical to the shipped pattern",
            )
            schema["properties"]["reopenCount"]["propertyNames"]["pattern"] = (
                f"^0[1-6]-({first}){tail}|^0[1-6]-({second}){tail}"
            )
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(
            any("one literal alternation group: found 2" in error for error in errors), errors
        )
        self.assertEqual(
            [error for error in errors if "unknown workflow" in error or "rejects workflow" in error],
            [],
            "the structural check must fire on its own, not as a side effect of a probe",
        )

    def test_workflow_added_to_both_the_enum_and_the_pattern_is_accepted(self) -> None:
        """Positive control: the guard is anti-drift, not anti-change.

        Asserting only that mismatched edits are rejected cannot tell a set
        comparison apart from a hardcoded list of the current eighteen names.
        A coordinated edit to both copies has to stay green, or the guard
        would make the workflow catalog unextendable.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/schemas/run.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["$defs"]["workflow"]["enum"].append("audit")
            pattern = schema["properties"]["reopenCount"]["propertyNames"]["pattern"]
            self.assertIn("(cover|", pattern)
            schema["properties"]["reopenCount"]["propertyNames"]["pattern"] = pattern.replace(
                "(cover|", "(audit|cover|", 1
            )
            path.write_text(json.dumps(schema), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertEqual(errors, [])

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
        "OpenCode", "pi", "Grok Build", or the allowlisted compound tokens is a
        real failure mode -- it would silently make the plugin's own
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

    def test_host_enums_agree_and_cover_every_documented_host(self) -> None:
        """The two schemas duplicate the host enum with no $ref, and hosts.md
        is the only place the detection order is written down. Drift between
        any two of the three is how a host becomes undetectable or unwritable."""
        expected = {
            "claude-cowork", "codex-cli", "opencode", "pi",
            "grok-build", "claude-code",
        }
        enums = {}
        for schema_name in ("run.schema.json", "lane.schema.json"):
            schema = json.loads(
                (REPO_ROOT / "plugins/orchestra/schemas" / schema_name)
                .read_text(encoding="utf-8")
            )
            enums[schema_name] = schema["properties"]["host"]["enum"]
        self.assertEqual(enums["run.schema.json"], enums["lane.schema.json"])
        self.assertEqual(set(enums["run.schema.json"]), expected)
        hosts = (REPO_ROOT / "plugins/orchestra/references/hosts.md").read_text(
            encoding="utf-8"
        )
        prose = {
            "claude-cowork": "Claude Cowork",
            "codex-cli": "Codex CLI",
            "opencode": "OpenCode",
            "pi": "`pi` when",
            "grok-build": "Grok Build",
            "claude-code": "Claude Code",
        }
        for token in expected:
            self.assertIn(prose[token], hosts, token)


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

    def test_write_lane_owning_a_path_that_names_no_path_is_rejected(self) -> None:
        """`mode: write -> ownedPaths minItems 1` has to constrain what it claims.

        The conditional says a write lane owns at least one path, but the
        items only said `minLength: 1`, so `[" "]`, `["."]` and `["/"]` all
        satisfied it while declaring no territory anything could be checked
        against. That is a conditional that does not constrain what it claims
        to -- the same defect class as an unreachable `if`, and worse, since
        it reads as enforcement.

        This is the schema half deliberately: a host that holds
        lane.schema.json and never runs the repository validator must fail
        closed on exactly the same values.
        """
        for raw in DEGENERATE_OWNED_PATHS:
            with self.subTest(ownedPath=raw):
                fixture = _load_valid_lane_fixture()
                lane = _lane_by_id(fixture, "implement-parser")
                self.assertEqual(lane["mode"], "write")
                lane["ownedPaths"] = [raw]
                self.assert_rejected(fixture)

    def test_owned_path_that_is_not_a_plain_relative_path_is_rejected(self) -> None:
        """The schema half of the grammar, and the wider hole it closes.

        `test_write_lane_owning_a_path_that_names_no_path_is_rejected` above
        only reached declarations made of whitespace, slashes and dots. Every
        value here carries a real path character, so it sailed through that
        rule -- and each one names territory the validator could not compare:
        `src/..` IS the repository root, `src\\lib` is one segment where
        `src/lib` is two, and `src/lib` with a zero-width character appended
        is a second, invisible owner of the same tree.

        This is the schema layer deliberately: a host that holds
        lane.schema.json and never runs the repository validator must fail
        closed on exactly the same values.
        """
        for raw in NON_RELATIVE_OWNED_PATHS:
            with self.subTest(ownedPath=raw):
                fixture = _load_valid_lane_fixture()
                lane = _lane_by_id(fixture, "implement-parser")
                self.assertEqual(lane["mode"], "write")
                lane["ownedPaths"] = [raw]
                self.assert_rejected(fixture)

    def test_ordinary_owned_paths_are_still_accepted(self) -> None:
        """Positive control: the rule is anti-degenerate, not anti-path.

        Asserting only that empty declarations are rejected cannot tell a
        "must carry a meaningful path character" rule apart from one that
        rejects any path with a dot or a slash in it -- which would refuse
        every value the shipped fixtures declare. Both dot-leading entries
        are the load-bearing cases.
        """
        for raw in REAL_OWNED_PATHS:
            with self.subTest(ownedPath=raw):
                fixture = _load_valid_lane_fixture()
                _lane_by_id(fixture, "implement-parser")["ownedPaths"] = [raw]
                self.assertEqual(list(self.validator.iter_errors(fixture)), [])

    def test_every_shipped_fixture_owned_path_satisfies_the_schema_items_rule(self) -> None:
        """The tightening must not have outrun the data it ships with.

        A pattern that rejected a real fixture value would be caught by
        `validate_repository` too, but only as one schema-validation error
        among many; this names the actual values so the failure says which
        declaration the rule no longer accepts.
        """
        rule = json.loads((PLUGIN_ROOT / "schemas/lane.schema.json").read_text(encoding="utf-8"))
        rule = rule["properties"]["lanePlan"]["items"]["properties"]["ownedPaths"]["items"]
        items = Draft202012Validator(rule)
        declared = {
            raw
            for name in LANE_FIXTURES
            for lane in json.loads(
                (PLUGIN_ROOT / "examples/lanes" / f"{name}.json").read_text(encoding="utf-8")
            )["lanePlan"]
            for raw in lane["ownedPaths"]
        }
        self.assertTrue(declared, "no shipped fixture declares an ownedPaths entry")
        for raw in sorted(declared):
            with self.subTest(ownedPath=raw):
                self.assertEqual(list(items.iter_errors(raw)), [])

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

    # -- role -> mode is a total function, not two free enums ----------------

    def test_read_only_role_with_write_mode_is_rejected(self) -> None:
        """The exact document the mode-only conditionals used to accept.

        ownedPaths must be non-empty here: flipping mode to write while
        leaving ownedPaths empty is already caught by the pre-existing
        mode->ownedPaths clause, so that variant would pass green without
        the role->mode conditionals and prove nothing.
        """
        fixture = _load_valid_lane_fixture()
        lane = _lane_by_id(fixture, "falsify")
        self.assertEqual(lane["role"], "adversary")
        lane["mode"] = "write"
        lane["ownedPaths"] = ["src/should-not-own.ts"]
        self.assert_rejected(fixture)

    def test_every_read_only_role_is_bound_to_read_only_mode(self) -> None:
        for role in ("scout", "analyst", "architect", "adversary", "judge"):
            with self.subTest(role=role):
                fixture = _load_valid_lane_fixture()
                lane = _lane_by_id(fixture, "inventory")
                lane["role"] = role
                lane["mode"] = "write"
                lane["ownedPaths"] = ["src/should-not-own.ts"]
                self.assert_rejected(fixture)

    def test_builder_lane_with_execute_mode_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        lane = _lane_by_id(fixture, "implement-parser")
        self.assertEqual(lane["role"], "builder")
        lane["mode"] = "execute"
        lane["ownedPaths"] = []
        self.assert_rejected(fixture)

    def test_mechanic_lane_with_read_only_mode_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        lane = _lane_by_id(fixture, "migrate-call-sites")
        self.assertEqual(lane["role"], "mechanic")
        lane["mode"] = "read_only"
        lane["ownedPaths"] = []
        self.assert_rejected(fixture)

    def test_prover_lane_with_read_only_mode_is_rejected(self) -> None:
        """No ownedPaths interaction at all, so this isolates the new
        role->mode clause from every pre-existing conditional."""
        fixture = _load_valid_lane_fixture()
        lane = _lane_by_id(fixture, "run-suite")
        self.assertEqual(lane["role"], "prover")
        lane["mode"] = "read_only"
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


class OrchestraLaneIdentityInvariantTest(unittest.TestCase):
    """Cross-lane identity invariants no JSON Schema keyword can express.

    ``uniqueItems`` compares whole objects, so two lanePlan entries sharing
    an id both validate; there is no uniqueness-by-property keyword and no
    cross-array reference keyword. These checks therefore live in the
    validator, and each test below mutates one field of a real fixture that
    currently passes both the schema and the identity checks.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()
        cls.schema = _load_lane_schema_validator()

    def assert_identity_error(self, document: dict, fragment: str) -> None:
        errors = self.validator.validate_lane_document(document)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_every_shipped_fixture_satisfies_the_identity_invariants(self) -> None:
        for name in LANE_FIXTURES:
            payload = json.loads((PLUGIN_ROOT / "examples/lanes" / f"{name}.json").read_text(encoding="utf-8"))
            with self.subTest(fixture=name):
                self.assertEqual(self.validator.validate_lane_document(payload), [])

    def test_duplicate_lane_id_is_rejected_though_the_schema_accepts_it(self) -> None:
        """The load-bearing case: two briefs would land on lanes/inventory.md.

        The schema assertion is not decoration -- it proves the gap is real
        rather than hypothetical, because uniqueItems compares whole objects
        and these two entries differ in deliverable.
        """
        fixture = _load_valid_lane_fixture()
        clone = json.loads(json.dumps(_lane_by_id(fixture, "inventory")))
        clone["deliverable"] = "A second brief that would overwrite lanes/inventory.md."
        fixture["lanePlan"].append(clone)
        self.assertEqual(list(self.schema.iter_errors(fixture)), [], "schema alone cannot catch this")
        self.assert_identity_error(fixture, "duplicate lane id in lanePlan: inventory")

    def test_duplicate_lane_result_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        fixture["normalizedLaneResults"].append(json.loads(json.dumps(_result_by_id(fixture, "inventory"))))
        self.assert_identity_error(fixture, "duplicate laneId in normalizedLaneResults: inventory")

    def test_results_must_cover_every_planned_lane(self) -> None:
        fixture = _load_valid_lane_fixture()
        fixture["normalizedLaneResults"] = [
            result for result in fixture["normalizedLaneResults"] if result["laneId"] != "adjudicate"
        ]
        self.assert_identity_error(fixture, "missing a result for lane: adjudicate")

    def test_result_for_an_unplanned_lane_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        _result_by_id(fixture, "inventory")["laneId"] = "ghost"
        self.assert_identity_error(fixture, "normalizedLaneResults names an unknown lane: ghost")

    def test_unresolvable_dependency_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        _lane_by_id(fixture, "decompose")["dependsOn"] = ["ghost"]
        self.assert_identity_error(fixture, "dependsOn an unknown lane: ghost")

    def test_dependency_in_the_same_wave_is_rejected(self) -> None:
        """Wave ordering is what makes dependsOn mean anything at dispatch
        time; it also makes a dependency cycle unrepresentable."""
        fixture = _load_valid_lane_fixture()
        _lane_by_id(fixture, "constraints")["dependsOn"] = ["inventory"]
        self.assert_identity_error(fixture, "must be scheduled in a later wave than its dependency inventory")

    def test_lane_missing_from_every_wave_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        for wave in fixture["dispatch"]["waves"]:
            if "inventory" in wave["laneIds"]:
                wave["laneIds"].remove("inventory")
        self.assert_identity_error(fixture, "dispatch.waves omit lane: inventory")

    def test_lane_scheduled_in_two_waves_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        fixture["dispatch"]["waves"][1]["laneIds"].append("inventory")
        self.assert_identity_error(fixture, "dispatch.waves schedule lane more than once: inventory")

    def test_wave_scheduling_an_unplanned_lane_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        fixture["dispatch"]["waves"][0]["laneIds"].append("ghost")
        self.assert_identity_error(fixture, "dispatch.waves schedule an unknown lane: ghost")

    # -- G7: one writer per path, scoped to the wave -------------------------

    def test_identical_owned_paths_in_one_wave_are_rejected(self) -> None:
        """The base case. `uniqueItems` is per-array and no keyword compares
        one lane's ownedPaths against another's, let alone conditioned on the
        wave they land in, so G7 has nowhere to live but the validator."""
        fixture = _load_valid_lane_fixture()
        _lane_by_id(fixture, "implement-parser")["ownedPaths"] = ["src/parser/callers.ts"]
        wave = _wave_of(fixture, "implement-parser")
        _reschedule_lane(fixture, "migrate-call-sites", wave)
        self.assertEqual(list(self.schema.iter_errors(fixture)), [], "schema alone cannot catch this")
        self.assert_identity_error(
            fixture,
            f"wave {wave} schedules two writers of the same path: "
            "lane implement-parser owns 'src/parser/callers.ts' and "
            "lane migrate-call-sites owns 'src/parser/callers.ts'",
        )

    def test_containing_owned_paths_in_one_wave_are_rejected(self) -> None:
        """The case equality alone misses, and the load-bearing one.

        A lane owning `src/parser/` and a lane owning `src/parser/callers.ts`
        are two writers of the same file: the directory owner cannot honour
        "no file outside my owned paths was modified" while the other lane
        edits inside its tree. Treating only exact equality as a conflict
        would let any pair of lanes evade G7 by declaring ownership at
        different depths of one tree.
        """
        fixture = _load_valid_lane_fixture()
        self.assertEqual(_lane_by_id(fixture, "implement-parser")["ownedPaths"], ["src/parser/"])
        self.assertEqual(
            _lane_by_id(fixture, "migrate-call-sites")["ownedPaths"], ["src/parser/callers.ts"]
        )
        wave = _wave_of(fixture, "implement-parser")
        _reschedule_lane(fixture, "migrate-call-sites", wave)
        self.assert_identity_error(
            fixture,
            f"wave {wave} schedules two writers of the same path: "
            "lane implement-parser owns 'src/parser' and "
            "lane migrate-call-sites owns 'src/parser/callers.ts'",
        )

    def test_sibling_owned_paths_sharing_a_prefix_in_one_wave_are_accepted(self) -> None:
        """The near miss the containment check must not swallow.

        `src/parser` contains `src/parser/callers.ts` but not
        `src/parser-utils/index.ts`; a check that compares raw string prefixes
        gets that second pair wrong and refuses a lane plan that is perfectly
        safe to dispatch in parallel. Too greedy is as wrong as too loose, and
        only this direction can tell the two implementations apart.
        """
        fixture = _load_valid_lane_fixture()
        _lane_by_id(fixture, "migrate-call-sites")["ownedPaths"] = ["src/parser-utils/index.ts"]
        _reschedule_lane(fixture, "migrate-call-sites", _wave_of(fixture, "implement-parser"))
        self.assertEqual(self.validator.validate_lane_document(fixture), [])

    def test_a_file_is_not_contained_by_a_sibling_of_the_same_stem(self) -> None:
        """The other half of the same near miss, one segment shallower:
        `src/parser.ts` is neither inside nor outside `src/parser/`, it is
        unrelated to it, and naive string prefixing gets it wrong both ways.
        """
        fixture = _load_valid_lane_fixture()
        _lane_by_id(fixture, "migrate-call-sites")["ownedPaths"] = ["src/parser.ts"]
        _reschedule_lane(fixture, "migrate-call-sites", _wave_of(fixture, "implement-parser"))
        self.assertEqual(self.validator.validate_lane_document(fixture), [])

    def test_an_owned_path_naming_no_path_is_rejected_rather_than_normalized_away(self) -> None:
        """The declaration that made G7 silently unenforceable.

        `.`, `/`, ` `, `./` and `//` all reduced to no path segments at all,
        and a lane with no segments intersects nothing -- so a lane declaring
        the repository root as its territory conflicted with NOTHING instead
        of with everything, and emitted no error whatsoever. Forcing these two
        write lanes into one wave is the exact reproduction: with
        `["src/parser/"]` it raises "two writers of the same path", and with
        `["."]` it used to raise nothing and read as G7-clean.

        Rejection is explicit rather than the obvious-looking alternative of
        reading `.` as the universal container, because that would only move
        the hole: G5 requires a lane's diff to be a subset of its declared
        paths, and a lane owning the root satisfies that no matter what it
        wrote. The message names the lane and the raw value so the author can
        see which declaration is the empty one.
        """
        for raw in DEGENERATE_OWNED_PATHS:
            with self.subTest(ownedPath=raw):
                fixture = _load_valid_lane_fixture()
                _lane_by_id(fixture, "implement-parser")["ownedPaths"] = [raw]
                _reschedule_lane(
                    fixture, "migrate-call-sites", _wave_of(fixture, "implement-parser")
                )
                self.assert_identity_error(
                    fixture,
                    "lane implement-parser declares an ownedPaths entry that names no path: "
                    f"{raw!r}",
                )

    def test_a_traversal_owned_path_cannot_be_used_to_dodge_g7(self) -> None:
        """The degenerate-path hole, reopened under a spelling `.` never had.

        `src/..`, `docs/..` and `x/../..` all resolve to the repository root
        under POSIX, so each is the same claim `.` makes -- but ".." survived
        as a literal segment, and a segment tuple ending in ".." is a prefix of
        nothing, so these two write lanes shared a wave and G7 said nothing at
        all. The reproduction is the same one that proved the `.` case: force
        the pair into one wave, where `["src/parser/"]` raises "two writers of
        the same path".

        Rejecting the entry, rather than resolving ".." and then comparing, is
        the same call made for `.`: a lane that owns the root satisfies G5 no
        matter what it wrote, so resolving it would only move the hole from G7
        to G5.
        """
        for raw in ("src/..", "docs/..", "x/../.."):
            with self.subTest(ownedPath=raw):
                fixture = _load_valid_lane_fixture()
                _lane_by_id(fixture, "implement-parser")["ownedPaths"] = [raw]
                _reschedule_lane(
                    fixture, "migrate-call-sites", _wave_of(fixture, "implement-parser")
                )
                self.assert_identity_error(
                    fixture,
                    "lane implement-parser declares an ownedPaths entry that is not a "
                    f"plain relative path: {raw!r}",
                )

    def test_a_respelled_owned_path_cannot_fork_one_territory_into_two_owners(self) -> None:
        """Every one of these IS `src/parser/callers.ts`, and none collided.

        `_owned_path_key` split on "/" and stripped only outer whitespace, so a
        backslash was never a separator, a space beside a separator survived
        into the segment, and a zero-width character -- which is not `\\s` in
        Python, so nothing stripped it and nothing rejected it -- forked the
        path INVISIBLY. Each spelling therefore produced a segment tuple that
        intersected the other lane's `src/parser/callers.ts` nowhere, and two
        writers of one file passed G7 in the same wave.

        Note what is asserted: not that the pair now collides, but that the
        declaration is refused outright. Repairing the spelling and then
        comparing would leave the author's real mistake in place.
        """
        for raw in (
            "src\\parser/callers.ts",
            "src/ parser/callers.ts",
            "src /parser/callers.ts",
            "src/parser/callers.ts​",
            "src/parser/callers.ts\n",
        ):
            with self.subTest(ownedPath=raw):
                fixture = _load_valid_lane_fixture()
                self.assertEqual(
                    _lane_by_id(fixture, "migrate-call-sites")["ownedPaths"],
                    ["src/parser/callers.ts"],
                )
                _lane_by_id(fixture, "implement-parser")["ownedPaths"] = [raw]
                _reschedule_lane(
                    fixture, "migrate-call-sites", _wave_of(fixture, "implement-parser")
                )
                self.assert_identity_error(
                    fixture,
                    "lane implement-parser declares an ownedPaths entry that is not a "
                    f"plain relative path: {raw!r}",
                )

    def test_the_owned_path_grammar_is_the_same_at_both_layers(self) -> None:
        """One grammar, two copies, and neither may be looser than the other.

        The schema is what a host holding only lane.schema.json enforces; the
        validator is what CI enforces. If the two disagree on any value, one of
        them fails open -- and a duplicated rule with no equivalence check is
        exactly how they drift. Every value this suite knows about is put
        through both, and the verdicts must match value for value.
        """
        rule = json.loads((PLUGIN_ROOT / "schemas/lane.schema.json").read_text(encoding="utf-8"))
        items = Draft202012Validator(
            rule["properties"]["lanePlan"]["items"]["properties"]["ownedPaths"]["items"]
        )
        corpus = (*REAL_OWNED_PATHS, *DEGENERATE_OWNED_PATHS, *NON_RELATIVE_OWNED_PATHS)
        self.assertEqual(len(set(corpus)), len(corpus), "the corpus must not repeat a value")
        for raw in corpus:
            with self.subTest(ownedPath=raw):
                fixture = _load_valid_lane_fixture()
                _lane_by_id(fixture, "implement-parser")["ownedPaths"] = [raw]
                declaration_errors = [
                    error
                    for error in self.validator.validate_lane_document(fixture)
                    if "ownedPaths entry" in error
                ]
                self.assertEqual(
                    list(items.iter_errors(raw)) == [],
                    declaration_errors == [],
                    f"{raw!r}: schema and validator disagree ({declaration_errors})",
                )

    def test_a_dot_relative_owned_path_still_names_real_territory(self) -> None:
        """The near miss the degenerate-entry rule must not swallow.

        `./src/parser/` opens with the same `.` segment that `./` does, but it
        goes on to name a real tree, so it is a declaration and not an empty
        one -- and it must still collide with `src/parser/callers.ts` in the
        same wave, exactly as `src/parser/` does. A rule that keyed off a
        leading dot rather than off the absence of any meaningful path
        character would reject it and lose the conflict outright, which is
        the same fail-open in a new place.
        """
        fixture = _load_valid_lane_fixture()
        _lane_by_id(fixture, "implement-parser")["ownedPaths"] = ["./src/parser/"]
        wave = _wave_of(fixture, "implement-parser")
        _reschedule_lane(fixture, "migrate-call-sites", wave)
        self.assertEqual(list(self.schema.iter_errors(fixture)), [], "schema accepts a real path")
        self.assert_identity_error(
            fixture,
            f"wave {wave} schedules two writers of the same path: "
            "lane implement-parser owns 'src/parser' and "
            "lane migrate-call-sites owns 'src/parser/callers.ts'",
        )

    def test_ordinary_owned_paths_raise_no_declaration_error(self) -> None:
        """Positive control on the rule itself, isolated from G7.

        Every one of these is a real declaration, so none may be reported as
        naming no path -- including the two dot-leading entries. Left in a
        wave of its own, each must leave the document completely clean.
        """
        for raw in REAL_OWNED_PATHS:
            with self.subTest(ownedPath=raw):
                fixture = _load_valid_lane_fixture()
                _lane_by_id(fixture, "implement-parser")["ownedPaths"] = [raw]
                self.assertEqual(self.validator.validate_lane_document(fixture), [])

    def test_intersecting_owned_paths_in_different_waves_are_accepted(self) -> None:
        """Positive control: the wave is the unit, and all three shipped
        fixtures depend on it being so.

        Ownership is only contended between lanes that run at the same time.
        The hoisted mechanic writes inside its parent builder's tree one wave
        earlier and hands the result down, so scoping G7 to the run rather
        than to the wave would reject every fixture in examples/lanes/.
        """
        for name in LANE_FIXTURES:
            payload = json.loads(
                (PLUGIN_ROOT / "examples/lanes" / f"{name}.json").read_text(encoding="utf-8")
            )
            with self.subTest(fixture=name):
                self.assertEqual(_lane_by_id(payload, "implement-parser")["ownedPaths"], ["src/parser/"])
                self.assertEqual(
                    _lane_by_id(payload, "migrate-call-sites")["ownedPaths"], ["src/parser/callers.ts"]
                )
                self.assertNotEqual(
                    _wave_of(payload, "implement-parser"), _wave_of(payload, "migrate-call-sites")
                )
                self.assertEqual(self.validator.validate_lane_document(payload), [])

    def test_depth_two_lane_must_be_parented_by_a_builder(self) -> None:
        """The one edge that makes the depth cap true of the data: builder is
        the only role with canDelegate, so a mechanic parented by anything
        else describes a graph the role set cannot produce."""
        fixture = _load_valid_lane_fixture()
        _lane_by_id(fixture, "migrate-call-sites")["parentLaneId"] = "decompose"
        self.assert_identity_error(fixture, "parentLaneId must name a builder lane: decompose is a architect lane")

    def test_unresolvable_parent_lane_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        _lane_by_id(fixture, "migrate-call-sites")["parentLaneId"] = "ghost"
        self.assert_identity_error(fixture, "parentLaneId names an unknown lane: ghost")

    def test_depth_one_lane_may_not_declare_a_parent(self) -> None:
        fixture = _load_valid_lane_fixture()
        _lane_by_id(fixture, "run-suite")["parentLaneId"] = "implement-parser"
        self.assert_identity_error(fixture, "only a depth-two lane may declare a parent")

    def test_hoisted_entry_must_agree_with_the_declared_parent(self) -> None:
        fixture = _load_valid_lane_fixture()
        fixture["dispatch"]["hoisted"][0]["hoistedFrom"] = "decompose"
        self.assert_identity_error(fixture, "must name its parentLaneId as hoistedFrom")

    def test_hoisted_entry_for_an_unplanned_lane_is_rejected(self) -> None:
        fixture = _load_valid_lane_fixture()
        fixture["dispatch"]["hoisted"].append({"laneId": "ghost", "hoistedFrom": "implement-parser"})
        self.assert_identity_error(fixture, "dispatch.hoisted names an unknown lane: ghost")

    def test_identity_violation_is_caught_end_to_end_by_the_repository_validator(self) -> None:
        """Proves the wiring, not just the function.

        dispatch is the one block allowed to differ per fixture, so mutating
        only dispatch isolates the identity failure from the byte-identical
        lanePlan/normalizedLaneResults check that would otherwise fire first.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/examples/lanes/sequential-roles.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            for wave in payload["dispatch"]["waves"]:
                if "inventory" in wave["laneIds"]:
                    wave["laneIds"] = ["adjudicate" if lane == "inventory" else lane for lane in wave["laneIds"]]
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(any("dispatch.waves omit lane: inventory" in error for error in errors), errors)

    def test_run_record_lane_identity_is_scoped_by_workflow_and_position(self) -> None:
        """A chained run can dispatch six different lanes all named
        `adjudicate`, so lane identity is (workflow, chainPosition, laneId)."""
        record = {
            "chain": [{"chainPosition": 1, "workflow": "implement"}],
            "reopenCount": {"01-implement/build": 1},
            "lanes": [
                {"laneId": "build", "workflow": "implement", "chainPosition": 1, "resolvedTier": "standard", "wave": 0},
                {"laneId": "build", "workflow": "implement", "chainPosition": 1, "resolvedTier": "standard", "wave": 1},
            ],
        }
        errors = self.validator.validate_run_record(record)
        self.assertTrue(any("duplicate lane entry" in error for error in errors), errors)

    def test_reopen_count_key_must_resolve_to_a_dispatched_lane(self) -> None:
        record = {
            "chain": [{"chainPosition": 1, "workflow": "implement"}],
            "reopenCount": {"03-verify/falsify": 1},
            "lanes": [
                {"laneId": "build", "workflow": "implement", "chainPosition": 1, "resolvedTier": "standard", "wave": 0},
            ],
        }
        errors = self.validator.validate_run_record(record)
        self.assertTrue(any("names no lane in lanes[]: 03-verify/falsify" in error for error in errors), errors)


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

    def test_delegation_depth_above_two_is_rejected_even_with_a_justification(self) -> None:
        """Replaces test_deep_delegation_without_justification_is_rejected.

        That test passed under both the old and the new schema (depth 3 with
        no justification was rejected either way), so keeping it unchanged
        would leave the actual fix unproven. The escape hatch is what
        changed, so the justification must be present for the assertion to
        mean anything.
        """
        record = _minimal_valid_run_record()
        record["delegationDepth"] = 3
        record["deeperDelegationJustification"] = "the host offered a third level"
        self.assert_rejected(record)

    def test_delegation_depth_of_two_is_accepted(self) -> None:
        """Positive control: the cap is two, not one -- a depth-two run is
        the mechanic case every fixture ships and must stay valid."""
        record = _minimal_valid_run_record()
        record["delegationDepth"] = 2
        self.assertEqual(list(self.validator.iter_errors(record)), [])

    def test_legacy_deeper_delegation_justification_key_is_rejected(self) -> None:
        """The root object is additionalProperties: true, so deleting the
        field from the schema alone would let a stale run.json keep carrying
        it and read as though the hatch still worked."""
        record = _minimal_valid_run_record()
        record["deeperDelegationJustification"] = "left over from the old escape hatch"
        self.assert_rejected(record)

    def test_degraded_isolation_without_verdict_cap_is_rejected(self) -> None:
        record = _minimal_valid_run_record()
        record["isolation"] = "degraded"
        self.assert_rejected(record)

    def test_reopen_count_over_the_cap_is_rejected(self) -> None:
        """Re-pointed at the per-lane cap, not deleted.

        Left as the bare integer 4 this test still passed -- 4 is not an
        object, so it was rejected for the wrong reason and would have
        silently stopped testing the cap at all.
        """
        record = _minimal_valid_run_record()
        record["reopenCount"] = {"01-implement/build": 4}
        self.assert_rejected(record)

    def test_run_wide_integer_reopen_count_is_rejected(self) -> None:
        """One run-wide counter cannot express a per-lane cap: incremented
        globally it hard-stops a lane that was never reopened, and reset
        between lanes it erases the history the cap is computed from."""
        record = _minimal_valid_run_record()
        record["reopenCount"] = 0
        self.assert_rejected(record)

    def test_reopen_count_accepts_a_per_lane_ledger_keyed_map(self) -> None:
        """Positive control at both bounds, with a hyphenated workflow name
        and a hyphenated lane id."""
        record = _minimal_valid_run_record()
        record["reopenCount"] = {"01-implement/build": 0, "03-fan-out/falsify-a": 3}
        self.assertEqual(list(self.validator.iter_errors(record)), [])

    def test_reopen_count_key_must_be_a_ledger_path(self) -> None:
        """In order: bare lane id, missing chain position, one-digit
        position, position past the six-link chain, non-workflow segment,
        uppercase lane id, nested path.
        """
        for key in ("build", "implement/build", "1-implement/build", "07-implement/build",
                    "01-deploy/build", "01-implement/Build", "01-implement/a/b"):
            with self.subTest(key=key):
                record = _minimal_valid_run_record()
                record["reopenCount"] = {key: 1}
                self.assert_rejected(record)

    def test_parallel_subagents_scheduler_requires_the_capability_flag(self) -> None:
        record = _minimal_valid_run_record()
        record["scheduler"] = "parallel-subagents"
        record["capabilities"]["parallelSubagents"] = False
        self.assert_rejected(record)


class OrchestraRunRecordIdentityInvariantTest(unittest.TestCase):
    """Cross-field invariants for run.json that no JSON Schema keyword reaches.

    run.schema.json can require that a lane carries a `workflow` and a
    `chainPosition`, and that a reopenCount key is spelled
    `<nn>-<workflow>/<lane-id>`, but it has no keyword that resolves either of
    those against another array in the same document. Those checks live in
    `validate_run_record`, the reference implementation an orchestrator runs
    over its own run.json, and each test below asserts the schema accepts the
    mutated record first -- otherwise nothing shows the gap is real rather
    than hypothetical.

    Records are built here rather than loaded because the point is a record
    that is schema-valid and still wrong. The shipped fixtures under
    examples/runs/ carry the positive and end-to-end halves.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()
        cls.schema = _load_run_schema_validator()

    def assert_run_record_error(self, record: dict, fragment: str) -> None:
        errors = self.validator.validate_run_record(record)
        self.assertTrue(any(fragment in error for error in errors), errors)

    # -- reopenCount keys resolve, chain declared or not ----------------------

    def test_reopen_count_cross_check_is_not_gated_on_a_declared_chain(self) -> None:
        """The gate is gone, and this is the record that proves it.

        The cross-check used to run only when the record carried a `chain`
        key, so the single record it skipped was one already broken in exactly
        the way that lets a reopen key point at nothing. Nothing else here is
        wrong: with no chain to resolve against, the lane-to-link check stays
        silent by design, so the reopen error has to arrive on its own -- which
        is why this asserts the whole error list, not just a fragment of it.
        """
        record = {
            "reopenCount": {"03-verify/falsify": 1},
            "lanes": [
                {"laneId": "build", "workflow": "implement", "chainPosition": 1,
                 "resolvedTier": "standard", "wave": 0},
            ],
        }
        errors = self.validator.validate_run_record(record)
        self.assertEqual(errors, ["reopenCount key names no lane in lanes[]: 03-verify/falsify"])

    def test_reopen_count_key_that_resolves_is_accepted_without_a_chain(self) -> None:
        """Positive control on the same boundary: `03-verify/falsify` is
        rejected above because no lane mints that ledger key, not because the
        record omits a chain. Same key, same missing chain, opposite verdict.
        """
        record = {
            "reopenCount": {"03-verify/falsify": 1},
            "lanes": [
                {"laneId": "falsify", "workflow": "verify", "chainPosition": 3,
                 "resolvedTier": "deep", "wave": 0},
            ],
        }
        self.assertEqual(self.validator.validate_run_record(record), [])

    # -- lanes[] are bound to the links chain[] declares ----------------------

    def test_lane_naming_an_undeclared_chain_link_is_rejected(self) -> None:
        """Each link owns the directory `<nn>-<workflow>/`, so a lane naming a
        link chain[] never declared claims a directory that does not exist --
        and, because reopen keys are derived from lanes[], mints a well-formed
        reopen key inside it that the check above would then accept.
        """
        record = _minimal_valid_run_record()
        record["chain"] = [
            {"chainPosition": 1, "workflow": "plan"},
            {"chainPosition": 2, "workflow": "implement"},
        ]
        record["lanes"] = [
            {"laneId": "build", "workflow": "verify", "chainPosition": 3,
             "resolvedTier": "standard", "wave": 0},
        ]
        self.assertEqual(list(self.schema.iter_errors(record)), [], "schema alone cannot catch this")
        self.assert_run_record_error(
            record, "lane build names a chain link chain[] does not declare: 03-verify"
        )

    def test_a_lane_link_must_match_chain_on_both_workflow_and_position(self) -> None:
        """Neither half of a link's identity is optional.

        `01-implement/` and `02-plan/` are different directories from the
        declared `01-plan/` and `02-implement/`, so a lane matching only one
        axis still points at a link the run never planned. Matching on
        workflow alone would accept the first row, on position alone the
        second.
        """
        chain = [
            {"chainPosition": 1, "workflow": "plan"},
            {"chainPosition": 2, "workflow": "implement"},
        ]
        for workflow, position, expected in (("implement", 1, "01-implement"), ("plan", 2, "02-plan")):
            with self.subTest(workflow=workflow, chainPosition=position):
                record = _minimal_valid_run_record()
                record["chain"] = json.loads(json.dumps(chain))
                record["lanes"] = [
                    {"laneId": "build", "workflow": workflow, "chainPosition": position,
                     "resolvedTier": "standard", "wave": 0},
                ]
                self.assertEqual(list(self.schema.iter_errors(record)), [])
                self.assert_run_record_error(
                    record, f"lane build names a chain link chain[] does not declare: {expected}"
                )

    def test_a_lane_naming_a_declared_link_is_accepted(self) -> None:
        """Positive control: a lane on a middle link of a real chain, with the
        reopen key that link mints, must pass both layers clean."""
        record = _minimal_valid_run_record()
        record["chain"] = [
            {"chainPosition": 1, "workflow": "plan"},
            {"chainPosition": 2, "workflow": "implement"},
            {"chainPosition": 3, "workflow": "verify"},
        ]
        record["lanes"] = [
            {"laneId": "build", "workflow": "implement", "chainPosition": 2,
             "resolvedTier": "standard", "wave": 0},
        ]
        record["reopenCount"] = {"02-implement/build": 1}
        self.assertEqual(list(self.schema.iter_errors(record)), [])
        self.assertEqual(self.validator.validate_run_record(record), [])

    def test_duplicate_chain_position_is_rejected(self) -> None:
        """Two links at one position are two directories with one name.

        chain[] declares no `uniqueItems`, and it would not help if it did:
        these two entries differ in workflow, so they are unique by the only
        comparison JSON Schema offers while still both claiming `01-`.
        """
        record = _minimal_valid_run_record()
        record["chain"] = [
            {"chainPosition": 1, "workflow": "plan"},
            {"chainPosition": 1, "workflow": "implement"},
        ]
        self.assertEqual(list(self.schema.iter_errors(record)), [], "schema alone cannot catch this")
        self.assert_run_record_error(record, "duplicate chainPosition in chain[]: 1")

    # -- a hand-written record comes back as errors, never as a traceback -----

    def test_a_non_scalar_identity_field_returns_errors_instead_of_raising(self) -> None:
        """run.json is hand-written by an agent mid-run, not serialized.

        The lane identity tuple goes into a set, so a composite here is not
        merely invalid, it is unhashable: without the type guard this call
        raises TypeError and takes the run down instead of reporting the
        problem. Reaching the assertion at all is half of what this proves --
        an unguarded validator makes this an ERROR, not a FAILURE.
        """
        record = _minimal_valid_run_record()
        record["lanes"][0]["workflow"] = ["implement"]
        errors = self.validator.validate_run_record(record)
        self.assertTrue(any("non-scalar identity field" in error for error in errors), errors)
        self.assertTrue(any("workflow=['implement']" in error for error in errors), errors)

    def test_every_lane_identity_field_is_type_guarded(self) -> None:
        """All three fields form the tuple, so all three have to be guarded."""
        for field, value in (
            ("workflow", ["implement"]),
            ("chainPosition", {"position": 1}),
            ("laneId", ["build"]),
        ):
            with self.subTest(field=field):
                record = _minimal_valid_run_record()
                record["lanes"][0][field] = value
                self.assert_run_record_error(record, "non-scalar identity field")

    def test_a_boolean_chain_position_mints_no_ledger_key(self) -> None:
        """The boundary just inside the type guard.

        `bool` is an `int` subclass, so `True` is both scalar and hashable and
        must not be reported as a composite -- but it is not a chain position
        either. Were it treated as one it would format as `01` and mint
        `01-plan/inventory`, so the reopen key below would resolve and read as
        valid for a lane that declared no position at all.
        """
        record = _minimal_valid_run_record()
        record["lanes"][0]["chainPosition"] = True
        record["reopenCount"] = {"01-plan/inventory": 1}
        errors = self.validator.validate_run_record(record)
        self.assertEqual(errors, ["reopenCount key names no lane in lanes[]: 01-plan/inventory"])

    def test_a_run_record_that_is_not_an_object_returns_an_error(self) -> None:
        self.assertEqual(
            self.validator.validate_run_record(["not", "a", "record"]),
            ["run record must be a JSON object"],
        )

    # -- shipped fixtures, and the wiring that runs the checks over them ------

    def test_every_shipped_run_fixture_satisfies_the_schema_and_the_invariants(self) -> None:
        paths = sorted(RUN_FIXTURE_DIR.glob("*.json"))
        self.assertTrue(paths, f"no run-record fixture under {RUN_FIXTURE_DIR}")
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(fixture=path.name):
                self.assertEqual(list(self.schema.iter_errors(payload)), [])
                self.assertEqual(self.validator.validate_run_record(payload), [])

    def test_run_fixtures_cover_the_chain_of_one_and_the_chained_shape(self) -> None:
        """A chain of one is the common case, not a degenerate one.

        A workflow invoked directly rather than through the router is a chain
        of one and writes to `01-<workflow>/` like any other link; there is no
        unscoped special case to fall back on. Fixtures for the multi-link
        shape alone would leave the shape every direct invocation produces
        unexercised by the schema and by validate_run_record both.
        """
        lengths = {
            path.name: len(json.loads(path.read_text(encoding="utf-8"))["chain"])
            for path in sorted(RUN_FIXTURE_DIR.glob("*.json"))
        }
        self.assertIn(1, lengths.values(), lengths)
        self.assertTrue(any(length > 1 for length in lengths.values()), lengths)

    def test_a_chain_of_one_scopes_every_lane_under_the_first_link(self) -> None:
        """Writing to `01-<workflow>/` is a claim about the data, so pin it.

        The single link sits at position 1 and every lane names that link,
        rather than leaving workflow and chainPosition off as though a
        one-link run had an unscoped directory to fall back on.
        """
        for path in sorted(RUN_FIXTURE_DIR.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if len(payload["chain"]) != 1:
                continue
            link = payload["chain"][0]
            with self.subTest(fixture=path.name):
                self.assertEqual(link["chainPosition"], 1)
                for lane in payload["lanes"]:
                    self.assertEqual(
                        (lane["workflow"], lane["chainPosition"]), (link["workflow"], 1)
                    )

    def test_run_record_lane_violation_is_caught_end_to_end_by_the_repository_validator(self) -> None:
        """Proves the wiring, not just the function.

        validate_run_record had a full unit-test suite and no caller, so in CI
        it was documentation: a drifting fixture, or the function deleted
        outright, would have left the build green. The mutation is
        deliberately schema-valid -- chainPosition 6 is inside the declared
        1..6 range -- so only the cross-field check can reject it.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/examples/runs/chained.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            lane = next(item for item in payload["lanes"] if item["laneId"] == "inventory")
            self.assertEqual(lane["workflow"], "plan")
            lane["chainPosition"] = 6
            self.assertEqual(list(self.schema.iter_errors(payload)), [], "schema alone cannot catch this")
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(
            any(
                "lane inventory names a chain link chain[] does not declare: 06-plan" in error
                for error in errors
            ),
            errors,
        )

    def test_run_record_reopen_key_violation_is_caught_end_to_end(self) -> None:
        """The other half of the same wiring, through a key the schema accepts:
        `05-ship/ghost` is a well-formed ledger path naming a lane the run
        never dispatched, so the pattern passes and only the cross-check can
        see it."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/examples/runs/chained.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["reopenCount"] = {"05-ship/ghost": 1}
            self.assertEqual(list(self.schema.iter_errors(payload)), [], "schema alone cannot catch this")
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(
            any("reopenCount key names no lane in lanes[]: 05-ship/ghost" in error for error in errors),
            errors,
        )

    def test_a_new_run_fixture_is_discovered_rather_than_pinned_by_name(self) -> None:
        """examples/runs/ is a directory contract, not a file list.

        The lane fixtures are an exact triple because their point is that one
        lane plan dispatches three ways; run records only have to be
        individually valid, so the validator globs. This pins that: a fixture
        added under a name nothing knows about is still checked, and an
        invalid one still fails the build.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = copy_repo(temp_dir)
            path = root / "plugins/orchestra/examples/runs/unregistered-name.json"
            payload = _minimal_valid_run_record()
            payload["reopenCount"] = {"01-plan/ghost": 1}
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = self.validator.validate_repository(root)
        self.assertTrue(
            any(
                "unregistered-name.json" in error
                and "reopenCount key names no lane in lanes[]: 01-plan/ghost" in error
                for error in errors
            ),
            errors,
        )


class OrchestraAnchoredPatternTest(unittest.TestCase):
    """Every anchored pattern must reject a trailing newline.

    Python's `re` treats `$` as matching at the end of the string OR just
    before a final newline, and `jsonschema` compiles a `pattern` with `re`.
    So `"^F-[0-9]{3,}$"` accepted `"F-001\\n"`: an id that reads as well-formed,
    names the ledger entry `F-001` in every message, and is a different string
    from `"F-001"` in every dict, set and cross-reference that resolves it.
    The portable spelling is `(?![\\s\\S])`, which asserts that no character of
    any kind follows and means the same thing in Python and in ECMA-262 -- the
    dialect a host validating these schemas in JavaScript would use.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.finding = _load_schema_validator("finding.schema.json")
        cls.verdict = _load_schema_validator("verdict.schema.json")

    def test_no_packaged_schema_pattern_anchors_with_a_bare_dollar(self) -> None:
        """The structural half, so this cannot regress in a file nobody probes.

        Two schemas were converted in an earlier pass and two were missed, and
        nothing failed -- because the only guard was a handful of behavioural
        probes over the two files that had already been fixed. This walks every
        pattern in every packaged schema, including `propertyNames.pattern` and
        anything added later, so a new `$` anywhere is a build failure.
        """
        for name in SCHEMA_FILES:
            schema = json.loads((PLUGIN_ROOT / "schemas" / name).read_text(encoding="utf-8"))
            patterns = _schema_patterns(schema)
            with self.subTest(schema=name):
                self.assertTrue(patterns, f"{name} declares no pattern at all")
                for pattern in patterns:
                    self.assertNotIn(
                        "$",
                        pattern,
                        f"{name}: anchor with (?![\\s\\S]), not $: {pattern!r}",
                    )

    def test_minimal_finding_and_verdict_documents_validate_cleanly(self) -> None:
        """The floor both mutation tables start from, pinned once."""
        self.assertEqual(list(self.finding.iter_errors(_minimal_valid_finding())), [])
        self.assertEqual(list(self.verdict.iter_errors(_minimal_valid_verdict())), [])

    def test_a_trailing_newline_is_rejected_in_every_anchored_finding_field(self) -> None:
        for field, value in (
            ("id", "F-001"),
            ("reportedByLaneId", "falsify"),
            ("retest.executedByLaneId", "falsify"),
        ):
            with self.subTest(field=field):
                document = _minimal_valid_finding()
                _set_path(document, field, value)
                self.assertEqual(
                    list(self.finding.iter_errors(document)), [], "positive control"
                )
                _set_path(document, field, value + "\n")
                self.assertTrue(list(self.finding.iter_errors(document)), field)

    def test_a_trailing_newline_is_rejected_in_every_anchored_verdict_field(self) -> None:
        for field, value in (("id", "V-001"), ("decidedByLaneId", "adjudicate")):
            with self.subTest(field=field):
                document = _minimal_valid_verdict()
                _set_path(document, field, value)
                self.assertEqual(
                    list(self.verdict.iter_errors(document)), [], "positive control"
                )
                _set_path(document, field, value + "\n")
                self.assertTrue(list(self.verdict.iter_errors(document)), field)

    def test_a_trailing_newline_is_rejected_in_a_verdict_finding_reference(self) -> None:
        """`findingIds` is the cross-reference that makes the anchor matter.

        A verdict citing `"F-001\\n"` resolves against no finding whose id is
        `"F-001"`, so the reference silently points at nothing while every
        rendering of it reads as though it points at the finding.
        """
        document = _minimal_valid_verdict()
        document["findingIds"] = ["F-001"]
        self.assertEqual(list(self.verdict.iter_errors(document)), [], "positive control")
        document["findingIds"] = ["F-001\n"]
        self.assertTrue(list(self.verdict.iter_errors(document)))


if __name__ == "__main__":
    unittest.main()
