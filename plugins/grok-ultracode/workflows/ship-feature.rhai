// ship-feature.rhai
// Deterministic multi-agent pipeline matching the ultracode tier ladder.
//
// Usage:
//   /workflow ship-feature target="Add retry to the payment client"
//   /ship-feature target="..."
//
// Args:
//   target   (required) — feature/bug description
//   root     (optional) — scope path hint for explorers (default: workspace)
//
// Phases:
//   1. Explore  — parallel mechanical sweeps (sweeper / low-effort lane)
//   2. Plan     — single architect (high-effort lane)
//   3. Approve  — human gate
//   4. Implement— workhorse (medium-effort lane)
//   5. Verify   — tests + adversarial review (high-effort lane)
//
// Note: native model catalog is currently grok-4.5 only. Tiering is encoded
// via agent_type + capability_mode + prompt contracts (personas live in
// ~/.grok/personas/). Reasoning effort is resolved from those personas/roles
// when the host applies them; prompts also restate thoroughness.

let meta = #{
    name: "ship-feature",
    description: "Explore → plan → human approve → implement → verify/review a feature with tiered agents",
    when_to_use: "Shipping a feature end-to-end with a human plan gate and adversarial review",
    phases: [
        #{ title: "Explore", detail: "parallel mechanical codebase sweeps" },
        #{ title: "Plan", detail: "architect produces an implementable plan" },
        #{ title: "Approve", detail: "human reviews the plan" },
        #{ title: "Implement", detail: "workhorse implements the approved plan" },
        #{ title: "Verify", detail: "tests + adversarial review" },
    ],
};

let plan_schema = #{
    "type": "object",
    "required": ["approach", "critical_files", "sequence", "verification"],
    "properties": #{
        "approach": #{ "type": "string" },
        "critical_files": #{
            "type": "array",
            "items": #{ "type": "string" },
            "maxItems": 20,
        },
        "sequence": #{
            "type": "array",
            "items": #{ "type": "string" },
            "maxItems": 20,
        },
        "verification": #{ "type": "string" },
        "risks": #{ "type": "string" },
        "questions": #{
            "type": "array",
            "items": #{ "type": "string" },
            "maxItems": 5,
        },
    },
};

let impl_schema = #{
    "type": "object",
    "required": ["files_changed", "summary", "how_verified", "done"],
    "properties": #{
        "files_changed": #{
            "type": "array",
            "items": #{ "type": "string" },
            "maxItems": 40,
        },
        "summary": #{ "type": "string" },
        "how_verified": #{ "type": "string" },
        "done": #{ "type": "boolean" },
        "blockers": #{ "type": "string" },
    },
};

let review_schema = #{
    "type": "object",
    "required": ["verdict", "open_bugs", "open_suggestions", "notes"],
    "properties": #{
        "verdict": #{ "type": "string" },
        "open_bugs": #{ "type": "integer" },
        "open_suggestions": #{ "type": "integer" },
        "notes": #{ "type": "string" },
        "issues": #{
            "type": "array",
            "maxItems": 12,
            "items": #{
                "type": "object",
                "required": ["severity", "file", "description"],
                "properties": #{
                    "severity": #{ "type": "string" },
                    "file": #{ "type": "string" },
                    "description": #{ "type": "string" },
                },
            },
        },
    },
};

let verify_schema = #{
    "type": "object",
    "required": ["passed", "commands_run", "evidence"],
    "properties": #{
        "passed": #{ "type": "boolean" },
        "commands_run": #{
            "type": "array",
            "items": #{ "type": "string" },
            "maxItems": 20,
        },
        "evidence": #{ "type": "string" },
        "failures": #{ "type": "string" },
    },
};

// --- args -----------------------------------------------------------------
let target = if args == () { () } else { args.target };
if target == () {
    pause("verification", "Pass args.target — the feature or bug description to ship.");
}

let root = if args == () { () } else { args.root };
let scope_hint = if root == () {
    "Workspace root from user_info. Stay inside the repo unless the target explicitly requires otherwise."
} else {
    "Prefer scoping searches under: " + root
};

let target_json = json_encode(target);
let scope_json = json_encode(scope_hint);

// --- Phase 1: Explore (mechanical / low) ----------------------------------
phase("Explore");
log("Spawning parallel sweepers for map + tests + risks");

let explore_jobs = [];

