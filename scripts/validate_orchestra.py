#!/usr/bin/env python3
"""Validate the installable orchestra package without host CLIs.

orchestra is a portable orchestration plugin: a router skill (``orchestra``)
plus 18 workflow skills, each making the executing agent a root orchestrator
that decomposes, delegates, and verifies rather than implementing inline.
This validator enforces the contract described in
``docs/agent-harness/`` and the approved orchestra plan without needing any
host CLI installed.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


PLUGIN_NAME = "orchestra"
PLUGIN_DIR = Path("plugins") / PLUGIN_NAME

ROUTER_SKILL = "orchestra"
WORKFLOW_SKILLS = {
    "plan", "design", "spike", "fan-out", "implement", "verify", "review",
    "debug", "triage", "research", "refactor", "migrate", "upgrade",
    "harden", "perf", "cover", "document", "ship",
}
ALL_SKILLS = WORKFLOW_SKILLS | {ROUTER_SKILL}

SEMVER = re.compile(r"^(?:0|[1-9]\d*)\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
FRONTMATTER = re.compile(r"^---\nname:\s*([^\n]+)\ndescription:\s*([^\n]+)\n---")
BARE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RESOURCE = re.compile(r"(?:\.\./)+(?:references|roles|schemas|examples)/[^\s)`]+")

# An ownedPaths entry must be a plain repository-relative path, and this is the
# grammar: an optional single leading "./", then one or more segments of
# [A-Za-z0-9._-] joined by a single "/", then an optional single trailing "/".
# No leading "/", no backslash, no whitespace anywhere, no empty segment, and
# no "." or ".." segment.
#
# The rule is a grammar rather than a normalizer on purpose. G7 compares
# territory by segment tuple, so every spelling that reaches the comparison
# unnormalized forks one path into two non-colliding owners: "src\lib" is not
# split at all on POSIX, "src/ lib" and "src /lib" keep the space inside a
# segment, and a zero-width character is not \s in Python, so it is neither
# stripped nor rejected and forks the path INVISIBLY. ".." is worse than a
# fork: "src/..", "docs/.." and "x/../.." all ARE the repository root under
# POSIX resolution, yet kept as literal segments they intersect nothing, which
# is exactly the hole the degenerate-path rule closed reopened under a new
# spelling. Chasing each normalization in turn only moves the hole; refusing
# every spelling but one closes it.
#
# A single leading "./" is the one alias kept, because it is the one that is
# already normalized on both sides: `_owned_path_key` drops the "." segment, so
# "./src/parser/" and "src/parser/" reduce to the same tuple and collide, and
# the schema pattern below admits it at most once and only at the front. It
# names no territory the bare spelling does not.
#
# lane.schema.json's ownedPaths items pattern states this same grammar
# character for character, so a host holding only the schema fails closed on
# exactly the same values. Both copies are anchored with `(?![\s\S])` rather
# than `$`, since Python's `re` lets `$` match before a trailing newline, and
# both use only constructs ECMA-262 shares with Python so the two layers cannot
# disagree by dialect.
OWNED_PATH = re.compile(
    r"^(?:\./)?(?!\.{1,2}(?:/|(?![\s\S])))[A-Za-z0-9._-]+"
    r"(?:/(?!\.{1,2}(?:/|(?![\s\S])))[A-Za-z0-9._-]+)*/?(?![\s\S])"
)
# Not a second gate -- OWNED_PATH is the only gate. This only sorts a rejected
# entry into the right diagnostic: an entry carrying no character that is other
# than whitespace, a separator or a dot ("." , "/", " ", "./", "//") declares no
# territory at all, which is a different mistake from declaring territory in an
# unusable spelling, and the author is told which one they made.
MEANINGFUL_PATH_CHARACTER = re.compile(r"[^\s/.]")

REQUIRED_SECTIONS = (
    "Required inputs",
    "Lane plan",
    "Delegation contract",
    "Quality gates",
    "Evidence and completion",
    "Hard stops",
    "Deterministic outputs",
    "Failure and recovery",
)
MANDATORY_LITERALS = (
    "ROOT ORCHESTRATOR",
    "Do not implement inline",
    "Maximum delegation depth is two",
    "Evidence, not assertions",
    "sequential fresh-context role-pass",
    "HARD STOP",
    ".orchestra/",
)
LANE_TABLE_HEADER = "| Lane | Role | Tier |"
SHAPES = {
    "fan-out barrier",
    "pipeline",
    "judge panel",
    "loop-until-dry",
    "adversarial verify",
    "staged escalation",
    "sweep",
}
SHAPE_LINE = re.compile(r"(?m)^Shape:\s*(.+?)\s*$")

ROUTER_LITERAL = "returning control is not the end of the run"
WORKFLOW_INDEX_HEADING = "## Workflow index"
SKILL_REFERENCE = re.compile(r"/orchestra:([a-z][a-z0-9-]*)")

SCHEMA_FILES = ("run.schema.json", "lane.schema.json", "finding.schema.json", "verdict.schema.json")
TIER_ENUM = ("deep", "standard", "fast")

LANE_FIXTURES = ("parallel-subagents", "sequential-roles", "no-delegation")

# The workflow segment of the reopenCount key pattern, spelled out as one
# alternation group. Matched structurally (not just probed) so the pattern
# and $defs/workflow can be compared as sets in both directions; the optional
# ``?:`` tolerates a non-capturing group, and the character class excludes
# ``?`` so a lookahead such as ``(?![\s\S])`` is never mistaken for it.
WORKFLOW_ALTERNATION = re.compile(r"\((?:\?:)?([a-z0-9|-]+)\)")
LANE_FIXTURE_DIR = "examples/lanes"
# Run fixtures are discovered rather than pinned by name: the lane fixtures are
# an exact triple because their whole point is that one lane plan dispatches
# three different ways, whereas a run record has no such matrix. Every JSON file
# here must be a valid run.json, and at least one must exist.
RUN_FIXTURE_DIR = "examples/runs"

# Two-layer defense against hardcoded model names: the tier enum (structural,
# see _validate_packaged_schemas) is the primary gate because an enum cannot
# be evaded. This denylist is the secondary, textual gate over prose. Vendor
# families require a following digit so the plugin's own host names
# ("Claude Code", "Codex CLI", "OpenCode", "Grok Build") never trip it, while
# a versioned model id ("grok-4", "claude-opus-4-5", "gpt-5.4",
# "gemini-3-pro") always does. Bare "Sonnet"/"Opus"/"Haiku" have no
# legitimate non-model usage in this plugin, so they are denylisted without
# requiring a digit.
MODEL_NAME_ALLOWLIST = frozenset({"claude-code", "claude-agent-sdk", "claude-plugin", "codex-plugin"})
MODEL_NAME = re.compile(
    r"\b(?:sonnet|opus|haiku)\b"
    r"|\b(?:claude|gpt|gemini|grok|codex|llama|mistral)(?:-[a-z]+)*-\d+(?:\.\d+)*(?:-[a-z0-9]+)*\b",
    re.IGNORECASE,
)


def find_model_name_violations(text: str) -> list[str]:
    """Return every substring matching the model-name denylist, minus the allowlist."""
    return [
        match.group(0)
        for match in MODEL_NAME.finditer(text)
        if match.group(0).lower() not in MODEL_NAME_ALLOWLIST
    ]


def _entries(node: Any) -> list[dict[str, Any]]:
    """Every dict element of ``node``, or an empty list if it is not an array."""
    return [item for item in node if isinstance(item, dict)] if isinstance(node, list) else []


def _is_scalar(value: Any) -> bool:
    """True for the JSON scalars an identity field may hold.

    Guards the identity tuple in ``validate_run_record``: a hand-written
    record carrying ``"workflow": ["implement"]`` must come back as an error,
    not as an unhashable-type traceback out of the ``seen`` set.
    """
    return value is None or isinstance(value, (str, int, float, bool))


def _text(value: Any) -> str | None:
    """``value`` if it is a string, else ``None``."""
    return value if isinstance(value, str) else None


def _index(value: Any) -> int | None:
    """``value`` if it is a real integer, else ``None``.

    ``bool`` is an ``int`` subclass, so ``True`` would otherwise format as a
    chain position of ``01`` and mint a ledger key for a lane that declared
    no position at all.
    """
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _owned_path_key(raw: str) -> tuple[str, ...]:
    """An ``OWNED_PATH``-checked entry split into comparable segments.

    Segment tuples are what make containment decidable: ``src/parser/`` and
    ``src/parser/callers.ts`` become ``("src", "parser")`` and
    ``("src", "parser", "callers.ts")``, while ``src/parser.ts`` becomes
    ``("src", "parser.ts")`` and is unrelated to either. Naive string
    prefixing gets that last case wrong in both directions.

    Callers must gate on ``OWNED_PATH`` first, and ``_owned_path_keys`` does.
    That is what lets this stay a split rather than grow into a path
    normalizer: the only two things the grammar leaves to drop are the empty
    segment an optional trailing "/" produces and the "." of an optional
    leading "./". Whitespace, backslashes and ".." cannot arrive here at all,
    so there is nothing here to strip them with -- by design, since a splitter
    that silently repaired them is what let two spellings of one path own it
    twice without colliding.
    """
    return tuple(part for part in raw.split("/") if part not in ("", "."))


def _owned_paths_intersect(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    """Whether two owned paths name overlapping writable territory.

    Containment counts, not just equality. G7 is "one writer per path": a lane
    owning ``src/parser/`` and a lane owning ``src/parser/callers.ts`` are two
    writers of the same file, and the directory owner cannot honour "no file
    outside my owned paths was modified" while the other lane edits inside it.
    Treating only exact equality as a conflict would let any pair of lanes
    evade G7 by declaring ownership at different depths of one tree.

    The empty-tuple guard is belt and braces rather than live enforcement:
    ``_owned_path_keys`` rejects a declaration that names no path instead of
    reducing it to no segments, so an empty tuple no longer reaches here. It
    stays because deleting it would silently hand the empty tuple
    universal-container semantics -- a prefix of every path, and so a
    conflict with every lane -- which is a reading of "owns nothing" that
    caller deliberately refuses to make.
    """
    shorter, longer = sorted((left, right), key=len)
    return bool(shorter) and longer[: len(shorter)] == shorter


def _owned_path_keys(
    lane_id: str,
    lane: dict[str, Any],
    errors: list[str],
) -> list[tuple[str, ...]]:
    """The territory one lane declares, as comparable segment tuples.

    An entry that is not a plain relative path is an error, not a value to
    normalize away. Dropping it silently is what made G7 unenforceable:
    ".", "/", " ", "./" and "//" all reduced to no segments at all, and a
    lane with no segments intersects nothing, so a lane claiming the whole
    repository as its territory conflicted with no lane whatsoever and the
    plan read as G7-clean.

    Reading such an entry as the universal container instead would only move
    the hole rather than close it: G5 requires a lane's diff to be a subset
    of its declared paths, and a lane owning the repository root satisfies
    that no matter what it wrote. Explicit rejection is the only reading that
    fails closed on both gates, so it is the one used here -- and
    lane.schema.json rejects the same values, so a host that has the schema
    and not this validator fails closed too.

    The gate is ``OWNED_PATH`` -- one grammar, applied whole -- because the
    same hole reopens under every other spelling of the same territory.
    ``src/..`` IS the repository root, and so are ``docs/..`` and ``x/../..``;
    ``src\\lib`` is one literal segment where ``src/lib`` is two;
    ``src/ lib``, ``src /lib`` and a zero-width character inside ``src/lib``
    each fork one path into two owners that never collide, the last of them
    invisibly. Every one of those was schema-clean and G7-silent under a rule
    that only asked for one meaningful character.
    """
    declared = lane.get("ownedPaths")
    keys: set[tuple[str, ...]] = set()
    for raw in declared if isinstance(declared, list) else []:
        # A non-string entry is lane.schema.json's to reject; repeating it
        # here would only report one type error twice.
        if not isinstance(raw, str):
            continue
        if not OWNED_PATH.match(raw):
            fault = (
                "names no path"
                if not MEANINGFUL_PATH_CHARACTER.search(raw)
                else "is not a plain relative path"
            )
            errors.append(
                f"lane {lane_id} declares an ownedPaths entry that {fault}: {raw!r}"
            )
            continue
        keys.add(_owned_path_key(raw))
    return sorted(keys)


def _check_one_writer_per_path(
    lanes: dict[str, dict[str, Any]],
    wave_members: dict[int, list[str]],
    errors: list[str],
) -> None:
    """G7: no path has two owners in one wave.

    ``references/gates.md`` lists G7 and ``references/lanes.md`` states that
    lanes whose owned paths intersect never run concurrently, but the schema
    cannot say it: ``uniqueItems`` is per-array, and no keyword compares one
    lane's ``ownedPaths`` against another's, let alone conditioned on the
    dispatch wave they land in. Two lanes owning the same file in one wave is
    a lost write on a parallel host and an unattributable diff on any host,
    which is exactly the failure "declare ownership before dispatch" exists to
    prevent. Waves are the unit because ownership is only contended between
    lanes that run at the same time; the shipped fixtures rely on that, since
    the hoisted mechanic writes inside its parent builder's tree one wave
    earlier and hands the result down.
    """
    owned = {
        lane_id: _owned_path_keys(lane_id, lane, errors) for lane_id, lane in lanes.items()
    }

    for index in sorted(wave_members):
        members = sorted(wave_members[index])
        for position, lane_id in enumerate(members):
            for other in members[position + 1:]:
                conflict = next(
                    (
                        (left, right)
                        for left in owned.get(lane_id, ())
                        for right in owned.get(other, ())
                        if _owned_paths_intersect(left, right)
                    ),
                    None,
                )
                if conflict is None:
                    continue
                left, right = ("/".join(part) for part in conflict)
                errors.append(
                    f"wave {index} schedules two writers of the same path: "
                    f"lane {lane_id} owns {left!r} and lane {other} owns {right!r}"
                )


def validate_lane_document(document: Any) -> list[str]:
    """Identity invariants JSON Schema 2020-12 cannot express.

    ``uniqueItems`` compares whole objects, so two lanePlan entries sharing
    an ``id`` both validate, and no keyword resolves a reference from one
    array into another. Orchestra stores each brief at
    ``lanes/<lane-id>.md``, so a duplicate id silently overwrites a brief
    and leaves ``dependsOn`` ambiguous while the document still validates.
    These checks are the orchestrator's, and this is their reference
    implementation.
    """
    if not isinstance(document, dict):
        return ["lane document must be a JSON object"]
    errors: list[str] = []
    dispatch = document.get("dispatch") if isinstance(document.get("dispatch"), dict) else {}

    lanes: dict[str, dict[str, Any]] = {}
    for lane in _entries(document.get("lanePlan")):
        lane_id = lane.get("id")
        if not isinstance(lane_id, str):
            continue
        if lane_id in lanes:
            errors.append(f"duplicate lane id in lanePlan: {lane_id}")
            continue
        lanes[lane_id] = lane

    seen_results: set[str] = set()
    for result in _entries(document.get("normalizedLaneResults")):
        lane_id = result.get("laneId")
        if not isinstance(lane_id, str):
            continue
        if lane_id in seen_results:
            errors.append(f"duplicate laneId in normalizedLaneResults: {lane_id}")
            continue
        seen_results.add(lane_id)
        if lane_id not in lanes:
            errors.append(f"normalizedLaneResults names an unknown lane: {lane_id}")
    for lane_id in sorted(set(lanes) - seen_results):
        errors.append(f"normalizedLaneResults is missing a result for lane: {lane_id}")

    wave_of: dict[str, int] = {}
    wave_members: dict[int, list[str]] = {}
    scheduled: set[str] = set()
    seen_waves: set[int] = set()
    for wave in _entries(dispatch.get("waves")):
        index = wave.get("wave")
        if isinstance(index, int):
            if index in seen_waves:
                errors.append(f"duplicate wave index in dispatch.waves: {index}")
            seen_waves.add(index)
        lane_ids = wave.get("laneIds")
        for lane_id in lane_ids if isinstance(lane_ids, list) else []:
            if not isinstance(lane_id, str):
                continue
            if lane_id in scheduled:
                errors.append(f"dispatch.waves schedule lane more than once: {lane_id}")
                continue
            scheduled.add(lane_id)
            if lane_id not in lanes:
                errors.append(f"dispatch.waves schedule an unknown lane: {lane_id}")
            elif isinstance(index, int):
                wave_of[lane_id] = index
                wave_members.setdefault(index, []).append(lane_id)
    for lane_id in sorted(set(lanes) - scheduled):
        errors.append(f"dispatch.waves omit lane: {lane_id}")

    _check_one_writer_per_path(lanes, wave_members, errors)

    for lane_id, lane in lanes.items():
        depends = lane.get("dependsOn")
        for dependency in depends if isinstance(depends, list) else []:
            if not isinstance(dependency, str):
                continue
            if dependency == lane_id:
                errors.append(f"lane depends on itself: {lane_id}")
            elif dependency not in lanes:
                errors.append(f"lane {lane_id} dependsOn an unknown lane: {dependency}")
            elif lane_id in wave_of and dependency in wave_of and wave_of[dependency] >= wave_of[lane_id]:
                errors.append(
                    f"lane {lane_id} must be scheduled in a later wave than its dependency {dependency}"
                )
        parent = lane.get("parentLaneId")
        if not isinstance(parent, str):
            continue
        if lane.get("depth") != 2:
            errors.append(
                f"lane {lane_id} declares parentLaneId at depth {lane.get('depth')}: "
                "only a depth-two lane may declare a parent"
            )
        if parent == lane_id:
            errors.append(f"lane is its own parentLaneId: {lane_id}")
        elif parent not in lanes:
            errors.append(f"lane {lane_id} parentLaneId names an unknown lane: {parent}")
        elif lanes[parent].get("role") != "builder":
            errors.append(
                f"lane {lane_id} parentLaneId must name a builder lane: "
                f"{parent} is a {lanes[parent].get('role')} lane"
            )

    hoisted_seen: set[str] = set()
    for entry in _entries(dispatch.get("hoisted")):
        lane_id = entry.get("laneId")
        source = entry.get("hoistedFrom")
        if not isinstance(lane_id, str):
            continue
        if lane_id in hoisted_seen:
            errors.append(f"dispatch.hoisted lists lane more than once: {lane_id}")
            continue
        hoisted_seen.add(lane_id)
        if lane_id not in lanes:
            errors.append(f"dispatch.hoisted names an unknown lane: {lane_id}")
        elif isinstance(source, str) and source not in lanes:
            errors.append(f"dispatch.hoisted hoistedFrom names an unknown lane: {source}")
        elif lanes[lane_id].get("parentLaneId") != source:
            errors.append(
                f"dispatch.hoisted entry {lane_id} must name its parentLaneId as hoistedFrom: "
                f"expected {lanes[lane_id].get('parentLaneId')!r}, got {source!r}"
            )
    return errors


def validate_run_record(record: Any) -> list[str]:
    """Cross-field invariants for run.json that the schema cannot state.

    This is the reference implementation an orchestrator runs over its own
    ``run.json``, and that run.json is hand-written by an agent mid-run rather
    than produced by a serializer. So every field access is guarded: a
    malformed record must come back as a list of errors, exactly like a merely
    invalid one, and never as a traceback that takes the run down with it.
    """
    if not isinstance(record, dict):
        return ["run record must be a JSON object"]
    errors: list[str] = []

    # chain[] declares the run's ledger links. Each link owns the directory
    # <nn>-<workflow>/, so a lane naming a link chain[] never declared claims
    # a directory that does not exist -- and, because reopenCount keys are
    # derived from lanes[], mints a well-formed reopen key inside it. Binding
    # lanes[] to chain[] is what closes that: the cross-check below can only
    # resolve keys against links the run actually planned.
    chain_links: set[tuple[str, int]] = set()
    seen_positions: set[int] = set()
    for link in _entries(record.get("chain")):
        workflow = _text(link.get("workflow"))
        position = _index(link.get("chainPosition"))
        if position is not None:
            if position in seen_positions:
                errors.append(f"duplicate chainPosition in chain[]: {position}")
            seen_positions.add(position)
        if workflow is not None and position is not None:
            chain_links.add((workflow, position))

    seen: set[tuple[Any, Any, Any]] = set()
    ledger_keys: set[str] = set()
    for lane in _entries(record.get("lanes")):
        workflow, position, lane_id = (
            lane.get("workflow"), lane.get("chainPosition"), lane.get("laneId")
        )
        if not all(_is_scalar(value) for value in (workflow, position, lane_id)):
            # A composite here is not merely invalid, it is unhashable: the
            # identity tuple below goes into a set.
            errors.append(
                "lanes[] entry has a non-scalar identity field: "
                f"laneId={lane_id!r}, workflow={workflow!r}, chainPosition={position!r}"
            )
            continue
        key = (workflow, position, lane_id)
        if key in seen:
            errors.append(
                f"duplicate lane entry in lanes[]: {key[2]} at workflow {key[0]} position {key[1]}"
            )
        seen.add(key)
        name, link_position, identifier = _text(workflow), _index(position), _text(lane_id)
        if name is None or link_position is None or identifier is None:
            continue
        ledger_keys.add(f"{link_position:02d}-{name}/{identifier}")
        # Only cross-check against a chain that parsed. An absent or wholly
        # malformed chain[] is run.schema.json's to reject (it is required),
        # and reporting every lane here as well would bury that one error.
        if chain_links and (name, link_position) not in chain_links:
            errors.append(
                f"lane {identifier} names a chain link chain[] does not declare: "
                f"{link_position:02d}-{name}"
            )

    # Unconditional: chain[] is required, so gating this on its presence only
    # ever skipped the check for a record already broken in a way that let a
    # reopen key point at nothing.
    reopen = record.get("reopenCount")
    if isinstance(reopen, dict):
        for name in sorted(str(key) for key in reopen):
            if name not in ledger_keys:
                errors.append(f"reopenCount key names no lane in lanes[]: {name}")
    return errors


def load_json(path: Path, errors: list[str]) -> dict[str, Any] | list[Any] | None:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON: {path}")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON: {path}: {exc.msg}")
        return None
    return parsed


def _json_type_name(value: Any) -> str:
    """The JSON type name of a parsed value, for a message a reader can act on."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, list):
        return "array"
    return "object"


