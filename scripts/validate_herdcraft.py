#!/usr/bin/env python3
"""Validate the Codex-only Herdcraft package and repository registrations."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_NAME = "herdcraft"
VERSION = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
REQUIRED_FILES = {
    "README.md",
    "CHANGELOG.md",
    "version.txt",
    ".codex-plugin/plugin.json",
    "scripts/init-run.py",
    "scripts/validate-run.py",
    "scripts/summarize-run.py",
    "skills/herdcraft/SKILL.md",
    "skills/herdcraft/agents/openai.yaml",
    "skills/herdcraft/assets/capability-ledger.yaml",
    "skills/herdcraft/assets/delivery-profile.yaml",
    "skills/herdcraft/assets/final-report.md",
    "skills/herdcraft/assets/run-state.json",
    "skills/herdcraft/assets/task-contract.md",
    "skills/herdcraft/assets/team-contract.yaml",
    "skills/herdcraft/assets/team-report.md",
    "skills/herdcraft/references/capabilities-and-delivery.md",
    "skills/herdcraft/references/operating-contract.md",
    "skills/herdcraft/references/specialists.yaml",
    "skills/herdcraft/references/team-operations.md",
}


def _json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read JSON {path}: {exc}")
        return None


def validate(root: Path) -> list[str]:
    root = Path(root).resolve()
    plugin = root / "plugins" / PLUGIN_NAME
    errors: list[str] = []
    for relative in sorted(REQUIRED_FILES):
        if not (plugin / relative).is_file():
            errors.append(f"missing Herdcraft file: {relative}")
    if (plugin / ".claude-plugin/plugin.json").exists():
        errors.append("Herdcraft v1 must not ship a Claude manifest")
    if errors:
        return errors

    manifest = _json(plugin / ".codex-plugin/plugin.json", errors)
    if not isinstance(manifest, dict):
        return errors
    if manifest.get("name") != PLUGIN_NAME:
        errors.append("Codex manifest name must be herdcraft")
    version = manifest.get("version")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        errors.append("Codex manifest version must be stable semantic versioning")
    if manifest.get("skills") != "./skills/":
        errors.append("Codex manifest skills path must be ./skills/")
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("Codex manifest interface must be an object")
    else:
        for field in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
        ):
            if not isinstance(interface.get(field), str) or not interface[field].strip():
                errors.append(f"Codex manifest interface.{field} must be non-empty")
        prompts = interface.get("defaultPrompt")
        if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3 or not all(
            isinstance(prompt, str) and prompt for prompt in prompts
        ):
            errors.append("Codex manifest defaultPrompt must contain one to three strings")
    if (plugin / "version.txt").read_text(encoding="utf-8").strip() != version:
        errors.append("version.txt must match the Codex manifest")

    skill = (plugin / "skills/herdcraft/SKILL.md").read_text(encoding="utf-8")
    if not skill.startswith("---\nname: herdcraft\n"):
        errors.append("Herdcraft skill frontmatter name must match its directory")
    if "[TODO:" in skill or "TBD" in skill:
        errors.append("Herdcraft skill contains unresolved placeholders")
    metadata = (plugin / "skills/herdcraft/agents/openai.yaml").read_text(
        encoding="utf-8"
    )
    if "$herdcraft" not in metadata:
        errors.append("Herdcraft UI default prompt must invoke $herdcraft")

    run_state = _json(plugin / "skills/herdcraft/assets/run-state.json", errors)
    if not isinstance(run_state, dict) or run_state.get("schema_version") != 4:
        errors.append("Herdcraft run-state template must use schema_version 4")
    for script in sorted((plugin / "scripts").glob("*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f"invalid Python helper {script.name}: {exc}")

    marketplace = _json(root / ".agents/plugins/marketplace.json", errors)
    codex_entries = marketplace.get("plugins", []) if isinstance(marketplace, dict) else []
    matching = [
        entry
        for entry in codex_entries
        if isinstance(entry, dict)
        and entry.get("name") == PLUGIN_NAME
        and entry.get("source")
        == {"source": "local", "path": "./plugins/herdcraft"}
    ]
    if len(matching) != 1:
        errors.append("Codex marketplace must register Herdcraft exactly once")

    claude_marketplace = _json(root / ".claude-plugin/marketplace.json", errors)
    claude_entries = (
        claude_marketplace.get("plugins", [])
        if isinstance(claude_marketplace, dict)
        else []
    )
    claude_names = {
        entry.get("name")
        for entry in claude_entries
        if isinstance(entry, dict)
    }
    if PLUGIN_NAME in claude_names:
        errors.append("Herdcraft v1 must not be registered in the Claude marketplace")

    release = _json(root / "release-please-config.json", errors)
    package_release = (
        release.get("packages", {}).get("plugins/herdcraft")
        if isinstance(release, dict)
        else None
    )
    if not isinstance(package_release, dict) or package_release.get("release-type") != "simple":
        errors.append("release-please must register Herdcraft as a simple package")
    else:
        extra_paths = {
            item.get("path")
            for item in package_release.get("extra-files", [])
            if isinstance(item, dict)
        }
        if extra_paths != {".codex-plugin/plugin.json"}:
            errors.append("release-please must synchronize only Herdcraft's Codex manifest")
    released = _json(root / ".release-please-manifest.json", errors)
    if isinstance(released, dict) and released.get("plugins/herdcraft") != version:
        errors.append("release-please manifest must match the Herdcraft version")

    package_json = _json(root / "package.json", errors)
    pi_skills = (
        package_json.get("pi", {}).get("skills", [])
        if isinstance(package_json, dict)
        else []
    )
    if "plugins/herdcraft/skills" in pi_skills:
        errors.append("Codex-only Herdcraft must not be exposed through pi")
    try:
        marker = (root / "skills/.generated").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read generated skill marker: {exc}")
    else:
        if "plugins/herdcraft/skills" in marker:
            errors.append("Codex-only Herdcraft must not be in the cross-agent mirror")
    return errors


def main(argv: list[str] | None = None) -> int:
    target = Path(argv[0]) if argv else Path(__file__).resolve().parents[1]
    errors = validate(target)
    if errors:
        print("Herdcraft validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Herdcraft validation passed: {(target / 'plugins/herdcraft').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
