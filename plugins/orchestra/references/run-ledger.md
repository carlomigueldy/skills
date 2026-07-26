# Run ledger

Every run writes to `.orchestra/`. `.orchestra/current` is a plain text file
holding the active run id — a file and never a symlink, so Windows checkouts
behave. Each run lives in `.orchestra/<UTC-timestamp>-<slug>/`.

A run is a chain of workflows rather than a single workflow, so the run
directory has two levels. Four files are run-level, opened once and shared by
every link: `run.json`, `baseline.md`, `stops.md`, and `handoff.md`.
Everything else belongs to the link that produced it and lives under that
link's own directory, `<nn>-<workflow>/`, where `nn` is the two-digit position
of the link in the chain, counting from `01` in dispatch order:

```
.orchestra/<UTC-timestamp>-<slug>/
  run.json
  baseline.md
  stops.md
  handoff.md
  01-plan/
    decomposition.md
    lanes/<lane-id>.md
    evidence/<nn>-<label>.txt
  02-implement/
    decomposition.md
    lanes/<lane-id>.md
    evidence/<nn>-<label>.txt
    findings.md
  03-verify/
    decomposition.md
    lanes/<lane-id>.md
    evidence/<nn>-<label>.txt
    findings.md
    verdicts.md
```

Scoping by link is what keeps a chain from overwriting itself. Lane ids are
unique inside one workflow and deliberately reused across the catalog — three
workflows dispatch a `falsify` lane and six dispatch an `adjudicate` lane — and
`decomposition.md`, `findings.md`, `verdicts.md`, and the `evidence/` counter
recur in every link. Flattened into one directory, the later link silently
overwrites the earlier one and `run.json` cannot say which lane a result
belonged to. That failure is invisible in a single-workflow run and certain in
a chained one, so the layout, not the caller's care, has to rule it out.

A workflow invoked directly rather than through the router is a chain of one
and writes to `01-<workflow>/`; there is no unscoped special case to fall back
on. A workflow re-entered later in the chain — dispatched as another link's
prerequisite, or reopened after a review — takes the next free position and
its own directory, so `02-implement/` and `05-implement/` are two links with
separate briefs and separate evidence rather than one link written twice.

Every path a workflow, a lane brief, or a normalized lane result names is
relative to that link's directory. Inside `02-implement/`, `lanes/build.md`
and `evidence/01-red.txt` resolve to `02-implement/lanes/build.md` and
`02-implement/evidence/01-red.txt`; the `evidence/` counter restarts at `01`
in every link. Only the four run-level files above are named relative to the
run directory itself. A workflow's deterministic-outputs list states what its
link contributes to the run — the run-level files are opened by the router and
appended to by each link, never rewritten from scratch by one.

`run.json` is the only place host specifics live: resolved host and
capabilities, the tier mapping, the planned chain with each link's position,
dispatch waves, worker identities, hoisted lanes, adversary escalation
triggers, degradation flags, delegation depth, and `reopenCount`. Every entry
in its `lanes[]` array carries the `workflow` that dispatched the lane and
that link's `chainPosition`, which is what lets a reader attribute a lane to a
link and find its file; a bare `laneId` of `adjudicate` in a chained run names
up to six different lanes. `baseline.md` captures `git status` and `git diff`
before the first link dispatches, and one baseline per run is what makes
quarantine safe across the whole chain. `stops.md` is the run's single ordered
record of hard-stop requests and their answers. `handoff.md` states the goal,
what is verified with pointers to evidence, what is open, and the next
dispatchable step.

Inside a link, `decomposition.md` holds the lane plan that was dispatched, not
a later summary of it. `lanes/<lane-id>.md` stores the brief verbatim followed
by the normalized result verbatim. `evidence/` holds raw command output, never
a paraphrase, never a truncation that removes the failing lines. `findings.md`
and `verdicts.md` exist only in the links that produced them.

Write the ledger as the run proceeds, not at the end. A run interrupted
mid-flight must be resumable from what is on disk: re-read `run.json`, treat
every lane not marked `verified` as unfinished, and re-derive nothing from
memory. `handoff.md` must carry enough for a different agent on a different
host to continue.

In a user's project, ignore the directory locally via `.git/info/exclude`,
which is untracked and touches no file the project owns. Never add
`.orchestra/` to a project's tracked `.gitignore` without asking, and never
package the directory into a plugin or release artifact.
