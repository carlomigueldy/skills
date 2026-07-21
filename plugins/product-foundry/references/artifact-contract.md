# Artifact contract

Canonical generated state belongs in the product repository's `docs/` hierarchy
for product, company, research, design, architecture, marketing, delivery,
releases, agents, and handoffs. Consolidate small products rather than creating
empty documents. `docs/implementation-manifest.json` indexes artifacts without
duplicating their content and validates against `schemas/implementation-manifest.schema.json`.

Build-free prototypes each have one canonical current version under
`docs/prototypes/low-fidelity/` and `docs/prototypes/high-fidelity/`. They use
plain HTML, vanilla JavaScript, and `@tailwindcss/browser@4`; Git is their
history. Context maps point to canonical docs and stay concise.
