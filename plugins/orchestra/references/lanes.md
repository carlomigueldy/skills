# Lane contract

A lane is the unit of delegation and the only abstraction the workflows
compose from. Every lane carries a stable id, exactly one role, exactly one
tier, one access mode (`read_only`, `write`, or `execute`), an ordered
`dependsOn` list, the writable paths it owns exclusively, its inputs, exactly
one deliverable, and acceptance stated as a condition someone other than the
lane can check. A lane without acceptance is not dispatchable; fail closed
rather than dispatch one. Only a `write` lane owns paths and it owns at least
one; `read_only` and `execute` lanes own none. Lanes whose owned paths
intersect never run concurrently on any host, and no path has two owners in
one wave. Declare ownership before dispatch, never after.

Every lane returns the same normalized result on every host:
`{laneId, status, deliverables[], evidence[], findingIds[]}` with status drawn
from `pending`, `in_progress`, `blocked`, `partial`, `verified`, and `stale`.
A `verified` status requires at least one evidence entry pointing at stored
raw output. A `blocked` status requires a recorded escalation naming what
would unblock it. Evidence entries reference files under the `evidence/`
directory of the ledger link that dispatched the lane, relative to that link,
and never paraphrase what those files contain. Every path in a lane plan or a
normalized result resolves inside that link's directory, which is what keeps
two workflows in one chain from writing the same `lanes/adjudicate.md`. The
layout is in `run-ledger.md`.

Host specifics never enter the result. Resolved tier, dispatch wave, worker
identity, hoisting, and degradation belong to the run record alone. That
separation is what makes a run opened on one host resumable on another: the
lane plan and the normalized results are portable, the dispatch record is not.
Inputs name artifacts, not conversations — a lane reads an upstream lane's
deliverable, never its reasoning.
