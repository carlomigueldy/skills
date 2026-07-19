/**
 * @{{PRODUCT_SLUG}}/schemas
 *
 * THE single source of truth for {{PRODUCT_NAME}} domain shapes. These zod
 * schemas are imported by every app (landing, pwa, mission-control) and by
 * Supabase edge functions / server actions to validate input at every
 * boundary. Do not redefine these shapes locally in an app — extend or
 * compose from here instead.
 */
import { z } from "zod";

// ---------------------------------------------------------------------------
// Tenant
// ---------------------------------------------------------------------------

/**
 * Lifecycle status of a tenant. Enforced both here (app-level validation)
 * and again in Postgres via RLS policies / a check constraint — never trust
 * only one layer.
 */
export const tenantStatusEnum = z.enum([
  "active",
  "suspended",
  "soft_banned",
  "banned",
  "cancelled"
]);
export type TenantStatus = z.infer<typeof tenantStatusEnum>;

export const tenantSchema = z.object({
  id: z.string().uuid(),
  slug: z
    .string()
    .min(2)
    .max(63)
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "must be a lowercase, hyphenated slug"),
  name: z.string().min(1).max(120),
  status: tenantStatusEnum,
  ownerUserId: z.string().uuid(),
  primaryLocale: z.string().min(2).max(10).default("{{PRIMARY_LOCALE}}"),
  contactEmail: z.string().email(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  statusReason: z.string().max(500).nullable().optional()
});
export type Tenant = z.infer<typeof tenantSchema>;

// ---------------------------------------------------------------------------
// Subscription
// ---------------------------------------------------------------------------

export const subscriptionTierEnum = z.enum(["free", "starter", "pro", "enterprise"]);
export type SubscriptionTier = z.infer<typeof subscriptionTierEnum>;

export const subscriptionSchema = z.object({
  id: z.string().uuid(),
  tenantId: z.string().uuid(),
  tier: subscriptionTierEnum,
  isTrial: z.boolean().default(false),
  trialEndsAt: z.string().datetime().nullable().optional(),
  expiresAt: z.string().datetime().nullable(),
  autoRenew: z.boolean().default(false),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime()
});
export type Subscription = z.infer<typeof subscriptionSchema>;

// ---------------------------------------------------------------------------
// Manual payment
// ---------------------------------------------------------------------------

/** Payment rails supported by the manual-payment-ops flow in mission-control. */
export const manualPaymentMethodEnum = z.enum([
  "gcash",
  "maya",
  "gotyme",
  "bank_transfer",
  "paypal",
  "crypto"
]);
export type ManualPaymentMethod = z.infer<typeof manualPaymentMethodEnum>;

export const manualPaymentStatusEnum = z.enum(["pending", "approved", "rejected"]);
export type ManualPaymentStatus = z.infer<typeof manualPaymentStatusEnum>;

export const manualPaymentSchema = z.object({
  id: z.string().uuid(),
  tenantId: z.string().uuid(),
  subscriptionId: z.string().uuid().nullable().optional(),
  method: manualPaymentMethodEnum,
  status: manualPaymentStatusEnum,
  amount: z.number().positive(),
  currency: z.string().length(3).default("PHP"),
  receiptUrl: z.string().url().nullable().optional(),
  note: z.string().max(1000).nullable().optional(),
  submittedAt: z.string().datetime(),
  reviewedAt: z.string().datetime().nullable().optional(),
  reviewedByUserId: z.string().uuid().nullable().optional(),
  rejectionReason: z.string().max(500).nullable().optional()
});
export type ManualPayment = z.infer<typeof manualPaymentSchema>;

// ---------------------------------------------------------------------------
// Audit log
// ---------------------------------------------------------------------------

export const auditLogEntrySchema = z.object({
  id: z.string().uuid(),
  tenantId: z.string().uuid().nullable(),
  actorUserId: z.string().uuid().nullable(),
  action: z.string().min(1).max(120),
  targetType: z.string().min(1).max(60),
  targetId: z.string().max(120).nullable().optional(),
  metadata: z.record(z.string(), z.unknown()).default({}),
  createdAt: z.string().datetime()
});
export type AuditLogEntry = z.infer<typeof auditLogEntrySchema>;
