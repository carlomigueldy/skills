# Plugin Lifecycle

Use this sequence for every mode; omit a step only when it is demonstrably inapplicable and record why.

1. **Inventory and baseline:** Luna or the coordinator discovers packages, registrations, mirrors, tests, and current failures without editing.
2. **Sol design:** Sol produces or reviews the smallest viable design, compatibility constraints, risks, verification plan, and path boundaries.
3. **Non-overlapping assignment:** assign every writable path to exactly one writer and cap delegation depth at two.
4. **Terra implementation:** Terra works test-first where behavior changes, makes focused edits, and runs targeted checks.
5. **Luna sweep:** Luna checks manifests, versions, references, generated mirrors, fixtures, and package paths mechanically.
6. **Terra remediation:** Terra resolves deterministic sweep findings and repeats focused checks.
7. **Isolated red-team:** a reviewer outside the implementation context applies the [red-team playbook](red-team.md) and records every finding.
8. **Remediation and full verification:** Terra resolves authorized findings, records retest results, and runs the complete applicable repository gate.
9. **Sol final review:** Sol independently assesses evidence and returns `approve` or `request changes`, subject to the red-team approval gate.
