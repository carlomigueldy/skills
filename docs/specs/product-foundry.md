# Product Foundry Plugin Specification

## Problem Statement

Founders and product teams can use coding agents to generate software quickly, but the result is often disconnected from customer evidence, business constraints, launch strategy, durable product context, and a coherent design direction. Planning is frequently trapped in a long conversation, implementation begins before the MVP is understood, agents repeat research or contradict prior decisions, and later sessions cannot reliably reconstruct the state of the product.

The user needs a cross-platform Claude Code and Codex plugin that can take an early company or product idea through rigorous discovery, product definition, executable prototyping, technical planning, marketing planning, and implementation handoff. It must produce enough structured context for a fresh agent session to implement the approved PRD autonomously, while remaining stack-agnostic, token-efficient, deterministic where possible, and proportionate to an MVP.

The output must feel like the work of a coordinated senior product-development organization without simulating unnecessary hierarchy or introducing speculative complexity. It must combine product, design, engineering, security, operations, release, marketing, sales, and company-building concerns while preserving DRY, KISS, YAGNI, explicit decision ownership, and an MVP-first path to product-market-fit validation.

## Solution

Create a dual-platform plugin named `product-foundry` with two primary user entry points:

- `$product-foundry` or `/product-foundry` runs a resumable, approval-gated foundry session. It orchestrates independently invokable phase skills that interview the user, research the opportunity, define the company and MVP, create build-free low- and high-fidelity prototypes, establish brand and architecture, define the agent harness, write the PRD, create the go-to-market plan, verify readiness, and prepare a durable handoff.
- `$implement-prd` or `/implement-prd` runs a separate implementation session. It accepts attached files, file arguments, directory arguments, or a generated implementation manifest; reconstructs the approved direction; discovers relevant skills; creates a product-specific agent roster; and implements or resumes the MVP through evidence-backed quality gates.

The foundry session stores canonical product state in a structured `docs/` hierarchy and generates `docs/implementation-manifest.json` as an index into those artifacts. Build-free prototypes live under `docs/prototypes/low-fidelity/` and `docs/prototypes/high-fidelity/` and use plain HTML, vanilla JavaScript, and the Tailwind CSS v4 browser CDN. Recursive `AGENTS.md` and `CLAUDE.md` files provide concise, maintained context maps at meaningful ownership boundaries without duplicating canonical documentation.

The implementation skill detects Claude Code or Codex and adapts its invocation and orchestration mechanics while preserving one platform-independent process, state model, safety boundary, and definition of done. It supports fresh and resume modes, delegates narrow work to the cheapest capable agents, escalates model capability only when justified, and requires user approval before consequential external actions.

## User Stories