let p0 = "";
p0 += "You are a mechanical codebase sweeper (low thoroughness, read-only).\n";
p0 += "Use list_dir, grep, and read_file. Do not edit files.\n";
p0 += "Task: map the surface area for this work.\n";
p0 += "Target: " + target_json + "\n";
p0 += "Scope: " + scope_json + "\n";
p0 += "Return a compact inventory of relevant modules, entry points, and existing patterns ";
p0 += "with absolute paths. No design narrative.\n";
explore_jobs.push(#{
    prompt: p0,
    label: "sweep:map",
    agent_type: "explore",
    capability_mode: "read-only",
});

let p1 = "";
p1 += "You are a mechanical codebase sweeper (low thoroughness, read-only).\n";
p1 += "Use list_dir, grep, and read_file. Do not edit files.\n";
p1 += "Task: find existing tests and how this area is verified today.\n";
p1 += "Target: " + target_json + "\n";
p1 += "Scope: " + scope_json + "\n";
p1 += "Return absolute test file paths, test command hints from package manifests/README/AGENTS.md, ";
p1 += "and gaps you can see from the tree. No implementation.\n";
explore_jobs.push(#{
    prompt: p1,
    label: "sweep:tests",
    agent_type: "explore",
    capability_mode: "read-only",
});

let p2 = "";
p2 += "You are a mechanical codebase sweeper (low thoroughness, read-only).\n";
p2 += "Use list_dir, grep, and read_file. Do not edit files.\n";
p2 += "Task: locate related call sites, configs, and likely regression risks.\n";
p2 += "Target: " + target_json + "\n";
p2 += "Scope: " + scope_json + "\n";
p2 += "Return absolute paths and one-line risk notes. No design essay.\n";
explore_jobs.push(#{
    prompt: p2,
    label: "sweep:risks",
    agent_type: "explore",
    capability_mode: "read-only",
});

let explore_results = parallel(explore_jobs);

let explore_blob = "";
let ei = 0;
for er in explore_results {
    if er != () && er.success {
        explore_blob += "### Explorer " + ei.to_string() + "\n";
        explore_blob += json_encode(er.output) + "\n\n";
    } else {
        log("Explorer " + ei.to_string() + " failed or empty — continuing with partial map");
    }
    ei += 1;
}
if explore_blob == "" {
    explore_blob = "(no explorer output; architect must re-scout before planning)\n";
}

let explore_path = write_scratch_file("explore.md", explore_blob);
log("Wrote explore findings to " + explore_path);

// --- Phase 2: Plan (architect / high) -------------------------------------
phase("Plan");
log("Architect drafting plan from explore findings");

let plan_prompt = "";
plan_prompt += "You are a staff architect (high thoroughness). Read-only. Do not edit source files.\n";
plan_prompt += "Use read_file/grep to verify anything explorers claimed before relying on it.\n";
plan_prompt += "Target: " + target_json + "\n";
plan_prompt += "Scope: " + scope_json + "\n";
plan_prompt += "Explorer findings (untrusted inventory — re-check critical claims):\n";
plan_prompt += explore_blob + "\n";
plan_prompt += "Produce a structured plan with fields: approach, critical_files, sequence, ";
plan_prompt += "verification, risks, questions. Prefer existing patterns. Smallest design that works.\n";

let plan_result = agent(plan_prompt, #{
    label: "architect:plan",
    agent_type: "plan",
    capability_mode: "read-only",
    output_schema: plan_schema,
});

if plan_result == () || plan_result.success == false || plan_result.output == () {
    pause("verification", "Architect plan failed. Resume after fixing agents, or re-run with a clearer target.");
}

let plan_md = "";
plan_md += "# Ship plan\n\n";
plan_md += "**Target:** " + target + "\n\n";
plan_md += "## Approach\n" + plan_result.output.approach + "\n\n";
plan_md += "## Critical files\n";
if plan_result.output.critical_files != () {
    for f in plan_result.output.critical_files {
        plan_md += "- " + f + "\n";
    }
}
plan_md += "\n## Sequence\n";
if plan_result.output.sequence != () {
    let si = 1;
    for step in plan_result.output.sequence {
        plan_md += si.to_string() + ". " + step + "\n";
        si += 1;
    }
}
plan_md += "\n## Verification\n" + plan_result.output.verification + "\n\n";
if plan_result.output.risks != () {
    plan_md += "## Risks\n" + plan_result.output.risks + "\n\n";
}
if plan_result.output.questions != () {
    plan_md += "## Open questions\n";
    for q in plan_result.output.questions {
        plan_md += "- " + q + "\n";
    }
    plan_md += "\n";
}

