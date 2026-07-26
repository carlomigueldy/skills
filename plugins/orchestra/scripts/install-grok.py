#!/usr/bin/env python3
"""Export the orchestra plugin to a Grok Build install (`~/.grok` by default).

Markdown is orchestra's single source of truth: role briefs live at
`roles/<role>.md` with YAML frontmatter, references at `references/*.md`,
schemas at `schemas/*.json`, skills at `skills/<name>/SKILL.md`. Claude Code,
Codex CLI, and OpenCode all read a role brief directly. Grok Build does not --
its persona loader wants a native TOML file per role, not Markdown.

An earlier attempt at this shipped hand-authored TOML personas and then told
the *agent*, at runtime, to `read_file` the TOML and hand-extract the
triple-quoted `instructions` body as a prompt step -- parsing a config
format by hand, on every run, forever. That is the defect this script
fixes: TOML is a **generated artifact**, derived from the Markdown briefs
once, at install time. Grok then loads a real persona file natively and
nothing at runtime hand-parses anything.

Two things this script handles, mirroring `scripts/sync-skills.py`:

1. **Install** (default). Stage a full export in a temp directory --
   untouched copies of `skills/`, `references/`, `schemas/`, `roles/*.md`,
   plus a generated `roles/<role>.toml` per role, sitting next to its source
   `.md` so both forms share one directory -- then merge it into `--target`
   one immediate child at a time (`skills/fan-out`, `references/lanes.md`,
   `roles/scout.toml`, ...). The merge never touches an entry it did not
   itself generate: the default target is `~/.grok`, and `skills/`,
   `references/`, `schemas/`, and `roles/` under it are shared,
   unnamespaced directories another installed Grok Build plugin's skills,
   references, or personas may already live in.

2. **Drift check** (`--check`). Two distinct questions, split on whether
   `--target` was explicitly given, so the CI invocation means the same
   thing on every machine it runs on:

   - **`--check` alone.** Target-independent: proves generation from source
     succeeds and is deterministic (build it twice, independently, and diff
     the two builds against each other) and emits valid TOML for every
     role. Never reads or writes `--target` -- not even to check whether it
     exists. This is what CI runs, and it is deliberately blind to whatever
     happens to live at the default `~/.grok` on the machine running it: a
     developer's real Grok Build install is not a committed repository
     artifact, so drift against it proves nothing about the repo's
     self-consistency, and asserting against it would make the same CI
     command mean something different depending on whether the runner's
     home directory happens to be populated.
   - **`--check --target DIR`.** Install-currency: diffs a freshly
     generated export against whatever is already installed at DIR, the
     way `sync-skills.py --check` diffs a generated mirror against a
     committed source. Useful for a person asking "is my install current?"
     Fails if DIR does not exist yet -- there is nothing to be current with.

Layout preserved: a relative link inside a copied `SKILL.md`, such as
`../../references/lanes.md`, resolves the same way under the export as it
does in the package, because the internal shape is identical -- only the
package root changes.

Stdlib only, by design: no `toml`/`tomli_w` dependency for writing, and no
runtime dependency on `tomllib` either (that's Python 3.11+, read-only, and
not needed here since this script never parses TOML -- it emits it, once, as
plain text with careful escaping. See `_toml_escape`.)

Usage:
    plugins/orchestra/scripts/install-grok.py                     # install to ~/.grok
    plugins/orchestra/scripts/install-grok.py --target DIR        # install elsewhere
    plugins/orchestra/scripts/install-grok.py --check             # CI: generation is valid + deterministic
    plugins/orchestra/scripts/install-grok.py --check --target DIR  # is DIR's install current?
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = Path.home() / ".grok"

# Copied verbatim, whole subtree, no per-file transformation.
PLAIN_COPY_DIRS = ("skills", "references", "schemas")

# `roles/` gets both: the source `.md` copied as-is, and a generated `.toml`
# next to it. Kept in the same directory (rather than a separate `personas/`
# tree) so there is exactly one place to look for a role's install-time
# artifacts, and so the Markdown stays visible as the thing that was
# actually the source, not a redundant copy nobody expects to find.
ROLES_DIR = "roles"

# Every top-level entry this script writes into `--target`. Used both to
# scope the drift check (ignore anything else already at the target) and to
# scope the install swap (never delete anything else already at the target).
OWNED_TOP_LEVEL = PLAIN_COPY_DIRS + (ROLES_DIR,)

# Never mirror these, regardless of what's on disk.
EXCLUDED_FILES = {".DS_Store"}

TIER_TO_REASONING_EFFORT = {
    "deep": "high",
    "standard": "medium",
    "fast": "low",
}


class GrokExportError(Exception):
    """Raised when a valid export cannot be built from the source package."""


def _should_skip(name: str) -> bool:
    return name in EXCLUDED_FILES


def _capability_mode(mode: str) -> str:
    """Map a role brief's `mode` to Grok's `default_capability_mode`.

    Only `read_only` gets the restrictive mapping; every other mode
    (`write`, `execute`) maps to `all` -- matching the two-way split the
    brief mappings actually need, not a full mode -> mode table.
    """
    return "read-only" if mode == "read_only" else "all"


def _toml_escape(text: str, *, multiline: bool) -> str:
    """Escape `text` for embedding in a TOML basic string.

    Every double quote is escaped, not only runs of three or more. That is
    more conservative than the TOML spec requires (one or two consecutive
    quotes are legal unescaped in a multi-line basic string), but it means
    the escaped text can *never* collide with the `\"\"\"` delimiter or
    produce an ambiguous closing sequence -- no matter what a future brief's
    prose contains. That collision, silently producing invalid TOML, is
    exactly the failure mode this script exists to avoid, so this trades a
    little prettiness for a proof that stands regardless of source content.

    Backslashes and disallowed control characters are escaped for the same
    reason: correctness over prettiness in a generated file nobody is meant
    to hand-edit anyway.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\n":
            out.append(ch if multiline else "\\n")
        elif ch == "\t":
            out.append(ch)
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    return "".join(out)