1. As a founder, I want the plugin to interview me about my goals and constraints, so that the proposed company fits my actual situation.
2. As a founder, I want questions asked one at a time, so that I can make deliberate decisions without being overwhelmed.
3. As a founder, I want unresolved assumptions identified explicitly, so that agent confidence is not mistaken for evidence.
4. As a founder, I want the workflow to investigate the customer problem before choosing features, so that the product addresses a credible need.
5. As a founder, I want market and competitor research to include sources, dates, confidence, and inference labels, so that I can assess its reliability.
6. As a founder, I want research delegated to cost-effective agents, so that broad discovery does not waste premium model capacity.
7. As a founder, I want model escalation justified and recorded, so that expensive reasoning is reserved for work that needs it.
8. As a founder, I want the plugin to help define the company as well as the software, so that the plan includes how the business will operate.
9. As a founder, I want the plugin to define my ideal customer profile and market segments, so that product and distribution decisions target the same audience.
10. As a founder, I want a clear product thesis and differentiation, so that the product is not a generic collection of features.
11. As a founder, I want pricing and packaging hypotheses, so that willingness to pay can be validated early.
12. As a founder, I want sales and distribution options matched to my capabilities, so that the go-to-market plan is executable.
13. As a founder, I want legal, privacy, and compliance assumptions surfaced, so that material obligations are not discovered after launch.
14. As a founder, I want basic financial and operating assumptions documented, so that the MVP reflects realistic business constraints.
15. As a founder, I want support and customer-success expectations defined, so that early customers receive a coherent experience.
16. As a founder, I want an MVP separated from later roadmap hypotheses, so that validation is not delayed by speculative scope.
17. As a founder, I want explicit MVP exclusions, so that agents do not quietly expand the build.
18. As a founder, I want the riskiest assumptions identified, so that experiments target what could invalidate the company.
19. As a founder, I want activation, retention, revenue, and qualitative PMF signals defined, so that launch results can guide the next decision.
20. As a founder, I want pivot, persevere, and stop criteria, so that post-launch decisions are not driven only by optimism.
21. As a founder, I want post-PMF expansion to remain conditional, so that the product grows in response to evidence.
22. As a product owner, I want a deterministic, comprehensive PRD, so that implementation agents receive one coherent contract.
23. As a product owner, I want requirements uniquely identified, prioritized, and testable, so that implementation can be traced and verified.
24. As a product owner, I want every material requirement tied to evidence or an explicit assumption, so that the rationale remains auditable.
25. As a product owner, I want user journeys and edge states documented, so that the product is complete beyond its happy path.
26. As a product owner, I want the PRD to include non-functional requirements, so that security, accessibility, reliability, and performance are planned.
27. As a product owner, I want risks, mitigations, and unresolved decisions recorded, so that uncertainty survives the handoff accurately.
28. As a designer, I want a low-fidelity executable prototype, so that information architecture and workflows can be validated before visual polish.
29. As a designer, I want a high-fidelity executable prototype, so that implementation has a concrete visual and interaction reference.
30. As a designer, I want both prototypes to be build-free, so that they remain portable and inexpensive to inspect.
31. As a designer, I want prototypes to use realistic fixtures and interactions, so that workflow problems are visible before production development.
32. As a designer, I want responsive desktop and mobile behavior represented, so that layout decisions are not deferred to implementation.
33. As a designer, I want loading, empty, error, permission, success, and validation states represented, so that the reference covers real product behavior.
34. As a designer, I want accessibility considered and verified in prototypes, so that the design direction does not create avoidable barriers.
35. As a designer, I want a product-specific visual thesis, so that premium quality is expressed through coherent decisions rather than decorative excess.
36. As a designer, I want rejected directions and important design changes documented, so that later agents do not repeat discarded work.
37. As an engineer, I want the technical stack selected through an interview, so that architecture follows product and deployment constraints.
38. As an engineer, I want a monorepo to be the default, so that related applications and shared packages have one coordinated workspace.
39. As an engineer, I want pnpm preferred and Bun considered when advantageous, so that package management is deliberate and compatible.
40. As an engineer, I want Turborepo used when compatible, so that monorepo task orchestration is consistent without forcing it onto unsuitable stacks.
41. As an engineer, I want Docker and Docker Compose included by default, so that local services and development environments are reproducible.
42. As an engineer, I want a modular monolith preferred for the MVP, so that the system is scalable without premature distribution.
43. As an engineer, I want deviations from defaults justified in decision records, so that unusual architecture remains understandable.
44. As an engineer, I want data, authentication, APIs, storage, jobs, notifications, billing, analytics, and migrations decided explicitly, so that core platform concerns are not implicit.
45. As an engineer, I want secrets, environments, backups, recovery, and observability planned, so that deployment is operationally credible.
46. As a security reviewer, I want threat, privacy, dependency, and authorization risks considered in proportion to the product, so that MVP does not mean unsafe.
47. As a delivery lead, I want the user to choose an appropriate agent-harness depth, so that controls match the product's duration and risk.
48. As a delivery lead, I want the plugin to recommend Lean, Standard, or Advanced harness setups with tradeoffs, so that the user can make an informed choice.
49. As a delivery lead, I want linting, formatting, type checking, schema validation, and tests proposed based on the stack, so that quality automation has a clear purpose.
50. As a delivery lead, I want commit hooks such as Husky or Lefthook considered rather than assumed, so that local enforcement matches the toolchain.
51. As a delivery lead, I want task state stored in structured JSON by default, so that long-running agents can resume deterministically.
52. As a delivery lead, I want the option to use an installable task system, so that longer-lived products can adopt a more capable tracker.
53. As a delivery lead, I want recursive context files at meaningful ownership boundaries, so that agents can quickly find relevant state.
54. As a delivery lead, I want context files to point to canonical documentation rather than duplicate it, so that product truth does not drift.
55. As a delivery lead, I want documentation updated with the code that changes it, so that handoffs remain accurate.
56. As a root orchestrator, I want a generated specialist roster, so that each agent receives a narrow responsibility and appropriate skills.
57. As a root orchestrator, I want `find-skills` to be mandatory before roster creation, so that existing expertise is discovered instead of recreated.
58. As a root orchestrator, I want agent ownership, inputs, outputs, tools, and escalation criteria recorded, so that delegation is auditable.
59. As a root orchestrator, I want subagents to be able to spawn narrowly scoped subagents, so that complex work can be decomposed efficiently.
60. As a root orchestrator, I want delegation depth and cross-domain authority bounded, so that recursive delegation does not create loops or conflicting changes.
61. As a root orchestrator, I want one writer at a time for shared state, so that parallel agents do not corrupt canonical artifacts.
62. As a root orchestrator, I want parent agents to review delegated documentation work, so that delegation does not dilute accountability.
63. As a root orchestrator, I want completed work accompanied by evidence, so that task state reflects verified outcomes rather than claims.
64. As a marketer, I want a full positioning and messaging system, so that product, brand, sales, and launch communication agree.
65. As a marketer, I want channel strategy matched to the founder's budget and capabilities, so that the plan can actually be executed.
66. As a marketer, I want landing-page, email, social, SEO, content, partnership, outbound, and paid-channel decisions considered where relevant, so that distribution is comprehensive but selective.
67. As a marketer, I want campaign briefs and reusable copy assets, so that the launch plan includes executable materials.
68. As a marketer, I want attribution and experiment plans, so that channel performance can be measured and improved.
69. As a product-growth owner, I want acquisition, activation, retention, referral, and revenue loops considered, so that growth is connected to product behavior.
70. As a release manager, I want Conventional Commits and release-please configured, so that versions and changelogs are automated.
71. As a release manager, I want repository and in-application release notes derived from one structured source, so that they cannot drift independently.
72. As a user of the finished product, I want an in-application changelog, so that I can understand what changed between releases.
73. As a plugin user, I want foundry phases to be independently invokable and resumable, so that I can revise one area without replaying the whole workflow.
74. As a plugin user, I want `$product-foundry` to remain the normal planning entry point, so that I do not need to coordinate phase skills manually.
75. As a plugin user, I want `$implement-prd` to remain the normal build entry point, so that implementation begins from a clean context window.
76. As a plugin user, I want implementation artifacts accepted as attachments, files, directories, or a manifest, so that the workflow fits both Codex and Claude Code.
77. As a plugin user, I want attached files read before inferred repository defaults, so that my explicitly supplied direction takes priority.
78. As a plugin user, I want missing or conflicting critical inputs reported before implementation, so that agents do not invent irreversible decisions.
79. As a plugin user, I want fresh implementation mode, so that a newly approved PRD can be built from a known starting state.
80. As a plugin user, I want resume implementation mode, so that an interrupted long-running build can continue without duplicating verified work.
81. As a plugin user, I want automatic resume detection with confirmation, so that existing progress is neither ignored nor overwritten accidentally.
82. As a plugin user, I want explicit fresh and resume overrides, so that I can control ambiguous repository state.
83. As a plugin user, I want completed tasks rechecked only when inputs changed or verification fails, so that resumption is efficient and idempotent.
84. As a plugin user, I want stale ownership and partial work reconciled before new tasks begin, so that resumed execution starts from a trustworthy state.
85. As a plugin user, I want the build orchestrator to delegate most implementation, so that the root context remains available for coordination and review.
86. As a plugin user, I want a 12-16 hour autonomous build session to be feasible, so that a substantial MVP can be completed in one focused run.
87. As a plugin user, I want local, reversible work to proceed autonomously, so that routine implementation does not stall on unnecessary confirmations.
88. As a plugin user, I want approval required for production deployments, paid services, domains, accounts, secrets, destructive data operations, and irreversible external actions, so that automation cannot create unapproved consequences.
89. As a plugin user, I want approval requests to state impact, cost, risk, rollback, and alternatives, so that I can make informed decisions.
90. As a plugin user, I want the same state and completion contract on Codex and Claude Code, so that switching harnesses does not change product intent.
91. As a plugin maintainer, I want dual native plugin manifests, so that the package can be installed and discovered on both platforms.
92. As a plugin maintainer, I want phase references and artifact schemas validated automatically, so that packaging cannot ship broken orchestration links.
93. As a plugin maintainer, I want the plugin registered in the marketplace and release pipeline, so that it versions independently from other plugins.
94. As a plugin maintainer, I want the package accepted by the existing manual-upload packager, so that Claude desktop distribution remains supported.
95. As a plugin maintainer, I want generated artifacts to be deterministic for identical approved inputs where practical, so that drift and debugging are minimized.
96. As a plugin maintainer, I want platform-specific behavior isolated behind a thin adapter, so that workflow rules have one canonical definition.
97. As a plugin user, I want to choose between being interviewed and delegating decisions at the start of every phase, so that I can control how much participation the foundry process requires.
98. As a plugin user, I want interactive questions presented through the native capabilities of my agent harness, so that the workflow feels consistent on Claude Code, Codex, and future compatible platforms.