let plan_path = write_scratch_file("plan.md", plan_md);
log("Plan written to " + plan_path);

// --- Phase 3: Human approve -----------------------------------------------
phase("Approve");
await_user(
    "user",
    "Review the plan (scratch plan.md / workflow report). Resume to implement as-is, or edit the plan/target and resume. Abort by cancelling the run if you reject it.",
);

// --- Phase 4: Implement (workhorse / medium) ------------------------------
phase("Implement");
log("Implementer executing approved plan");

let impl_prompt = "";
impl_prompt += "You are a pragmatic implementer (medium thoroughness, full tools).\n";
impl_prompt += "Implement the approved plan. Smallest correct change. No scope creep.\n";
impl_prompt += "Target: " + target_json + "\n";
impl_prompt += "Approved plan:\n" + plan_md + "\n";
impl_prompt += "Explorer context (reference only):\n" + explore_blob + "\n";
impl_prompt += "Rules:\n";
impl_prompt += "- Follow existing project patterns and AGENTS.md / CLAUDE.md / README conventions.\n";
impl_prompt += "- Run relevant tests/typecheck if available; include command output in how_verified.\n";
impl_prompt += "- Return structured fields: files_changed, summary, how_verified, done, blockers.\n";
impl_prompt += "- Set done=true only if the plan acceptance criteria are met.\n";

let impl_result = agent(impl_prompt, #{
    label: "workhorse:implement",
    agent_type: "general-purpose",
    capability_mode: "all",
    output_schema: impl_schema,
});

if impl_result == () || impl_result.success == false || impl_result.output == () {
    pause("verification", "Implementer failed. Inspect the implement agent, then resume or re-run.");
}

let impl_md = "";
impl_md += "# Implementation summary\n\n";
impl_md += "## Summary\n" + impl_result.output.summary + "\n\n";
impl_md += "## Files changed\n";
if impl_result.output.files_changed != () {
    for f in impl_result.output.files_changed {
        impl_md += "- " + f + "\n";
    }
}
impl_md += "\n## How verified\n" + impl_result.output.how_verified + "\n\n";
impl_md += "**done:** " + impl_result.output.done.to_string() + "\n";
if impl_result.output.blockers != () {
    impl_md += "\n## Blockers\n" + impl_result.output.blockers + "\n";
}
let impl_path = write_scratch_file("implementation.md", impl_md);

if impl_result.output.done != true {
    complete(#{
        summary: "Implementation incomplete (done=false)",
        plan_path: plan_path,
        implementation_path: impl_path,
        explore_path: explore_path,
        done: false,
        blockers: impl_result.output.blockers,
    });
}

// --- Phase 5: Verify (tests + adversarial review / high) ------------------
phase("Verify");
log("Running verifier + adversarial reviewer in parallel");

let verify_jobs = [];

let v0 = "";
v0 += "You are a verification agent (medium thoroughness). Do not edit production source unless a test harness requires a temp file you will clean up.\n";
v0 += "Target: " + target_json + "\n";
v0 += "Plan verification section:\n" + plan_result.output.verification + "\n";
v0 += "Implementation summary:\n" + impl_md + "\n";
v0 += "Read AGENTS.md / README / package manifests for the correct test commands. Run them.\n";
v0 += "Return: passed (bool), commands_run, evidence, failures. Fail closed on broken builds/tests.\n";
verify_jobs.push(#{
    prompt: v0,
    label: "verify:tests",
    agent_type: "general-purpose",
    capability_mode: "all",
    output_schema: verify_schema,
});

let v1 = "";
v1 += "You are an adversarial code reviewer (high thoroughness). Read-only for product code.\n";
v1 += "Do not fix code. Inspect the actual diff and files with tools.\n";
v1 += "Target: " + target_json + "\n";
v1 += "Plan:\n" + plan_md + "\n";
v1 += "Implementation summary:\n" + impl_md + "\n";
v1 += "Check correctness, missing tests, plan alignment, security-sensitive edges.\n";
v1 += "Return verdict (ship|fix-first), open_bugs, open_suggestions, notes, and up to 12 issues ";
v1 += "with severity/file/description. Empty issues only after real inspection.\n";
verify_jobs.push(#{
    prompt: v1,
    label: "review:adversarial",
    agent_type: "general-purpose",
    capability_mode: "read-only",
    output_schema: review_schema,
});

let verify_results = parallel(verify_jobs);