def _load_json_object(path: Path, errors: list[str]) -> dict[str, Any] | None:
    """``load_json`` narrowed to an object, reporting anything else.

    ``load_json`` reports only what it could not parse, so a file holding
    ``[]``, ``null``, ``"nope"`` or ``17`` comes back as a clean parse of a
    value that is not a document. A caller that merely skips such a value
    fails OPEN, and ``None`` is the sharpest case of all: ``json.loads`` maps
    the literal ``null`` onto exactly the value ``load_json`` returns on
    failure, so ``is None`` cannot tell "already reported" apart from "parsed
    to nothing". The error count is what distinguishes them, since it is the
    one signal ``load_json`` actually emits.
    """
    reported = len(errors)
    parsed = load_json(path, errors)
    if len(errors) != reported:
        return None
    if not isinstance(parsed, dict):
        errors.append(
            f"{path}: must contain a JSON object, got {_json_type_name(parsed)}"
        )
        return None
    return parsed


def _fixture_validator(
    schema_name: str, schema: dict[str, Any] | None, errors: list[str]
) -> Draft202012Validator | None:
    """The instantiated schema, or ``None`` plus a report that nothing was checked.

    A schema that failed to load or to check has already been reported by
    ``_validate_packaged_schemas``, and repeating that failure here is what
    the de-duplication removed. What must not be repeated is the SILENCE.
    Skipping the fixture pass without a word let one unreadable schema file
    void the entire schema layer -- no instantiation, no conditional
    invariant, no fixture checked -- while the run still printed success and
    exited 0. That the schema is broken and that the fixtures consequently
    went unchecked are two different facts; the first is reported once,
    upstream, and this is the second.
    """
    if schema is None:
        errors.append(
            f"fixtures were not validated against {schema_name}: the schema did not "
            "load, so every invariant it declares went unchecked"
        )
        return None
    return Draft202012Validator(schema)


