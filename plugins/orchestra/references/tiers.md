# Tiers and roles

Tiers are `deep`, `standard`, and `fast`. A tier names reasoning depth, never
a model, a vendor, or a version. Resolve the mapping from tier to host setting
once at run start and record it in `run.json`; briefs, gates, and workflows
name tiers only.

| Role | Tier | Mode | Writes |
| --- | --- | --- | --- |
| `scout` | fast | read_only | never |
| `analyst` | standard | read_only | never |
| `architect` | deep | read_only | never |
| `builder` | standard | write | its declared paths only |
| `prover` | standard | execute | never |
| `adversary` | standard | read_only | never |
| `judge` | deep | read_only | never |
| `mechanic` | fast | write | its parent's declared paths only |

`builder` is the only writer of product code. `mechanic` is the only role
legally dispatchable at depth two, which is what makes the depth cap
mechanical rather than aspirational. `adversary` never runs in the context
that authored the work it examines.

Run `adversary` at `standard` by default; most falsification is mechanical —
run the negative case, check the boundary, apply the reverse check. Escalate
it to `deep` only on a declared trigger and record that trigger in `run.json`:
the change touches a G4 security surface; the change spans more than one
domain or module boundary; the `adversary` and `prover` lanes disagree; or the
`adversary` returns no findings on a change above the declared size threshold.
Empty findings on a large change is a signal that the cheap pass was
insufficient, not a clean result. `judge` stays `deep` because it runs only on
genuine disagreement, which is the case that needs it.
