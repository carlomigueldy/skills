#!/usr/bin/env python3
"""Render a concise Markdown summary from Herdcraft run state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _metric(metrics: dict[str, Any], key: str) -> Any:
    value = metrics.get(key)
    return "unavailable" if value is None else value


def render_summary(state: dict[str, Any]) -> str:
    metrics = state.get("workflow_metrics")
    metrics = metrics if isinstance(metrics, dict) else {}
    usage = state.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    tokens = usage.get("tokens") if isinstance(usage.get("tokens"), dict) else {}
    context = usage.get("context") if isinstance(usage.get("context"), dict) else {}

    lines = [
        f"# Herdcraft run {state.get('run_id', 'unknown')}",
        "",
        f"- Objective: {state.get('objective', 'unavailable')}",
        f"- Status: {state.get('status', 'unavailable')}",
        f"- Teams activated: {_metric(metrics, 'teams_activated')}",
        f"- Agents spawned: {_metric(metrics, 'agents_spawned')}",
        f"- Dispatch waves: {_metric(metrics, 'dispatch_waves')}",
        f"- Peak concurrency: {_metric(metrics, 'peak_concurrency')}",
        f"- Retries: {_metric(metrics, 'retry_count')}",
        f"- Tokens: {tokens.get('availability', 'unavailable')}",
        f"- Context: {context.get('availability', 'unavailable')}",
        "",
        "## Verification",
        "",
    ]
    verification = state.get("verification")
    if isinstance(verification, list) and verification:
        for item in verification:
            if isinstance(item, dict):
                lines.append(
                    f"- {item.get('gate', 'unnamed')}: {item.get('result', 'unavailable')}"
                )
            else:
                lines.append(f"- {item}")
    else:
        lines.append("- No verification evidence recorded.")

    lines.extend(["", "## Residual risks", ""])
    risks = state.get("risks")
    if isinstance(risks, list) and risks:
        lines.extend(f"- {risk}" for risk in risks)
    else:
        lines.append("- None recorded.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    state_path = args.run_dir / "run-state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"error: cannot read {state_path}: {exc}") from exc
    if not isinstance(state, dict):
        raise SystemExit("error: run-state.json must contain an object")
    summary = render_summary(state)
    if args.output:
        args.output.write_text(summary, encoding="utf-8")
        print(args.output)
    else:
        print(summary, end="")


if __name__ == "__main__":
    main()
