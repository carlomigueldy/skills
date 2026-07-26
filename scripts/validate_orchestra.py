#!/usr/bin/env python3
"""Validate the installable orchestra package without host CLIs.

orchestra is a portable orchestration plugin: a router skill (``orchestra``)
plus 18 workflow skills, each making the executing agent a root orchestrator
that decomposes, delegates, and verifies rather than implementing inline.
This validator enforces the contract described in
``docs/agent-harness/`` and the approved orchestra plan without needing any
host CLI installed.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


PLUGIN_NAME = "orchestra"
PLUGIN_DIR = Path("plugins") / PLUGIN_NAME

ROUTER_SKILL = "orchestra"
WORKFLOW_SKILLS = {
    "plan", "design", "spike", "fan-out", "implement", "verify", "review",
    "debug", "triage", "research", "refactor", "migrate", "upgrade",
    "harden", "perf", "cover", "document", "ship",
}
ALL_SKILLS = WORKFLOW_SKILLS | {ROUTER_SKILL}

SEMVER = re.compile(r"^(?:0|[1-9]\d*)\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
FRONTMATTER = re.compile(r"^---\nname:\s*([^\n]+)\ndescription:\s*([^\n]+)\n---")
BARE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RESOURCE = re.compile(r"(?:\.\./)+(?:references|roles|schemas|examples)/[^\s)`]+")

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

SCHEMA_FILES = ("run.schema.json", "lane.schema.json", "finding.schema.json", "verdict.schema.json")
TIER_ENUM = ("deep", "standard", "fast")

LANE_FIXTURES = ("parallel-subagents", "sequential-roles", "no-delegation")

# Two-layer defense against hardcoded model names: the tier enum (structural,
# see _validate_packaged_schemas) is the primary gate because an enum cannot
# be evaded. This denylist is the secondary, textual gate over prose. Vendor
# families require a following digit so the plugin's own host names
# ("Claude Code", "Codex CLI", "OpenCode", "Grok Build") never trip it, while
# a versioned model id ("grok-4", "claude-opus-4-5", "gpt-5.4",
# "gemini-3-pro") always does. Bare "Sonnet"/"Opus"/"Haiku" have no
# legitimate non-model usage in this plugin, so they are denylisted without
# requiring a digit.
MODEL_NAME_ALLOWLIST = frozenset({"claude-code", "claude-agent-sdk", "claude-plugin", "codex-plugin"})
MODEL_NAME = re.compile(
    r"\b(?:sonnet|opus|haiku)\b"
    r"|\b(?:claude|gpt|gemini|grok|codex|llama|mistral)(?:-[a-z]+)*-\d+(?:\.\d+)*(?:-[a-z0-9]+)*\b",
    re.IGNORECASE,
)


def find_model_name_violations(text: str) -> list[str]:
    """Return every substring matching the model-name denylist, minus the allowlist."""
    return [
        match.group(0)
        for match in MODEL_NAME.finditer(text)
        if match.group(0).lower() not in MODEL_NAME_ALLOWLIST
    ]


def load_json(path: Path, errors: list[str]) -> dict[str, Any] | list[Any] | None:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON: {path}")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON: {path}: {exc.msg}")
        return None
    return parsed


def _find_tier_enums(node: Any) -> list[list[Any]]:
    found: list[list[Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "tier" and isinstance(value, dict) and isinstance(value.get("enum"), list):
                found.append(value["enum"])
            found.extend(_find_tier_enums(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_find_tier_enums(item))
    return found


def _validate_resource_links(path: Path, text: str, package_root: Path, errors: list[str]) -> None:
    for raw in RESOURCE.findall(text):
        resolved = (path.parent / raw.rstrip(".,")).resolve()
        if not resolved.exists():
            errors.append(f"{path}: missing local resource {raw}")
            continue
        try:
            resolved.relative_to(package_root)
        except ValueError:
            errors.append(f"{path}: resource link escapes the package: {raw}")


def _validate_workflow_sections(path: Path, text: str, errors: list[str]) -> None:
    positions = [text.find(f"## {section}") for section in REQUIRED_SECTIONS]
    for section, index in zip(REQUIRED_SECTIONS, positions):
        if index == -1:
            errors.append(f"{path}: missing required section {section!r}")
    present = [index for index in positions if index != -1]
    if present != sorted(present):
        errors.append(
            f"{path}: required sections must appear in order: {', '.join(REQUIRED_SECTIONS)}"
        )


def _validate_workflow_literals(path: Path, text: str, errors: list[str]) -> None:
    for phrase in MANDATORY_LITERALS:
        if phrase not in text:
            errors.append(f"{path}: missing mandatory phrase {phrase!r}")
    if LANE_TABLE_HEADER not in text:
        errors.append(f"{path}: missing lane table header {LANE_TABLE_HEADER!r}")
    match = SHAPE_LINE.search(text)
    if not match:
        errors.append(f"{path}: missing a 'Shape: <shape>' line")
    elif match.group(1) not in SHAPES:
        errors.append(
            f"{path}: Shape line must be exactly one of {sorted(SHAPES)}: got {match.group(1)!r}"
        )


def _validate_router(path: Path, text: str, errors: list[str]) -> None:
    if ROUTER_LITERAL not in text:
        errors.append(f"{path}: missing mandatory phrase {ROUTER_LITERAL!r}")

    all_refs = SKILL_REFERENCE.findall(text)
    unknown_refs = sorted({ref for ref in all_refs if ref not in WORKFLOW_SKILLS})
    if unknown_refs:
        errors.append(f"{path}: references unknown skill(s): {', '.join(unknown_refs)}")

    start = text.find(WORKFLOW_INDEX_HEADING)
    if start == -1:
        errors.append(f"{path}: missing {WORKFLOW_INDEX_HEADING!r} section")
        return
    next_heading = text.find("\n## ", start + len(WORKFLOW_INDEX_HEADING))
    section = text[start:next_heading] if next_heading != -1 else text[start:]
    counts = Counter(SKILL_REFERENCE.findall(section))
    missing = sorted(WORKFLOW_SKILLS - counts.keys())
    if missing:
        errors.append(f"{path}: workflow index missing: {', '.join(missing)}")
    duplicated = sorted(
        name for name, count in counts.items() if name in WORKFLOW_SKILLS and count != 1
    )
    if duplicated:
        errors.append(
            f"{path}: workflow index must name each workflow exactly once: {', '.join(duplicated)}"
        )


def _validate_skills(root: Path, errors: list[str]) -> None:
    skills_root = root / PLUGIN_DIR / "skills"
    actual = {path.parent.name for path in skills_root.glob("*/SKILL.md")}
    for name in sorted(ALL_SKILLS - actual):
        errors.append(f"missing required skill: {name}")
    for name in sorted(actual - ALL_SKILLS):
        errors.append(f"unexpected package skill: {name}")

    package_root = (root / PLUGIN_DIR).resolve()
    seen_names: set[str] = set()
    router_seen = False
    for path in sorted(skills_root.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER.match(text)
        if not match:
            errors.append(f"{path}: invalid SKILL.md frontmatter")
            continue
        name = match.group(1).strip().strip('"')
        if name in seen_names:
            errors.append(f"duplicate skill frontmatter name: {name}")
        seen_names.add(name)
        if not match.group(2).strip():
            errors.append(f"{path}: description must be non-empty")
        if not BARE_NAME.fullmatch(name):
            errors.append(f"{path}: skill name {name!r} must be a bare name")
        if name != ROUTER_SKILL and name.startswith("orchestra-"):
            errors.append(f"{path}: skill name {name!r} must not use the orchestra- prefix")
        if name != path.parent.name:
            errors.append(
                f"{path}: skill name {name!r} must match directory {path.parent.name!r}"
            )

        _validate_resource_links(path, text, package_root, errors)

        if name == ROUTER_SKILL:
            router_seen = True
            _validate_router(path, text, errors)
        elif name in WORKFLOW_SKILLS:
            _validate_workflow_sections(path, text, errors)
            _validate_workflow_literals(path, text, errors)

    if not router_seen:
        errors.append(f"missing router skill: {ROUTER_SKILL}")


def _validate_packaged_schemas(root: Path, errors: list[str]) -> None:
    package = root / PLUGIN_DIR
    tier_enums: list[list[Any]] = []
    for schema_name in SCHEMA_FILES:
        schema_path = package / "schemas" / schema_name
        schema = load_json(schema_path, errors)
        if not isinstance(schema, dict):
            continue
        required = schema.get("required")
        if not isinstance(required, list) or not required:
            errors.append(f"{schema_path}: schema must declare a non-empty required field list")
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            errors.append(f"{schema_path}: invalid Draft202012 schema: {exc.message}")
            continue
        tier_enums.extend(_find_tier_enums(schema))
    if not tier_enums:
        errors.append("no packaged schema declares a tier enum")
    for enum in tier_enums:
        if sorted(enum) != sorted(TIER_ENUM):
            errors.append(f"tier enum must be exactly {list(TIER_ENUM)}: got {enum}")


def _validate_lane_fixtures(root: Path, errors: list[str]) -> None:
    package = root / PLUGIN_DIR
    fixtures: dict[str, Any] = {}
    for name in LANE_FIXTURES:
        path = package / "examples/lanes" / f"{name}.json"
        payload = load_json(path, errors)
        if isinstance(payload, dict):
            fixtures[name] = payload
    if len(fixtures) != len(LANE_FIXTURES):
        return

    for key in ("lanePlan", "normalizedLaneResults"):
        values = [fixtures[name].get(key) for name in LANE_FIXTURES]
        if any(value is None for value in values):
            errors.append(f"lane fixtures missing required key: {key}")
            continue
        serialized = {json.dumps(value, sort_keys=True) for value in values}
        if len(serialized) != 1:
            errors.append(
                f"lane fixtures {key} must be byte-identical across {', '.join(LANE_FIXTURES)}"
            )

    dispatches = [fixtures[name].get("dispatch") for name in LANE_FIXTURES]
    if any(dispatch is None for dispatch in dispatches):
        errors.append("lane fixtures missing required key: dispatch")
    else:
        serialized_dispatch = {json.dumps(dispatch, sort_keys=True) for dispatch in dispatches}
        if len(serialized_dispatch) != len(LANE_FIXTURES):
            errors.append(
                "lane fixtures dispatch must differ across all three fixtures "
                "(identical dispatch proves nothing)"
            )

    # check_schema (in _validate_packaged_schemas) only proves the schema is
    # well-formed; it never instantiates it against a document. Without this,
    # every conditional invariant in lane.schema.json is dead weight as far
    # as CI is concerned -- a fixture could drift, or the schema could be
    # tightened into something no real document satisfies, and the build
    # would stay green either way.
    schema_path = package / "schemas" / "lane.schema.json"
    schema = load_json(schema_path, errors)
    if isinstance(schema, dict):
        try:
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema)
        except SchemaError as exc:
            errors.append(f"{schema_path}: invalid Draft202012 schema: {exc.message}")
        else:
            for name in LANE_FIXTURES:
                fixture_path = package / "examples/lanes" / f"{name}.json"
                for error in sorted(validator.iter_errors(fixtures[name]), key=lambda item: list(item.path)):
                    location = "/".join(str(part) for part in error.path) or "root"
                    errors.append(f"{fixture_path}: schema validation at {location}: {error.message}")


def _validate_packaged_paths(root: Path, errors: list[str]) -> None:
    package = root / PLUGIN_DIR
    if not package.is_dir():
        return
    for path in package.rglob("*"):
        if ".orchestra" in path.relative_to(package).parts:
            errors.append(f"packaged path must not contain .orchestra: {path.relative_to(package)}")


def _validate_model_names(root: Path, errors: list[str]) -> None:
    package = root / PLUGIN_DIR
    if not package.is_dir():
        return
    for path in sorted(package.rglob("*")):
        # .py covers install-grok.py, the package's only executable file and
        # exactly the boundary where an abstract tier gets mapped onto a
        # concrete host setting -- the likeliest place a hardcoded model id
        # would be written. Every other suffix shipped under plugins/orchestra
        # is .md or .json (see the package's own layout); .pyc is a compiled
        # artifact, never source, and is deliberately excluded.
        if not path.is_file() or path.suffix not in (".md", ".json", ".py"):
            continue
        text = path.read_text(encoding="utf-8")
        for violation in find_model_name_violations(text):
            errors.append(f"{path}: hardcoded model reference: {violation!r}")


def _validate_native_manifest(path: Path, errors: list[str], *, codex: bool) -> dict[str, Any] | None:
    data = load_json(path, errors)
    if not isinstance(data, dict):
        return None
    if data.get("name") != PLUGIN_NAME:
        errors.append(f"{path}: name must be {PLUGIN_NAME!r}")
    version = data.get("version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        errors.append(f"{path}: version must be semantic")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        errors.append(f"{path}: description must be non-empty")
    if codex and data.get("skills") != "./skills/":
        errors.append(f"{path}: skills must point to ./skills/")
    return data


def validate_codex_manifest(path: Path) -> list[str]:
    """Validate the native Codex manifest independently from package checks."""
    errors: list[str] = []
    _validate_native_manifest(path, errors, codex=True)
    return errors


def _validate_manifests(root: Path, errors: list[str]) -> str | None:
    claude = _validate_native_manifest(root / PLUGIN_DIR / ".claude-plugin/plugin.json", errors, codex=False)
    codex = _validate_native_manifest(root / PLUGIN_DIR / ".codex-plugin/plugin.json", errors, codex=True)
    versions = [data["version"] for data in (claude, codex) if isinstance(data, dict) and isinstance(data.get("version"), str)]
    if len(set(versions)) > 1:
        errors.append("Claude and Codex plugin versions must match")
    return versions[0] if versions else None


def _validate_registration(root: Path, version: str | None, errors: list[str]) -> None:
    marketplace = load_json(root / ".claude-plugin/marketplace.json", errors)
    entries = marketplace.get("plugins", []) if isinstance(marketplace, dict) else []
    if not any(
        isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME and entry.get("source") == f"./{PLUGIN_DIR.as_posix()}"
        for entry in entries
    ):
        errors.append(f"marketplace must register {PLUGIN_NAME}")
    release = load_json(root / "release-please-config.json", errors)
    packages = release.get("packages", {}) if isinstance(release, dict) else {}
    config = packages.get(PLUGIN_DIR.as_posix()) if isinstance(packages, dict) else None
    if not isinstance(config, dict):
        errors.append(f"release-please must register {PLUGIN_NAME}")
    else:
        if config.get("release-type") != "simple":
            errors.append(f"release-please {PLUGIN_NAME} release-type must be simple")
        paths = {item.get("path") for item in config.get("extra-files", []) if isinstance(item, dict)}
        for path in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            if path not in paths:
                errors.append(f"release-please must synchronize {path}")
    released = load_json(root / ".release-please-manifest.json", errors)
    released_version = released.get(PLUGIN_DIR.as_posix()) if isinstance(released, dict) else None
    if version and released_version != version:
        errors.append("release-please manifest version must match plugin manifests")
    version_path = root / PLUGIN_DIR / "version.txt"
    if version and (not version_path.is_file() or version_path.read_text(encoding="utf-8").strip() != version):
        errors.append("version.txt must match plugin manifests")


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    version = _validate_manifests(root, errors)
    _validate_skills(root, errors)
    _validate_packaged_schemas(root, errors)
    _validate_lane_fixtures(root, errors)
    _validate_packaged_paths(root, errors)
    _validate_model_names(root, errors)
    _validate_registration(root, version, errors)
    return errors


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--codex-manifest-only"]:
        if len(args) != 2:
            print("usage: validate_orchestra.py --codex-manifest-only <manifest>", file=sys.stderr)
            return 2
        errors = validate_codex_manifest(Path(args[1]))
        if errors:
            print("Codex manifest validation failed:\n" + "\n".join(f"- {error}" for error in errors), file=sys.stderr)
            return 1
        print(f"Codex manifest validation passed: {Path(args[1]).resolve()}")
        return 0
    root = Path(args[0]) if len(args) == 1 else Path(__file__).resolve().parents[1]
    if len(args) > 1:
        print("usage: validate_orchestra.py [repository-root]", file=sys.stderr)
        return 2
    errors = validate_repository(root)
    if errors:
        print("Orchestra contract validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Orchestra contract validation passed: {root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