def parse_role_brief(path: Path) -> tuple[dict[str, str], str]:
    """Split a role brief into (frontmatter, body).

    Role frontmatter is a flat block of `key: value` scalar pairs -- no
    nesting, no YAML quoting, no multi-line values -- so a small hand-rolled
    parser covers it without a YAML dependency for four fields.

    The returned body is everything after the closing `---`, with a leading
    `# <heading>` line and the blank line after it stripped when present, so
    what lands in the persona's `instructions` is the brief's prose, not a
    restatement of its own title.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise GrokExportError(f"{path}: does not start with a '---' frontmatter block.")
    try:
        closing_index = lines.index("---", 1)
    except ValueError:
        raise GrokExportError(f"{path}: frontmatter block is never closed with '---'.") from None

    frontmatter: dict[str, str] = {}
    for offset, line in enumerate(lines[1:closing_index], start=2):
        if not line.strip():
            continue
        if ":" not in line:
            raise GrokExportError(
                f"{path}:{offset}: expected 'key: value' in frontmatter, got {line!r}."
            )
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip()

    body = "\n".join(lines[closing_index + 1 :]).strip("\n")

    role_id = frontmatter.get("id", "")
    heading = f"# {role_id}"
    body_lines = body.split("\n")
    if body_lines and body_lines[0].strip() == heading:
        body_lines = body_lines[1:]
        if body_lines and not body_lines[0].strip():
            body_lines = body_lines[1:]
        body = "\n".join(body_lines)

    body = body.strip("\n")
    if body:
        body += "\n"
    return frontmatter, body


def render_persona_toml(*, role_id: str, tier: str, mode: str, body: str, source: Path) -> str:
    """Render one role's frontmatter + body as a Grok Build persona TOML.

    Raises `GrokExportError` -- never emits invalid or silently-wrong TOML --
    when the tier has no known mapping or the body is empty. Both indicate
    the source brief needs a human decision, not a guess baked into the
    export.
    """
    try:
        effort = TIER_TO_REASONING_EFFORT[tier]
    except KeyError:
        raise GrokExportError(
            f"{source}: unknown tier {tier!r} -- expected one of "
            f"{', '.join(sorted(TIER_TO_REASONING_EFFORT))}."
        ) from None
    if not body.strip():
        raise GrokExportError(
            f"{source}: brief body is empty after stripping frontmatter and heading."
        )

    capability_mode = _capability_mode(mode)
    id_literal = _toml_escape(role_id, multiline=False)
    instructions_literal = _toml_escape(body, multiline=True)

    return (
        "# Generated by plugins/orchestra/scripts/install-grok.py from "
        f"roles/{source.name} -- edit the source brief, not this file.\n"
        f'id = "{id_literal}"\n'
        f'reasoning_effort = "{effort}"\n'
        f'default_capability_mode = "{capability_mode}"\n'
        f'instructions = """\n{instructions_literal}"""\n'
    )


def build_export(dest: Path, package_root: Path) -> None:
    """Populate `dest` with a full Grok Build export derived from `package_root`.

    Layout mirrors the package: `skills/`, `references/`, `schemas/` copied
    whole; `roles/<id>.md` copied as-is with `roles/<id>.toml` generated
    alongside it. Raises `GrokExportError` and leaves `dest` partially
    written on any problem -- callers only swap `dest` into a real target
    after this returns successfully.
    """
    dest.mkdir(parents=True, exist_ok=True)

    for name in PLAIN_COPY_DIRS:
        source = package_root / name
        if not source.is_dir():
            raise GrokExportError(f"source dir {source} does not exist.")
        shutil.copytree(source, dest / name, ignore=shutil.ignore_patterns(*EXCLUDED_FILES))

    roles_source = package_root / ROLES_DIR
    if not roles_source.is_dir():
        raise GrokExportError(f"source dir {roles_source} does not exist.")
    role_paths = sorted(p for p in roles_source.glob("*.md") if not _should_skip(p.name))
    if not role_paths:
        raise GrokExportError(f"no role briefs (*.md) found in {roles_source}.")

    roles_dest = dest / ROLES_DIR
    roles_dest.mkdir(parents=True, exist_ok=True)
    for role_path in role_paths:
        shutil.copy2(role_path, roles_dest / role_path.name)

        frontmatter, body = parse_role_brief(role_path)
        role_id = frontmatter.get("id")
        tier = frontmatter.get("tier")
        mode = frontmatter.get("mode")
        missing = [key for key, value in (("id", role_id), ("tier", tier), ("mode", mode)) if not value]
        if missing:
            raise GrokExportError(
                f"{role_path}: frontmatter is missing required key(s): {', '.join(missing)}."
            )

        toml_text = render_persona_toml(
            role_id=role_id, tier=tier, mode=mode, body=body, source=role_path
        )
        (roles_dest / f"{role_path.stem}.toml").write_text(toml_text, encoding="utf-8")


def iter_owned_files(root: Path) -> set[str]:
    """Every file under `root`'s owned subtrees, relative and POSIX-formatted.

    Each path is prefixed by its owning top-level name (e.g. `roles/x.toml`)
    so files from different subtrees never collide in the returned set, and
    anything under `root` outside `OWNED_TOP_LEVEL` -- another plugin's
    install living alongside this one -- is invisible to this function by
    construction.
    """
    found: set[str] = set()
    for name in OWNED_TOP_LEVEL:
        sub = root / name
        if not sub.is_dir():
            continue
        for entry in sub.rglob("*"):
            if entry.is_file() and not _should_skip(entry.name):
                found.add(f"{name}/{entry.relative_to(sub).as_posix()}")
    return found


def diff_dirs(expected: Path, actual: Path, *, report_unexpected: bool = True) -> list[str]:
    """Sorted, concise drift descriptions between two owned-subtree sets, empty if equal.

    `report_unexpected` is off when `actual` is a real `--target`: its owned
    subtrees (`skills/`, `references/`, `schemas/`, `roles/`) are shared,
    unnamespaced directories another installed Grok Build plugin may already
    have entries in (confirmed against a real `~/.grok` during development --
    it already had unrelated skills sitting directly under `skills/`), so an
    entry present in `actual` but not in this export is not necessarily
    drift. It stays on when both sides are this script's own generated
    output (the `--check` determinism comparison), where an extra file on
    either side is a genuine non-determinism bug.
    """
    expected_files = iter_owned_files(expected)
    actual_files = iter_owned_files(actual)

    missing = sorted(expected_files - actual_files)
    common = sorted(expected_files & actual_files)

    problems = [f"missing: {rel}" for rel in missing]
    if report_unexpected:
        extra = sorted(actual_files - expected_files)
        problems += [f"unexpected: {rel}" for rel in extra]
    for rel in common:
        if not filecmp.cmp(expected / rel, actual / rel, shallow=False):
            problems.append(f"changed: {rel}")
    return problems


def swap_into_target(staged: Path, target: Path) -> None:
    """Merge each owned subtree's *immediate children* from `staged` into
    `target`, replacing only entries this export actually produces.

    Deliberately not a directory-level replace of `target/skills`,
    `target/references`, etc.: on Grok Build those are shared, unnamespaced
    directories another installed plugin's skills, references, or personas
    may already live in (the previous grok-ultracode installer wrote
    `~/.grok/skills/<skill-name>/` the same flat way). Replacing a whole
    owned directory would delete siblings this package never wrote. Merging
    at the immediate-child level -- `skills/fan-out`, `references/lanes.md`,
    `roles/scout.toml`, and so on -- touches only what this export declares.

    Known gap: if a role or reference is later removed from the source
    package, its stale copy is not deleted from a previous install, because
    nothing here tracks which target entries this script wrote versus some
    other tool. That is judged a smaller risk than a directory-level replace
    silently deleting a sibling plugin's content.

    Only ever called after `build_export(staged, ...)` has already
    succeeded in full, so nothing here runs unless the entire new export is
    ready -- a failure partway through generation leaves `target` completely
    untouched.
    """
    target.mkdir(parents=True, exist_ok=True)
    for name in OWNED_TOP_LEVEL:
        staged_sub = staged / name
        target_sub = target / name
        target_sub.mkdir(parents=True, exist_ok=True)
        for child in staged_sub.iterdir():
            target_child = target_sub / child.name
            if target_child.exists():
                if target_child.is_dir():
                    shutil.rmtree(target_child)
                else:
                    target_child.unlink()
            shutil.move(str(child), str(target_child))


def run_install(target: Path, package_root: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="install-grok-build-") as tmp:
        staged = Path(tmp) / "export"
        build_export(staged, package_root)
        swap_into_target(staged, target)

    file_count = len(iter_owned_files(target))
    print(f"Installed orchestra -> {target} ({file_count} files) from {package_root}.")
    return 0


def run_check(target: Path, package_root: Path, *, target_given: bool) -> int:
    """Implements the two `--check` meanings described in the module docstring.

    `target_given` distinguishes "the caller explicitly asked about this
    path" from "this is just the default `~/.grok`" -- it is *not* the same
    as `target.is_dir()`. Branching on existence instead of on whether the
    flag was passed would make a bare `--check` behave differently on a
    machine that happens to already have a `~/.grok` (this diff-check
    branch, `report_unexpected=False`) versus one that does not (the
    determinism branch below) -- exactly the environment-dependent CI
    behavior this split exists to remove. `target_given=False` always takes
    the determinism branch and never looks at `target` at all, regardless
    of what is or isn't already there.
    """
    with tempfile.TemporaryDirectory(prefix="install-grok-check-") as tmp:
        staged = Path(tmp) / "export"
        build_export(staged, package_root)  # proves generation succeeds

        if target_given:
            if not target.is_dir():
                print(f"error: {target} does not exist -- nothing installed there to check.")
                print(
                    "Run plugins/orchestra/scripts/install-grok.py "
                    f"--target {target} to install it first."
                )
                return 1
            problems = diff_dirs(staged, target, report_unexpected=False)
            if problems:
                print(f"error: {target} is out of date with {package_root}:")
                for problem in problems:
                    print(f"  {problem}")
                print(
                    "\nRun plugins/orchestra/scripts/install-grok.py "
                    f"--target {target} to regenerate it."
                )
                return 1
            print(f"OK: {target} matches {package_root}.")
            return 0

        # No --target given: target-independent, and deliberately blind to
        # whatever is or isn't at the default ~/.grok. Build a second,
        # independent copy and diff the two builds against each other --
        # any difference here, on either side, is a real non-determinism
        # bug in generation, never legitimate drift.
        with tempfile.TemporaryDirectory(prefix="install-grok-check-repeat-") as tmp2:
            staged2 = Path(tmp2) / "export"
            build_export(staged2, package_root)
            problems = diff_dirs(staged, staged2)

        if problems:
            print(f"error: generation from {package_root} is not deterministic:")
            for problem in problems:
                print(f"  {problem}")
            return 1
        print(f"OK: generation from {package_root} succeeds and is deterministic.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export the orchestra plugin to a Grok Build install: copies "
            "skills/, references/, schemas/, and roles/*.md, and generates "
            "a native roles/<role>.toml persona per role."
        ),
        epilog=(
            "Known gap: a role or reference removed from source is not "
            "auto-deleted from a previous --target install, and --check "
            "does not surface it either -- nothing here tracks which "
            "target entries this script wrote versus another installed "
            "plugin's, so a leftover can't be told apart from unrelated "
            "content in the same shared directory. Re-running the install "
            "adds and updates but never prunes; delete a stale roles/<id> "
            "or references/<name> by hand if a brief is removed from source."
        ),
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help=(
            "Grok config root to install into, or to check currency against "
            f"with --check (default: {DEFAULT_TARGET}). With --check, "
            "*passing* this flag switches the check from CI's target-"
            "independent determinism check to an install-currency diff -- "
            "see the module docstring."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "verify without writing anything. Alone: target-independent -- "
            "generation succeeds and is deterministic (what CI runs). With "
            "--target DIR: DIR's install is current with source."
        ),
    )
    parser.add_argument(
        "--package-root",
        type=Path,
        default=PACKAGE_ROOT,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    target_given = args.target is not None
    target = (args.target if target_given else DEFAULT_TARGET).expanduser().resolve()
    package_root = args.package_root.resolve()

    try:
        if args.check:
            return run_check(target, package_root, target_given=target_given)
        return run_install(target, package_root)
    except GrokExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