## Implementation Decisions

- The plugin is a new sibling named `product-foundry`; it does not replace or extend the existing SaaS-specific plugin.
- The plugin is category- and stack-agnostic, with strong defaults for software and SaaS companies when the interview does not establish a better fit.
- The plugin ships native metadata for both Claude Code and Codex and follows the repository's existing marketplace, packaging, changelog, and independent release conventions.
- Two primary skills form the public workflow: `product-foundry` for planning and `implement-prd` for fresh or resumed implementation.
- The foundry orchestrator invokes real, independently resumable phase skills named `foundry-intake`, `foundry-research`, `foundry-company-strategy`, `foundry-mvp`, `foundry-low-fidelity`, `foundry-brand`, `foundry-architecture`, `foundry-agent-harness`, `foundry-prd`, `foundry-high-fidelity`, `foundry-go-to-market`, `foundry-readiness`, and `foundry-handoff`.
- Each phase declares required inputs, deterministic outputs, completion criteria, invalidation rules, and a user approval gate. A phase may return to an earlier phase when new evidence invalidates a decision.
- At the start of every phase, the executing agent asks the user to choose one of two participation modes: `Interview me` or `Decide for me`.
- All questions flow through a platform-neutral interaction adapter. Phase skills describe the question, options, recommendation, and consequences without depending directly on a provider-specific tool name.
- On Claude Code, the interaction adapter uses `AskUserQuestion` for structured choices and interview questions whenever that tool is available.
- On Codex, the interaction adapter uses the native structured user-input tool exposed by the active Codex surface, such as `request_user_input`, whenever available. Because tool availability can vary by Codex client or collaboration mode, the adapter discovers capabilities at runtime rather than assuming the tool always exists.
- On other harnesses, or when no structured input tool is available, the adapter asks one concise plain-text question through the normal user-facing response channel and waits for the answer before continuing. It must not fabricate a response or treat silence as approval for a material decision.
- Structured questions use stable option identifiers, short labels, a clear recommended option when one exists, and concise impact or tradeoff descriptions. The adapter maps the native response back to one platform-independent answer shape consumed by the phase skill.
- `Interview me` uses the phase's complete one-question-at-a-time interview contract and requires the user to resolve material product decisions.
- `Decide for me` allows the executing agent to make the phase's planning decisions using available evidence, project context, industry practices, and the option it would recommend to the user. Each delegated decision records its rationale, evidence, assumptions, confidence, risks, and conditions that would cause it to be revisited.
- Participation mode is selected independently for each phase. A prior choice does not silently opt the user into the same mode for later phases, and the user may switch from delegated decisions to interviewing at any point.
- Delegated decision authority does not override the external-action safety policy. The executing agent still requires explicit user approval for production, paid, legal, account-level, secret-bearing, destructive, or irreversible actions and must stop when a decision cannot be made responsibly from available evidence.
- The foundry interview is relentless but focused: one material question at a time, environment facts discovered through tools where possible, and decisions left to the user.
- Research uses provider-agnostic fan-out. Mechanical collection goes to low-cost agents; synthesis and scoped implementation go to balanced agents; highly capable agents are reserved for ambiguous architecture, security-critical judgment, cross-domain reconciliation, and final quality review. Escalations are recorded.
- `find-skills` is a hard runtime dependency before the orchestrator creates the product-specific agent roster. The roster records responsibilities, required skills, inputs, outputs, tools, ownership, and escalation rules.
- `frontend-design` is a hard runtime dependency for both executable prototype phases. If either mandatory skill is unavailable, the relevant phase fails closed with installation or recovery guidance instead of silently substituting a weaker workflow.
- The default foundry outcome is a planning and design package for a fresh implementation session. In-session implementation remains available only after warning that a fresh context is recommended.
- Canonical generated product state lives under a structured `docs/` hierarchy covering product, company, research, design, architecture, marketing, delivery, releases, agents, and handoffs. Smaller products consolidate artifacts rather than creating empty ceremonial documents.
- `docs/implementation-manifest.json` is the stable machine-readable handoff contract. It indexes canonical artifacts, their status, approved MVP boundaries, unresolved decisions, design references, architecture decisions, quality gates, required skills, harness state, environment constraints, implementation order, and completion criteria without duplicating their content.
- Build-free prototypes live under `docs/prototypes/low-fidelity/` and `docs/prototypes/high-fidelity/`. Each has one canonical current version; Git stores history, while rejected directions and design rationale are recorded in design documentation.
- Both prototype levels use plain HTML, vanilla JavaScript, and the Tailwind CSS v4 browser CDN. They require no package installation, framework, compiler, or build step. They may use linked pages or lightweight client-side routing, local fixtures, and browser-local state.
- The prototype contract permits custom Tailwind components that follow useful shadcn interaction conventions, but it does not claim or depend on a shadcn/ui CDN. Prototype CDN usage does not establish the production stack.
- Low-fidelity prototypes establish information architecture, navigation, workflows, content hierarchy, interaction states, and responsive behavior. High-fidelity prototypes establish the approved visual thesis, realistic content, complete core interactions, design tokens, component conventions, accessibility behavior, motion guidance, and non-happy-path states.
- Prototype code is a reference, not production code. The implementation skill may selectively carry forward validated flows, tokens, components, assets, and interaction decisions after checking them against the PRD and production architecture.
- Recursive `AGENTS.md` and `CLAUDE.md` files may be created at meaningful ownership boundaries. They are concise maps of purpose, entry points, commands, constraints, applicable decisions, documentation responsibilities, and relevant specialist agents; they point to canonical documentation rather than copying it.
- Agents update affected documentation and context maps in the same task as the corresponding implementation. Documentation subagents may be used, but the owning parent agent validates and reconciles their output.
- The default delegation depth is two. Deeper delegation requires a recorded justification. Every task and artifact has an explicit owner, shared state has one writer at a time, parent agents review delegated work, and the root orchestrator approves cross-domain changes.
- The agent harness is interview-selected from Lean, Standard, or Advanced starting levels. Standard is recommended by default, but the executing agent explains tradeoffs and receives the user's decision.
- Lean uses version-controlled context, structured task state, and local commands. Standard adds CI gates, specialist agents, recursive context maps, and automated releases. Advanced adds external tracking, richer orchestration, telemetry, policy enforcement, and long-running delivery controls.
- Tooling such as ESLint, formatters, type checking, schema validation, Husky or Lefthook, unit tests, integration tests, contract tests, end-to-end tests, accessibility tests, visual regression, security scanning, coverage, performance budgets, bundle budgets, and Lighthouse is selected according to the stack and risk. Every tool must protect a concrete quality or operational requirement.
- Structured JSON is the default long-term feature and task state. The user is offered compatible installable task-management alternatives when product duration or team workflow justifies them.
- The default production architecture is a monorepo using pnpm, or Bun when it offers a product-specific advantage. Turborepo is used when compatible. Dockerfiles and Docker Compose are provided for reproducible local development.
- Stack selection remains interview-driven. Any compatible stack is valid. Meaningful deviations from defaults are explained in architecture decision records.
- A modular monolith is the default MVP architecture. Microservices or distributed infrastructure require demonstrated domain, scale, isolation, or operational justification.
- Architecture explicitly decides application and package boundaries, data ownership, database, authentication, authorization, contracts, validation, errors, storage, jobs, notifications, email, payments, analytics, experimentation, observability, secrets, environments, CI/CD, backups, migrations, recovery, privacy, retention, performance, and availability.
- The PRD uses a deterministic comprehensive structure and includes company context, evidence, ICP, competitive landscape, differentiation, MVP and exclusions, user journeys, functional and non-functional requirements, domain model, design direction, architecture, security, privacy, analytics, PMF criteria, pricing, marketing, sales, launch, support, operations, harness, quality gates, deployment, risks, milestones, post-launch learning, conditional roadmap, and releases.
- Requirements have stable identifiers, priority, acceptance criteria, and traceability to evidence or labeled assumptions.
- The marketing suite covers segmentation, positioning, category, messaging, brand narrative, voice, pricing, packaging, channels, launch calendar, landing-page strategy and copy, lifecycle email, social, content, SEO, paid acquisition where relevant, community, partnerships, outbound, sales enablement, product-led growth, referral, retention, campaign briefs, reusable copy, attribution, experiments, budget, and founder constraints.
- MVP governance defines the core hypothesis, riskiest assumptions, validation method, activation event, retention signal, willingness-to-pay or revenue signal, qualitative evidence, experiment duration, decision thresholds, and pivot, persevere, or stop criteria. Roadmap expansion remains conditional on evidence of product-market fit.
- Generated products use Conventional Commits and release-please where compatible. Repository changelogs and in-application release notes derive from one structured source. Release plans include versioning, tags, migration notes, rollback notes, approvals, and verification gates.
- `implement-prd` resolves context in this order: explicit attachments, explicit file and directory arguments, the implementation manifest, recognized canonical documentation, then repository context files.
- `implement-prd` validates that required artifacts exist, are readable, and do not conflict before implementation. Critical missing decisions trigger a focused interview; non-critical gaps are recorded as assumptions within the authority granted by the approved artifacts.
- Fresh mode validates the manifest, creates the roster and task graph, establishes harness state, and begins the approved MVP. Resume mode reconstructs progress from structured task state, handoff state, repository state, verification evidence, and decisions.
- Existing implementation state triggers automatic resume detection and a confirmation summary. Explicit `--fresh` and `--resume` modes resolve ambiguity. Fresh mode must not silently overwrite credible prior state.
- Resume is idempotent: verified tasks are not repeated unless their inputs changed or verification fails. Stale ownership, abandoned tasks, partial changes, conflicting state, and documentation drift are reconciled before new implementation begins.
- Platform-specific details are isolated behind a thin adapter. Claude Code supports slash-command invocation and Claude-native subagent mechanisms; Codex supports skill invocation and Codex-native delegation. Both share the same artifact schemas, task semantics, authority model, quality gates, and completion contract.
- The platform adapter owns skill invocation syntax, structured user prompting, subagent dispatch, approval requests, attachment discovery, and user-facing artifact presentation. Domain phase skills remain provider-agnostic and consume normalized capability and response contracts.
- The implementation session is designed for a token-efficient 12-16 hour run in which the root orchestrator primarily validates, plans, delegates, reconciles, reviews, and maintains state.
- Local and reversible repository work is autonomous, including code, tests, documentation, development tooling, local containers, and development infrastructure.
- Explicit approval is required before production deployment, paid-resource creation, domain or account changes, secret creation or rotation, destructive data operations, or irreversible external actions. Approval requests explain the action, impact, cost or risk, rollback path, and safer alternatives.
- Completion is fail-closed: agents cannot mark a task or build complete when required state updates, documentation, tests, security checks, accessibility checks, design comparison, release readiness, or evidence are missing.

