# Payment Lifecycle — {{PRODUCT_NAME}}

Task id prefix: `payments-`. Covers the FULL manual-payment lifecycle across both the PWA (customer-facing) and Mission Control (admin) — not just the lockout side. Ground truth is the PRD's Product section "FULL payment lifecycle" bullet; this playbook builds the software around a payment rail that is always verified by a human (the founder), never automated. Nothing here ever auto-approves a payment.

Read the PRD's locked pricing tiers, accepted rails for the chosen geography (PH: GCash/Maya/GoTyme/bank transfer; Worldwide: PayPal/crypto as primary + PH rails), trial policy, dunning cadence, grace-period length, and refund/cancellation policy before starting — the specifics below are the shape of the work, the PRD has the numbers.

## Stages

Build and verify each stage as its own `feature_list.json` entry (or several, if the PRD's breakdown is finer-grained). Do not start the next stage's `in_progress` entry until the current one is `passing` or explicitly `blocked`.

### 1. Activation

- Customer-facing "how to pay" screen listing the accepted rails for this tenant's geography, with a reference-number/receipt-upload field and a clear "submitted — pending verification" state.
- Mission Control payment intake queue: pending payments listed with tenant, amount, rail, reference, and note field; approve/reject actions.
- On approve: record the receipt, set the subscription period from the PRD's pricing tier, transition the tenant per `tenant-lifecycle.md`.
- On reject: tenant stays gated; customer sees the rejection reason.
- Verify: Playwright walkthrough of submit → admin approve → customer sees active state, and submit → admin reject → customer sees the reason. Confirm via RLS that a customer cannot see another tenant's payment records.

### 2. Trial

- PRD's trial length and feature gating during trial.
- PWA: trial countdown/status UI, no payment prompt until the trial nears its end.
- Mission Control: view trial tenants, force-convert or extend a trial (the DEFAULT stack's "comps/trials" power).
- Verify: trial-to-active and trial-to-expired transitions both render correctly; Mission Control extend action changes the countdown.

### 3. Renewal reminders + dunning cadence

- PRD's cadence (N days before expiry, in-app + Messenger/email nudges).
- In-app reminder banner that escalates in urgency as expiry approaches; outbound nudge (email/Messenger) if that channel is wired for this product — if not wired yet, file it as an owner-ledger item, don't silently skip the in-app half.
- Mission Control renewal-reminder oversight view: which tenants are in the reminder window, last nudge sent.
- Verify: reminder logic fires at the correct day-offsets against fixture dates (Vitest); banner renders at each offset (Playwright).

### 4. Grace period

- Post-expiry grace window from the PRD — a state distinct from both active and locked: reduced functionality, persistent payment CTA.
- PWA: grace-period banner + restricted actions. Mission Control: view tenants in grace, manual override to extend.
- Verify: crossing from active → grace at expiry, and grace → locked at grace-window end, both render the correct restricted state.

### 5. Expiry / lockout

- Hard lockout after the grace window ends. This MUST be enforced server-side (RLS/tenant-status policy) — hiding it in the UI alone is not sufficient and fails the Definition of Done's RLS non-negotiable.
- PWA: locked-out screen with a payment CTA back to Activation. Mission Control: force-expire action (DEFAULT stack power).
- Verify: attempt an authenticated request as a locked-out tenant and confirm the server denies it (RLS test), not just that the UI hides the option.

### 6. Refund / cancellation

- PRD's refund/cancellation policy. Since there's no automated billing to reverse, route this through Mission Control (admin records the refund/cancel with reason + amount) unless the PRD explicitly asks for a customer-initiated request flow — check before assuming.
- On cancel: tenant transitions to `cancelled` per `tenant-lifecycle.md`.
- Verify: Mission Control refund/cancel action produces a payment-history entry and the correct tenant-status transition.

### 7. Dispute handling

- PRD's dispute runbook, including PayPal chargebacks and the personal-account freeze mitigation if the product is Worldwide.
- Mission Control dispute log: tenant, rail, amount, status, resolution notes. Disputes on manual rails resolve outside the app (bank/PayPal dispute centers) — the app's job is to record status and let the founder lock the tenant pending investigation, not to adjudicate.
- Verify: logging a dispute is visible in the tenant's history; the founder's lock action from the dispute log actually transitions tenant status.

### 8. Customer-facing receipts

- Every approved payment generates a receipt viewable/downloadable in the PWA, meeting whatever the PRD's Legal & compliance section requires (pre-DTI vs BIR-registered receipt format differs — don't assume one).
- Manual receipt notes (the admin's free-text note on a payment) default to admin-only visibility in Mission Control's payment history — confirm against the PRD if it says otherwise before exposing notes to the customer.
- Verify: a receipt is generated and downloadable immediately after admin approval; receipt content matches the PRD's required fields.

## Verify + track (every stage)

- Verification loop: Playwright (the MCP tool if the agent has one, otherwise the project's own Playwright test run) walking the full PWA + Mission Control round-trip for that stage, plus Vitest for the underlying logic (dunning-cadence math, RLS policy behavior where it can be exercised without a live browser).
- AGENTS.md's Definition of Done must be fully satisfied before a stage's entry moves to `passing` — no partial credit for "mostly works."
- Update the corresponding `payments-NN` entry in `feature_list.json`: `verification` names what proved it, `evidence` is the actual run output/artifact reference, `notes` carries anything the next reader (qa-verifier, code-reviewer, or the founder) needs to know.
- If a stage depends on something not yet configured (a messaging provider, a legal receipt format not yet decided), mark it `blocked` with notes naming the exact owner-ledger item that unblocks it — never fudge `passing` to move on.