def _find_tier_enums(node: Any) -> list[list[Any]]:
    found: list[list[Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "tier" and isinstance(value, dict) and isinstance(value.get("enum"), list):
                found.append(value["enum"])
            found.extend(_find_tier_enums(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_find_tier_enums(item))
    return found


def _validate_reopen_key_pattern(path: Path, schema: dict[str, Any], errors: list[str]) -> None:
    """The reopenCount key's workflow segment must track the workflow enum.

    The pattern spells the workflow names out so a host holding only the
    schema still fails closed on a bogus key; this check is the anti-drift
    half, so adding a workflow to the enum and forgetting the pattern is a
    build failure rather than a silently unenforceable key.

    Drift runs both ways and so does this check. Probing the enum only proves
    the pattern is not too narrow; a pattern that still accepts a workflow the
    enum has since dropped keeps ``01-ship/<lane>`` legal for a workflow that
    no longer exists, and no amount of forward probing can see it. The two
    duplicated lists are therefore compared as sets, which is only possible
    because the pattern states its workflows literally -- so the alternation
    is extracted structurally, with the behavioural probes kept as a backstop
    for the case where extraction itself is what went wrong.
    """
    workflows = schema.get("$defs", {}).get("workflow", {}).get("enum")
    reopen = schema.get("properties", {}).get("reopenCount", {})
    pattern = reopen.get("propertyNames", {}).get("pattern") if isinstance(reopen, dict) else None
    if not isinstance(workflows, list) or not isinstance(pattern, str):
        errors.append(f"{path}: reopenCount must be keyed by <nn>-<workflow>/<lane-id>")
        return
    compiled = re.compile(pattern)
    for workflow in workflows:
        if not compiled.search(f"01-{workflow}/lane-id"):
            errors.append(f"{path}: reopenCount key pattern rejects workflow {workflow!r}")
    for bogus in ("deploy", "orchestra"):
        if compiled.search(f"01-{bogus}/lane-id"):
            errors.append(f"{path}: reopenCount key pattern accepts unknown workflow {bogus!r}")

    groups = [group for group in WORKFLOW_ALTERNATION.findall(pattern) if "|" in group]
    if len(groups) != 1:
        # Fail closed. A pattern with no single literal alternation cannot be
        # compared against the enum at all, which is the whole point of it
        # spelling the names out rather than using a character class.
        errors.append(
            f"{path}: reopenCount key pattern must spell its workflow segment out as exactly "
            f"one literal alternation group: found {len(groups)}"
        )
        return
    accepted = set(groups[0].split("|"))
    declared = {workflow for workflow in workflows if isinstance(workflow, str)}
    for extra in sorted(accepted - declared):
        errors.append(f"{path}: reopenCount key pattern accepts unknown workflow {extra!r}")
    for missing in sorted(declared - accepted):
        errors.append(f"{path}: reopenCount key pattern omits declared workflow {missing!r}")


def _validate_resource_links(path: Path, text: str, package_root: Path, errors: list[str]) -> None:
    for raw in RESOURCE.findall(text):
        resolved = (path.parent / raw.rstrip(".,")).resolve()
        if not resolved.exists():
            errors.append(f"{path}: missing local resource {raw}")
            continue
        try:
            resolved.relative_to(package_root)
        except ValueError:
            errors.append(f"{path}: resource link escapes the package: {raw}")


def _validate_workflow_sections(path: Path, text: str, errors: list[str]) -> None:
    positions = [text.find(f"## {section}") for section in REQUIRED_SECTIONS]
    for section, index in zip(REQUIRED_SECTIONS, positions):
        if index == -1:
            errors.append(f"{path}: missing required section {section!r}")
    present = [index for index in positions if index != -1]
    if present != sorted(present):
        errors.append(
            f"{path}: required sections must appear in order: {', '.join(REQUIRED_SECTIONS)}"
        )


def _validate_workflow_literals(path: Path, text: str, errors: list[str]) -> None:
    for phrase in MANDATORY_LITERALS:
        if phrase not in text:
            errors.append(f"{path}: missing mandatory phrase {phrase!r}")
    if LANE_TABLE_HEADER not in text:
        errors.append(f"{path}: missing lane table header {LANE_TABLE_HEADER!r}")
    match = SHAPE_LINE.search(text)
    if not match:
        errors.append(f"{path}: missing a 'Shape: <shape>' line")
    elif match.group(1) not in SHAPES:
        errors.append(
            f"{path}: Shape line must be exactly one of {sorted(SHAPES)}: got {match.group(1)!r}"
        )


def _validate_router(path: Path, text: str, errors: list[str]) -> None:
    if ROUTER_LITERAL not in text:
        errors.append(f"{path}: missing mandatory phrase {ROUTER_LITERAL!r}")

    all_refs = SKILL_REFERENCE.findall(text)
    unknown_refs = sorted({ref for ref in all_refs if ref not in WORKFLOW_SKILLS})
    if unknown_refs:
        errors.append(f"{path}: references unknown skill(s): {', '.join(unknown_refs)}")

    start = text.find(WORKFLOW_INDEX_HEADING)
    if start == -1:
        errors.append(f"{path}: missing {WORKFLOW_INDEX_HEADING!r} section")
        return
    next_heading = text.find("\n## ", start + len(WORKFLOW_INDEX_HEADING))
    section = text[start:next_heading] if next_heading != -1 else text[start:]
    counts = Counter(SKILL_REFERENCE.findall(section))
    missing = sorted(WORKFLOW_SKILLS - counts.keys())
    if missing:
        errors.append(f"{path}: workflow index missing: {', '.join(missing)}")
    duplicated = sorted(
        name for name, count in counts.items() if name in WORKFLOW_SKILLS and count != 1
    )
    if duplicated:
        errors.append(
            f"{path}: workflow index must name each workflow exactly once: {', '.join(duplicated)}"
        )


def _validate_skills(root: Path, errors: list[str]) -> None:
    skills_root = root / PLUGIN_DIR / "skills"
    actual = {path.parent.name for path in skills_root.glob("*/SKILL.md")}
    for name in sorted(ALL_SKILLS - actual):
        errors.append(f"missing required skill: {name}")
    for name in sorted(actual - ALL_SKILLS):
        errors.append(f"unexpected package skill: {name}")

    package_root = (root / PLUGIN_DIR).resolve()
    seen_names: set[str] = set()
    router_seen = False
    for path in sorted(skills_root.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER.match(text)
        if not match:
            errors.append(f"{path}: invalid SKILL.md frontmatter")
            continue
        name = match.group(1).strip().strip('"')
        if name in seen_names:
            errors.append(f"duplicate skill frontmatter name: {name}")
        seen_names.add(name)
        if not match.group(2).strip():
            errors.append(f"{path}: description must be non-empty")
        if not BARE_NAME.fullmatch(name):
            errors.append(f"{path}: skill name {name!r} must be a bare name")
        if name != ROUTER_SKILL and name.startswith("orchestra-"):
            errors.append(f"{path}: skill name {name!r} must not use the orchestra- prefix")
        if name != path.parent.name:
            errors.append(
                f"{path}: skill name {name!r} must match directory {path.parent.name!r}"
            )

        _validate_resource_links(path, text, package_root, errors)

        if name == ROUTER_SKILL:
            router_seen = True
            _validate_router(path, text, errors)
        elif name in WORKFLOW_SKILLS:
            _validate_workflow_sections(path, text, errors)
            _validate_workflow_literals(path, text, errors)

    if not router_seen:
        errors.append(f"missing router skill: {ROUTER_SKILL}")


def _validate_packaged_schemas(root: Path, errors: list[str]) -> dict[str, dict[str, Any]]:
    """Check every packaged schema once, and hand the survivors on.

    Returns the schemas that both parsed and passed ``check_schema``, keyed
    by file name. The fixture passes instantiate those objects rather than
    re-reading and re-checking the files: one rule deserves one enforcement,
    and loading lane.schema.json and run.schema.json twice per run meant
    every schema-level failure was reported twice, doubling the noise in the
    CI log that a reader is trying to diagnose from. A schema missing from
    the returned mapping has been reported here exactly once, and a caller
    that finds nothing to instantiate must report that IT could not run --
    which is a different fact from the load failure, not a repeat of it.

    Every rejection here appends before it skips. A packaged schema holding
    valid JSON that is not an object ("[]", "null", a bare string, a number)
    used to be dropped in silence: no required-key check, no ``check_schema``,
    no entry in the returned mapping, and so no fixture ever instantiated
    against it -- one such file voided the whole schema layer and the run
    still exited 0.
    """
    package = root / PLUGIN_DIR
    checked: dict[str, dict[str, Any]] = {}
    tier_enums: list[list[Any]] = []
    for schema_name in SCHEMA_FILES:
        schema_path = package / "schemas" / schema_name
        schema = _load_json_object(schema_path, errors)
        if schema is None:
            continue
        required = schema.get("required")
        if not isinstance(required, list) or not required:
            errors.append(f"{schema_path}: schema must declare a non-empty required field list")
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            errors.append(f"{schema_path}: invalid Draft202012 schema: {exc.message}")
            continue
        checked[schema_name] = schema
        if schema_name == "run.schema.json":
            _validate_reopen_key_pattern(schema_path, schema, errors)
        tier_enums.extend(_find_tier_enums(schema))
    if not tier_enums:
        errors.append("no packaged schema declares a tier enum")
    for enum in tier_enums:
        if sorted(enum) != sorted(TIER_ENUM):
            errors.append(f"tier enum must be exactly {list(TIER_ENUM)}: got {enum}")
    return checked


def _validate_lane_fixtures(
    root: Path, schema: dict[str, Any] | None, errors: list[str]
) -> None:
    package = root / PLUGIN_DIR
    fixtures: dict[str, Any] = {}
    for name in LANE_FIXTURES:
        path = package / LANE_FIXTURE_DIR / f"{name}.json"
        # _load_json_object, not load_json: a fixture holding "[]" or "null"
        # parses cleanly, is not a document, and used to drop out of `fixtures`
        # without a word -- which took the count below under three and returned
        # from this whole pass in silence, skipping the byte-identical check,
        # the schema instantiation and the identity checks all at once.
        payload = _load_json_object(path, errors)
        if payload is not None:
            fixtures[name] = payload
    if len(fixtures) != len(LANE_FIXTURES):
        # Every absentee has been reported by now, individually and by name.
        return

    for key in ("lanePlan", "normalizedLaneResults"):
        values = [fixtures[name].get(key) for name in LANE_FIXTURES]
        if any(value is None for value in values):
            errors.append(f"lane fixtures missing required key: {key}")
            continue
        serialized = {json.dumps(value, sort_keys=True) for value in values}
        if len(serialized) != 1:
            errors.append(
                f"lane fixtures {key} must be byte-identical across {', '.join(LANE_FIXTURES)}"
            )

    dispatches = [fixtures[name].get("dispatch") for name in LANE_FIXTURES]
    if any(dispatch is None for dispatch in dispatches):
        errors.append("lane fixtures missing required key: dispatch")
    else:
        serialized_dispatch = {json.dumps(dispatch, sort_keys=True) for dispatch in dispatches}
        if len(serialized_dispatch) != len(LANE_FIXTURES):
            errors.append(
                "lane fixtures dispatch must differ across all three fixtures "
                "(identical dispatch proves nothing)"
            )

    # ``check_schema`` (in _validate_packaged_schemas, which already ran it
    # and handed the result down) only proves the schema is well-formed; it
    # never instantiates it against a document. Without this, every
    # conditional invariant in lane.schema.json is dead weight as far as CI
    # is concerned -- a fixture could drift, or the schema could be tightened
    # into something no real document satisfies, and the build would stay
    # green either way. A schema that failed to load or to check arrives as
    # None; the failure itself was reported upstream, and _fixture_validator
    # reports that this pass could not run, which is the half that used to be
    # missing.
    validator = _fixture_validator("lane.schema.json", schema, errors)
    if validator is not None:
        for name in LANE_FIXTURES:
            fixture_path = package / LANE_FIXTURE_DIR / f"{name}.json"
            for error in sorted(validator.iter_errors(fixtures[name]), key=lambda item: list(item.path)):
                location = "/".join(str(part) for part in error.path) or "root"
                errors.append(f"{fixture_path}: schema validation at {location}: {error.message}")

    # Identity is the half the schema cannot reach: uniqueItems compares
    # whole objects, so two lanePlan entries sharing an id both validate,
    # and no keyword resolves a reference from one array into another.
    for name in LANE_FIXTURES:
        fixture_path = package / LANE_FIXTURE_DIR / f"{name}.json"
        for message in validate_lane_document(fixtures[name]):
            errors.append(f"{fixture_path}: {message}")


def _validate_run_fixtures(
    root: Path, schema: dict[str, Any] | None, errors: list[str]
) -> None:
    """Run the run-record half of the contract over the shipped fixtures.

    ``validate_run_record`` had a full unit-test suite and no caller, so in CI
    it was documentation: the lane half was proven end to end by
    ``_validate_lane_fixtures`` while the run half could have been deleted
    without turning anything red. This is the missing symmetric wiring --
    every fixture is checked against run.schema.json (``check_schema`` only
    proves the schema is well-formed, never that a real document satisfies
    it) and then against the cross-field invariants the schema cannot state.

    Fixtures are discovered rather than pinned by name: the lane fixtures are
    an exact triple because their point is that one lane plan dispatches three
    different ways, whereas run records only have to be individually valid.
    The contract here is the directory, not the file list.
    """
    package = root / PLUGIN_DIR
    fixture_dir = package / RUN_FIXTURE_DIR

    # Already loaded and check_schema'd by _validate_packaged_schemas; None
    # means it failed there and was reported there, and that this pass could
    # not run -- reported here, before the fixture-discovery early return, so
    # a broken schema is never masked by an empty fixture directory.
    validator = _fixture_validator("run.schema.json", schema, errors)

    paths = sorted(fixture_dir.glob("*.json")) if fixture_dir.is_dir() else []
    if not paths:
        errors.append(
            f"no run-record fixture under {PLUGIN_DIR.as_posix()}/{RUN_FIXTURE_DIR}: "
            "the run half of the contract has nothing to run against"
        )
        return

    for path in paths:
        # Same reason as the lane pass: `null` is the value load_json returns
        # on failure, so `is None` could not tell an already-reported failure
        # apart from a fixture that parsed to nothing, and the latter was
        # skipped without a word.
        payload = _load_json_object(path, errors)
        if payload is None:
            continue
        if validator is not None:
            ordered = sorted(
                validator.iter_errors(payload),
                key=lambda item: [str(part) for part in item.path],
            )
            for error in ordered:
                location = "/".join(str(part) for part in error.path) or "root"
                errors.append(f"{path}: schema validation at {location}: {error.message}")
        for message in validate_run_record(payload):
            errors.append(f"{path}: {message}")


def _validate_packaged_paths(root: Path, errors: list[str]) -> None:
    package = root / PLUGIN_DIR
    if not package.is_dir():
        return
    for path in package.rglob("*"):
        if ".orchestra" in path.relative_to(package).parts:
            errors.append(f"packaged path must not contain .orchestra: {path.relative_to(package)}")


def _validate_model_names(root: Path, errors: list[str]) -> None:
    package = root / PLUGIN_DIR
    if not package.is_dir():
        return
    for path in sorted(package.rglob("*")):
        # .py covers install-grok.py, the package's only executable file and
        # exactly the boundary where an abstract tier gets mapped onto a
        # concrete host setting -- the likeliest place a hardcoded model id
        # would be written. Every other suffix shipped under plugins/orchestra
        # is .md or .json (see the package's own layout); .pyc is a compiled
        # artifact, never source, and is deliberately excluded.
        if not path.is_file() or path.suffix not in (".md", ".json", ".py"):
            continue
        text = path.read_text(encoding="utf-8")
        for violation in find_model_name_violations(text):
            errors.append(f"{path}: hardcoded model reference: {violation!r}")


def _validate_native_manifest(path: Path, errors: list[str], *, codex: bool) -> dict[str, Any] | None:
    # _load_json_object, not load_json: a manifest holding "[]" or "null"
    # parsed cleanly and returned None, and `_validate_manifests` then read
    # None as "nothing to compare" -- so a wholly bogus plugin.json produced no
    # name check, no version check, no description check, and no mismatch
    # against its sibling manifest, because there was no version to mismatch.
    data = _load_json_object(path, errors)
    if data is None:
        return None
    if data.get("name") != PLUGIN_NAME:
        errors.append(f"{path}: name must be {PLUGIN_NAME!r}")
    version = data.get("version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        errors.append(f"{path}: version must be semantic")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        errors.append(f"{path}: description must be non-empty")
    if codex and data.get("skills") != "./skills/":
        errors.append(f"{path}: skills must point to ./skills/")
    return data


def validate_codex_manifest(path: Path) -> list[str]:
    """Validate the native Codex manifest independently from package checks."""
    errors: list[str] = []
    _validate_native_manifest(path, errors, codex=True)
    return errors


def _validate_manifests(root: Path, errors: list[str]) -> str | None:
    claude = _validate_native_manifest(root / PLUGIN_DIR / ".claude-plugin/plugin.json", errors, codex=False)
    codex = _validate_native_manifest(root / PLUGIN_DIR / ".codex-plugin/plugin.json", errors, codex=True)
    versions = [data["version"] for data in (claude, codex) if isinstance(data, dict) and isinstance(data.get("version"), str)]
    if len(set(versions)) > 1:
        errors.append("Claude and Codex plugin versions must match")
    return versions[0] if versions else None


def _validate_registration(root: Path, version: str | None, errors: list[str]) -> None:
    marketplace = load_json(root / ".claude-plugin/marketplace.json", errors)
    entries = marketplace.get("plugins", []) if isinstance(marketplace, dict) else []
    if not any(
        isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME and entry.get("source") == f"./{PLUGIN_DIR.as_posix()}"
        for entry in entries
    ):
        errors.append(f"marketplace must register {PLUGIN_NAME}")
    release = load_json(root / "release-please-config.json", errors)
    packages = release.get("packages", {}) if isinstance(release, dict) else {}
    config = packages.get(PLUGIN_DIR.as_posix()) if isinstance(packages, dict) else None
    if not isinstance(config, dict):
        errors.append(f"release-please must register {PLUGIN_NAME}")
    else:
        if config.get("release-type") != "simple":
            errors.append(f"release-please {PLUGIN_NAME} release-type must be simple")
        paths = {item.get("path") for item in config.get("extra-files", []) if isinstance(item, dict)}
        for path in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            if path not in paths:
                errors.append(f"release-please must synchronize {path}")
    released = load_json(root / ".release-please-manifest.json", errors)
    released_version = released.get(PLUGIN_DIR.as_posix()) if isinstance(released, dict) else None
    if version and released_version != version:
        errors.append("release-please manifest version must match plugin manifests")
    version_path = root / PLUGIN_DIR / "version.txt"
    if version and (not version_path.is_file() or version_path.read_text(encoding="utf-8").strip() != version):
        errors.append("version.txt must match plugin manifests")


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    version = _validate_manifests(root, errors)
    _validate_skills(root, errors)
    schemas = _validate_packaged_schemas(root, errors)
    _validate_lane_fixtures(root, schemas.get("lane.schema.json"), errors)
    _validate_run_fixtures(root, schemas.get("run.schema.json"), errors)
    _validate_packaged_paths(root, errors)
    _validate_model_names(root, errors)
    _validate_registration(root, version, errors)
    return errors


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--codex-manifest-only"]:
        if len(args) != 2:
            print("usage: validate_orchestra.py --codex-manifest-only <manifest>", file=sys.stderr)
            return 2
        errors = validate_codex_manifest(Path(args[1]))
        if errors:
            print("Codex manifest validation failed:\n" + "\n".join(f"- {error}" for error in errors), file=sys.stderr)
            return 1
        print(f"Codex manifest validation passed: {Path(args[1]).resolve()}")
        return 0
    root = Path(args[0]) if len(args) == 1 else Path(__file__).resolve().parents[1]
    if len(args) > 1:
        print("usage: validate_orchestra.py [repository-root]", file=sys.stderr)
        return 2
    errors = validate_repository(root)
    if errors:
        print("Orchestra contract validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Orchestra contract validation passed: {root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
