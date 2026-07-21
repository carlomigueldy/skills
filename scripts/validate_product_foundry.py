#!/usr/bin/env python3
"""Validate the installable product-foundry package without host CLIs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


PLUGIN_NAME = "product-foundry"
PLUGIN_DIR = Path("plugins") / PLUGIN_NAME
PUBLIC_SKILLS = {"product-foundry", "implement-prd"}
PHASE_SKILLS = {
    "foundry-intake", "foundry-research", "foundry-company-strategy",
    "foundry-mvp", "foundry-low-fidelity", "foundry-brand",
    "foundry-architecture", "foundry-agent-harness", "foundry-prd",
    "foundry-high-fidelity", "foundry-go-to-market", "foundry-readiness",
    "foundry-handoff",
}
REQUIRED_TEMPLATES = {
    "templates/docs/README.md", "templates/docs/AGENTS.md", "templates/docs/CLAUDE.md",
    "templates/docs/implementation-manifest.json", "templates/docs/task-state.json",
    "templates/docs/agent-roster.json", "templates/docs/decision.json", "templates/prototypes/low-fidelity/index.html",
    "templates/prototypes/high-fidelity/index.html",
}
REQUIRED_SCHEMAS = {
    "schemas/implementation-manifest.schema.json", "schemas/task-state.schema.json",
    "schemas/agent-roster.schema.json", "schemas/decision.schema.json",
}
SEMVER = re.compile(r"^(?:0|[1-9]\d*)\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
RESOURCE = re.compile(r"(?:\.\./)+(?:references|schemas|templates)/[^\s)`]+")
UNSAFE_PARTS = {".git", "node_modules", "dist", ".next", ".turbo", "__pycache__"}
PHASE_SECTIONS = (
    "Required inputs", "Deterministic outputs", "Completion criteria",
    "Invalidation rules", "Participation gate", "Approval gate",
)
DECISION_METADATA = ("rationale", "evidence", "assumptions", "confidence", "risks", "revisit conditions")
PROTOTYPE_STATES = ("loading", "empty", "error", "permission", "success", "validation")
ADAPTER_FIXTURES = ("claude", "codex-structured", "plain-fallback")
SCHEMA_FIXTURES = {
    "implementation-manifest.schema.json": (
        "templates/docs/implementation-manifest.json",
        "examples/lean/implementation-manifest.json",
        "examples/standard/implementation-manifest.json",
        "examples/advanced-custom/implementation-manifest.json",
    ),
    "task-state.schema.json": ("templates/docs/task-state.json",),
    "agent-roster.schema.json": ("templates/docs/agent-roster.json",),
    "decision.schema.json": ("templates/docs/decision.json",),
}
SCHEMA_REQUIRED = {
    "implementation-manifest.schema.json": {"requirements", "inputFingerprints", "implementationOrder", "reconciliation"},
    "task-state.schema.json": {"tasks", "inputFingerprints", "reconciliation"},
    "agent-roster.schema.json": {"agents", "delegationDepth"},
    "decision.schema.json": {"mode", "rationale", "evidence", "assumptions", "confidence", "risks", "revisitConditions"},
}


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


def validate_manifest(payload: Any) -> list[str]:
    """Validate the stable handoff shape with no third-party dependency."""
    errors: list[str] = []
    required = {
        "schemaVersion", "product", "artifacts", "mvp", "unresolvedDecisions",
        "designReferences", "architectureDecisions", "qualityGates", "requiredSkills",
        "harness", "environmentConstraints", "implementationOrder",
        "completionCriteria", "state", "inputFingerprints", "unresolvedBlockers",
        "reconciliation", "changedInputInvalidation",
    }
    if not isinstance(payload, dict):
        return ["manifest must be an object"]
    missing = sorted(required - payload.keys())
    if missing:
        errors.append(f"manifest missing required fields: {', '.join(missing)}")
    if payload.get("schemaVersion") != "1.0":
        errors.append("manifest schemaVersion must be '1.0'")
    product = payload.get("product")
    if not isinstance(product, dict) or not isinstance(product.get("name"), str) or not product["name"].strip():
        errors.append("manifest product.name must be a non-empty string")
    if isinstance(product, dict) and product.get("status") not in {"draft", "approved", "implementation"}:
        errors.append("manifest product.status must be draft, approved, or implementation")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("manifest artifacts must be an array")
    else:
        ids: set[str] = set()
        paths: set[str] = set()
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                errors.append("each manifest artifact must be an object")
                continue
            artifact_id, path, status = artifact.get("id"), artifact.get("path"), artifact.get("status")
            if not isinstance(artifact_id, str) or not artifact_id:
                errors.append("each manifest artifact needs an id")
            elif artifact_id in ids:
                errors.append(f"duplicate manifest artifact id: {artifact_id}")
            else:
                ids.add(artifact_id)
            if not isinstance(path, str) or not path.startswith("docs/") or ".." in Path(path).parts:
                errors.append(f"artifact path must be a safe docs/ path: {path!r}")
            elif path in paths:
                errors.append(f"duplicate manifest artifact path: {path}")
            else:
                paths.add(path)
            if status not in {"draft", "approved", "stale"}:
                errors.append(f"artifact {artifact_id!r} has invalid status")
    requirements = payload.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        errors.append("manifest requirements must be a non-empty array")
    else:
        requirement_ids: set[str] = set()
        for requirement in requirements:
            if not isinstance(requirement, dict):
                errors.append("each requirement must be an object")
                continue
            requirement_id = requirement.get("id")
            if not isinstance(requirement_id, str) or not requirement_id:
                errors.append("each requirement needs a stable id")
            elif requirement_id in requirement_ids:
                errors.append(f"duplicate requirement id: {requirement_id}")
            else:
                requirement_ids.add(requirement_id)
            if requirement.get("status") not in {"draft", "approved", "implemented", "verified", "stale"}:
                errors.append(f"requirement {requirement_id!r} has invalid status")
            if requirement.get("priority") not in {"must", "should", "could", "wont"}:
                errors.append(f"requirement {requirement_id!r} has invalid priority")
            criteria = requirement.get("acceptanceCriteria")
            if not isinstance(criteria, list) or not criteria or not all(isinstance(item, str) and item.strip() for item in criteria):
                errors.append(f"requirement {requirement_id!r} needs testable acceptanceCriteria")
            traceability = requirement.get("traceability")
            if not isinstance(traceability, dict):
                errors.append(f"requirement {requirement_id!r} needs traceability")
            else:
                evidence, assumptions = traceability.get("evidence"), traceability.get("assumptions")
                if not isinstance(evidence, list) or not isinstance(assumptions, list) or not (evidence or assumptions):
                    errors.append(f"requirement {requirement_id!r} traceability needs evidence or labeled assumptions")
                if not all(isinstance(item, str) and item.strip() for item in evidence or []):
                    errors.append(f"requirement {requirement_id!r} evidence must be strings")
                if not all(isinstance(item, str) and item.startswith("ASSUMPTION-") for item in assumptions or []):
                    errors.append(f"requirement {requirement_id!r} assumptions must use labeled assumption ids")
    for field in ("unresolvedDecisions", "unresolvedBlockers", "designReferences", "architectureDecisions", "qualityGates", "requiredSkills", "environmentConstraints", "implementationOrder", "completionCriteria"):
        if field in payload and not isinstance(payload[field], list):
            errors.append(f"manifest {field} must be an array")
    for field in ("mvp", "harness", "state", "inputFingerprints", "reconciliation", "changedInputInvalidation"):
        if field in payload and not isinstance(payload[field], dict):
            errors.append(f"manifest {field} must be an object")
    fingerprints = payload.get("inputFingerprints")
    if not isinstance(fingerprints, dict) or not fingerprints or not all(
        isinstance(path, str) and path and isinstance(value, str) and value
        for path, value in fingerprints.items()
    ):
        errors.append("manifest inputFingerprints must be a non-empty string map")
    order = payload.get("implementationOrder")
    order_ids: set[str] = set()
    if not isinstance(order, list) or not order:
        errors.append("manifest implementationOrder must be a non-empty array")
    else:
        for task_id in order:
            if not isinstance(task_id, str) or not re.fullmatch(r"TASK-[A-Z0-9][A-Z0-9-]*", task_id):
                errors.append(f"manifest implementationOrder has invalid task id: {task_id!r}")
            elif task_id in order_ids:
                errors.append(f"manifest implementationOrder has duplicate task id: {task_id}")
            else:
                order_ids.add(task_id)
    reconciliation = payload.get("reconciliation")
    if isinstance(reconciliation, dict):
        for field in ("staleOwners", "partialTasks", "conflicts", "preservedVerifiedTaskIds"):
            references = reconciliation.get(field)
            if not isinstance(references, list):
                errors.append(f"manifest reconciliation.{field} must be an array")
                continue
            seen: set[str] = set()
            for task_id in references:
                if not isinstance(task_id, str) or not re.fullmatch(r"TASK-[A-Z0-9][A-Z0-9-]*", task_id):
                    errors.append(f"manifest reconciliation.{field} has invalid task id: {task_id!r}")
                elif task_id in seen:
                    errors.append(f"manifest reconciliation.{field} has duplicate task id: {task_id}")
                elif task_id not in order_ids:
                    errors.append(f"manifest reconciliation.{field} references unknown implementation task id: {task_id}")
                else:
                    seen.add(task_id)
    changed = payload.get("changedInputInvalidation")
    if isinstance(changed, dict) and not isinstance(changed.get("policy"), str):
        errors.append("manifest changedInputInvalidation.policy must be a string")
    return errors


def validate_task_state(payload: Any) -> list[str]:
    """Validate fresh/resume task-state invariants without third-party schema tooling."""
    if not isinstance(payload, dict):
        return ["task state must be an object"]
    errors: list[str] = []
    for field in ("version", "mode", "inputFingerprints", "reconciliation", "tasks"):
        if field not in payload:
            errors.append(f"task state missing required field: {field}")
    if payload.get("version") != "1.0":
        errors.append("task state version must be '1.0'")
    if payload.get("mode") not in {"fresh", "resume"}:
        errors.append("task state mode must be fresh or resume")
    def valid_fingerprints(value: Any) -> bool:
        return isinstance(value, dict) and bool(value) and all(
            isinstance(path, str) and path and isinstance(fingerprint, str) and fingerprint
            for path, fingerprint in value.items()
        )

    if not valid_fingerprints(payload.get("inputFingerprints")):
        errors.append("task state inputFingerprints must be a non-empty string map")
    reconciliation = payload.get("reconciliation")
    if not isinstance(reconciliation, dict):
        errors.append("task state reconciliation must be an object")
    else:
        for field in ("staleOwners", "partialTasks", "conflicts", "preservedVerifiedTaskIds", "changedInputInvalidation", "failedVerificationReopens"):
            if field not in reconciliation:
                errors.append(f"task state reconciliation missing {field}")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        return errors + ["task state tasks must be an array"]
    ids: set[str] = set()
    task_by_id: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            errors.append("each task must be an object")
            continue
        for field in ("id", "owner", "status", "inputFingerprints", "verificationEvidence"):
            if field not in task:
                errors.append(f"task missing required field: {field}")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            errors.append("task id must be a non-empty string")
        elif task_id in ids:
            errors.append(f"duplicate task id: {task_id}")
        else:
            ids.add(task_id)
            task_by_id[task_id] = task
        if task.get("status") not in {"pending", "in_progress", "blocked", "partial", "stale", "verified"}:
            errors.append(f"task {task_id!r} has invalid status")
        evidence = task.get("verificationEvidence")
        if not isinstance(evidence, list):
            errors.append(f"task {task_id!r} verificationEvidence must be an array")
        elif task.get("status") == "verified" and not evidence:
            errors.append(f"verified task {task_id!r} requires verificationEvidence")
        if not valid_fingerprints(task.get("inputFingerprints")):
            errors.append(f"task {task_id!r} inputFingerprints must be a non-empty string map")
    if isinstance(reconciliation, dict):
        for field in ("staleOwners", "partialTasks", "conflicts", "preservedVerifiedTaskIds", "changedInputInvalidation", "failedVerificationReopens"):
            references = reconciliation.get(field)
            if not isinstance(references, list):
                errors.append(f"task state reconciliation.{field} must be an array of task ids")
                continue
            seen: set[str] = set()
            for task_id in references:
                if not isinstance(task_id, str) or not task_id:
                    errors.append(f"task state reconciliation.{field} contains an invalid task id")
                elif task_id in seen:
                    errors.append(f"task state reconciliation.{field} contains duplicate task id: {task_id}")
                elif task_id not in ids:
                    errors.append(f"task state reconciliation.{field} references unknown task id: {task_id}")
                else:
                    seen.add(task_id)
                    if field == "preservedVerifiedTaskIds" and task_by_id[task_id].get("status") != "verified":
                        errors.append(f"task state reconciliation.{field} must reference verified task id: {task_id}")
    if isinstance(reconciliation, dict):
        preserved = reconciliation.get("preservedVerifiedTaskIds", [])
        if isinstance(preserved, list):
            for task_id, task in task_by_id.items():
                if task.get("status") == "verified" and task_id not in preserved:
                    errors.append(f"verified task {task_id!r} must be preserved in reconciliation")
    return errors


def validate_agent_roster(payload: Any) -> list[str]:
    """Validate roster ownership and delegation controls beyond JSON Schema shape."""
    if not isinstance(payload, dict):
        return ["agent roster must be an object"]
    errors: list[str] = []
    depth = payload.get("delegationDepth")
    if not isinstance(depth, int) or isinstance(depth, bool) or depth < 0:
        errors.append("agent roster delegationDepth must be an integer >= 0")
    elif depth > 2 and not isinstance(payload.get("deeperDelegationJustification"), str):
        errors.append("agent roster depth > 2 requires deeperDelegationJustification")
    elif depth > 2 and not payload["deeperDelegationJustification"].strip():
        errors.append("agent roster depth > 2 requires deeperDelegationJustification")
    agents = payload.get("agents")
    if not isinstance(agents, list) or not agents:
        return errors + ["agent roster agents must be a non-empty array"]
    agent_ids: set[str] = set()
    owners: set[str] = set()
    for agent in agents:
        if not isinstance(agent, dict):
            errors.append("each agent roster entry must be an object")
            continue
        for field in ("id", "role", "responsibility", "skills", "inputs", "outputs", "tools", "ownership", "escalation"):
            if field not in agent:
                errors.append(f"agent roster entry missing {field}")
        agent_id = agent.get("id")
        if not isinstance(agent_id, str) or not agent_id:
            errors.append("agent roster id must be a non-empty string")
        elif agent_id in agent_ids:
            errors.append(f"duplicate agent roster id: {agent_id}")
        else:
            agent_ids.add(agent_id)
        ownership = agent.get("ownership")
        if not isinstance(ownership, list) or not ownership:
            errors.append(f"agent {agent_id!r} ownership must be a non-empty array")
        else:
            for owner in ownership:
                if not isinstance(owner, str) or not owner:
                    errors.append(f"agent {agent_id!r} ownership must contain strings")
                elif owner in owners:
                    errors.append(f"duplicate agent ownership: {owner}")
                else:
                    owners.add(owner)
        for field in ("skills", "inputs", "outputs", "tools"):
            if not isinstance(agent.get(field), list) or (field == "tools" and not agent[field]):
                errors.append(f"agent {agent_id!r} {field} must be an array" + (" with entries" if field == "tools" else ""))
    return errors


def _validate_packaged_schemas(root: Path, errors: list[str]) -> None:
    package = root / PLUGIN_DIR
    for schema_name, fixtures in SCHEMA_FIXTURES.items():
        schema_path = package / "schemas" / schema_name
        schema = load_json(schema_path, errors)
        if not isinstance(schema, dict):
            continue
        for field in SCHEMA_REQUIRED[schema_name]:
            if field not in schema.get("required", []):
                errors.append(f"{schema_path}: schema contract missing required field {field}")
        try:
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema)
        except SchemaError as exc:
            errors.append(f"{schema_path}: invalid Draft202012 schema: {exc.message}")
            continue
        for relative in fixtures:
            fixture_path = package / relative
            fixture = load_json(fixture_path, errors)
            if fixture is None:
                continue
            for error in sorted(validator.iter_errors(fixture), key=lambda item: list(item.path)):
                location = "/".join(str(part) for part in error.path) or "root"
                errors.append(f"{fixture_path}: schema validation at {location}: {error.message}")


def _validate_adapter_fixture(path: Path, errors: list[str]) -> dict[str, Any] | None:
    payload = load_json(path, errors)
    if not isinstance(payload, dict):
        return None
    question = payload.get("question")
    response = payload.get("response")
    normalized = payload.get("normalizedAnswer")
    if not isinstance(question, dict) or not isinstance(question.get("id"), str) or not question["id"]:
        errors.append(f"{path}: question needs a stable id")
        return None
    options = question.get("options")
    if not isinstance(options, list) or not options:
        errors.append(f"{path}: question needs options")
        return None
    option_ids: set[str] = set()
    for option in options:
        if not isinstance(option, dict):
            errors.append(f"{path}: option must be an object")
            continue
        option_id = option.get("id")
        if not isinstance(option_id, str) or not option_id:
            errors.append(f"{path}: option needs stable id")
        elif option_id in option_ids:
            errors.append(f"{path}: duplicate option id: {option_id}")
        else:
            option_ids.add(option_id)
        if not isinstance(option.get("label"), str) or not option["label"].strip():
            errors.append(f"{path}: option needs label")
        if not isinstance(option.get("recommended"), bool):
            errors.append(f"{path}: option needs boolean recommended")
        consequence = option.get("consequence")
        if not isinstance(consequence, str) or not consequence.strip() or len(consequence) > 180:
            errors.append(f"{path}: option needs concise consequence")
    selected = response.get("selectedOptionId") if isinstance(response, dict) else None
    if not isinstance(selected, str) or selected not in option_ids:
        errors.append(f"{path}: response must select an offered option; silence is not approval")
    if not isinstance(normalized, dict) or normalized != {"questionId": question["id"], "selectedOptionId": selected}:
        errors.append(f"{path}: normalizedAnswer must use the shared answer shape")
    return normalized if isinstance(normalized, dict) else None


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


def _validate_skills(root: Path, errors: list[str]) -> None:
    skills_root = root / PLUGIN_DIR / "skills"
    actual = {path.parent.name for path in skills_root.glob("*/SKILL.md")}
    expected = PUBLIC_SKILLS | PHASE_SKILLS
    for name in sorted(expected - actual):
        errors.append(f"missing required skill: {name}")
    for name in sorted(actual - expected):
        errors.append(f"unexpected package skill: {name}")
    seen_names: set[str] = set()
    for path in sorted(skills_root.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        match = re.match(r"^---\nname:\s*([^\n]+)\ndescription:\s*([^\n]+)\n---", text)
        if not match:
            errors.append(f"{path}: invalid SKILL.md frontmatter")
            continue
        name = match.group(1).strip().strip('"')
        if name in seen_names:
            errors.append(f"duplicate skill frontmatter name: {name}")
        seen_names.add(name)
        if not match.group(2).strip():
            errors.append(f"{path}: description must be non-empty")
        if path.parent.name in PHASE_SKILLS:
            for section in PHASE_SECTIONS:
                if f"## {section}" not in text:
                    errors.append(f"{path}: missing required phase section {section}")
            for phrase in ("Interview me", "Decide for me", "selected independently at the start of every phase"):
                if phrase not in text:
                    errors.append(f"{path}: participation gate must declare {phrase!r}")
            for field in DECISION_METADATA:
                if field not in text:
                    errors.append(f"{path}: delegated decision metadata must include {field}")
        if path.parent.name == "implement-prd":
            for phrase in ("find-skills", "fail closed", "installation", "recovery guidance"):
                if phrase not in text:
                    errors.append(f"{path}: find-skills fail-closed roster contract requires {phrase!r}")
        if path.parent.name in {"foundry-low-fidelity", "foundry-high-fidelity"}:
            for phrase in ("frontend-design", "fail closed", "installation", "recovery guidance", "../../references/policies.md"):
                if phrase not in text:
                    errors.append(f"{path}: frontend-design fail-closed prototype contract requires {phrase!r}")
        for raw in RESOURCE.findall(text):
            resolved = (path.parent / raw.rstrip(".,")).resolve()
            if not resolved.exists():
                errors.append(f"{path}: missing local resource {raw}")


def _validate_files(root: Path, errors: list[str]) -> None:
    package = root / PLUGIN_DIR
    for relative in sorted(REQUIRED_TEMPLATES | REQUIRED_SCHEMAS):
        if not (package / relative).is_file():
            errors.append(f"missing required package resource: {relative}")
    for path in package.rglob("*"):
        if any(part in UNSAFE_PARTS for part in path.relative_to(package).parts):
            errors.append(f"unsafe packaged path: {path.relative_to(package)}")
        if any(char in path.name for char in "[]<>:\\|?*"):
            errors.append(f"unsafe packaged path: {path.relative_to(package)}")
        if path.suffix == ".json":
            load_json(path, errors)
    for prototype in (
        package / "templates/prototypes/low-fidelity/index.html",
        package / "templates/prototypes/high-fidelity/index.html",
    ):
        if prototype.is_file():
            text = prototype.read_text(encoding="utf-8")
            if "@tailwindcss/browser@4" not in text or "<meta name=\"viewport\"" not in text:
                errors.append(f"{prototype}: must be a responsive Tailwind v4 browser-CDN prototype")
            for state in PROTOTYPE_STATES:
                if f'data-state="{state}"' not in text:
                    errors.append(f"{prototype}: missing interactive {state} state")
            for marker in ("aria-live", "<button", "addEventListener"):
                if marker not in text:
                    errors.append(f"{prototype}: missing keyboard/accessibility marker {marker}")


def _validate_examples(root: Path, errors: list[str]) -> None:
    examples = root / PLUGIN_DIR / "examples"
    names = {path.name for path in examples.iterdir()} if examples.is_dir() else set()
    required = {"lean", "standard", "advanced-custom"}
    for name in sorted(required - names):
        errors.append(f"missing required example fixture: {name}")
    for name in sorted(required & names):
        path = examples / name / "implementation-manifest.json"
        payload = load_json(path, errors)
        if payload is not None:
            errors.extend(f"{path}: {error}" for error in validate_manifest(payload))
    manifest_template = load_json(root / PLUGIN_DIR / "templates/docs/implementation-manifest.json", errors)
    if manifest_template is not None:
        errors.extend(f"implementation-manifest template: {error}" for error in validate_manifest(manifest_template))
    task_template = load_json(root / PLUGIN_DIR / "templates/docs/task-state.json", errors)
    if task_template is not None:
        errors.extend(f"task-state template: {error}" for error in validate_task_state(task_template))
    roster_template = load_json(root / PLUGIN_DIR / "templates/docs/agent-roster.json", errors)
    if roster_template is not None:
        errors.extend(f"agent-roster template: {error}" for error in validate_agent_roster(roster_template))


def _validate_adapter_contract(root: Path, errors: list[str]) -> None:
    adapter_path = root / PLUGIN_DIR / "references/platform-adapter.md"
    if adapter_path.is_file():
        text = adapter_path.read_text(encoding="utf-8")
        for phrase in ("runtime", "stable id", "recommended", "consequence", "one question", "wait", "silence", "same shape"):
            if phrase not in text:
                errors.append(f"{adapter_path}: adapter contract must declare {phrase!r}")
    fixtures = root / PLUGIN_DIR / "examples/adapters"
    normalized: list[dict[str, Any]] = []
    for name in ADAPTER_FIXTURES:
        answer = _validate_adapter_fixture(fixtures / f"{name}.json", errors)
        if answer is not None:
            normalized.append(answer)
    if len(normalized) == len(ADAPTER_FIXTURES) and any(answer != normalized[0] for answer in normalized[1:]):
        errors.append("adapter fixtures must normalize to the same answer shape")


def _validate_registration(root: Path, version: str | None, errors: list[str]) -> None:
    marketplace = load_json(root / ".claude-plugin/marketplace.json", errors)
    entries = marketplace.get("plugins", []) if isinstance(marketplace, dict) else []
    if not any(isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME and entry.get("source") == "./plugins/product-foundry" for entry in entries):
        errors.append("marketplace must register product-foundry")
    release = load_json(root / "release-please-config.json", errors)
    packages = release.get("packages", {}) if isinstance(release, dict) else {}
    config = packages.get(str(PLUGIN_DIR)) if isinstance(packages, dict) else None
    if not isinstance(config, dict):
        errors.append("release-please must register product-foundry")
    else:
        if config.get("release-type") != "simple":
            errors.append("release-please product-foundry release-type must be simple")
        paths = {item.get("path") for item in config.get("extra-files", []) if isinstance(item, dict)}
        for path in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            if path not in paths:
                errors.append(f"release-please must synchronize {path}")
    released = load_json(root / ".release-please-manifest.json", errors)
    released_version = released.get(str(PLUGIN_DIR)) if isinstance(released, dict) else None
    if version and released_version != version:
        errors.append("release-please manifest version must match plugin manifests")
    version_path = root / PLUGIN_DIR / "version.txt"
    if version and (not version_path.is_file() or version_path.read_text(encoding="utf-8").strip() != version):
        errors.append("version.txt must match plugin manifests")


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    version = _validate_manifests(root, errors)
    _validate_skills(root, errors)
    _validate_files(root, errors)
    _validate_packaged_schemas(root, errors)
    _validate_examples(root, errors)
    _validate_adapter_contract(root, errors)
    _validate_registration(root, version, errors)
    return errors


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--codex-manifest-only"]:
        if len(args) != 2:
            print("usage: validate_product_foundry.py --codex-manifest-only <manifest>", file=sys.stderr)
            return 2
        errors = validate_codex_manifest(Path(args[1]))
        if errors:
            print("Codex manifest validation failed:\n" + "\n".join(f"- {error}" for error in errors), file=sys.stderr)
            return 1
        print(f"Codex manifest validation passed: {Path(args[1]).resolve()}")
        return 0
    root = Path(args[0]) if len(args) == 1 else Path(__file__).resolve().parents[1]
    if len(args) > 1:
        print("usage: validate_product_foundry.py [repository-root]", file=sys.stderr)
        return 2
    errors = validate_repository(root)
    if errors:
        print("Product Foundry contract validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Product Foundry contract validation passed: {root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
