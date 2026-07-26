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

Part of this contract cannot be written as a schema. JSON Schema reaches
only what is local to a single lane: the role, mode, and depth pairings,
and that a `write` lane owns at least one path while a `read_only` or
`execute` lane owns none. It has no keyword for uniqueness by property and
none for a reference from one array into another, so the identity
invariants that span lanes are checked mechanically before dispatch: ids
are unique across the lane plan, normalized results map one-to-one onto
those ids, and every `dependsOn`, `parentLaneId`, dispatch wave entry, and
hoisted entry resolves to a declared lane. A dependency is scheduled in an
earlier wave than the lane declaring it, the waves partition the plan's ids
exactly, no two lanes scheduled in the same wave declare intersecting
`ownedPaths` — the mechanical form of G7 — and a depth-two `mechanic` may
name only a `builder` lane as its parent, that last edge being what makes
the depth-two ceiling true of the data rather than only of the prose. These
are contract terms, not advice: a duplicate lane id overwrites a brief at
`lanes/<lane-id>.md` and leaves a document that still validates. The
repository's `scripts/validate_orchestra.py` is the reference
implementation of that list; a root on a host that cannot run it owes the
same checks itself.

What neither layer reaches is the root's alone, because it is not in the
documents to check: that a lane's actual diff stays inside the paths it
declared (G5), that acceptance is genuinely checkable by someone other than
the lane, and that a hoisted lane's deliverable reaches the parent it was
hoisted from as a declared input.

Host specifics never enter the result. Resolved tier, dispatch wave, worker
identity, hoisting, and degradation belong to the run record alone. That
separation is what makes a run opened on one host resumable on another: the
lane plan and the normalized results are portable, the dispatch record is not.
Inputs name artifacts, not conversations — a lane reads an upstream lane's
deliverable, never its reasoning.