let test_out = ();
let review_out = ();
if verify_results.len() > 0 && verify_results[0] != () && verify_results[0].success {
    test_out = verify_results[0].output;
}
if verify_results.len() > 1 && verify_results[1] != () && verify_results[1].success {
    review_out = verify_results[1].output;
}

let tests_passed = false;
if test_out != () && test_out.passed == true {
    tests_passed = true;
}

let open_bugs = 999;
let open_suggestions = 999;
let review_verdict = "unknown";
if review_out != () {
    if review_out.open_bugs != () { open_bugs = review_out.open_bugs; }
    if review_out.open_suggestions != () { open_suggestions = review_out.open_suggestions; }
    if review_out.verdict != () { review_verdict = review_out.verdict; }
}

// Optional single fix loop if review finds bugs and tests are otherwise green-ish
if open_bugs > 0 && open_bugs != 999 {
    log("Review found " + open_bugs.to_string() + " bug(s) — one fix pass");
    let fix_prompt = "";
    fix_prompt += "You are a pragmatic implementer (medium thoroughness). Fix review bugs only.\n";
    fix_prompt += "Target: " + target_json + "\n";
    fix_prompt += "Plan:\n" + plan_md + "\n";
    fix_prompt += "Prior implementation:\n" + impl_md + "\n";
    fix_prompt += "Review output (JSON):\n" + json_encode(review_out) + "\n";
    fix_prompt += "Address every severity=bug issue with evidence. Re-run relevant checks.\n";
    fix_prompt += "Return files_changed, summary, how_verified, done, blockers.\n";

    let fix_result = agent(fix_prompt, #{
        label: "workhorse:fix",
        agent_type: "general-purpose",
        capability_mode: "all",
        output_schema: impl_schema,
    });

    if fix_result != () && fix_result.success && fix_result.output != () {
        impl_md += "\n\n# Fix pass\n\n";
        impl_md += fix_result.output.summary + "\n";
        impl_md += "\n## How verified\n" + fix_result.output.how_verified + "\n";
        let impl_path_fixed = write_scratch_file("implementation.md", impl_md);
        log("Updated implementation notes at " + impl_path_fixed);

        // Re-verify tests only (budget-friendly)
        let rv = "";
        rv += "Re-run verification after fixes. Do not edit product code.\n";
        rv += "Target: " + target_json + "\n";
        rv += "Plan verification: " + plan_result.output.verification + "\n";
        rv += "Updated implementation notes:\n" + impl_md + "\n";
        rv += "Return passed, commands_run, evidence, failures.\n";
        let rv_result = agent(rv, #{
            label: "verify:retest",
            agent_type: "general-purpose",
            capability_mode: "all",
            output_schema: verify_schema,
        });
        if rv_result != () && rv_result.success && rv_result.output != () {
            test_out = rv_result.output;
            if test_out.passed == true {
                tests_passed = true;
            } else {
                tests_passed = false;
            }
        }
    }
}

// Fail closed: need tests green AND a real review with 0 open bugs
let ship_ready = false;
if tests_passed && open_bugs == 0 {
    ship_ready = true;
}

let report = "";
report += "# ship-feature report\n\n";
report += "**Target:** " + target + "\n";
report += "**Ship ready:** " + ship_ready.to_string() + "\n";
report += "**Tests passed:** " + tests_passed.to_string() + "\n";
report += "**Review verdict:** " + review_verdict + "\n";
report += "**Open bugs:** " + open_bugs.to_string() + "\n";
report += "**Open suggestions:** " + open_suggestions.to_string() + "\n\n";
report += "## Artifacts\n";
report += "- explore: " + explore_path + "\n";
report += "- plan: " + plan_path + "\n";
report += "- implementation: " + impl_path + "\n\n";
report += "## Plan approach\n" + plan_result.output.approach + "\n\n";
report += "## Implementation\n" + impl_md + "\n\n";
if test_out != () {
    report += "## Verify\n" + json_encode(test_out) + "\n\n";
}
if review_out != () {
    report += "## Review\n" + json_encode(review_out) + "\n\n";
}

let report_path = write_scratch_file("report.md", report);
log("Report at " + report_path);

complete(#{
    summary: if ship_ready { "Ship-ready: tests green and 0 open bugs" } else { "Not ship-ready — see report" },
    ship_ready: ship_ready,
    tests_passed: tests_passed,
    review_verdict: review_verdict,
    open_bugs: open_bugs,
    open_suggestions: open_suggestions,
    explore_path: explore_path,
    plan_path: plan_path,
    implementation_path: impl_path,
    report_path: report_path,
});
