#!/usr/bin/env python3
"""Validate the minimum reconstructable contract of a Herdcraft run."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "run-state.json",
    "delivery-profile.yaml",
    "specialists.yaml",
    "final-report.md",
    "templates/task-contract.md",
    "templates/team-report.md",
)
RUN_STATUSES = {
    "planning",
    "ready",
    "running",
    "blocked",
    "integrating",
    "verifying",
    "completed",
    "failed",
    "cancelled",
}
TEAM_STATES = {
    "planned",
    "ready",
    "active",
    "blocked",
    "integrating",
    "complete",
    "retired",
    "failed",
}
DISPATCH_STATUSES = {"ready", "running", "blocked", "integrating", "verifying", "completed"}
RETIRED_RESOURCE_STATES = {"retired", "retained-for-recovery"}
REPORT_PLACEHOLDER = re.compile(r"<[^>]+>")
FINAL_REPORT_SECTIONS = {
    "# Workflow report",
    "## Outcome",
    "## Topology and models",
    "## Delivery evidence",
    "## Delivery profile and capabilities",
    "## Retirement",
    "## Usage telemetry",
    "## Residual risk",
}
FINAL_REPORT_FIELDS = {
    "- Run ID/status:",
    "- Shipped scope:",
    "- Independent verification:",
    "- Final absence verification:",
    "- Token availability:",
    "- Residual risks:",
}
RESOURCE_REQUIRED_FIELDS = {
    "resource_id",
    "resource_type",
    "owner_team",
    "owner_task",
    "created_by_run",
    "herdr_id",
    "path",
    "branch",
    "state",
    "preserved_commit",
    "retirement_action",
    "retirement_evidence",
    "verified_absent",
    "retired_at",
}


def _load_state(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"run-state.json is unreadable or invalid: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append("run-state.json must contain an object")
        return None
    return payload


def _run_owned_file(
    run_dir: Path,
    value: object,
    field: str,
    errors: list[str],
) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{field} must name a run-owned file")
        return None
    candidate = (run_dir / value).resolve()
    try:
        candidate.relative_to(run_dir)
    except ValueError:
        errors.append(f"{field} must stay within the run directory")
        return None
    if not candidate.is_file():
        errors.append(f"{field} points to missing file: {value}")
        return None
    return candidate


def validate_run(run_dir: Path) -> list[str]:
    run_dir = run_dir.resolve()
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (run_dir / relative).is_file():
            errors.append(f"missing required file: {relative}")

    state = _load_state(run_dir / "run-state.json", errors)
    if state is None:
        return errors
    if state.get("schema_version") != 4:
        errors.append("schema_version must be 4")
    if state.get("run_id") != run_dir.name:
        errors.append("run_id must match the run directory name")
    repo_root = state.get("repo_root")
    if not isinstance(repo_root, str) or not Path(repo_root).is_absolute():
        errors.append("repo_root must be an absolute path")
    for field in ("objective", "status"):
        if not isinstance(state.get(field), str) or not state[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if isinstance(state.get("status"), str) and state["status"] not in RUN_STATUSES:
        errors.append(f"status must be one of: {', '.join(sorted(RUN_STATUSES))}")
    base_revision = state.get("base_revision")
    if not isinstance(base_revision, str) or not base_revision.strip() or base_revision == "replace-me":
        errors.append("base_revision is unresolved")
    for field in ("tasks", "teams", "agents", "resources", "verification", "risks"):
        if not isinstance(state.get(field), list):
            errors.append(f"{field} must be a list")
    delivery_profile = _run_owned_file(
        run_dir, state.get("delivery_profile"), "delivery_profile", errors
    )
    final_report = _run_owned_file(
        run_dir, state.get("final_report_path"), "final_report_path", errors
    )

    teams_dir = run_dir / "teams"
    directory_team_ids: set[str] = set()
    if teams_dir.exists():
        for team_dir in sorted(path for path in teams_dir.iterdir() if path.is_dir()):
            directory_team_ids.add(team_dir.name)
            for filename in ("team-contract.yaml", "capability-ledger.yaml"):
                if not (team_dir / filename).is_file():
                    errors.append(f"team {team_dir.name} is missing {filename}")
    state_team_ids: list[str] = []
    teams = state.get("teams")
    if isinstance(teams, list):
        for index, team in enumerate(teams):
            if not isinstance(team, dict):
                errors.append(f"teams[{index}] must be an object")
                continue
            team_id = team.get("team_id")
            if not isinstance(team_id, str) or not team_id:
                errors.append(f"teams[{index}].team_id must be a non-empty string")
            else:
                state_team_ids.append(team_id)
            team_state = team.get("state")
            if team_state not in TEAM_STATES:
                errors.append(
                    f"teams[{index}].state must be one of: "
                    f"{', '.join(sorted(TEAM_STATES))}"
                )
        if len(state_team_ids) != len(set(state_team_ids)):
            errors.append("run-state teams must have unique team_id values")
        if set(state_team_ids) != directory_team_ids:
            errors.append("team directories and run-state teams must match")

    status = state.get("status")
    if status in DISPATCH_STATUSES:
        product_contract = state.get("product_contract")
        if product_contract == "replace-me":
            errors.append("product_contract is unresolved before dispatch")
        else:
            _run_owned_file(run_dir, product_contract, "product_contract", errors)
        if delivery_profile is not None and "replace-me" in delivery_profile.read_text(
            encoding="utf-8"
        ):
            errors.append("delivery-profile.yaml contains unresolved placeholders")
        for team_id in sorted(directory_team_ids):
            contract = teams_dir / team_id / "team-contract.yaml"
            if contract.is_file() and "replace-me" in contract.read_text(encoding="utf-8"):
                errors.append(f"team {team_id} contract contains unresolved placeholders")
        if isinstance(teams, list):
            agent_names = {
                agent.get("name")
                for agent in state.get("agents", [])
                if isinstance(agent, dict) and isinstance(agent.get("name"), str)
            }
            for index, team in enumerate(teams):
                if not isinstance(team, dict):
                    continue
                for field in ("lead_agent", "mission"):
                    if not isinstance(team.get(field), str) or not team[field].strip():
                        errors.append(f"teams[{index}].{field} is unresolved before dispatch")
                lead_agent = team.get("lead_agent")
                if isinstance(lead_agent, str) and lead_agent not in agent_names:
                    errors.append(
                        f"teams[{index}].lead_agent must reference a recorded agent"
                    )
                team_state = team.get("state")
                if status == "ready" and team_state != "ready":
                    errors.append(f"teams[{index}].state must be ready before dispatch")
                elif status != "ready" and team_state == "planned":
                    errors.append(f"teams[{index}].state cannot remain planned after dispatch")
        metrics = state.get("workflow_metrics")
        if not isinstance(metrics, dict):
            errors.append("workflow_metrics must be an object before dispatch")
        elif metrics.get("teams_activated") != len(state_team_ids):
            errors.append("workflow_metrics.teams_activated must match active teams")

    if status == "completed":
        verification = state.get("verification")
        if not isinstance(verification, list) or not verification:
            errors.append("completed run must record verification evidence")
        elif any(
            not isinstance(item, dict)
            or not isinstance(item.get("gate"), str)
            or not item["gate"].strip()
            or item.get("result") != "passed"
            or not isinstance(item.get("evidence"), list)
            or not item["evidence"]
            or not all(
                isinstance(evidence, str) and evidence.strip()
                for evidence in item["evidence"]
            )
            for item in verification
        ):
            errors.append(
                "completed run verification entries must record a named gate, "
                "passed result, and non-empty evidence"
            )
        resources = state.get("resources")
        if isinstance(resources, list) and any(
            not isinstance(resource, dict)
            or resource.get("state") not in RETIRED_RESOURCE_STATES
            for resource in resources
        ):
            errors.append("completed run has resources that are not retired")
        if isinstance(resources, list) and any(
            not isinstance(resource, dict)
            or not RESOURCE_REQUIRED_FIELDS <= resource.keys()
            or not isinstance(resource.get("resource_id"), str)
            or not resource["resource_id"].strip()
            or not isinstance(resource.get("resource_type"), str)
            or not resource["resource_type"].strip()
            or not resource.get("retirement_evidence")
            or not resource.get("retirement_action")
            or (
                resource.get("state") == "retired"
                and (
                    resource.get("verified_absent") is not True
                    or not resource.get("retired_at")
                )
            )
            for resource in resources
        ):
            errors.append(
                "completed run resource entries must include identity and retirement evidence"
            )
        if isinstance(teams, list) and any(
            not isinstance(team, dict) or team.get("state") != "retired"
            for team in teams
        ):
            errors.append("completed run has teams that are not retired")
        if final_report is not None:
            report = final_report.read_text(encoding="utf-8")
            if "replace-me" in report or REPORT_PLACEHOLDER.search(report):
                errors.append("completed run final report contains unresolved placeholders")
            present_headings = {
                line.strip() for line in report.splitlines() if line.startswith("#")
            }
            if not FINAL_REPORT_SECTIONS <= present_headings:
                errors.append("completed run final report is missing required sections")
            report_lines = report.splitlines()
            if any(
                not any(
                    line.startswith(prefix) and line.removeprefix(prefix).strip()
                    for line in report_lines
                )
                for prefix in FINAL_REPORT_FIELDS
            ):
                errors.append("completed run final report is missing substantive fields")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    errors = validate_run(args.run_dir)
    if errors:
        for error in errors:
            print(f"error: {error}")
        raise SystemExit(1)
    print(f"Herdcraft run is valid: {args.run_dir.resolve()}")


if __name__ == "__main__":
    main()
