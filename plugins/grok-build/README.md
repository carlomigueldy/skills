# grok-build

Grok Build multi-agent orchestration kit for shipping features with a
tiered plan → explore → implement → verify → adversarial-review loop.

This package is **Grok-native**. Primary install copies artifacts into your
Grok user config (`~/.grok/`), not the Claude Code marketplace runtime.

## Contents

| Path | Installs to | Purpose |
| --- | --- | --- |
| `skills/ultracode/` | `~/.grok/skills/ultracode/` | `/ultracode` pure-orchestrator pipeline |
| `workflows/ship-feature.rhai` | `~/.grok/workflows/ship-feature.rhai` | Deterministic `/workflow ship-feature` harness |
| `personas/*.toml` | `~/.grok/personas/` | Architect, sweeper, implementer, reviewer |
| `roles/*.toml` | `~/.grok/roles/` | Effort + capability defaults for those lanes |

## Install (Grok Build)

From a checkout of this repo:

```bash
# User-level (recommended)
python3 plugins/grok-build/scripts/install.py

# Or from repo root helper
python3 scripts/install-grok-build.py

# Project-level instead of ~/.grok
python3 plugins/grok-build/scripts/install.py --target .grok

# Preview without writing
python3 plugins/grok-build/scripts/install.py --dry-run
```

Requirements: [Grok Build](https://grok.com) CLI installed and authenticated
(`XAI_API_KEY` or `grok login`). After install, restart the TUI or open a new
session so skill/workflow discovery reloads.

### What the installer does

1. Creates `skills/`, `workflows/`, `personas/`, and `roles/` under the target.
2. Copies `ultracode` skill (including `references/tiering.md`).
3. Copies `ship-feature.rhai`.
4. Copies the four persona and four role TOML files (overwrites same-named
   files; leaves unrelated local files alone).

## Usage

### Skill (interactive orchestrator)

```text
/ultracode Add retry + backoff to the payment client
/ultracode --skip-plan Fix the null deref in auth middleware
```

The parent agent stays a pure orchestrator: it spawns plan / explore /
implement / verify / review children, injects personas into prompts, and
runs a fix loop until open bugs are zero.

### Workflow (deterministic Rhai harness)

```text
/workflow ship-feature target="Add retry to the payment client"
/ship-feature target="..."
```

Same tier ladder as ultracode, expressed as a Rhai workflow script.

## Tier map (grok-4.5)

Native catalog is currently `grok-4.5` only. Tiering is **reasoning effort +
agent type + capability**, not separate model IDs:

| Lane | Effort | Agent type | Capability | Persona |
| --- | --- | --- | --- | --- |
| Plan | high | `plan` | read-only | `architect` |
| Explore | low | `explore` | read-only | `sweeper` |
| Implement / fix | medium | `general-purpose` | all | `implementer` |
| Verify | medium | `general-purpose` | all | implementer brief |
| Review | high | `general-purpose` | read-only | `reviewer` |

See `skills/ultracode/references/tiering.md` for the full contract.

## Claude / Codex note

A `.claude-plugin/plugin.json` is present so this package participates in the
repo marketplace registry and release-please pipeline. Ultracode and the Rhai
workflow target **Grok Build** APIs (`spawn_subagent`, personas, workflows).
Do not expect full behavior under Claude Code or Codex without a port.

## Versioning

Released independently via release-please. Tags look like `grok-build--v0.1.0`.
See the root [`docs/VERSIONING.md`](../../docs/VERSIONING.md).
