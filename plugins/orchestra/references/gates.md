# Quality gates

Gates are not advisory. A gate that cannot be evaluated fails closed, and a
gate is never waived by a lane that would benefit from waiving it.

| ID | Gate |
| --- | --- |
| G1 | Tests precede implementation. A `builder` lane's first artifact is a failing test with its raw output stored. |
| G2 | Evidence, not assertions. A claimed pass with no stored raw output is a failure, not a warning. |
| G3 | Adversarial verification runs in a context that never saw the authoring work. |
| G4 | A security pass triggers automatically on auth or authz, payments, secrets, deserialization, file upload, and shell, SQL, or template construction. |
| G5 | No scope creep. A lane's diff is a subset of its declared paths; the check is mechanical and blocking. |
| G6 | Maximum delegation depth is two. A run that needs a third level is a HARD STOP for human escalation, not a justification recorded in the run record. |
| G7 | One writer per path, declared before dispatch. |
| G8 | HARD STOP before every irreversible or outward-facing action. |
| G9 | N green lanes are not a green whole. The full repository gate runs once after integration, and only that run counts. |

G9 is the failure mode that kills parallel orchestration in practice. Lane
results are inputs to integration, never a substitute for it: a set of lanes
that each passed in isolation says nothing about the merged tree. Run the full
gate exactly once, after every lane has landed, and record its raw output as
the run's completion evidence. A rerun after a fix replaces that record; it
never accumulates alongside it.

G4 detection is by surface, not by lane intent — inspect the integrated diff
for the listed surfaces and trigger the security pass on a match even when no
lane declared security work. G5 and G7 are checked against the declared path
ownership from the lane plan, so a lane that widens its own declaration fails
both.

G6 is structural, not procedural. `run.json` caps `delegationDepth` at two,
a lane plan caps each lane's `depth` at two, `mechanic` is the only role
dispatchable at depth two, and only a `builder` lane may parent one. No
field raises that ceiling: a goal that appears to need a third level is
decomposed into more depth-one lanes or escalated to a human.
