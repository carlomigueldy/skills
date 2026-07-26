# Findings and verdicts

A finding has exactly seven fields: `id`, `severity`, the `precondition` or
attack that reaches it, `evidence` pointing at stored raw output, `impact`,
`remediation`, and `retest`. A report without a reachable precondition and
stored evidence is an opinion, not a finding, and does not enter the ledger.

Severity is one of `critical`, `high`, `medium`, `low`, `informational` and
describes consequence alone. Status is separate and is one of `open`, `fixed`,
`accepted`, `wontfix`; changing status never changes severity, and a finding
downgraded to close a run is a falsified record. Normalize inbound reports
from other tools and reviewers — `bug` maps to `high`, `suggestion` to `low`,
`nit` to `informational` — then re-rate on the evidence rather than trusting
the inbound label.

A finding moves to `fixed` only when its `retest` records `result: pass`
against evidence produced after the remediation landed. Reusing the evidence
that opened the finding, or a retest run by the lane that authored the fix,
leaves it `open`. `accepted` and `wontfix` each require a named human decision
recorded in the ledger.

A verdict is `approve`, `request_changes`, or `unverified`. `approve` is
impossible while any `critical` or `high` finding is unresolved unless a human
exception is recorded with the accepting party and the reason. `unverified` is
the honest outcome when the evidence needed to decide does not exist — when
adversary isolation degraded, when a gate could not run, or when a lane
returned `partial`. Never present `unverified` as a pass and never let an
absent check become a green one.