## Testing Decisions

- The highest testing seam is the installable, packaged plugin contract. One validation entry point should exercise the plugin as a consumer sees it: manifests parse, both platforms discover the expected skills, all phase and reference links resolve, templates and schemas are present, generated JSON examples validate, and the package contains no rejected or unsafe paths.
- Tests assert external contracts rather than wording or internal Markdown layout. They verify discoverability, routing declarations, artifact schemas, mode selection, precedence rules, safety gates, and expected generated-file characteristics.
- Existing marketplace validation remains the Claude-side prior art. The existing JSON sanity check, per-plugin validation, manual-upload packaging verification, and independent release-please configuration should be extended to cover the new plugin.
- A Codex-native manifest validation step is added alongside the Claude validation rather than treating successful Claude packaging as proof of Codex compatibility.
- A plugin contract validator checks that the two public entry skills and all thirteen foundry phase skills exist, have valid frontmatter, use unique names, and reference only existing local resources.
- Dependency-contract tests verify that roster creation cannot proceed without `find-skills` and that neither prototype phase can proceed without `frontend-design`.
- Phase-interaction tests verify that every phase presents both participation modes, does not inherit a previous phase's choice silently, permits switching modes, and records the required decision metadata when `Decide for me` is selected.
- Delegated-decision tests verify that recommendation mode can resolve ordinary planning choices but cannot bypass approval requirements or invent unsupported high-consequence decisions.
- Interaction-adapter contract tests run the same phase question through Claude Code, Codex-with-structured-input, and plain-text-fallback fixtures and verify that each produces the same normalized answer without silently selecting an option.
- Fixture-based artifact tests cover a minimal Lean product, a typical Standard monorepo product, and an Advanced or custom-stack product. The same approved fixture inputs must produce structurally equivalent manifests and state contracts across repeated runs wherever generation is deterministic.
- Manifest schema tests cover required fields, artifact indexing, requirement status, unresolved blockers, harness level, implementation ordering, platform-neutral state, and rejection of malformed or conflicting inputs.
- Input-resolution tests verify precedence across attachments, explicit paths, directories, the default manifest, canonical documentation, and repository context maps.
- Fresh-mode tests verify that a clean repository produces a new task graph and harness state, while credible existing state causes a safe stop or explicit override requirement rather than silent replacement.
- Resume-mode tests verify automatic state detection, confirmation summaries, stale-owner recovery, partial-task reconciliation, changed-input invalidation, failed-verification reopening, and preservation of completed verified work.
- Delegation-policy tests verify the default depth limit, justification requirements for deeper delegation, single-writer protection for shared state, parent review evidence, and root approval for cross-domain changes.
- Authority-policy tests verify that reversible local actions are allowed and that production, paid, secret-bearing, destructive, account-level, or irreversible actions produce an approval request containing impact, risk or cost, rollback, and alternatives.
- Prototype contract tests inspect both prototype roots for build-free HTML entry points, Tailwind CSS v4 browser-CDN usage, absence of package or framework build requirements, valid internal links, responsive viewport behavior, keyboard navigation, accessibility violations, console errors, and representative workflow interactions.
- Visual tests capture desktop and mobile screenshots of high-fidelity prototype routes and compare them against approved references with deliberate review thresholds. Tests focus on layout integrity, clipping, overlap, missing assets, responsive behavior, and state coverage rather than fragile pixel identity.
- PRD contract tests verify the presence of required sections, stable requirement identifiers, priorities, acceptance criteria, evidence or assumption links, MVP exclusions, PMF criteria, marketing coverage, architecture decisions, harness decisions, release strategy, and unresolved risks.
- Harness tests verify that selected tools correspond to declared gates, task JSON conforms to schema, recursive context maps link to canonical documents, no duplicate source-of-truth artifacts are introduced, and task completion requires documentation and evidence updates.
- Release tests verify independent plugin version configuration, changelog generation, manifest version synchronization, tag naming, marketplace registration, and successful manual-upload packaging.
- Documentation tests verify that public skill names, invocation examples, fresh and resume behavior, prototype constraints, safety boundaries, and platform compatibility agree with the executable contracts.
- Live-model quality cannot be made byte-deterministic. Evaluation fixtures and rubrics therefore assess observable completeness, traceability, contradiction handling, token discipline, delegation quality, and compliance with approval gates rather than exact prose.

