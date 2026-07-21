# Platform adapter contract

Domain phase skills describe normalized questions, options, recommendation, and
consequences; they never assume a host-specific prompt tool. At runtime, the
adapter discovers whether Codex exposes structured input. Claude Code uses its
native prompt mechanism; Codex uses structured input when available, otherwise
a numbered plain-text fallback. Encode every option with a stable id, label,
boolean recommended flag, and concise consequence. Ask one question, wait for
an explicit answer, and never treat silence as approval. Claude, Codex, and the
plain fallback normalize answers to the same shape:
`{"questionId":"<stable id>","selectedOptionId":"<stable id>"}`.

For `implement-prd`, resolve context in strict precedence: explicit attachments,
explicit files/directories, `docs/implementation-manifest.json`, recognized
canonical docs, then repository `AGENTS.md`/`CLAUDE.md` maps. Validate readable,
non-conflicting critical artifacts before implementation. Detect credible prior
state and request confirmation for resume; `--fresh` and `--resume` are the
only overrides.
