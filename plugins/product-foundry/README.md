# Product Foundry

`$product-foundry` (Codex) or `/product-foundry` (Claude Code) runs a
resumable, approval-gated product-foundry session. It interviews one material
decision at a time and produces canonical planning artifacts under the target
product's `docs/` tree, ending in `docs/implementation-manifest.json`.

`$implement-prd` or `/implement-prd` starts a separate fresh or resume build
session from attachments, explicit paths, a manifest, canonical documentation,
then repository context maps (in that order). It never silently overwrites
credible implementation state.

The package exposes thirteen directly invokable `foundry-*` revision phases.
They share the workflow, policy, artifact, and platform-adapter contracts in
`references/`. Prototype templates are plain HTML, vanilla JavaScript, and the
Tailwind CSS v4 browser CDN: no framework, package install, or build step.

## Safety and portability

The process is platform-neutral. The adapter selects Claude-native prompts or
Codex structured input when available and falls back to explicit plain text.
Every consequential external action requires approval with impact, cost/risk,
rollback, and alternatives; local reversible work can proceed autonomously.
Run `python3 scripts/validate_product_foundry.py` to validate the packaged
contract before publishing.