## Out of Scope

- Replacing or migrating the existing SaaS-specific plugin.
- Shipping a universal production application template that predetermines framework, database, cloud provider, authentication provider, billing provider, or deployment platform.
- Treating prototype code as production-ready or automatically copying it into the finished application.
- Providing an unofficial shadcn/ui CDN or requiring shadcn/ui in build-free prototypes.
- Guaranteeing commercial success, product-market fit, awards, a fixed valuation, or a literal development cost equivalent.
- Forming a legal entity, opening financial accounts, purchasing domains, accepting legal terms, or procuring paid infrastructure without explicit user action and approval.
- Performing production deployment or other consequential external actions by default.
- Building post-MVP roadmap features before the approved validation criteria justify them.
- Creating a large fixed agent organization when the product does not need it.
- Enforcing monorepo, pnpm, Bun, Turborepo, Docker, or modular-monolith defaults when they are incompatible with confirmed requirements.
- Publishing this specification to an issue tracker as part of the current request; the requested deliverable is the concrete local specification file first.

## Further Notes

- The normal experience exposes two entry points even though the foundry phases remain directly invokable for advanced revisions and recovery.
- The foundry session and implementation session are intentionally separated so that implementation begins with a fresh context and durable attached artifacts rather than hidden conversation history.
- Premium and award-worthy quality is an evaluation direction, not a promise based on visual decoration. The plugin should require a product-specific design thesis, coherent interaction design, realistic content, complete states, accessibility, responsive execution, and verified implementation fidelity.
- Determinism means stable schemas, ordering, templates, routing, validation, state transitions, and reproducible local scaffolding for identical approved inputs. Research findings, human decisions, and model-authored design or implementation remain variable and must be controlled through evidence, rubrics, and gates.
- The recommended default harness is Standard, the recommended production architecture is a pnpm monorepo with Turborepo when compatible, and the recommended MVP topology is a modular monolith with Docker and Docker Compose. These remain recommendations subject to the user interview.
- The repository's existing release-please and Conventional Commit model should version `product-foundry` independently and maintain its own changelog.
