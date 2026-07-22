# Ultracode model tiering (Grok Build)

Native catalog today is **`grok-4.5` only**. Tiering is **reasoning effort + agent type + capability**, not Opus/Sonnet/Haiku model IDs.

| Lane | Claude analog | Effort | Agent type | Capability | Persona file |
|------|---------------|--------|------------|------------|--------------|
| Orchestrator (parent) | Fable/Opus | high | parent session | all | — |
| Architect / plan | Fable/Opus | high | `plan` | read-only | `~/.grok/personas/architect.toml` |
| Final review | Fable/Opus | high | `general-purpose` | read-only | `~/.grok/personas/reviewer.toml` |
| Implement + fix loops | Sonnet | medium | `general-purpose` | all | `~/.grok/personas/implementer.toml` |
| Verify (tests) | Sonnet | medium | `general-purpose` | all/execute | implementer brief |
| Mechanical sweeps | Haiku/Explore | low | `explore` | read-only | `~/.grok/personas/sweeper.toml` |

## Hard constraints

- Subagent depth is **1** (children cannot spawn children). Parent owns all fan-out.
- `spawn_subagent` has **no persona parameter** — inject persona instructions into the prompt.
- Prefix `description` with a bracketed role tag: `[architect]`, `[sweeper]`, `[implementer]`, `[reviewer]`, `[verify]`.
- Prefer `isolation: "worktree"` only for parallel implementers that would collide.

## Parent effort

At the start of `/ultracode`, set parent effort high if the session supports it:

```
/effort high
```

Do not lower parent effort for the whole run; children get effort via persona defaults and prompt contracts.
