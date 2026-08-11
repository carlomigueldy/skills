#!/usr/bin/env python3
"""Initialize a non-overwriting Herdcraft run ledger in a Git repository."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "herdcraft"


def _validate_identifier(value: str, label: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(
            f"{label} must start with a lowercase letter or digit and contain "
            "only lowercase letters, digits, dots, underscores, or hyphens"
        )


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def initialize_run(
    *,
    repo_root: Path,
    run_id: str,
    objective: str,
    base_revision: str,
    teams: list[str],
) -> Path:
    """Create a run ledger from bundled templates without overwriting one."""
    _validate_identifier(run_id, "run id")
    for team in teams:
        _validate_identifier(team, "team id")
    if len(set(teams)) != len(teams):
        raise ValueError("team ids must be unique")
    if not objective.strip():
        raise ValueError("objective must not be empty")
    if not base_revision.strip() or base_revision == "replace-me":
        raise ValueError("base revision must identify an existing commit")

    repo_root = repo_root.resolve()
    run_dir = (repo_root / ".orchestration" / "runs" / run_id).resolve()
    try:
        run_dir.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError("run ledger must stay within the repository") from exc
    run_dir.mkdir(parents=True, exist_ok=False)
    try:
        assets = SKILL_ROOT / "assets"
        references = SKILL_ROOT / "references"
        shutil.copy2(assets / "delivery-profile.yaml", run_dir / "delivery-profile.yaml")
        shutil.copy2(assets / "final-report.md", run_dir / "final-report.md")
        shutil.copy2(references / "specialists.yaml", run_dir / "specialists.yaml")

        templates = run_dir / "templates"
        templates.mkdir()
        shutil.copy2(assets / "task-contract.md", templates / "task-contract.md")
        shutil.copy2(assets / "team-report.md", templates / "team-report.md")

        state = json.loads((assets / "run-state.json").read_text(encoding="utf-8"))
        state.update(
            {
                "run_id": run_id,
                "objective": objective.strip(),
                "repo_root": str(repo_root),
                "base_revision": base_revision.strip(),
                "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
        )
        state["startup_context"].update(
            {
                "requested_cwd": str(repo_root),
                "repository_status": "existing",
                "resolution": "resolved Git repository",
            }
        )
        state["teams"] = [
            {
                "team_id": team,
                "lead_agent": None,
                "mission": None,
                "team_contract": f"teams/{team}/team-contract.yaml",
                "ownership": {
                    "allowed_paths": [],
                    "forbidden_paths": [],
                    "stable_interfaces": [],
                },
                "delegation_budget": {
                    "maximum_depth": 1,
                    "maximum_active_children": 3,
                    "maximum_total_children": 6,
                },
                "state": "planned",
                "integration_revision": None,
                "report_paths": {
                    "checkpoint": f"teams/{team}/checkpoint.md",
                    "incidents": f"teams/{team}/incidents",
                    "final_handoff": f"teams/{team}/final-handoff.md",
                },
                "resource_ids": [],
            }
            for team in teams
        ]
        _write_text(run_dir / "run-state.json", json.dumps(state, indent=2) + "\n")

        team_root = run_dir / "teams"
        team_root.mkdir()
        for team in teams:
            team_dir = team_root / team
            (team_dir / "incidents").mkdir(parents=True)
            contract = (assets / "team-contract.yaml").read_text(encoding="utf-8")
            contract = contract.replace("team_id: replace-me", f"team_id: {team}", 1)
            contract = contract.replace(
                "capability_ledger: replace-me",
                f"capability_ledger: teams/{team}/capability-ledger.yaml",
                1,
            )
            contract = contract.replace(
                "checkpoint_path: replace-me",
                f"checkpoint_path: teams/{team}/checkpoint.md",
                1,
            )
            contract = contract.replace(
                "incident_directory: replace-me",
                f"incident_directory: teams/{team}/incidents",
                1,
            )
            contract = contract.replace(
                "final_handoff_path: replace-me",
                f"final_handoff_path: teams/{team}/final-handoff.md",
                1,
            )
            _write_text(team_dir / "team-contract.yaml", contract)

            ledger = (assets / "capability-ledger.yaml").read_text(encoding="utf-8")
            ledger = ledger.replace(
                "repo_root: replace-me",
                f"repo_root: {json.dumps(str(repo_root))}",
                1,
            )
            ledger = ledger.replace("team_id: replace-me", f"team_id: {team}", 1)
            _write_text(team_dir / "capability-ledger.yaml", ledger)
        return run_dir
    except Exception:
        shutil.rmtree(run_dir)
        raise


def resolve_git_context(requested: Path) -> tuple[Path, str]:
    """Return the repository root and current commit for a requested path."""
    root = subprocess.run(
        ["git", "-C", str(requested), "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    revision = subprocess.run(
        ["git", "-C", root, "rev-parse", "--verify", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    return Path(root), revision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--team", action="append", default=[])
    args = parser.parse_args()
    try:
        repo_root, revision = resolve_git_context(args.repo)
        run_dir = initialize_run(
            repo_root=repo_root,
            run_id=args.run_id,
            objective=args.objective,
            base_revision=revision,
            teams=args.team,
        )
    except (FileExistsError, OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"error: {exc}") from exc
    print(run_dir)


if __name__ == "__main__":
    main()
