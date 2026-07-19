/**
 * @{{PRODUCT_SLUG}}/ui
 *
 * This file intentionally does NOT export hand-rolled components. Per
 * README.md, components come from `pnpm dlx shadcn@latest add <name>`
 * generated straight into this package's src/components directory at
 * scaffold time. Once generated, re-export them below, e.g.:
 *
 *   export * from "./components/button";
 *   export * from "./components/card";
 *
 * The one thing this package hand-writes is the `cn` classname helper,
 * because shadcn/ui's generated components import it directly.
 */
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
