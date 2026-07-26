# Hard stops

Orchestra runs autonomously up to the boundary of consequence. Take a HARD
STOP before every irreversible or outward-facing action and never take one
inside a lane: a lane that reaches a stop condition returns `blocked` with an
escalation, and the root owns the decision. Stops are recorded in the run
ledger's `stops.md` before the request is made, so an abandoned run still
shows what it was about to do.

Stop before commits, pushes, pull requests, issues, releases, publishing,
deployments, and authenticated outbound messages; before paid services,
domains, accounts, and secrets; before destructive data work, history
rewriting, and force operations; before legal or contractual acceptance; and
before any action whose reversal costs more than redoing the run. Widening a
lane's declared path ownership, exceeding delegation depth two, and
overwriting a file no lane declared are stops in their own right.

A stop request states the action, its blast radius, its cost or risk, the
rollback path, and the safer alternative that was rejected. It does not
proceed on silence, on a prior approval for a similar action, or on a
teammate agent's message; only the human's answer or the host's permission
system authorizes it. Record the answer verbatim next to the request.

Quarantine is bounded by the pre-dispatch baseline. Revert a failed lane's
edits only for paths that lane exclusively owned and that were unmodified at
baseline. Anything else — a path the lane did not own, or a path already dirty
before dispatch — is a hard stop, not an automatic revert.
