"""Contract tests for the orchestra plugin's Grok Build exporter.

`plugins/orchestra/scripts/install-grok.py` derives native Grok Build
persona TOML from the Markdown role briefs at install time, replacing an
earlier approach that shipped hand-authored TOML and told the *agent* to
`read_file` + hand-extract the `instructions` body at runtime. The load-
bearing tests here are the tomllib round-trip (proves the generated TOML is
actually valid, not just plausible-looking) and the tier/mode mapping
(proves the frontmatter -> persona translation matches the documented
table in plugins/orchestra/references/tiers.md).

`tomllib` is stdlib only from Python 3.11 -- this repo's dev venv currently
runs 3.10, so tomllib-dependent assertions are skipped there rather than
failing for an environment reason unrelated to the code under test. CI's
`python3` (Ubuntu 24.04 / ubuntu-latest, 3.12) has tomllib built in, so
those assertions still run for real in the environment that matters; they
were also verified directly against a 3.11 interpreter during development.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 -- see module docstring.
    tomllib = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "plugins" / "orchestra" / "scripts" / "install-grok.py"
REAL_ORCHESTRA_ROOT = REPO_ROOT / "plugins" / "orchestra"

TOMLLIB_REASON = "requires tomllib (Python 3.11+); this interpreter is older"


def load_install_grok():
    # The hyphen in the filename makes this un-importable by name -- same
    # trick tests/test_sync_skills.py uses for its script.
    spec = importlib.util.spec_from_file_location("install_grok", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load install-grok.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_role_brief(path: Path, *, role_id: str, tier: str, mode: str, body: str) -> None:
    write_text(
        path,
        f"---\nid: {role_id}\nlineage: Test\ntier: {tier}\nmode: {mode}\n"
        f"canDelegate: false\ndeliverable: Test deliverable.\n---\n\n"
        f"# {role_id}\n\n{body}\n",
    )


PILOT_SENTENCE = "Distinctive pilot sentence for round trip verification."
WRENCH_SENTENCE = "Distinctive wrench sentence proving the body survived generation."


def make_fixture_package(root: Path) -> Path:
    """A minimal synthetic package shaped like plugins/orchestra: two roles
    (one deep/read_only, one fast/write), a skill with a relative link out
    to references/, one reference, one schema."""
    package = root / "orchestra"

    write_text(
        package / "skills" / "demo" / "SKILL.md",
        "---\nname: demo\ndescription: Test skill\n---\n\n"
        "# demo\n\nSee `../../references/notes.md` for background.\n",
    )
    write_text(package / "references" / "notes.md", "# Notes\n\nBackground reading.\n")
    write_text(
        package / "schemas" / "demo.schema.json",
        json.dumps({"title": "demo", "type": "object"}, indent=2) + "\n",
    )
    make_role_brief(
        package / "roles" / "pilot.md",
        role_id="pilot",
        tier="deep",
        mode="read_only",
        body=f"{PILOT_SENTENCE}\n\nSecond paragraph of pilot's brief.",
    )
    make_role_brief(
        package / "roles" / "wrench.md",
        role_id="wrench",
        tier="fast",
        mode="write",
        body=(
            f'{WRENCH_SENTENCE} She said "go" and left, with a backslash \\ '
            'and a triple quote right here: """ done.'
        ),
    )
    return package


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace (including the newlines Markdown's soft
    line-wrapping introduces mid-sentence) to single spaces, so a
    "distinctive sentence" check isn't fragile to exactly where a brief's
    prose happens to wrap."""
    return " ".join(text.split())


def snapshot(directory: Path) -> dict[str, bytes]:
    """Every file under `directory`, as relative-path -> raw bytes."""
    if not directory.is_dir():
        return {}
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


class InstallGrokRealRolesTests(unittest.TestCase):
    """Tests against the actual plugins/orchestra/roles/*.md briefs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_install_grok()
        cls.role_paths = sorted((REAL_ORCHESTRA_ROOT / "roles").glob("*.md"))

    def _render(self, role_path: Path) -> tuple[dict[str, str], str, str]:
        frontmatter, body = self.module.parse_role_brief(role_path)
        toml_text = self.module.render_persona_toml(
            role_id=frontmatter["id"],
            tier=frontmatter["tier"],
            mode=frontmatter["mode"],
            body=body,
            source=role_path,
        )
        return frontmatter, body, toml_text

    def test_role_briefs_exist(self) -> None:
        # Sanity check the fixture assumption every other test in this class
        # relies on -- if this fails, the real package moved and every test
        # below is testing nothing.
        self.assertTrue(self.role_paths, "expected role briefs under plugins/orchestra/roles")

    def test_parse_role_brief_strips_frontmatter_and_heading(self) -> None:
        frontmatter, body = self.module.parse_role_brief(REAL_ORCHESTRA_ROOT / "roles" / "scout.md")
        self.assertEqual(frontmatter["id"], "scout")
        self.assertEqual(frontmatter["tier"], "fast")
        self.assertEqual(frontmatter["mode"], "read_only")
        self.assertFalse(body.lstrip().startswith("#"))
        self.assertTrue(body.startswith("You are a `scout` lane"))

    def test_tier_to_reasoning_effort_mapping_matches_documented_table(self) -> None:
        # plugins/orchestra/references/tiers.md: deep -> high, standard ->
        # medium, fast -> low.
        self.assertEqual(
            self.module.TIER_TO_REASONING_EFFORT,
            {"deep": "high", "standard": "medium", "fast": "low"},
        )

    def test_capability_mode_mapping(self) -> None:
        capability_mode = self.module._capability_mode
        self.assertEqual(capability_mode("read_only"), "read-only")
        self.assertEqual(capability_mode("write"), "all")
        self.assertEqual(capability_mode("execute"), "all")
        # "anything else" -> "all", per the brief's explicit two-way mapping.
        self.assertEqual(capability_mode("some_future_mode"), "all")

    def test_tier_and_mode_mapping_for_every_real_role(self) -> None:
        expected_effort = {
            "adversary": "medium",
            "analyst": "medium",
            "architect": "high",
            "builder": "medium",
            "judge": "high",
            "mechanic": "low",
            "prover": "medium",
            "scout": "low",
        }
        expected_capability = {
            "adversary": "read-only",
            "analyst": "read-only",
            "architect": "read-only",
            "builder": "all",
            "judge": "read-only",
            "mechanic": "all",
            "prover": "all",
            "scout": "read-only",
        }
        self.assertEqual({p.stem for p in self.role_paths}, set(expected_effort))
        self.assertEqual({p.stem for p in self.role_paths}, set(expected_capability))

        for role_path in self.role_paths:
            _, _, toml_text = self._render(role_path)
            self.assertIn(
                f'reasoning_effort = "{expected_effort[role_path.stem]}"',
                toml_text,
                f"{role_path.name}: wrong reasoning_effort",
            )
            self.assertIn(
                f'default_capability_mode = "{expected_capability[role_path.stem]}"',
                toml_text,
                f"{role_path.name}: wrong default_capability_mode",
            )

    def test_instructions_nonempty_and_contains_distinctive_sentence_for_every_role(self) -> None:
        # A short, quote-free sentence per brief, chosen so a substring
        # check is unambiguous and unaffected by TOML quote-escaping.
        # Compared after whitespace normalization since Markdown's soft
        # line-wrapping means a "sentence" can span a newline in the raw
        # source (e.g. mechanic.md wraps mid-clause, "You are\nthe only
        # role...").
        distinctive = {
            "adversary": "Attack, do not review.",
            "analyst": "You do not design the change and you do not make the change.",
            "architect": "A lane without acceptance is not dispatchable — do not emit one.",
            "builder": "Write the failing test first.",
            "judge": "Judge the whole, not the parts.",
            "mechanic": "You are the only role dispatchable at depth two, and you are the last level",
            "prover": "You execute; you do not write.",
            "scout": "You do not rank, judge, redesign, or fix.",
        }
        self.assertEqual({p.stem for p in self.role_paths}, set(distinctive))

        for role_path in self.role_paths:
            _, body, toml_text = self._render(role_path)
            self.assertTrue(body.strip(), f"{role_path.name}: empty body")
            sentence = normalize_whitespace(distinctive[role_path.stem])
            self.assertIn(
                sentence,
                normalize_whitespace(body),
                f"{role_path.name}: fixture sentence is stale -- brief text changed",
            )
            self.assertIn(
                sentence,
                normalize_whitespace(toml_text),
                f"{role_path.name}: generated TOML lost the brief's body text",
            )

    @unittest.skipUnless(tomllib is not None, TOMLLIB_REASON)
    def test_every_real_role_round_trips_through_tomllib(self) -> None:
        for role_path in self.role_paths:
            frontmatter, body, toml_text = self._render(role_path)
            with self.subTest(role=role_path.stem):
                parsed = tomllib.loads(toml_text)  # raises TOMLDecodeError if invalid
                self.assertEqual(parsed["id"], frontmatter["id"])
                self.assertEqual(parsed["instructions"], body)
                self.assertIn(parsed["reasoning_effort"], {"high", "medium", "low"})
                self.assertIn(parsed["default_capability_mode"], {"read-only", "all"})


class RenderPersonaTomlTests(unittest.TestCase):
    """Unit tests for the escaping logic in isolation from frontmatter parsing."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_install_grok()

    def test_raises_on_unknown_tier(self) -> None:
        with self.assertRaises(self.module.GrokExportError):
            self.module.render_persona_toml(
                role_id="x", tier="ultra", mode="read_only", body="Some body.\n",
                source=Path("roles/x.md"),
            )

    def test_raises_on_empty_body(self) -> None:
        with self.assertRaises(self.module.GrokExportError):
            self.module.render_persona_toml(
                role_id="x", tier="deep", mode="read_only", body="   \n",
                source=Path("roles/x.md"),
            )

    def test_escapes_triple_quote_and_backslash_without_crashing(self) -> None:
        body = 'See """ this and a backslash \\ end.\n'
        toml_text = self.module.render_persona_toml(
            role_id="tricky", tier="fast", mode="write", body=body,
            source=Path("roles/tricky.md"),
        )
        # Every quote is escaped independently, so the delimiter sequence
        # never appears unescaped inside the string body.
        self.assertIn('\\"\\"\\"', toml_text)
        self.assertIn("\\\\", toml_text)
        self.assertNotIn('""" this', toml_text)

    @unittest.skipUnless(tomllib is not None, TOMLLIB_REASON)
    def test_embedded_triple_quote_and_backslash_round_trip_through_tomllib(self) -> None:
        tricky_body = (
            'Body with an embedded delimiter: """ right there, a lone '
            'backslash \\ and a quoted word "go".\n'
        )
        toml_text = self.module.render_persona_toml(
            role_id="tricky", tier="standard", mode="read_only", body=tricky_body,
            source=Path("roles/tricky.md"),
        )
        parsed = tomllib.loads(toml_text)
        self.assertEqual(parsed["instructions"], tricky_body)
        self.assertEqual(parsed["id"], "tricky")


class InstallGrokFixtureTests(unittest.TestCase):
    """Tests against a synthetic package, isolated from the real (and
    concurrently-changing) plugins/orchestra tree."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_install_grok()

    def test_build_export_raises_on_unknown_tier_and_leaves_nothing_swappable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            write_text(
                package / "roles" / "broken.md",
                "---\nid: broken\ntier: nonsense\nmode: read_only\n---\n\n"
                "# broken\n\nSome body text.\n",
            )
            dest = root / "staged"

            with self.assertRaises(self.module.GrokExportError):
                self.module.build_export(dest, package)

    def test_build_export_raises_on_missing_frontmatter_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            write_text(
                package / "roles" / "broken.md",
                "---\nid: broken\nmode: read_only\n---\n\n# broken\n\nSome body text.\n",
            )
            dest = root / "staged"

            with self.assertRaises(self.module.GrokExportError):
                self.module.build_export(dest, package)

    def test_relative_link_resolves_the_same_in_export_as_in_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            dest = root / "staged"
            self.module.build_export(dest, package)

            # skills/demo/SKILL.md links to ../../references/notes.md --
            # prove that resolves under the export exactly like it does
            # under the package.
            for base in (package, dest):
                skill_dir = base / "skills" / "demo"
                linked = (skill_dir / ".." / ".." / "references" / "notes.md").resolve()
                self.assertTrue(linked.is_file(), f"link did not resolve under {base}")

    def test_check_with_target_passes_on_fresh_install_and_fails_after_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            target = root / "grok-home"

            self.assertEqual(self.module.run_install(target, package), 0)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                fresh_code = self.module.run_check(target, package, target_given=True)
            self.assertEqual(fresh_code, 0)
            self.assertIn("OK", stdout.getvalue())

            (target / "roles" / "pilot.toml").write_text("drifted\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                drifted_code = self.module.run_check(target, package, target_given=True)
            self.assertEqual(drifted_code, 1)
            self.assertIn("changed: roles/pilot.toml", stdout.getvalue())

    def test_check_with_target_fails_when_target_does_not_exist(self) -> None:
        """`--check --target DIR` asks "is DIR current?" -- if nothing is
        installed at DIR yet, that is a clear failure, not a silent pass and
        not a fallback to the determinism check (that fallback only applies
        to a bare `--check`, see test_check_without_target_*)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            target = root / "not-installed" / "grok-home"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = self.module.run_check(target, package, target_given=True)

            self.assertEqual(exit_code, 1)
            self.assertIn("does not exist", stdout.getvalue())
            self.assertFalse(target.exists(), "--check must never write to the target")

    def test_check_with_target_ignores_unrelated_content_already_there(self) -> None:
        """Regression test: a real `~/.grok` on a development machine was
        found, during development of this script, to already have unrelated
        skills sitting directly under `skills/` (installed by some other
        tool). `--check --target DIR` must not flag those as drift -- only
        entries this export actually declares (missing or changed) are
        checked against an existing target.

        Decoys mirror what that real `~/.grok` actually contains: top-level
        `bin/`, `bundled/`, `completions/` (untouched by construction --
        outside OWNED_TOP_LEVEL entirely) plus entries inside the shared
        owned directories themselves (`skills/`, `roles/`), which is the
        part that actually has to be handled deliberately.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            target = root / "grok-home"

            self.assertEqual(self.module.run_install(target, package), 0)
            write_text(target / "bin" / "grok", "#!/bin/sh\necho unrelated\n")
            write_text(target / "bundled" / "thing.json", '{"unrelated": true}\n')
            write_text(target / "completions" / "grok.bash", "# unrelated\n")
            write_text(target / "skills" / "some-other-skill" / "SKILL.md", "unrelated\n")
            write_text(target / "roles" / "other-plugin.toml", 'description = "unrelated"\n')

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = self.module.run_check(target, package, target_given=True)
            self.assertEqual(exit_code, 0, stdout.getvalue())
            self.assertIn("OK", stdout.getvalue())

    def test_check_without_target_is_blind_to_whatever_is_at_the_default_target(self) -> None:
        """The load-bearing proof for the --check semantic split: a bare
        `--check` (`target_given=False`) must give the *same* answer
        regardless of what is or is not sitting at `target` -- it never
        looks. Proven here the strong way: point `target` at a directory
        that is deliberately NOT a valid orchestra install (missing
        everything a currency diff would require), which would fail a
        target-comparison check immediately, and confirm run_check still
        reports success via the determinism path and never touches it.

        This is the machine-independent guarantee the earlier design was
        missing: `--check` used to silently switch between "diff against
        target" and "check determinism" depending on whether `target`
        happened to exist on whatever machine ran it -- so the exact same
        command passed on a bare CI runner (no ~/.grok) for a different
        reason than it would on a developer's machine (~/.grok already
        populated with real, unrelated content). `target_given=False` now
        removes that branch entirely instead of relying on an environment
        fact to land on the right one.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            target = root / "grok-home"
            write_text(target / "skills" / "nothing-to-do-with-orchestra" / "SKILL.md", "x\n")
            before = snapshot(target)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = self.module.run_check(target, package, target_given=False)

            self.assertEqual(exit_code, 0, stdout.getvalue())
            self.assertIn("deterministic", stdout.getvalue())
            self.assertEqual(snapshot(target), before, "--check without --target must not touch it")

    def test_check_without_target_passes_even_when_target_does_not_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            target = root / "not-installed" / "grok-home"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = self.module.run_check(target, package, target_given=False)

            self.assertEqual(exit_code, 0)
            self.assertIn("deterministic", stdout.getvalue())
            self.assertFalse(target.exists(), "--check must never write to the target")

    def test_check_reports_failure_when_generation_itself_is_broken(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            write_text(
                package / "roles" / "broken.md",
                "---\nid: broken\ntier: nonsense\nmode: read_only\n---\n\n"
                "# broken\n\nSome body text.\n",
            )
            target = root / "grok-home"

            with self.assertRaises(self.module.GrokExportError):
                self.module.run_check(target, package, target_given=False)

    def test_install_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            target = root / "grok-home"

            self.assertEqual(self.module.run_install(target, package), 0)
            first = snapshot(target)

            self.assertEqual(self.module.run_install(target, package), 0)
            second = snapshot(target)

        self.assertEqual(first, second)
        self.assertTrue(first)  # sanity: the snapshot isn't empty

    def test_install_writes_expected_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            target = root / "grok-home"

            self.assertEqual(self.module.run_install(target, package), 0)

            self.assertTrue((target / "skills" / "demo" / "SKILL.md").is_file())
            self.assertTrue((target / "references" / "notes.md").is_file())
            self.assertTrue((target / "schemas" / "demo.schema.json").is_file())
            self.assertTrue((target / "roles" / "pilot.md").is_file())
            self.assertTrue((target / "roles" / "pilot.toml").is_file())
            self.assertTrue((target / "roles" / "wrench.md").is_file())
            self.assertTrue((target / "roles" / "wrench.toml").is_file())

            # The copied .md is untouched (byte-identical to source) --
            # only the generated .toml is a derived artifact.
            self.assertEqual(
                (target / "roles" / "pilot.md").read_bytes(),
                (package / "roles" / "pilot.md").read_bytes(),
            )

    @unittest.skipUnless(tomllib is not None, TOMLLIB_REASON)
    def test_a_triple_quote_in_a_real_brief_file_survives_the_full_pipeline(self) -> None:
        """RenderPersonaTomlTests exercises the escaping in isolation; this
        proves the same guarantee end-to-end through the actual code path
        install writes: `wrench.md`'s body (embedded via make_fixture_package
        above) contains `\"\"\"`, a backslash, and a quoted word -- parsed
        from a real file on disk by build_export, written to
        `roles/wrench.toml`, then reloaded from disk and parsed by tomllib.
        If the emitter's escaping had a gap, this is where a real install
        would silently ship broken TOML to a user's Grok config."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            target = root / "grok-home"

            self.assertEqual(self.module.run_install(target, package), 0)

            _, expected_body = self.module.parse_role_brief(package / "roles" / "wrench.md")
            toml_text = (target / "roles" / "wrench.toml").read_text(encoding="utf-8")
            parsed = tomllib.loads(toml_text)  # raises TOMLDecodeError if this ever regresses
            self.assertEqual(parsed["instructions"], expected_body)
            self.assertIn('"""', expected_body)  # sanity: the fixture still exercises the case
            self.assertIn(WRENCH_SENTENCE, parsed["instructions"])

    def test_install_does_not_clobber_unrelated_target_content(self) -> None:
        """Regression test for the hazard this exporter must avoid: on Grok
        Build, skills/, references/, schemas/, and roles/ under the default
        `~/.grok` target are shared, unnamespaced directories another
        installed plugin may already have content in. Installing orchestra
        must never delete a sibling entry it did not itself write.

        Decoys mirror what a real `~/.grok` on a development machine
        actually contains: a live Grok CLI install with top-level `bin/`,
        `bundled/`, `completions/`, `config.toml`, `sessions/`, plus five
        pre-existing unrelated skills directly under `skills/`. Every one
        of those must survive an orchestra install byte-for-byte -- this
        test proves it without ever touching that real directory itself.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            target = root / "grok-home"

            unrelated = {
                # Top-level entries outside OWNED_TOP_LEVEL entirely --
                # untouched by construction, verified directly anyway.
                "bin/grok": "#!/bin/sh\necho unrelated\n",
                "bundled/thing.json": '{"unrelated": true}\n',
                "completions/grok.bash": "# unrelated\n",
                "config.toml": 'unrelated = "config"\n',
                "sessions/abc123.json": "{}\n",
                # Entries inside the shared owned directories themselves --
                # the part that requires the immediate-child merge, not
                # directory-level replace, to get right.
                "personas/other-plugin.toml": 'description = "unrelated"\n',
                "workflows/ship.rhai": "// unrelated\n",
                "skills/other-plugin/SKILL.md": "unrelated skill\n",
                "skills/some-other-skill/SKILL.md": "unrelated skill\n",
                "references/other-plugin-notes.md": "# unrelated\n",
                "roles/other-plugin.toml": 'description = "unrelated role"\n',
            }
            for rel, content in unrelated.items():
                write_text(target / rel, content)
            unrelated_before = {rel: (target / rel).read_bytes() for rel in unrelated}

            self.assertEqual(self.module.run_install(target, package), 0)

            for rel, before in unrelated_before.items():
                self.assertEqual(
                    (target / rel).read_bytes(), before, f"{rel} was touched by install"
                )

            # Owned content still installed correctly alongside it.
            self.assertTrue((target / "roles" / "pilot.toml").is_file())
            self.assertTrue((target / "skills" / "demo" / "SKILL.md").is_file())

    def test_install_creates_target_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = make_fixture_package(root)
            target = root / "does" / "not" / "exist" / "yet"

            self.assertFalse(target.exists())
            self.assertEqual(self.module.run_install(target, package), 0)
            self.assertTrue((target / "roles" / "pilot.toml").is_file())

    def test_help_documents_both_check_meanings_and_the_staleness_gap(self) -> None:
        """A person deciding whether to trust `--check` reads `--help`, not
        the module docstring -- so both `--check` meanings and the known
        "stale entries aren't pruned" gap must be visible there too, not
        only in source comments. Runs the actual script as a subprocess
        (rather than calling `main()` in-process) so this exercises real
        `--help` output, including argparse's line-wrapping."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True, text=True, check=True,
        )
        help_text = " ".join(result.stdout.split())  # argparse hard-wraps; normalize

        # Both --check meanings. "currency" rather than the hyphenated
        # "install-currency" compound: argparse hard-wraps at the hyphen in
        # this help text ("install-\ncurrency"), which `.split()`-based
        # whitespace normalization turns into "install- currency" -- same
        # class of hard-wrap brittleness as the sentence-matching tests
        # above, caught here by actually running the assertion rather than
        # assuming it.
        self.assertIn("target-independent", help_text)
        self.assertIn("deterministic", help_text)
        self.assertIn("what CI runs", help_text)
        self.assertIn("currency", help_text)

        # The known staleness gap.
        self.assertIn("not auto-deleted", help_text)
        self.assertIn("never prunes", help_text)


if __name__ == "__main__":
    unittest.main()
