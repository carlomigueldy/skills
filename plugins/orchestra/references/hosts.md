# Host detection and degradation

Detect the host once, before any dispatch, by scanning environment variable
NAMES only and never their values. First match wins: Claude Cowork when a
remote-session variable is set or `/mnt/user-data` or `/mnt/skills` exists;
Codex CLI when any `CODEX_*` variable is present; OpenCode when any
`OPENCODE*` variable is present; `pi` when any of `PI_CODING_AGENT`,
`PI_CODING_AGENT_DIR`, `PI_SESSION_ID`, `PI_SESSION_FILE`, or
`PI_PACKAGE_DIR` is present; Grok Build when any `GROK_*` variable is
present or a `~/.grok` install root exists; Claude Code when none of the above
match and `$HOME` is a real user home. If the signals conflict, ask once and
never guess silently. Record the resolved host, its capabilities, and the tier
mapping in `run.json`.

Two capabilities decide the scheduler: whether the host dispatches parallel
subagents, and `childDepth`, the number of levels it can dispatch below the
root. `childDepth` is a host capability and equals 1 on Claude Code and Grok
Build alike; the cap of two is an authorization limit and never a runtime
guarantee. When `childDepth` is below 2, hoist the `mechanic` lane to
root-dispatched, run it before its declared parent, pass its deliverable path
down as an input, and mark `hoistedFrom` in the run record. At `childDepth: 0`
the root self-executes each lane under its role brief, one lane at a time. The
lane plan and the normalized results are identical in every case; only the
dispatch record differs.

`pi` is the zero-delegation baseline. Its core ships no subagent tool, so
assume `parallelSubagents: false`, `childDepth: 0`, and `isolatedContext:
false`, self-execute every lane under its role brief, record `isolation:
degraded`, and cap the verdict at `unverified`. Raise those values only when
a tool that dispatches an isolated child agent is actually present in the
session's tool list; probe the tool list, never the filesystem and never the
package settings, because an optional subagent package that is installed but
did not load is not a capability. When such a tool is present, record
`parallelSubagents: true`, `childDepth: 1`, and `isolatedContext: true`, and
schedule exactly as on any other depth-one host.

Degradation obeys three rules. The briefs and the gates never change — only
the scheduler does; a host that cannot parallelize runs the same lanes more
slowly, never fewer of them, and never merges lanes into one worker. A later
sequential fresh-context role-pass reads an earlier lane's artifact and never
its reasoning, which preserves independence when the barrier is trivially met.
Adversary isolation is the one capability that cannot degrade: when the host
cannot give the adversary a context that never saw the authoring work, record
`isolation: degraded` in `run.json` and cap the verdict at `unverified` —
never `approve`.
