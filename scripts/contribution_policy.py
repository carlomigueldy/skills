#!/usr/bin/env python3
"""Enforce repository contribution metadata and attribution policy."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / ".github" / "contribution-policy.json"
ZERO_OID = re.compile(r"^0+$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
IDENT_RE = re.compile(r"^(.*?) <([^<>]+)>(?: .*)?$")
TRAILER_LINE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9-]*)\s*:\s*(.*?)\s*$")
MODEL = (
    r"(?:AI|LLM|Claude|Codex|ChatGPT|OpenAI|Anthropic(?:\s+Claude)?|"
    r"GPT(?:-?\d[\w.-]*)?|Gemini|Copilot)"
)
ATTRIBUTION_PATTERNS = (
    re.compile(
        rf"(?im)^\s*(?:[-*>]\s*)?(?:(?:credit|attribution)\s*:\s*)?"
        rf"(?:(?:this|the\s+(?:change|commit|pull request|patch|work|implementation|document|code))\s+"
        rf"(?:was|were|is)\s+)?"
        rf"(?:generated|written|authored|created|implemented|produced|assisted|built|developed|reviewed|made)\s+"
        rf"(?:by|with|using)\s+(?:an?\s+)?{MODEL}\b"
    ),
    re.compile(
        rf"(?im)^\s*(?:[-*>]\s*)?"
        rf"(?:code|content|text|documentation|document|implementation|patch|change|commit)\s+"
        rf"(?:generated|written|authored|created|implemented|produced|assisted|built|developed|reviewed|made)\s+"
        rf"(?:by|with|using)\s+(?:an?\s+)?{MODEL}\s*[.!]?\s*$"
    ),
    re.compile(
        rf"(?im)^\s*(?:[-*>]\s*)?{MODEL}[ -]"
        rf"(?:generated|authored|assisted|written)(?:\s+(?:code|content|text))?\s*[.!]?\s*$"
    ),
    re.compile(rf"(?im)^(?:generated|assisted|authored|written)-by:\s*.*{MODEL}\b"),
    re.compile(
        rf"(?im)^\s*(?:[-*>]\s*)?"
        rf"(?:co-authored-by|co-developed-by|reviewed-by|assisted-by|generated-by|"
        rf"written-by|authored-by|implemented-by|pair-programmed-by|pair-programmed-with)"
        rf"\s*:\s*.*{MODEL}\b"
    ),
    re.compile(
        rf"(?i)\b(?:I|we)\s+(?:used|relied\s+on)\s+{MODEL}\s+to\s+"
        rf"(?:generate|write|author|create|implement|produce|assist|build|develop|review)\b"
    ),
    re.compile(rf"(?im)^\s*(?:[-*>]\s*)?pair-programmed\s+with\s+{MODEL}\b"),
    re.compile(
        rf"(?im)^\s*(?:[-*>]\s*)?thanks\s+to\s+{MODEL}\s+for\s+"
        rf"(?:writing|authoring|creating|implementing|building|reviewing)\b"
    ),
    re.compile(
        rf"(?im)^\s*(?:[-*>]\s*)?{MODEL}\s+"
        rf"(?:wrote|authored|created|implemented|built|reviewed|helped\s+(?:write|author|create|implement|build|review))\b"
    ),
    re.compile(
        rf"(?im)^\s*(?:[-*>]\s*)?(?:implementation|code|document|content|work)\s+"
        rf"credit\s+goes\s+to\s+{MODEL}\b"
    ),
    re.compile(
        r"(?im)^\s*(?:[-*>]\s*)?(?:AI|LLM)\s+assistance\s+was\s+used\s+to\s+"
        r"(?:write|author|create|implement|build|review)\b"
    ),
    re.compile(
        rf"(?im)^\s*(?:[-*>]\s*)?(?:this|the)\s+"
        rf"(?:patch|change|commit|implementation|document|code)\s+(?:was|is)\s+"
        rf"(?:written|authored|created|implemented|built|reviewed)\s+with\s+help\s+from\s+{MODEL}\b"
    ),
)


class PolicyError(RuntimeError):
    pass


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def run_git(*args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], capture_output=True, text=text, check=False
    )


def require_git(*args: str, text: bool = True):
    result = run_git(*args, text=text)
    if result.returncode:
        stderr = result.stderr.strip() if text else result.stderr.decode(errors="replace").strip()
        raise PolicyError(f"git {' '.join(args)} failed: {stderr or 'unknown error'}")
    return result.stdout


def approved_humans(config: dict[str, Any]) -> set[tuple[str, str]]:
    return {(item["name"], item["email"]) for item in config["approved_humans"]}


def conventional_pattern(config: dict[str, Any]) -> re.Pattern[str]:
    types = "|".join(re.escape(item) for item in config["conventional_types"])
    return re.compile(
        rf"^(?:{types})(?:\([a-z0-9][a-z0-9._/-]*\))?!?: \S(?:.*\S)?$"
    )


def validate_header(header: str, config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not conventional_pattern(config).fullmatch(header):
        errors.append(
            "title must be a Conventional Commit with an accepted lowercase type, "
            "optional lowercase scope, and a non-empty description"
        )
    if header.endswith("."):
        errors.append("title description must not end with a full stop")
    return errors


def conventional_subject(header: str) -> str:
    return header.split(": ", 1)[1] if ": " in header else header


def normalize_attribution_text(text: str) -> str:
    normalized = html.unescape(text)
    normalized = unicodedata.normalize("NFKC", normalized)
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Cf"
    )
    normalized = re.sub(r"<!--.*?-->", " ", normalized, flags=re.DOTALL)
    normalized = re.sub(r"<[^>]+>", "", normalized)
    normalized = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", normalized)
    return re.sub(r"[*_`~]", "", normalized)


def attribution_errors(text: str, location: str) -> list[str]:
    normalized = normalize_attribution_text(text)
    return [
        f"{location} contains prohibited generation or assistance attribution"
        for pattern in ATTRIBUTION_PATTERNS
        if pattern.search(normalized)
    ][:1]


def terminal_trailers(message: str) -> list[tuple[str, str]]:
    lines = message.splitlines()
    index = len(lines) - 1
    while index >= 0 and not lines[index].strip():
        index -= 1
    trailers: list[tuple[str, str]] = []
    continuation: list[str] = []
    while index >= 1:
        line = lines[index]
        if line[:1].isspace() and line.strip():
            continuation.insert(0, line.strip())
            index -= 1
            continue
        match = TRAILER_LINE_RE.fullmatch(line)
        if not match:
            break
        value = " ".join([match.group(2), *continuation]).strip()
        trailers.append((match.group(1), value))
        continuation = []
        index -= 1
    return list(reversed(trailers))


def validate_message_text(message: str, config: dict[str, Any]) -> list[str]:
    header = message.splitlines()[0] if message.splitlines() else ""
    errors = validate_header(header, config)
    errors.extend(attribution_errors(conventional_subject(header), "title"))
    errors.extend(attribution_errors(message, "message"))
    humans = approved_humans(config)
    model_identity = re.compile(rf"(?i)\b{MODEL}\b")
    for token, value in terminal_trailers(message):
        normalized_token = token.casefold()
        if normalized_token == "signed-off-by":
            errors.append("sign-off trailers are prohibited")
            continue
        if normalized_token == "co-authored-by":
            identity_match = re.fullmatch(r"(.*?)\s*<([^<>]+)>", value)
            identity = (
                (identity_match.group(1).strip(), identity_match.group(2).strip())
                if identity_match
                else None
            )
            if identity not in humans:
                errors.append(f"unauthorized co-author trailer: {value}")
            continue
        if model_identity.search(normalize_attribution_text(value)):
            errors.append(f"prohibited model or vendor attribution trailer: {token}")
    return errors


def parse_ident(value: str) -> tuple[str, str]:
    match = IDENT_RE.match(value.strip())
    if not match:
        raise PolicyError(f"could not parse Git identity: {value!r}")
    return match.group(1), match.group(2)


def identity_errors(
    author: tuple[str, str],
    committer: tuple[str, str],
    header: str,
    config: dict[str, Any],
) -> list[str]:
    humans = approved_humans(config)
    release = config["release_bot"]
    bot = (release["name"], release["email"])
    platform = (
        config["platform_committer"]["name"],
        config["platform_committer"]["email"],
    )
    release_context = author == bot and re.fullmatch(release["header_pattern"], header) is not None
    author_ok = author in humans or release_context
    if not author_ok:
        return [f"unauthorized author: {author[0]} <{author[1]}>"]

    # GitHub's web merge transport rewrites the committer only. It is never a
    # valid author or co-author and remains paired with a valid author/context.
    committer_ok = committer in humans or committer == platform or (
        release_context and committer == bot
    )
    if not committer_ok:
        return [f"unauthorized committer: {committer[0]} <{committer[1]}>"]
    return []


def added_text(base: str | None = None, head: str | None = None, *, staged: bool = False) -> str:
    args = [
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--unified=0",
        "--output-indicator-new=>",
    ]
    if staged:
        args.append("--cached")
    elif base is not None and head is not None:
        args.extend([base, head])
    args.extend(["--diff-filter=ACMR", "--"])
    output = require_git(*args, text=False)
    decoded = output.decode("utf-8", errors="replace")
    additions = []
    for line in decoded.splitlines():
        if line.startswith(">"):
            additions.append(line[1:])
    return "\n".join(additions)


def command_staged(config: dict[str, Any]) -> list[str]:
    author = parse_ident(require_git("var", "GIT_AUTHOR_IDENT"))
    committer = parse_ident(require_git("var", "GIT_COMMITTER_IDENT"))
    errors = identity_errors(author, committer, "", config)
    errors.extend(attribution_errors(added_text(staged=True), "staged additions"))
    return errors


def commit_details(oid: str) -> tuple[tuple[str, str], tuple[str, str], str]:
    raw = require_git(
        "show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce%x00%B", oid
    )
    parts = raw.split("\0", 4)
    if len(parts) != 5:
        raise PolicyError(f"could not read commit metadata for {oid}")
    return (parts[0], parts[1]), (parts[2], parts[3]), parts[4].rstrip("\n")


def object_exists(oid: str) -> bool:
    return run_git("cat-file", "-e", f"{oid}^{{commit}}").returncode == 0


def command_range(base: str, head: str, config: dict[str, Any]) -> list[str]:
    git_dir = Path(require_git("rev-parse", "--git-dir").strip())
    if not git_dir.is_absolute():
        git_dir = Path.cwd() / git_dir
    if (git_dir / "shallow").exists():
        raise PolicyError("cannot validate a shallow repository; fetch complete history first")
    if ZERO_OID.fullmatch(head) or not object_exists(head):
        raise PolicyError(f"head commit is unavailable: {head}")

    is_root_range = ZERO_OID.fullmatch(base) is not None
    if is_root_range:
        revision = head
    else:
        if not object_exists(base):
            raise PolicyError(f"base commit is unavailable: {base}")
        if run_git("merge-base", "--is-ancestor", base, head).returncode:
            raise PolicyError(f"base {base} is not an ancestor of head {head}")
        revision = f"{base}..{head}"

    commits = [line for line in require_git("rev-list", "--reverse", revision).splitlines() if line]
    errors: list[str] = []
    for oid in commits:
        author, committer, message = commit_details(oid)
        header = message.splitlines()[0] if message.splitlines() else ""
        for error in validate_message_text(message, config):
            errors.append(f"commit {oid[:12]}: {error}")
        for error in identity_errors(author, committer, header, config):
            errors.append(f"commit {oid[:12]}: {error}")
        parent_line = require_git("rev-list", "--parents", "-n", "1", oid).split()
        parents = parent_line[1:] or [EMPTY_TREE]
        for parent in parents:
            for error in attribution_errors(
                added_text(parent, oid), f"commit {oid[:12]} additions"
            ):
                errors.append(error)
    return errors


def command_event(path: Path, config: dict[str, Any]) -> list[str]:
    with path.open(encoding="utf-8") as handle:
        event = json.load(handle)
    subjects = [
        (key, event.get(key))
        for key in ("pull_request", "issue")
        if event.get(key) is not None
    ]
    if len(subjects) != 1 or not isinstance(subjects[0][1], dict):
        raise PolicyError("event must contain exactly one pull_request or issue")
    subject_kind, subject = subjects[0]
    title = subject.get("title") or ""
    body = subject.get("body") or ""
    errors = validate_header(title, config)
    errors.extend(attribution_errors(conventional_subject(title), "event title"))
    errors.extend(attribution_errors(body, "event body"))
    if subject_kind == "pull_request":
        user = subject.get("user")
        login = user.get("login") if isinstance(user, dict) else None
        if not isinstance(login, str) or not login:
            raise PolicyError("pull request does not contain an authenticated GitHub login")
        if login not in config["approved_github_logins"]:
            errors.append(f"unauthorized GitHub contributor: {login}")
        release = config["release_bot"]
        if login == release["github_login"] and not re.fullmatch(
            release["header_pattern"], title
        ):
            errors.append("release automation may open only release pull requests")
    return errors


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    subparsers.add_parser("staged")
    message = subparsers.add_parser("message")
    message.add_argument("file", type=Path)
    range_parser = subparsers.add_parser("range")
    range_parser.add_argument("base")
    range_parser.add_argument("head")
    event = subparsers.add_parser("event")
    event.add_argument("file", type=Path)
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config = load_config()
        if args.command == "staged":
            errors = command_staged(config)
        elif args.command == "message":
            errors = validate_message_text(args.file.read_text(encoding="utf-8"), config)
        elif args.command == "range":
            errors = command_range(args.base, args.head, config)
        else:
            errors = command_event(args.file, config)
    except (OSError, ValueError, json.JSONDecodeError, PolicyError) as error:
        print(f"Contribution policy error: {error}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"Contribution policy violation: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
